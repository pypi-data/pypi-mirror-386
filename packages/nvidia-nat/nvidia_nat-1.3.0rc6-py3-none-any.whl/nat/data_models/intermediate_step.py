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

import time
import typing
import uuid
from enum import Enum
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from nat.builder.framework_enum import LLMFrameworkEnum
from nat.data_models.invocation_node import InvocationNode
from nat.profiler.callbacks.token_usage_base_model import TokenUsageBaseModel


class IntermediateStepCategory(str, Enum):
    LLM = "LLM"
    TOOL = "TOOL"
    WORKFLOW = "WORKFLOW"
    TASK = "TASK"
    FUNCTION = "FUNCTION"
    CUSTOM = "CUSTOM"
    SPAN = "SPAN"


class IntermediateStepType(str, Enum):
    LLM_START = "LLM_START"
    LLM_END = "LLM_END"
    LLM_NEW_TOKEN = "LLM_NEW_TOKEN"
    TOOL_START = "TOOL_START"
    TOOL_END = "TOOL_END"
    WORKFLOW_START = "WORKFLOW_START"
    WORKFLOW_END = "WORKFLOW_END"
    TASK_START = "TASK_START"
    TASK_END = "TASK_END"
    FUNCTION_START = "FUNCTION_START"
    FUNCTION_END = "FUNCTION_END"
    CUSTOM_START = "CUSTOM_START"
    CUSTOM_END = "CUSTOM_END"
    SPAN_START = "SPAN_START"
    SPAN_CHUNK = "SPAN_CHUNK"
    SPAN_END = "SPAN_END"


class IntermediateStepState(str, Enum):
    START = "START"
    CHUNK = "CHUNK"
    END = "END"


class StreamEventData(BaseModel):
    """
    StreamEventData is a data model that represents the data field in an streaming event.
    """

    # Allow extra fields in the model_config to support derived models
    model_config = ConfigDict(extra="allow")

    input: typing.Any | None = None
    output: typing.Any | None = None
    chunk: typing.Any | None = None


class UsageInfo(BaseModel):
    token_usage: TokenUsageBaseModel = TokenUsageBaseModel()
    num_llm_calls: int = 0
    seconds_between_calls: int = 0


class ToolParameters(BaseModel):
    properties: dict[str, typing.Any] = Field(..., description="The properties of the function parameters.")
    required: list[str] = Field(default_factory=list, description="The required properties of the function parameters.")
    type_: Literal["object"] = Field(default="object", description="The type of the function parameters.", alias="type")
    additionalProperties: bool = Field(default=False,
                                       description="Enable function parameters allow additional properties.")
    strict: bool = Field(default=True, description="Ensure function calls reliably adhere to the function schema.")


class ToolDetails(BaseModel):
    name: str = Field(..., description="The name of the function.")
    description: str = Field(..., description="The description of the function.")
    parameters: ToolParameters = Field(..., description="The parameters of the function.")


class ToolSchema(BaseModel):
    type: Literal["function"] = Field(..., description="The type of the tool.")
    function: ToolDetails = Field(..., description="The function details.")


class TraceMetadata(BaseModel):
    chat_responses: typing.Any | None = None
    chat_inputs: typing.Any | None = None
    tool_inputs: typing.Any | None = None
    tool_outputs: typing.Any | None = None
    tool_info: typing.Any | None = None
    span_inputs: typing.Any | None = None
    span_outputs: typing.Any | None = None
    provided_metadata: typing.Any | None = None
    tools_schema: list[ToolSchema] = Field(default_factory=list,
                                           description="The schema of tools used in a tool calling request.")

    # Allow extra fields in the model_config to support derived models
    model_config = ConfigDict(extra="allow")


