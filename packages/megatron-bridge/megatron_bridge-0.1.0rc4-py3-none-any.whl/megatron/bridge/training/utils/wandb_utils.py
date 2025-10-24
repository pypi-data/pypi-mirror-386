# Copyright (c) 2025, NVIDIA CORPORATION.  All rights reserved.
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

from pathlib import Path
from typing import Any, Optional

from megatron.bridge.utils.common_utils import print_rank_last


def on_save_checkpoint_success(
    checkpoint_path: str,
    save_dir: str,
    iteration: int,
    wandb_writer: Optional[Any],
) -> None:
    """Callback executed after a checkpoint is successfully saved.

    If a wandb writer is provided, logs the checkpoint as a wandb artifact,
    referencing the local file path. Also saves a tracker file containing
    the wandb entity/project for later use.

    Args:
        checkpoint_path: The path to the specific checkpoint file/directory saved.
        save_dir: The base directory where checkpoints are being saved.
        iteration: The training iteration at which the checkpoint was saved.
        wandb_writer: The wandb writer instance (e.g., wandb.run).
                      If None, this function is a no-op.
    """
    if wandb_writer:
        metadata = {"iteration": iteration}
        artifact_name, artifact_version = _get_artifact_name_and_version(Path(save_dir), Path(checkpoint_path))
        artifact = wandb_writer.Artifact(artifact_name, type="model", metadata=metadata)
        # wandb's artifact.add_reference requires absolute paths
        checkpoint_path = str(Path(checkpoint_path).resolve())
        artifact.add_reference(f"file://{checkpoint_path}", checksum=False)
        wandb_writer.run.log_artifact(artifact, aliases=[artifact_version])
        wandb_tracker_filename = _get_wandb_artifact_tracker_filename(save_dir)
        wandb_tracker_filename.write_text(f"{wandb_writer.run.entity}/{wandb_writer.run.project}")


def on_load_checkpoint_success(checkpoint_path: str, load_dir: str, wandb_writer: Optional[Any]) -> None:
    """Callback executed after a checkpoint is successfully loaded.

    If a wandb writer is provided, attempts to mark the corresponding
    wandb artifact as used. It reads the entity/project from the tracker
    file saved during the checkpoint save process.

    Args:
        checkpoint_path: The path to the specific checkpoint file/directory loaded.
        load_dir: The base directory from which the checkpoint was loaded.
        wandb_writer: The wandb writer instance (e.g., wandb.run).
                      If None, or if artifact tracking fails, this function is a no-op.
    """
    if wandb_writer:
        try:
            artifact_name, artifact_version = _get_artifact_name_and_version(Path(load_dir), Path(checkpoint_path))
            wandb_tracker_filename = _get_wandb_artifact_tracker_filename(load_dir)
            artifact_path = ""
            if wandb_tracker_filename.is_file():
                artifact_path = wandb_tracker_filename.read_text().strip()
                artifact_path = f"{artifact_path}/"
            wandb_writer.run.use_artifact(f"{artifact_path}{artifact_name}:{artifact_version}")
        except Exception:
            print_rank_last(f"  failed to find checkpoint {checkpoint_path} in wandb")


def _get_wandb_artifact_tracker_filename(save_dir: str) -> Path:
    """Wandb artifact tracker file rescords the latest artifact wandb entity and project"""
    return Path(save_dir) / "latest_wandb_artifact_path.txt"


def _get_artifact_name_and_version(save_dir: Path, checkpoint_path: Path) -> tuple[str, str]:
    return save_dir.stem, checkpoint_path.stem
