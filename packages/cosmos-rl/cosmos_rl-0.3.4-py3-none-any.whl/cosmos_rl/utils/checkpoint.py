# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import boto3
import os
import re
import json
import heapq
import torch
import random
import shutil
import numpy as np
import concurrent.futures as futures
from botocore.exceptions import ClientError
from botocore.config import Config as BotoConfig
from cosmos_rl.utils.util import is_master_rank
from cosmos_rl.utils.logging import logger
from cosmos_rl.utils.parallelism import ParallelDims
from cosmos_rl.policy.config import Config as CosmosConfig
from typing import List, Callable, Union


def upload_file_to_s3(
    local_file_path: str,
    bucket_name: str,
    s3_file_path: str,
    max_retries: int = 3,
):
    config = BotoConfig(retries={"max_attempts": 10, "mode": "standard"})
    s3_client = boto3.client("s3", config=config)
    retry = 0
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError:
        logger.info(f"Bucket {bucket_name} does not exist, creating it now.")
        s3_client.create_bucket(Bucket=bucket_name)
    while retry < max_retries:
        try:
            s3_client.upload_file(local_file_path, bucket_name, s3_file_path)
            logger.info(
                f"Uploaded {local_file_path} to s3://{bucket_name}/{s3_file_path}"
            )
            return
        except ClientError as e:
            retry += 1
            logger.error(
                f"Failed to upload {local_file_path} to s3://{bucket_name}/{s3_file_path}. "
                f"Retry {retry}/{max_retries}. Error: {e}"
            )
    logger.error(
        f"Failed to upload {local_file_path} to s3://{bucket_name}/{s3_file_path} "
        f"after {max_retries} retries."
    )


def upload_folder_to_s3(
    local_folder: str,
    bucket_name: str,
    s3_folder: str,
    max_retries: int = 3,
):
    for root, _, files in os.walk(local_folder):
        for file in files:
            local_file_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_file_path, local_folder)
            s3_file_path = os.path.join(s3_folder, relative_path)
            upload_file_to_s3(
                local_file_path, bucket_name, s3_file_path, max_retries=max_retries
            )