class IntermediateStepPayload(BaseModel):
    """
    IntermediateStep is a data model that represents an intermediate step in the NAT. Intermediate steps are
    captured while a request is running and can be used to show progress or to evaluate the path a workflow took to get
    a response.
    """

    # Allow extra fields in the model_config to support derived models
    model_config = ConfigDict(extra="allow")

    event_type: IntermediateStepType
    # Create an event timestamp field with the default being a lambda that returns the current time
    event_timestamp: float = Field(default_factory=lambda: time.time())
    span_event_timestamp: float | None = None  # Used for tracking the start time of a task if this is end
    framework: LLMFrameworkEnum | None = None
    name: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, typing.Any] | TraceMetadata | None = None
    data: StreamEventData | None = None
    usage_info: UsageInfo | None = None
    UUID: str = Field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def event_category(self) -> IntermediateStepCategory:
        match self.event_type:
            case IntermediateStepType.LLM_START:
                return IntermediateStepCategory.LLM
            case IntermediateStepType.LLM_END:
                return IntermediateStepCategory.LLM
            case IntermediateStepType.LLM_NEW_TOKEN:
                return IntermediateStepCategory.LLM
            case IntermediateStepType.TOOL_START:
                return IntermediateStepCategory.TOOL
            case IntermediateStepType.TOOL_END:
                return IntermediateStepCategory.TOOL
            case IntermediateStepType.WORKFLOW_START:
                return IntermediateStepCategory.WORKFLOW
            case IntermediateStepType.WORKFLOW_END:
                return IntermediateStepCategory.WORKFLOW
            case IntermediateStepType.TASK_START:
                return IntermediateStepCategory.TASK
            case IntermediateStepType.TASK_END:
                return IntermediateStepCategory.TASK
            case IntermediateStepType.FUNCTION_START:
                return IntermediateStepCategory.FUNCTION
            case IntermediateStepType.FUNCTION_END:
                return IntermediateStepCategory.FUNCTION
            case IntermediateStepType.CUSTOM_START:
                return IntermediateStepCategory.CUSTOM
            case IntermediateStepType.CUSTOM_END:
                return IntermediateStepCategory.CUSTOM
            case IntermediateStepType.SPAN_START:
                return IntermediateStepCategory.SPAN
            case IntermediateStepType.SPAN_CHUNK:
                return IntermediateStepCategory.SPAN
            case IntermediateStepType.SPAN_END:
                return IntermediateStepCategory.SPAN
            case _:
                raise ValueError(f"Unknown event type: {self.event_type}")

    @property
    def event_state(self) -> IntermediateStepState:
        match self.event_type:
            case IntermediateStepType.LLM_START:
                return IntermediateStepState.START
            case IntermediateStepType.LLM_END:
                return IntermediateStepState.END
            case IntermediateStepType.LLM_NEW_TOKEN:
                return IntermediateStepState.CHUNK
            case IntermediateStepType.TOOL_START:
                return IntermediateStepState.START
            case IntermediateStepType.TOOL_END:
                return IntermediateStepState.END
            case IntermediateStepType.WORKFLOW_START:
                return IntermediateStepState.START
            case IntermediateStepType.WORKFLOW_END:
                return IntermediateStepState.END
            case IntermediateStepType.TASK_START:
                return IntermediateStepState.START
            case IntermediateStepType.TASK_END:
                return IntermediateStepState.END
            case IntermediateStepType.FUNCTION_START:
                return IntermediateStepState.START
            case IntermediateStepType.FUNCTION_END:
                return IntermediateStepState.END
            case IntermediateStepType.CUSTOM_START:
                return IntermediateStepState.START
            case IntermediateStepType.CUSTOM_END:
                return IntermediateStepState.END
            case IntermediateStepType.SPAN_START:
                return IntermediateStepState.START
            case IntermediateStepType.SPAN_CHUNK:
                return IntermediateStepState.CHUNK
            case IntermediateStepType.SPAN_END:
                return IntermediateStepState.END
            case _:
                raise ValueError(f"Unknown event type: {self.event_type}")

    @model_validator(mode="after")
    def check_span_event_timestamp(self) -> "IntermediateStepPayload":
        if self.event_state != IntermediateStepState.END and self.span_event_timestamp is not None:
            raise ValueError("span_event_timestamp can only be provided for events with an END state")
        return self


class IntermediateStep(BaseModel):
    """
    IntermediateStep is a data model that represents an intermediate step in the NAT. Intermediate steps are
    captured while a request is running and can be used to show progress or to evaluate the path a workflow took to get
    a response.
    """

    # Allow extra fields in the model_config to support derived models
    model_config = ConfigDict(extra="forbid")

    parent_id: str
    """
    The parent step ID for the current step. The parent ID is the ID of the last START step which has a different UUID
    than the current step. This value is different from the function_ancestry.parent_id value which tracks the last
    parent FUNCTION step. For the first START step, the parent_id is 'root'.
    """

    function_ancestry: InvocationNode
    """
    The function ancestry for the current step showing the current NAT function that was being executed when the step
    was created.
    """

    payload: IntermediateStepPayload
    """
    The payload for the current step.
    """

    # ===== Payload Properties =====
    @property
    def event_type(self) -> IntermediateStepType:
        return self.payload.event_type

    @property
    def event_timestamp(self) -> float:
        return self.payload.event_timestamp

    @property
    def span_event_timestamp(self) -> float | None:
        return self.payload.span_event_timestamp

    @property
    def framework(self) -> LLMFrameworkEnum | None:
        return self.payload.framework

    @property
    def name(self) -> str | None:
        return self.payload.name

    @property
    def tags(self) -> list[str] | None:
        return self.payload.tags

    @property
    def metadata(self) -> dict[str, typing.Any] | TraceMetadata | None:
        return self.payload.metadata

    @property
    def data(self) -> StreamEventData | None:
        return self.payload.data

    @property
    def usage_info(self) -> UsageInfo | None:
        return self.payload.usage_info

    @property
    def UUID(self) -> str:
        return self.payload.UUID

    @property
    def event_category(self) -> IntermediateStepCategory:
        return self.payload.event_category

    @property
    def event_state(self) -> IntermediateStepState:
        return self.payload.event_state
