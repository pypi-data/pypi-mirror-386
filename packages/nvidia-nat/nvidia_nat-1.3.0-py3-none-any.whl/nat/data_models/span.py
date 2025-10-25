# SPDX-FileCopyrightText: Copyright (c) 2024-2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import logging
import os
import time
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

logger = logging.getLogger(__name__)

_SPAN_PREFIX = os.getenv("NAT_SPAN_PREFIX", "nat").strip() or "nat"


class SpanKind(Enum):
    LLM = "LLM"
    TOOL = "TOOL"
    WORKFLOW = "WORKFLOW"
    TASK = "TASK"
    FUNCTION = "FUNCTION"
    CUSTOM = "CUSTOM"
    SPAN = "SPAN"
    EMBEDDER = "EMBEDDER"
    RETRIEVER = "RETRIEVER"
    AGENT = "AGENT"
    RERANKER = "RERANKER"
    GUARDRAIL = "GUARDRAIL"
    EVALUATOR = "EVALUATOR"
    UNKNOWN = "UNKNOWN"


EVENT_TYPE_TO_SPAN_KIND_MAP = {
    "LLM_START": SpanKind.LLM,
    "LLM_END": SpanKind.LLM,
    "LLM_NEW_TOKEN": SpanKind.LLM,
    "TOOL_START": SpanKind.TOOL,
    "TOOL_END": SpanKind.TOOL,
    "WORKFLOW_START": SpanKind.WORKFLOW,
    "WORKFLOW_END": SpanKind.WORKFLOW,
    "TASK_START": SpanKind.TASK,
    "TASK_END": SpanKind.TASK,
    "FUNCTION_START": SpanKind.FUNCTION,
    "FUNCTION_END": SpanKind.FUNCTION,
    "CUSTOM_START": SpanKind.CUSTOM,
    "CUSTOM_END": SpanKind.CUSTOM,
    "SPAN_START": SpanKind.SPAN,
    "SPAN_END": SpanKind.SPAN,
    "EMBEDDER_START": SpanKind.EMBEDDER,
    "EMBEDDER_END": SpanKind.EMBEDDER,
    "RETRIEVER_START": SpanKind.RETRIEVER,
    "RETRIEVER_END": SpanKind.RETRIEVER,
    "AGENT_START": SpanKind.AGENT,
    "AGENT_END": SpanKind.AGENT,
    "RERANKER_START": SpanKind.RERANKER,
    "RERANKER_END": SpanKind.RERANKER,
    "GUARDRAIL_START": SpanKind.GUARDRAIL,
    "GUARDRAIL_END": SpanKind.GUARDRAIL,
    "EVALUATOR_START": SpanKind.EVALUATOR,
    "EVALUATOR_END": SpanKind.EVALUATOR,
}


def event_type_to_span_kind(event_type: str) -> SpanKind:
    """Convert an event type to a span kind.

    Args:
        event_type (str): The event type to convert.

    Returns:
        SpanKind: The span kind.
    """
    return EVENT_TYPE_TO_SPAN_KIND_MAP.get(event_type, SpanKind.UNKNOWN)


class SpanAttributes(Enum):
    NAT_SPAN_KIND = f"{_SPAN_PREFIX}.span.kind"
    INPUT_VALUE = "input.value"
    INPUT_MIME_TYPE = "input.mime_type"
    LLM_TOKEN_COUNT_PROMPT = "llm.token_count.prompt"
    LLM_TOKEN_COUNT_COMPLETION = "llm.token_count.completion"
    LLM_TOKEN_COUNT_TOTAL = "llm.token_count.total"
    OUTPUT_VALUE = "output.value"
    OUTPUT_MIME_TYPE = "output.mime_type"
    NAT_USAGE_NUM_LLM_CALLS = f"{_SPAN_PREFIX}.usage.num_llm_calls"
    NAT_USAGE_SECONDS_BETWEEN_CALLS = f"{_SPAN_PREFIX}.usage.seconds_between_calls"
    NAT_USAGE_TOKEN_COUNT_PROMPT = f"{_SPAN_PREFIX}.usage.token_count.prompt"
    NAT_USAGE_TOKEN_COUNT_COMPLETION = f"{_SPAN_PREFIX}.usage.token_count.completion"
    NAT_USAGE_TOKEN_COUNT_TOTAL = f"{_SPAN_PREFIX}.usage.token_count.total"
    NAT_EVENT_TYPE = f"{_SPAN_PREFIX}.event_type"