class CheckpointMananger:
    def __init__(
        self,
        config: CosmosConfig,
        parallel_dims: ParallelDims = None,
        global_rank: int = 0,
        metric: str = "val_loss",
    ):
        self.config = config
        self.parallel_dims = parallel_dims
        self.global_rank = global_rank
        self.max_keep = config.train.ckpt.max_keep
        self.metric = metric
        self.save_mode = config.train.ckpt.save_mode
        self.ckpt_output_dir = os.path.join(config.train.output_dir, "checkpoints")
        if self.config.train.ckpt.upload_s3:
            self.ckpt_s3_output_dir = os.path.join(
                config.train.ckpt.s3_prefix, "checkpoints"
            )
        if self.config.train.ckpt.enable_checkpoint:
            if not os.path.exists(self.ckpt_output_dir):
                os.makedirs(self.ckpt_output_dir, exist_ok=True)
            if self.save_mode == "async":
                self.executor = futures.ThreadPoolExecutor(max_workers=4)
        self.pre_save_futures = []
        self.saved_steps = []
        self.best_score = float("inf") if "loss" in metric else -float("inf")

    @staticmethod
    def ckpt_path_check(ckpt_path: str):
        return os.path.exists(os.path.join(ckpt_path, "cosmos_config"))

    def get_ckpt_path(self) -> List[str]:
        def digit_ascending_key(name: str):
            # grab the last integer found in the folder name; put non-numeric names at the end (sorted by name)
            nums = re.findall(r"\d+", name)
            return (1, name) if not nums else (0, int(nums[-1]))

        # find the latest checkpoint under output_dir
        if self.config.train.resume == True:  # noqa: E712
            root_output_dir = os.path.dirname(os.path.dirname(self.ckpt_output_dir))
            cur_timestamp = os.path.basename(os.path.dirname(self.ckpt_output_dir))
            timestamps = os.listdir(root_output_dir)
            timestamps.sort()
            for timestamp in reversed(timestamps):
                if timestamp < cur_timestamp:
                    break
            steps = os.listdir(os.path.join(root_output_dir, timestamp, "checkpoints"))
            steps = sorted(steps, key=digit_ascending_key)
            return [
                os.path.join(root_output_dir, timestamp, "checkpoints", step, "policy")
                for step in reversed(steps)
            ]
        else:
            return [self.config.train.resume]

    @staticmethod
    def get_rng_state():
        return {
            "torch": torch.get_rng_state(),
            "cuda": torch.cuda.get_rng_state(),
            "numpy": np.random.get_state(),
            "python": random.getstate(),
        }

    @staticmethod
    def set_rng_state(rng_state):
        torch.set_rng_state(rng_state["torch"])
        torch.cuda.set_rng_state(rng_state["cuda"])
        np.random.set_state(rng_state["numpy"])
        random.setstate(rng_state["python"])

    @staticmethod
    def load_extra_info(extra_info_path: str):
        if os.path.exists(extra_info_path):
            with open(extra_info_path, "rb") as f:
                extra_info = torch.load(f, weights_only=False)
            return extra_info
        else:
            logger.warning(f"Extra info file {extra_info_path} does not exist.")
            return {}

    def offload_state_dict_cpu(self, state_dict: dict):
        state_dict_cpu = {}
        for key, value in state_dict.items():
            if isinstance(value, torch.Tensor):
                state_dict_cpu[key] = value.cpu()
            else:
                state_dict_cpu[key] = value
        return state_dict

    def save_checkpoint(
        self,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        scheduler: torch.optim.lr_scheduler._LRScheduler,
        step: int,
        total_steps: int,
        **kwargs,
    ):
        """
        Save the model, optimizer, scheduler state dicts and extra info to disk.
        Also upload the checkpoint to S3 if configured.
        Args:
            model (torch.nn.Module): The model to save.
            optimizer (torch.optim.Optimizer): The optimizer to save.
            scheduler (torch.optim.lr_scheduler._LRScheduler): The scheduler to save.
            step (int): The current training step.
            **kwargs: Additional information to save, e.g., is_final.
        """

        def _save_upload(state_dict, local_rel_path, is_final=False):
            local_abs_path = os.path.join(self.ckpt_output_dir, local_rel_path)
            torch.save(state_dict, local_abs_path)
            if self.config.train.ckpt.upload_s3:
                if (self.config.train.ckpt.upload_s3 == "final" and is_final) or (
                    self.config.train.ckpt.upload_s3 == "all"
                ):
                    s3_path = os.path.join(self.ckpt_s3_output_dir, local_rel_path)
                    upload_file_to_s3(
                        local_file_path=local_abs_path,
                        bucket_name=self.config.train.ckpt.s3_bucket,
                        s3_file_path=s3_path,
                    )

        is_final = kwargs.get("is_final", False)
        cur_step_ckpt_dir = os.path.join(f"step_{step}", "policy")
        os.makedirs(
            os.path.join(self.ckpt_output_dir, cur_step_ckpt_dir), exist_ok=True
        )

        # construct the extra info dict
        with open(
            os.path.join(self.ckpt_output_dir, cur_step_ckpt_dir, "cosmos_config"), "w"
        ) as f:
            f.write(json.dumps(self.config.model_dump(), indent=4))
        extra_info = {
            "rng_state": self.get_rng_state(),
            "step": step,
            "total_steps": total_steps,
        }
        for key, value in kwargs.items():
            if key in extra_info:
                extra_info[key] = value
            else:
                extra_info[key] = value

        # paths for saving the state dicts
        model_ckpt_path = os.path.join(
            cur_step_ckpt_dir, f"model_rank_{self.global_rank}.pth"
        )
        optimizer_ckpt_path = os.path.join(
            cur_step_ckpt_dir, f"optimizer_rank_{self.global_rank}.pth"
        )
        scheduler_ckpt_path = os.path.join(
            cur_step_ckpt_dir, f"scheduler_rank_{self.global_rank}.pth"
        )
        extra_info_ckpt_path = os.path.join(
            cur_step_ckpt_dir, f"extra_info_rank_{self.global_rank}.pth"
        )

        if self.save_mode == "async":
            # wait for the previous save to finish
            if len(self.pre_save_futures) > 0:
                for future in futures.as_completed(self.pre_save_futures):
                    future.result()
                self.pre_save_futures = []

            # offload the state dict to CPU
            model_state_dict_cpu = self.offload_state_dict_cpu(model.state_dict())
            optimizer_state_dict_cpu = self.offload_state_dict_cpu(
                optimizer.state_dict()
            )
            scheduler_state_dict_cpu = self.offload_state_dict_cpu(
                scheduler.state_dict()
            )
            extra_info_state_dict_cpu = self.offload_state_dict_cpu(extra_info)

            # save the state dicts to disk
            self.pre_save_futures.append(
                self.executor.submit(
                    _save_upload, model_state_dict_cpu, model_ckpt_path, is_final
                )
            )
            self.pre_save_futures.append(
                self.executor.submit(
                    _save_upload,
                    optimizer_state_dict_cpu,
                    optimizer_ckpt_path,
                    is_final,
                )
            )
            self.pre_save_futures.append(
                self.executor.submit(
                    _save_upload,
                    scheduler_state_dict_cpu,
                    scheduler_ckpt_path,
                    is_final,
                )
            )
            self.pre_save_futures.append(
                self.executor.submit(
                    _save_upload,
                    extra_info_state_dict_cpu,
                    extra_info_ckpt_path,
                    is_final,
                )
            )
            if is_final:
                # wait for all futures to complete before returning for final save
                futures.wait(self.pre_save_futures)
                self.pre_save_futures = []
        else:  # sync
            _save_upload(model.state_dict(), model_ckpt_path, is_final)
            _save_upload(optimizer.state_dict(), optimizer_ckpt_path, is_final)
            _save_upload(scheduler.state_dict(), scheduler_ckpt_path, is_final)
            _save_upload(extra_info, extra_info_ckpt_path, is_final)

        logger.info(
            f"[Policy] Step: {step}, checkpoint saved successfully at {os.path.join(self.ckpt_output_dir, cur_step_ckpt_dir)}."
        )

    def load_checkpoint(
        self,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        scheduler: Union[torch.optim.lr_scheduler._LRScheduler, Callable],
    ):
        extra_vars = {}
        base_paths: List[str] = self.get_ckpt_path()
        # check whether checkpoint existing
        for base_path in base_paths:
            try:
                logger.info(f"Trying to load checkpoint from {base_path}...")
                if self.ckpt_path_check(base_path):
                    logger.info(
                        f"Cosmos checkpoint found at {self.config.train.resume}. Resuming..."
                    )
                    model_path = os.path.join(
                        base_path, f"model_rank_{self.global_rank}.pth"
                    )
                    optimizer_path = os.path.join(
                        base_path, f"optimizer_rank_{self.global_rank}.pth"
                    )
                    scheduler_path = os.path.join(
                        base_path, f"scheduler_rank_{self.global_rank}.pth"
                    )
                    extra_info_path = os.path.join(
                        base_path, f"extra_info_rank_{self.global_rank}.pth"
                    )
                    extra_info = self.load_extra_info(extra_info_path)
                    for key in extra_info:
                        if key == "rng_state":
                            self.set_rng_state(extra_info["rng_state"])
                        else:
                            extra_vars[key] = extra_info[key]

                    outputs = [extra_vars]
                    # Create a new scheduler upon ``training_steps``
                    if isinstance(scheduler, Callable):
                        scheduler = scheduler(training_steps=extra_vars["total_steps"])
                        outputs.append(scheduler)

                    model.load_state_dict(torch.load(model_path, weights_only=False))
                    optimizer.load_state_dict(
                        torch.load(optimizer_path, weights_only=False)
                    )
                    scheduler.load_state_dict(
                        torch.load(scheduler_path, weights_only=False)
                    )
                    logger.info(
                        f"[Policy] Checkpoint loaded successfully from {base_path}."
                    )
                    return outputs[0] if len(outputs) == 1 else outputs
            except Exception as e:
                logger.error(
                    f"Error loading checkpoint from {base_path}: {e}, try next checkpoint..."
                )

        raise FileNotFoundError(f"No checkpoint found at {base_paths}")

    def load_extra_info_from_checkpoint(self):
        extra_vars = {}
        base_paths = self.get_ckpt_path()
        # check whether checkpoint existing

        for base_path in base_paths:
            try:
                is_ckpt_path = self.ckpt_path_check(base_path)
                if is_ckpt_path:
                    logger.info(
                        f"Cosmos checkpoint found at {self.config.train.resume}. Loading extra info..."
                    )
                    extra_info_path = os.path.join(
                        base_path, f"extra_info_rank_{self.global_rank}.pth"
                    )
                    extra_info = self.load_extra_info(extra_info_path)
                    for key in extra_info:
                        if key == "rng_state":
                            self.set_rng_state(extra_info["rng_state"])
                        else:
                            extra_vars[key] = extra_info[key]
                    logger.info(
                        f"[Policy] Checkpoint extra info loaded successfully from {base_path}."
                    )
                    return extra_vars
                else:
                    raise FileNotFoundError(f"No checkpoint found at {base_path}")
            except Exception as e:
                logger.error(
                    f"Error loading checkpoint from {base_path}: {e}, try next checkpoint..."
                )

        raise FileNotFoundError(f"No checkpoint found at {base_paths}")

    def save_check(self, step: int, **kwargs):
        if is_master_rank(self.parallel_dims, self.global_rank):
            heapq.heappush(self.saved_steps, step)
            # remove the old checkpoints
            if len(self.saved_steps) > self.max_keep:
                oldest = heapq.heappop(self.saved_steps)
                ckpt_dir = os.path.join(self.ckpt_output_dir, f"step_{oldest}")
                safetensors_dir = os.path.join(
                    self.config.train.output_dir, "safetensors", f"step_{oldest}"
                )
                if os.path.exists(ckpt_dir):
                    shutil.rmtree(ckpt_dir)
                    logger.info(f"Removed old checkpoint: {ckpt_dir}")
                if os.path.exists(safetensors_dir):
                    shutil.rmtree(safetensors_dir)
                    logger.info(f"Removed old safetensors: {safetensors_dir}")

            val_score = kwargs.get("val_score", None)
            if val_score is not None:
                if ("loss" in self.metric and val_score < self.best_score) or (
                    "loss" not in self.metric and val_score > self.best_score
                ):
                    self.best_score = val_score
                    best_ckpt_dir = os.path.join(
                        self.config.train.output_dir, "checkpoints", "best"
                    )
                    if os.path.islink(best_ckpt_dir):
                        os.unlink(best_ckpt_dir)
                    os.symlink(f"step_{step}", best_ckpt_dir)
                    logger.info(
                        f"Best checkpoint updated to step_{step} with score: {val_score}"
                    )
                    if self.config.train.ckpt.export_safetensors:
                        best_safetensors_dir = os.path.join(
                            self.config.train.output_dir, "safetensors", "best"
                        )
                        if os.path.islink(best_safetensors_dir):
                            os.unlink(best_safetensors_dir)
                        os.symlink(f"step_{step}", best_safetensors_dir)
                        logger.info(f"Best safetensors updated to step_{step}")
