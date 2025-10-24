"""
Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import annotations

import copy
import logging
import math
import os
import random
from collections import defaultdict
from contextlib import nullcontext
from functools import wraps
from typing import TYPE_CHECKING, Protocol, Sequence

import hydra
import numpy as np
import torch
import torch.distributed as dist
from monty.dev import requires
from torch.distributed.elastic.utils.distributed import get_free_port
from torchtnt.framework import PredictUnit, State

from fairchem.core.common import gp_utils
from fairchem.core.common.distutils import (
    CURRENT_DEVICE_TYPE_STR,
    assign_device_for_local_rank,
    get_device_for_local_rank,
    setup_env_local_multi_gpu,
)
from fairchem.core.datasets.atomic_data import AtomicData
from fairchem.core.units.mlip_unit import InferenceSettings
from fairchem.core.units.mlip_unit.utils import (
    load_inference_model,
    tf32_context_manager,
)

if TYPE_CHECKING:
    from fairchem.core.units.mlip_unit.mlip_unit import Task

try:
    import ray
    from ray import remote
    from ray.util.scheduling_strategies import PlacementGroupSchedulingStrategy

    ray_installed = True
except ImportError:
    ray = None

    def remote(cls):
        # dummy
        return cls

    ray_installed = False


def collate_predictions(predict_fn):
    @wraps(predict_fn)
    def collated_predict(
        predict_unit, data: AtomicData, undo_element_references: bool = True
    ):
        # Get the full prediction dictionary from the original predict method
        preds = predict_fn(predict_unit, data, undo_element_references)
        collated_preds = defaultdict(list)
        for i, dataset in enumerate(data.dataset):
            for task in predict_unit.dataset_to_tasks[dataset]:
                if task.level == "system":
                    collated_preds[task.property].append(
                        preds[task.name][i].unsqueeze(0)
                    )
                elif task.level == "atom":
                    collated_preds[task.property].append(
                        preds[task.name][data.batch == i]
                    )
                else:
                    raise RuntimeError(
                        f"Unrecognized task level={task.level} found in data batch at position {i}"
                    )

        return {prop: torch.cat(val) for prop, val in collated_preds.items()}

    return collated_predict


class MLIPPredictUnitProtocol(Protocol):
    def predict(self, data: AtomicData, undo_element_references: bool) -> dict: ...

    @property
    def dataset_to_tasks(self) -> dict[str, list]: ...


class MLIPPredictUnit(PredictUnit[AtomicData], MLIPPredictUnitProtocol):
    def __init__(
        self,
        inference_model_path: str,
        device: str = "cpu",
        overrides: dict | None = None,
        inference_settings: InferenceSettings | None = None,
        seed: int = 41,
        atom_refs: dict | None = None,
        assert_on_nans: bool = False,
    ):
        super().__init__()
        os.environ[CURRENT_DEVICE_TYPE_STR] = device

        self.set_seed(seed)
        # note these are different from the element references used for model training
        self.atom_refs = (
            {task.replace("_elem_refs", ""): refs for task, refs in atom_refs.items()}
            if atom_refs is not None
            else {}
        )

        if inference_settings is None:
            inference_settings = InferenceSettings()
        if inference_settings.torch_num_threads is not None:
            torch.set_num_threads(inference_settings.torch_num_threads)
            torch.set_num_interop_threads(inference_settings.torch_num_threads)

        if overrides is None:
            overrides = {}
        if "backbone" not in overrides:
            overrides["backbone"] = {}
        # always disable always_use_pbc for inference
        overrides["backbone"]["always_use_pbc"] = False
        if inference_settings.activation_checkpointing is not None:
            overrides["backbone"]["activation_checkpointing"] = (
                inference_settings.activation_checkpointing
            )
        if inference_settings.external_graph_gen is not None:
            overrides["backbone"][
                "otf_graph"
            ] = not inference_settings.external_graph_gen

        if inference_settings.internal_graph_gen_version is not None:
            overrides["backbone"]["radius_pbc_version"] = (
                inference_settings.internal_graph_gen_version
            )

        if inference_settings.wigner_cuda:
            logging.warning(
                "The wigner_cuda flag is deprecated and will be removed in future versions."
            )

        self.model, checkpoint = load_inference_model(
            inference_model_path, use_ema=True, overrides=overrides
        )
        tasks = [
            hydra.utils.instantiate(task_config)
            for task_config in checkpoint.tasks_config
        ]
        self.tasks = {t.name: t for t in tasks}

        self._dataset_to_tasks = get_dataset_to_tasks_map(self.tasks.values())
        assert set(self._dataset_to_tasks.keys()).issubset(
            set(self.model.module.backbone.dataset_list)
        ), "Datasets in tasks is not a strict subset of datasets in backbone."
        assert device in ["cpu", "cuda"], "device must be either 'cpu' or 'cuda'"

        self.device = get_device_for_local_rank() if device == "cuda" else "cpu"

        self.model.eval()

        self.lazy_model_intialized = False
        self.inference_mode = inference_settings

        # store composition embedding of system the model was merged on
        self.merged_on = None

        self.assert_on_nans = assert_on_nans

        if self.direct_forces:
            logging.warning(
                "This is a direct-force model. Direct force predictions may lead to discontinuities in the potential "
                "energy surface and energy conservation errors."
            )

    @property
    def direct_forces(self) -> bool:
        return self.model.module.backbone.direct_forces

    @property
    def dataset_to_tasks(self) -> dict[str, list]:
        return self._dataset_to_tasks

    def set_seed(self, seed: int):
        logging.debug(f"Setting random seed to {seed}")
        self._seed = seed
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    def move_to_device(self):
        self.model.to(self.device)
        for task in self.tasks.values():
            task.normalizer.to(self.device)
            if task.element_references is not None:
                task.element_references.to(self.device)

    def predict_step(self, state: State, data: AtomicData) -> dict[str, torch.tensor]:
        return self.predict(data)

    def get_composition_charge_spin_dataset(self, data):
        composition_sum = data.atomic_numbers.new_zeros(
            self.model.module.backbone.max_num_elements,
            dtype=torch.int,
        ).index_add(
            0,
            data.atomic_numbers.to(torch.int),
            data.atomic_numbers.new_ones(data.atomic_numbers.shape[0], dtype=torch.int),
        )
        comp_charge_spin = (
            composition_sum,
            getattr(data, "charge", None),
            getattr(data, "spin", None),
        )
        return comp_charge_spin, getattr(data, "dataset", [None])

    @collate_predictions
    def predict(
        self, data: AtomicData, undo_element_references: bool = True
    ) -> dict[str, torch.tensor]:
        if not self.lazy_model_intialized:
            # merge everything on CPU
            if self.inference_mode.merge_mole:
                # replace backbone with non MOE version
                assert (
                    data.natoms.numel() == 1
                ), f"Cannot merge model with multiple systems in batch. Must be exactly 1 system, found {data.natoms.numel()}"
                self.model.module.backbone = (
                    self.model.module.backbone.merge_MOLE_model(data.clone())
                )
                self.model.eval()
            # move to device
            self.move_to_device()
            if self.inference_mode.compile:
                logging.warning(
                    "Model is being compiled this might take a while for the first time"
                )
                self.model = torch.compile(self.model, dynamic=True)
            self.lazy_model_intialized = True

        if self.inference_mode.external_graph_gen and data.edge_index.shape[1] == 0:
            raise ValueError(
                "Cannot run inference with external graph generation on empty edge index. "
                "Please ensure the input data has valid edges."
            )

        # this needs to be .clone() to avoid issues with graph parallel modifying this data with MOLE
        data_device = data.to(self.device).clone()

        if self.inference_mode.merge_mole:
            if self.merged_on is None:
                # only get embeddings after moved to final device to get right types
                self.merged_on = self.get_composition_charge_spin_dataset(data_device)
            else:
                this_sys = self.get_composition_charge_spin_dataset(data_device)
                assert (
                    data_device.natoms.numel() == 1
                ), f"Cannot run merged model on batch with multiple systems. Must be exactly 1 system, found {data_device.natoms.numel()}"
                assert (
                    self.merged_on[0][0].isclose(this_sys[0][0], rtol=1e-5).all()
                ), "Cannot run on merged model on system. Embeddings seem different..."
                assert (
                    self.merged_on[0][1] == this_sys[0][1]
                ), f"Cannot run on merged model on system. Charge is diferrent {self.merged_on[0][1]} vs {this_sys[0][1]}"
                assert (
                    self.merged_on[0][2] == this_sys[0][2]
                ), f"Cannot run on merged model on system. Spin is diferrent {self.merged_on[0][2]} vs {this_sys[0][2]}"
                assert (
                    self.merged_on[1] == this_sys[1]
                ), f"Cannot run on merged model on system. Dataset is diferrent {self.merged_on[1]} vs {this_sys[1]}"

        inference_context = torch.no_grad() if self.direct_forces else nullcontext()
        tf32_context = (
            tf32_context_manager() if self.inference_mode.tf32 else nullcontext()
        )

        pred_output = {}
        with inference_context, tf32_context:
            output = self.model(data_device)
            for task_name, task in self.tasks.items():
                pred_output[task_name] = task.normalizer.denorm(
                    output[task_name][task.property]
                )
                if self.assert_on_nans:
                    assert torch.isfinite(
                        pred_output[task_name]
                    ).all(), f"NaNs/Infs found in prediction for task {task_name}.{task.property}"
                if undo_element_references and task.element_references is not None:
                    pred_output[task_name] = task.element_references.undo_refs(
                        data_device, pred_output[task_name]
                    )

        return pred_output


def get_dataset_to_tasks_map(tasks: Sequence[Task]) -> dict[str, list[Task]]:
    """Create a mapping from dataset names to their associated tasks.

    Args:
        tasks: A sequence of Task objects to be organized by dataset

    Returns:
        A dictionary mapping dataset names (str) to lists of Task objects
        that are associated with that dataset
    """
    dset_to_tasks_map = defaultdict(list)
    for task in tasks:
        for dataset_name in task.datasets:
            dset_to_tasks_map[dataset_name].append(task)
    return dict(dset_to_tasks_map)


def move_tensors_to_cpu(data):
    """
    Recursively move all PyTorch tensors in a nested data structure to CPU.

    Args:
        data: Input data structure (dict, list, tuple, tensor, or other)

    Returns:
        Data structure with all tensors moved to CPU
    """
    if isinstance(data, torch.Tensor):
        return data.cpu()
    elif isinstance(data, dict):
        return {key: move_tensors_to_cpu(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [move_tensors_to_cpu(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(move_tensors_to_cpu(item) for item in data)
    else:
        # Return as-is for non-tensor types (str, int, float, etc.)
        return data


@remote
class MLIPWorker:
    def __init__(
        self,
        worker_id: int,
        world_size: int,
        predictor_config: dict,
        master_port: int | None = None,
        master_address: str | None = None,
    ):
        if ray_installed is False:
            raise RuntimeError("Requires `ray` to be installed")

        self.worker_id = worker_id
        self.world_size = world_size
        self.predictor_config = predictor_config
        self.master_address = (
            ray.util.get_node_ip_address() if master_address is None else master_address
        )
        self.master_port = get_free_port() if master_port is None else master_port
        self.is_setup = False

    def get_master_address_and_port(self):
        return (self.master_address, self.master_port)

    def _distributed_setup(
        self,
        worker_id: int,
        master_port: int,
        world_size: int,
        predictor_config: dict,
        master_address: str,
    ):
        # initialize distributed environment
        # TODO, this wont work for multi-node, need to fix master addr
        logging.info(f"Initializing worker {worker_id}...")
        setup_env_local_multi_gpu(worker_id, master_port, master_address)
        # local_rank = int(os.environ["LOCAL_RANK"])
        device = predictor_config.get("device", "cpu")
        assign_device_for_local_rank(device == "cpu", 0)
        backend = "gloo" if device == "cpu" else "nccl"
        dist.init_process_group(
            backend=backend,
            rank=worker_id,
            world_size=world_size,
        )
        gp_utils.setup_graph_parallel_groups(world_size, backend)
        self.predict_unit = hydra.utils.instantiate(predictor_config)
        logging.info(
            f"Worker {worker_id}, gpu_id: {ray.get_gpu_ids()}, loaded predict unit: {self.predict_unit}, "
            f"on port {self.master_port}, with device: {get_device_for_local_rank()}, config: {self.predictor_config}"
        )

    def predict(self, data: AtomicData) -> dict[str, torch.tensor] | None:
        if not self.is_setup:
            self._distributed_setup(
                self.worker_id,
                self.master_port,
                self.world_size,
                self.predictor_config,
                self.master_address,
            )
            self.is_setup = True
        out = self.predict_unit.predict(data)
        out = move_tensors_to_cpu(out)
        if self.worker_id == 0:
            return out
        else:
            return None


@requires(ray_installed, message="Requires `ray` to be installed")
class ParallelMLIPPredictUnit(MLIPPredictUnitProtocol):
    def __init__(
        self,
        inference_model_path: str,
        device: str = "cpu",
        overrides: dict | None = None,
        inference_settings: InferenceSettings | None = None,
        seed: int = 41,
        atom_refs: dict | None = None,
        assert_on_nans: bool = False,
        num_workers: int = 1,
        num_workers_per_node: int = 8,
    ):
        super().__init__()
        _mlip_pred_unit = MLIPPredictUnit(
            inference_model_path=inference_model_path,
            device="cpu",
            overrides=overrides,
            inference_settings=inference_settings,
            seed=seed,
            atom_refs=atom_refs,
        )
        self._dataset_to_tasks = copy.deepcopy(_mlip_pred_unit.dataset_to_tasks)

        predict_unit_config = {
            "_target_": "fairchem.core.units.mlip_unit.predict.MLIPPredictUnit",
            "inference_model_path": inference_model_path,
            "device": device,
            "overrides": overrides,
            "inference_settings": inference_settings,
            "seed": seed,
            "atom_refs": atom_refs,
            "assert_on_nans": assert_on_nans,
        }
        if not ray.is_initialized():
            ray.init(
                logging_level=logging.INFO,
                # runtime_env={
                #     "env_vars": {"RAY_DEBUG": "1"},
                # },
            )

        num_nodes = math.ceil(num_workers / num_workers_per_node)
        num_workers_on_node_array = [num_workers_per_node] * num_nodes
        if num_workers % num_workers_per_node > 0:
            num_workers_on_node_array[-1] = num_workers % num_workers_per_node
        logging.info(
            f"Creating placement groups with {num_workers_on_node_array} workers on {device}"
        )

        # first create one placement group for each node
        num_gpu_per_worker = 1 if device == "cuda" else 0
        placement_groups = []
        for workers in num_workers_on_node_array:
            bundle = {"CPU": workers}
            if device == "cuda":
                bundle["GPU"] = workers
            pg = ray.util.placement_group([bundle], strategy="STRICT_PACK")
            placement_groups.append(pg)
        ray.get(pg.ready())  # Wait for each placement group to be scheduled

        # place rank 0 on placement group 0
        rank0_worker = MLIPWorker.options(
            num_gpus=num_gpu_per_worker,
            scheduling_strategy=PlacementGroupSchedulingStrategy(
                placement_group=placement_groups[0],
                placement_group_bundle_index=0,  # Use the first (and only) bundle in the PG
                placement_group_capture_child_tasks=True,  # Ensure child tasks also run in this PG
            ),
        ).remote(0, num_workers, predict_unit_config)
        master_addr, master_port = ray.get(
            rank0_worker.get_master_address_and_port.remote()
        )
        logging.info(f"Started rank0 on {master_addr}:{master_port}")
        self.workers = [rank0_worker]

        # next place all ranks in order and pack them on placement groups
        # ie: rank0-7 -> placement group 0, 8->15 -> placement group 1 etc.
        worker_id = 0
        for pg_idx, pg in enumerate(placement_groups):
            workers = num_workers_on_node_array[pg_idx]
            logging.info(
                f"Launching workers for placement group {pg_idx} (Node {pg_idx}), workers={workers}"
            )

            for i in range(workers):
                # skip the first one because it's already been initialized above
                if pg_idx == 0 and i == 0:
                    worker_id += 1
                    continue
                # Each actor requests 1 worker worth of resources and uses the specific placement group
                actor = MLIPWorker.options(
                    num_gpus=num_gpu_per_worker,
                    scheduling_strategy=PlacementGroupSchedulingStrategy(
                        placement_group=pg,
                        placement_group_bundle_index=0,  # Use the first (and only) bundle in the PG
                        placement_group_capture_child_tasks=True,  # Ensure child tasks also run in this PG
                    ),
                ).remote(
                    worker_id,
                    num_workers,
                    predict_unit_config,
                    master_port,
                    master_addr,
                )
                self.workers.append(actor)
                worker_id += 1

    def predict(
        self, data: AtomicData, undo_element_references: bool = True
    ) -> dict[str, torch.tensor]:
        # put the reference in the object store only once
        # this data transfer should be made more efficienct by using a shared memory transfer + nccl broadcast
        data_ref = ray.put(data)
        futures = [w.predict.remote(data_ref) for w in self.workers]
        # just get the first result that is ready since they are identical
        # the rest of the futures should go out of scope and memory garbage collected
        # ready_ids, _ = ray.wait(futures, num_returns=1)
        # result = ray.get(ready_ids[0])
        # result = ray.get(futures)
        # return result[0]
        return ray.get(futures[0])

    @property
    def dataset_to_tasks(self) -> dict[str, list]:
        return self._dataset_to_tasks