class MimeTypes(Enum):
    TEXT = "text/plain"
    JSON = "application/json"


class SpanStatusCode(Enum):
    OK = "OK"
    ERROR = "ERROR"
    UNSET = "UNSET"


class SpanEvent(BaseModel):
    timestamp: float = Field(default_factory=lambda: int(time.time() * 1e9), description="The timestamp of the event.")
    name: str = Field(description="The name of the event.")
    attributes: dict[str, Any] = Field(default_factory=dict, description="The attributes of the event.")


class SpanStatus(BaseModel):
    code: SpanStatusCode = Field(default=SpanStatusCode.OK, description="The status code of the span.")
    message: str | None = Field(default=None, description="The status message of the span.")


def _generate_nonzero_trace_id() -> int:
    """Generate a non-zero 128-bit trace ID."""
    return uuid.uuid4().int


def _generate_nonzero_span_id() -> int:
    """Generate a non-zero 64-bit span ID."""
    return uuid.uuid4().int >> 64


class SpanContext(BaseModel):
    trace_id: int = Field(default_factory=_generate_nonzero_trace_id,
                          description="The OTel-syle 128-bit trace ID of the span.")
    span_id: int = Field(default_factory=_generate_nonzero_span_id,
                         description="The OTel-syle 64-bit span ID of the span.")

    @field_validator("trace_id", mode="before")
    @classmethod
    def _validate_trace_id(cls, v: int | str | None) -> int:
        """Regenerate if trace_id is None; raise an exception if trace_id is invalid;"""
        if isinstance(v, str):
            v = uuid.UUID(v).int
        if isinstance(v, type(None)):
            v = _generate_nonzero_trace_id()
        if v <= 0 or v >> 128:
            raise ValueError(f"Invalid trace_id: must be a non-zero 128-bit integer, got {v}")
        return v

    @field_validator("span_id", mode="before")
    @classmethod
    def _validate_span_id(cls, v: int | str | None) -> int:
        """Regenerate if span_id is None; raise an exception if span_id is invalid;"""
        if isinstance(v, str):
            try:
                v = int(v, 16)
            except ValueError:
                raise ValueError(f"span_id unable to be parsed: {v}")
        if isinstance(v, type(None)):
            v = _generate_nonzero_span_id()
        if v <= 0 or v >> 64:
            raise ValueError(f"Invalid span_id: must be a non-zero 64-bit integer, got {v}")
        return v


class Span(BaseModel):
    name: str = Field(description="The name of the span.")
    context: SpanContext | None = Field(default=None, description="The context of the span.")
    parent: "Span | None" = Field(default=None, description="The parent span of the span.")
    start_time: int = Field(default_factory=lambda: int(time.time() * 1e9), description="The start time of the span.")
    end_time: int | None = Field(default=None, description="The end time of the span.")
    attributes: dict[str, Any] = Field(default_factory=dict, description="The attributes of the span.")
    events: list[SpanEvent] = Field(default_factory=list, description="The events of the span.")
    status: SpanStatus = Field(default_factory=SpanStatus, description="The status of the span.")

    @field_validator('context', mode='before')
    @classmethod
    def set_default_context(cls, v: SpanContext | None) -> SpanContext:
        """Set the default context if the context is not provided.

        Args:
            v (SpanContext | None): The context to set.

        Returns:
            SpanContext: The context.
        """
        if v is None:
            return SpanContext()
        return v

    def set_attribute(self, key: str, value: Any) -> None:
        """Set the attribute of the span.

        Args:
            key (str): The key of the attribute.
            value (Any): The value of the attribute.
        """
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Add an event to the span.

        Args:
            name (str): The name of the event.
            attributes (dict[str, Any] | None): The attributes of the event.
        """
        if attributes is None:
            attributes = {}
        self.events = self.events + [SpanEvent(name=name, attributes=attributes)]

    def end(self, end_time: int | None = None) -> None:
        """End the span.

        Args:
            end_time (int | None): The end time of the span.
        """
        if end_time is None:
            end_time = int(time.time() * 1e9)
        self.end_time = end_time
