# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import re

from pydantic import BaseModel
from pydantic import Field

from nat.data_models.gated_field_mixin import GatedFieldMixin

# Currently the control logic for thinking is only implemented for Nemotron models
_NEMOTRON_REGEX = re.compile(r"^nvidia/(llama|nvidia).*nemotron", re.IGNORECASE)
# The keys are the fields that are used to determine if the model supports thinking
_MODEL_KEYS = ("model_name", "model", "azure_deployment")


class ThinkingMixin(
        BaseModel,
        GatedFieldMixin,
        field_name="thinking",
        default_if_supported=None,
        keys=_MODEL_KEYS,
        supported=(_NEMOTRON_REGEX, ),
):
    """
    Mixin class for thinking configuration. Only supported on Nemotron models.

    Attributes:
        thinking: Whether to enable thinking. Defaults to None when supported on the model.
    """
    thinking: bool | None = Field(
        default=None,
        description="Whether to enable thinking. Defaults to None when supported on the model.",
    )

    @property
    def thinking_system_prompt(self) -> str | None:
        """
        Returns the system prompt to use for thinking.
        For NVIDIA Nemotron, returns "/think" if enabled, else "/no_think".
        For Llama Nemotron v1.5, returns "/think" if enabled, else "/no_think".
        For Llama Nemotron v1.0 or v1.1, returns "detailed thinking on" if enabled, else "detailed thinking off".
        If thinking is not supported on the model, returns None.

        Returns:
            str | None: The system prompt to use for thinking.
        """
        if self.thinking is None:
            return None

        for key in _MODEL_KEYS:
            model = getattr(self, key, None)
            if not isinstance(model, str) or model is None:
                continue

            # Normalize name to reduce checks
            model = model.lower().translate(str.maketrans("_.", "--"))

            if model.startswith("nvidia/nvidia"):
                return "/think" if self.thinking else "/no_think"

            if model.startswith("nvidia/llama"):
                if "v1-0" in model or "v1-1" in model or model.endswith("v1"):
                    return f"detailed thinking {'on' if self.thinking else 'off'}"

                if "v1-5" in model:
                    # v1.5 models are updated to use the /think and /no_think system prompts
                    return "/think" if self.thinking else "/no_think"

                # Assume any other model is a newer model that uses the /think and /no_think system prompts
                return "/think" if self.thinking else "/no_think"

        # Unknown model
        return None
