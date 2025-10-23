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

import os
from cosmos_rl.policy.config import Config as CosmosConfig
from cosmos_rl.utils.parallelism import ParallelDims
from cosmos_rl.utils.logging import logger

try:
    import wandb
except ImportError:
    logger.warning(
        "wandb is not installed. Please install it to use wandb logging features."
    )


def is_wandb_available() -> bool:
    """
    Check if wandb is available in the current environment.

    Returns:
        bool: True if wandb is available, False otherwise.
    """
    try:
        import wandb  # noqa: F401

        return wandb.api.api_key is not None
    except ImportError:
        return False


wandb_run = None


def init_wandb(config: CosmosConfig, parallel_dims: ParallelDims = None):
    # Avoid duplicate initialization of wandb
    if wandb.run is not None:
        logger.warning("Wandb is already initialized. Skipping initialization.")
        return
    # Only initialize wandb on the first dp replicate coord and first rank for policy
    if parallel_dims and parallel_dims.dp_replicate_coord[0] > 0:
        return
    global_rank = int(os.environ.get("RANK", 0))
    if global_rank != 0:
        return

    output_dir = config.train.output_dir
    logger.info(
        f"Initialize wandb at {global_rank}, project: {config.logging.project_name}, experiment: {config.logging.experiment_name}. Saved to {output_dir}"
    )
    os.makedirs(output_dir, exist_ok=True)
    if (
        config.logging.experiment_name is None
        or config.logging.experiment_name == "None"
        or config.logging.experiment_name == ""
    ):
        experiment_name = output_dir
    else:
        experiment_name = os.path.join(
            config.logging.experiment_name, config.train.timestamp
        )
    try:
        run = wandb.init(
            project=config.logging.project_name,
            name=experiment_name,
            config=config.model_dump(),
            dir=output_dir,
            id=config.train.timestamp,  # Use timestamp as the run ID
            resume="allow",
        )
        global wandb_run
        wandb_run = run
        return run
    except Exception as e:
        logger.error(f"Failed to initialize wandb: {e}")
        return None


def log_wandb(data: dict, step: int):
    global wandb_run
    if wandb_run is not None:
        wandb_run.log(data, step=step)
    else:
        logger.warning("Wandb is not initialized. Please check the configuration.")
