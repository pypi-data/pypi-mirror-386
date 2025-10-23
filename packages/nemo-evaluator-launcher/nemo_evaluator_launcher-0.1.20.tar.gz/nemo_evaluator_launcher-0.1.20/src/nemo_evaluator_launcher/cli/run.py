# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import pathlib
import time
from dataclasses import dataclass

from simple_parsing import field

from nemo_evaluator_launcher.common.logging_utils import logger
from nemo_evaluator_launcher.common.printing_utils import (
    bold,
    cyan,
    green,
    magenta,
    red,
)


@dataclass
class Cmd:
    """Run command parameters"""

    config_name: str = field(
        default="default",
        alias=["-c", "--config-name"],
        metadata={
            "help": "Config name to use. Consult `nemo_evaluator_launcher.configs`"
        },
    )
    config_dir: str | None = field(
        default=None,
        alias=["-d", "--config-dir"],
        metadata={
            "help": "Path to user config directory. If provided, searches here first, then falls back to internal configs."
        },
    )
    run_config_file: str | None = field(
        default=None,
        alias=["-f", "--run-config-file"],
        metadata={
            "help": "Path to a run config file to load directly (bypasses Hydra config loading)."
        },
    )
    override: list[str] = field(
        default_factory=list,
        action="append",
        nargs="?",
        alias=["-o"],
        metadata={
            "help": "Hydra override in the form some.param.path=value (pass multiple `-o` for multiple overrides).",
        },
    )
    dry_run: bool = field(
        default=False,
        alias=["-n", "--dry-run"],
        metadata={"help": "Do not run the evaluation, just print the config."},
    )
    config_output: str | None = field(
        default=None,
        alias=["--config-output"],
        metadata={
            "help": "Directory to save the complete run config. Defaults to ~/.nemo-evaluator/run_configs/"
        },
    )

    def execute(self) -> None:
        # Import heavy dependencies only when needed
        import yaml
        from omegaconf import OmegaConf

        from nemo_evaluator_launcher.api.functional import RunConfig, run_eval

        # Load configuration either from Hydra or from a run config file
        if self.run_config_file:
            # Validate that run config file is not used with other config options
            if self.config_name != "default":
                raise ValueError("Cannot use --run-config-file with --config-name")
            if self.config_dir is not None:
                raise ValueError("Cannot use --run-config-file with --config-dir")
            if self.override:
                raise ValueError("Cannot use --run-config-file with --override")

            # Load from run config file
            with open(self.run_config_file, "r") as f:
                config_dict = yaml.safe_load(f)

            # Create RunConfig from the loaded data
            config = OmegaConf.create(config_dict)
        else:
            # Load the complete Hydra configuration
            config = RunConfig.from_hydra(
                config_name=self.config_name,
                hydra_overrides=self.override,
                config_dir=self.config_dir,
            )

        try:
            invocation_id = run_eval(config, self.dry_run)
        except Exception as e:
            print(red(f"✗ Job submission failed, see logs | Error: {e}"))
            logger.error("Job submission failed", error=e)
            raise

        # Save the complete configuration
        if not self.dry_run and invocation_id is not None:
            # Determine config output directory
            if self.config_output:
                # Use custom directory specified by --config-output
                config_dir = pathlib.Path(self.config_output)
            else:
                # Default to original location: ~/.nemo-evaluator/run_configs
                home_dir = pathlib.Path.home()
                config_dir = home_dir / ".nemo-evaluator" / "run_configs"

            # Ensure the directory exists
            config_dir.mkdir(parents=True, exist_ok=True)

            # Convert DictConfig to dict and save as YAML
            config_dict = OmegaConf.to_container(config, resolve=True)
            config_yaml = yaml.dump(
                config_dict, default_flow_style=False, sort_keys=False, indent=2
            )

            # Create config filename with invocation ID
            config_filename = f"{invocation_id}_config.yml"
            config_path = config_dir / config_filename

            # Save the complete Hydra configuration
            with open(config_path, "w") as f:
                f.write("# Complete configuration from nemo-evaluator-launcher\n")
                f.write(
                    f"# Generated at: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                f.write(f"# Invocation ID: {invocation_id}\n")
                f.write("#\n")
                f.write("# This is the complete raw configuration\n")
                f.write("#\n")
                f.write("# To rerun this exact configuration:\n")
                f.write(
                    f"# nemo-evaluator-launcher run --run-config-file {config_path}\n"
                )
                f.write("#\n")
                f.write(config_yaml)

            print(bold(cyan("Complete run config saved to: ")) + f"\n  {config_path}\n")
            logger.info("Saved complete config", path=config_path)

        # Print general success message with invocation ID and helpful commands
        if invocation_id is not None and not self.dry_run:
            print(
                bold(cyan("To check status: "))
                + f"nemo-evaluator-launcher status {invocation_id}"
            )
            print(
                bold(cyan("To kill all jobs: "))
                + f"nemo-evaluator-launcher kill {invocation_id}"
            )

            # Show actual job IDs and task names
            print(bold(cyan("To kill individual jobs:")))
            # Access tasks - will work after normalization in run_eval
            tasks = (
                config.evaluation.tasks
                if hasattr(config.evaluation, "tasks")
                else config.evaluation
            )
            for idx, task in enumerate(tasks):
                job_id = f"{invocation_id}.{idx}"
                print(f"  nemo-evaluator-launcher kill {job_id}  # {task.name}")

            print(
                magenta(
                    "(all commands accept shortened IDs as long as there are no conflicts)"
                )
            )
            print(
                bold(cyan("To print all jobs: ")) + "nemo-evaluator-launcher ls runs"
                "\n  (--since 1d or --since 6h for time span, see --help)"
            )

            print(
                green(
                    bold(
                        f"✓ Job submission successful | Invocation ID: {invocation_id}"
                    )
                )
            )
