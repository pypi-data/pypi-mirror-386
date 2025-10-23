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

os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"
import subprocess
import sys
import tempfile
import unittest

import toml

from cosmos_rl.utils import util


class TestPolicyOverfit(unittest.TestCase):
    def test_policy_overfit(self):
        """Tests if policy trains on fixed samples, overfits, and decreases training loss."""
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        world_size = 8
        port = util.find_available_port(8123)
        config_path = os.path.join(
            cur_dir,
            "configs",
            "sft_integration_deepseek_simple.toml",
        )
        with open(config_path, "r") as f:
            config = toml.load(f)
        config["train"]["train_policy"]["dataset"]["name"] = os.path.join(
            cur_dir, "data_fixtures", "sharegpt52k_small"
        )
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".toml", delete=False
        ) as tmpfile:
            toml.dump(config, tmpfile)
            tmpfile_toml = tmpfile.name
        controller_cmd = f"{sys.executable} -m cosmos_rl.dispatcher.run_web_panel --config {tmpfile_toml}"
        controller_cmd += f" --port {port}"
        env_dict = os.environ.copy()
        env_dict["COSMOS_ROLE"] = "Controller"
        controller_process = subprocess.Popen(
            controller_cmd,
            shell=True,
            stdout=sys.stderr,
            stderr=sys.stderr,
            env=env_dict,
        )
        os.environ["COSMOS_CONTROLLER_HOST"] = f"localhost:{port}"
        # Create the Python command for torchrun
        policy_cmd = [
            "torchrun",
            f"--nproc_per_node={world_size}",  # Use 2 GPUs
            "--role=rank",
            "--tee=3",
            "--rdzv_backend=c10d",
            "--rdzv_endpoint=localhost:0",
            os.path.join(cur_dir, "launch_test_worker.py"),
            "--shm_name",
            "-1",
            "--shm_size",
            "-1",
            "--mode",
            "test_overfit",
        ]
        policy_env = dict(os.environ)
        policy_env["CUDA_VISIBLE_DEVICES"] = "0,1,2,3,4,5,6,7"
        # Start the process
        policy_process = subprocess.Popen(
            policy_cmd,
            stdout=sys.stderr,
            stderr=sys.stderr,
            env=policy_env,
        )

        processes = [controller_process, policy_process]

        # Wait for process to complete
        for process in processes:
            stdout, stderr = process.communicate()
            # Check if process completed successfully
            assert (
                process.returncode == 0
            ), f"Process failed with code: {process.returncode}"


if __name__ == "__main__":
    unittest.main()
