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


import torch
from megatron.core.transformer import TransformerConfig


def apply_deepep(model_config: TransformerConfig) -> None:
    """Apply DeepEP optimizations to the model config."""
    model_config.moe_token_dispatcher_type = "flex"
    model_config.moe_enable_deepep = True
    model_config.moe_shared_expert_overlap = False


def validate_deepep(model_config: TransformerConfig) -> None:
    """Validate DeepEP is supported for the current GPU architecture."""
    if model_config.moe_enable_deepep and torch.cuda.get_device_properties(0).major not in (8, 9):
        raise ValueError("DeepEP is supported for Ampere (SM80) and Hopper (SM90) GPUs")
