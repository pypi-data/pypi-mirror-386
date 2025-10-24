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
import typing
from collections.abc import AsyncIterator
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from contextlib import contextmanager
from copy import deepcopy
from functools import cached_property
from logging import Handler

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import Tag
from pydantic import computed_field
from pydantic import field_validator

from nat.authentication.interfaces import AuthProviderBase
from nat.builder.builder import Builder
from nat.builder.builder import EvalBuilder
from nat.builder.embedder import EmbedderProviderInfo
from nat.builder.evaluator import EvaluatorInfo
from nat.builder.front_end import FrontEndBase
from nat.builder.function import Function
from nat.builder.function import FunctionGroup
from nat.builder.function_base import FunctionBase
from nat.builder.function_info import FunctionInfo
from nat.builder.llm import LLMProviderInfo
from nat.builder.retriever import RetrieverProviderInfo
from nat.data_models.authentication import AuthProviderBaseConfig
from nat.data_models.authentication import AuthProviderBaseConfigT
from nat.data_models.common import TypedBaseModelT
from nat.data_models.component import ComponentEnum
from nat.data_models.config import Config
from nat.data_models.discovery_metadata import DiscoveryMetadata
from nat.data_models.embedder import EmbedderBaseConfig
from nat.data_models.embedder import EmbedderBaseConfigT
from nat.data_models.evaluator import EvaluatorBaseConfig
from nat.data_models.evaluator import EvaluatorBaseConfigT
from nat.data_models.front_end import FrontEndBaseConfig
from nat.data_models.front_end import FrontEndConfigT
from nat.data_models.function import FunctionBaseConfig
from nat.data_models.function import FunctionConfigT
from nat.data_models.function import FunctionGroupBaseConfig
from nat.data_models.function import FunctionGroupConfigT
from nat.data_models.llm import LLMBaseConfig
from nat.data_models.llm import LLMBaseConfigT
from nat.data_models.logging import LoggingBaseConfig
from nat.data_models.logging import LoggingMethodConfigT
from nat.data_models.memory import MemoryBaseConfig
from nat.data_models.memory import MemoryBaseConfigT
from nat.data_models.object_store import ObjectStoreBaseConfig
from nat.data_models.object_store import ObjectStoreBaseConfigT
from nat.data_models.registry_handler import RegistryHandlerBaseConfig
from nat.data_models.registry_handler import RegistryHandlerBaseConfigT
from nat.data_models.retriever import RetrieverBaseConfig
from nat.data_models.retriever import RetrieverBaseConfigT
from nat.data_models.telemetry_exporter import TelemetryExporterBaseConfig
from nat.data_models.telemetry_exporter import TelemetryExporterConfigT
from nat.data_models.ttc_strategy import TTCStrategyBaseConfig
from nat.data_models.ttc_strategy import TTCStrategyBaseConfigT
from nat.experimental.test_time_compute.models.strategy_base import StrategyBase
from nat.memory.interfaces import MemoryEditor
from nat.object_store.interfaces import ObjectStore
from nat.observability.exporter.base_exporter import BaseExporter
from nat.registry_handlers.registry_handler_base import AbstractRegistryHandler

logger = logging.getLogger(__name__)

AuthProviderBuildCallableT = Callable[[AuthProviderBaseConfigT, Builder], AsyncIterator[AuthProviderBase]]
EmbedderClientBuildCallableT = Callable[[EmbedderBaseConfigT, Builder], AsyncIterator[typing.Any]]
EmbedderProviderBuildCallableT = Callable[[EmbedderBaseConfigT, Builder], AsyncIterator[EmbedderProviderInfo]]
EvaluatorBuildCallableT = Callable[[EvaluatorBaseConfigT, EvalBuilder], AsyncIterator[EvaluatorInfo]]
FrontEndBuildCallableT = Callable[[FrontEndConfigT, Config], AsyncIterator[FrontEndBase]]
FunctionBuildCallableT = Callable[[FunctionConfigT, Builder], AsyncIterator[FunctionInfo | Callable | FunctionBase]]
FunctionGroupBuildCallableT = Callable[[FunctionGroupConfigT, Builder], AsyncIterator[FunctionGroup]]
TTCStrategyBuildCallableT = Callable[[TTCStrategyBaseConfigT, Builder], AsyncIterator[StrategyBase]]
LLMClientBuildCallableT = Callable[[LLMBaseConfigT, Builder], AsyncIterator[typing.Any]]
LLMProviderBuildCallableT = Callable[[LLMBaseConfigT, Builder], AsyncIterator[LLMProviderInfo]]
LoggingMethodBuildCallableT = Callable[[LoggingMethodConfigT, Builder], AsyncIterator[Handler]]
MemoryBuildCallableT = Callable[[MemoryBaseConfigT, Builder], AsyncIterator[MemoryEditor]]
ObjectStoreBuildCallableT = Callable[[ObjectStoreBaseConfigT, Builder], AsyncIterator[ObjectStore]]
RegistryHandlerBuildCallableT = Callable[[RegistryHandlerBaseConfigT], AsyncIterator[AbstractRegistryHandler]]
RetrieverClientBuildCallableT = Callable[[RetrieverBaseConfigT, Builder], AsyncIterator[typing.Any]]
RetrieverProviderBuildCallableT = Callable[[RetrieverBaseConfigT, Builder], AsyncIterator[RetrieverProviderInfo]]
TelemetryExporterBuildCallableT = Callable[[TelemetryExporterConfigT, Builder], AsyncIterator[BaseExporter]]
ToolWrapperBuildCallableT = Callable[[str, Function, Builder], typing.Any]

AuthProviderRegisteredCallableT = Callable[[AuthProviderBaseConfigT, Builder],
                                           AbstractAsyncContextManager[AuthProviderBase]]
EmbedderClientRegisteredCallableT = Callable[[EmbedderBaseConfigT, Builder], AbstractAsyncContextManager[typing.Any]]
EmbedderProviderRegisteredCallableT = Callable[[EmbedderBaseConfigT, Builder],
                                               AbstractAsyncContextManager[EmbedderProviderInfo]]
EvaluatorRegisteredCallableT = Callable[[EvaluatorBaseConfigT, EvalBuilder], AbstractAsyncContextManager[EvaluatorInfo]]
FrontEndRegisteredCallableT = Callable[[FrontEndConfigT, Config], AbstractAsyncContextManager[FrontEndBase]]
FunctionRegisteredCallableT = Callable[[FunctionConfigT, Builder],
                                       AbstractAsyncContextManager[FunctionInfo | Callable | FunctionBase]]
FunctionGroupRegisteredCallableT = Callable[[FunctionGroupConfigT, Builder], AbstractAsyncContextManager[FunctionGroup]]
TTCStrategyRegisterCallableT = Callable[[TTCStrategyBaseConfigT, Builder], AbstractAsyncContextManager[StrategyBase]]
LLMClientRegisteredCallableT = Callable[[LLMBaseConfigT, Builder], AbstractAsyncContextManager[typing.Any]]
LLMProviderRegisteredCallableT = Callable[[LLMBaseConfigT, Builder], AbstractAsyncContextManager[LLMProviderInfo]]
LoggingMethodRegisteredCallableT = Callable[[LoggingMethodConfigT, Builder], AbstractAsyncContextManager[typing.Any]]
MemoryRegisteredCallableT = Callable[[MemoryBaseConfigT, Builder], AbstractAsyncContextManager[MemoryEditor]]
ObjectStoreRegisteredCallableT = Callable[[ObjectStoreBaseConfigT, Builder], AbstractAsyncContextManager[ObjectStore]]
RegistryHandlerRegisteredCallableT = Callable[[RegistryHandlerBaseConfigT],
                                              AbstractAsyncContextManager[AbstractRegistryHandler]]
RetrieverClientRegisteredCallableT = Callable[[RetrieverBaseConfigT, Builder], AbstractAsyncContextManager[typing.Any]]
RetrieverProviderRegisteredCallableT = Callable[[RetrieverBaseConfigT, Builder],
                                                AbstractAsyncContextManager[RetrieverProviderInfo]]
TeleExporterRegisteredCallableT = Callable[[TelemetryExporterConfigT, Builder], AbstractAsyncContextManager[typing.Any]]


class RegisteredInfo(BaseModel, typing.Generic[TypedBaseModelT]):

    model_config = ConfigDict(frozen=True)

    full_type: str
    config_type: type[TypedBaseModelT]
    discovery_metadata: DiscoveryMetadata = DiscoveryMetadata()

    @computed_field
    @cached_property
    def module_name(self) -> str:
        return self.full_type.split("/")[0]

    @computed_field
    @cached_property
    def local_name(self) -> str:
        return self.full_type.split("/")[-1]

    @field_validator("full_type", mode="after")
    @classmethod
    def validate_full_type(cls, full_type: str) -> str:
        parts = full_type.split("/")

        if (len(parts) != 2):
            raise ValueError(f"Invalid full type: {full_type}. Expected format: `module_name/local_name`")

        return full_type


class RegisteredTelemetryExporter(RegisteredInfo[TelemetryExporterBaseConfig]):

    build_fn: TeleExporterRegisteredCallableT = Field(repr=False)


class RegisteredLoggingMethod(RegisteredInfo[LoggingBaseConfig]):

    build_fn: LoggingMethodRegisteredCallableT = Field(repr=False)


class RegisteredFrontEndInfo(RegisteredInfo[FrontEndBaseConfig]):
    """
    Represents a registered front end. Front ends are the entry points to the workflow and are responsible for
    orchestrating the workflow.
    """

    build_fn: FrontEndRegisteredCallableT = Field(repr=False)


class RegisteredFunctionInfo(RegisteredInfo[FunctionBaseConfig]):
    """
    Represents a registered function. Functions are the building blocks of the workflow with predefined inputs, outputs,
    and a description.
    """

    build_fn: FunctionRegisteredCallableT = Field(repr=False)
    framework_wrappers: list[str] = Field(default_factory=list)


class RegisteredFunctionGroupInfo(RegisteredInfo[FunctionGroupBaseConfig]):
    """
    Represents a registered function group. Function groups are collections of functions that share configuration
    and resources.
    """

    build_fn: FunctionGroupRegisteredCallableT = Field(repr=False)
    framework_wrappers: list[str] = Field(default_factory=list)


class RegisteredLLMProviderInfo(RegisteredInfo[LLMBaseConfig]):
    """
    Represents a registered LLM provider. LLM Providers are the operators of the LLMs. i.e. NIMs, OpenAI, Anthropic,
    etc.
    """

    build_fn: LLMProviderRegisteredCallableT = Field(repr=False)


class RegisteredAuthProviderInfo(RegisteredInfo[AuthProviderBaseConfig]):
    """
    Represents a registered Authentication provider. Authentication providers facilitate the authentication process.
    """

    build_fn: AuthProviderRegisteredCallableT = Field(repr=False)


class RegisteredLLMClientInfo(RegisteredInfo[LLMBaseConfig]):
    """
    Represents a registered LLM client. LLM Clients are the clients that interact with the LLM providers and are
    specific to a particular LLM framework.
    """

    llm_framework: str
    build_fn: LLMClientRegisteredCallableT = Field(repr=False)


class RegisteredEmbedderProviderInfo(RegisteredInfo[EmbedderBaseConfig]):
    """
    Represents a registered Embedder provider. Embedder Providers are the operators of the Embedder models. i.e. NIMs,
    OpenAI, Anthropic, etc.
    """

    build_fn: EmbedderProviderRegisteredCallableT = Field(repr=False)


class RegisteredEmbedderClientInfo(RegisteredInfo[EmbedderBaseConfig]):
    """
    Represents a registered Embedder client. Embedder Clients are the clients that interact with the Embedder providers
    and are specific to a particular LLM framework.
    """

    llm_framework: str
    build_fn: EmbedderClientRegisteredCallableT = Field(repr=False)


class RegisteredEvaluatorInfo(RegisteredInfo[EvaluatorBaseConfig]):
    """
    Represents a registered Evaluator e.g. RagEvaluator, TrajectoryEvaluator, etc.
    """

    build_fn: EvaluatorRegisteredCallableT = Field(repr=False)


class RegisteredMemoryInfo(RegisteredInfo[MemoryBaseConfig]):
    """
    Represents a registered Memory object which adheres to the memory interface.
    """

    build_fn: MemoryRegisteredCallableT = Field(repr=False)


class RegisteredObjectStoreInfo(RegisteredInfo[ObjectStoreBaseConfig]):
    """
    Represents a registered Object Store object which adheres to the object store interface.
    """

    build_fn: ObjectStoreRegisteredCallableT = Field(repr=False)


class RegisteredTTCStrategyInfo(RegisteredInfo[TTCStrategyBaseConfig]):
    """
    Represents a registered TTC strategy.
    """

    build_fn: TTCStrategyRegisterCallableT = Field(repr=False)


class RegisteredToolWrapper(BaseModel):
    """
    Represents a registered tool wrapper. Tool wrappers are used to wrap the functions in a particular LLM framework.
    They do not have their own configuration, but they are used to wrap the functions in a particular LLM framework.
    """

    llm_framework: str
    build_fn: ToolWrapperBuildCallableT = Field(repr=False)
    discovery_metadata: DiscoveryMetadata


class RegisteredRetrieverProviderInfo(RegisteredInfo[RetrieverBaseConfig]):
    """
    Represents a registered Retriever object which adheres to the retriever interface.
    """

    build_fn: RetrieverProviderRegisteredCallableT = Field(repr=False)


class RegisteredRetrieverClientInfo(RegisteredInfo[RetrieverBaseConfig]):
    """
    Represents a registered Retriever Client. Retriever Clients are the LLM Framework-specific clients that expose an
    interface to the Retriever object.
    """
    llm_framework: str | None
    build_fn: RetrieverClientRegisteredCallableT = Field(repr=False)


class RegisteredRegistryHandlerInfo(RegisteredInfo[RegistryHandlerBaseConfig]):
    """
    Represents a registered LLM client. LLM Clients are the clients that interact with the LLM providers and are
    specific to a particular LLM framework.
    """

    build_fn: RegistryHandlerRegisteredCallableT = Field(repr=False)


class RegisteredPackage(BaseModel):
    package_name: str
    discovery_metadata: DiscoveryMetadata


class TypeRegistry:

    def __init__(self) -> None:
        # Telemetry Exporters
        self._registered_telemetry_exporters: dict[type[TelemetryExporterBaseConfig], RegisteredTelemetryExporter] = {}

        # Logging Methods
        self._registered_logging_methods: dict[type[LoggingBaseConfig], RegisteredLoggingMethod] = {}

        # Front Ends
        self._registered_front_end_infos: dict[type[FrontEndBaseConfig], RegisteredFrontEndInfo] = {}

        # Functions
        self._registered_functions: dict[type[FunctionBaseConfig], RegisteredFunctionInfo] = {}

        # Function Groups
        self._registered_function_groups: dict[type[FunctionGroupBaseConfig], RegisteredFunctionGroupInfo] = {}

        # LLMs
        self._registered_llm_provider_infos: dict[type[LLMBaseConfig], RegisteredLLMProviderInfo] = {}
        self._llm_client_provider_to_framework: dict[type[LLMBaseConfig], dict[str, RegisteredLLMClientInfo]] = {}
        self._llm_client_framework_to_provider: dict[str, dict[type[LLMBaseConfig], RegisteredLLMClientInfo]] = {}

        # Authentication
        self._registered_auth_provider_infos: dict[type[AuthProviderBaseConfig], RegisteredAuthProviderInfo] = {}

        # Embedders
        self._registered_embedder_provider_infos: dict[type[EmbedderBaseConfig], RegisteredEmbedderProviderInfo] = {}
        self._embedder_client_provider_to_framework: dict[type[EmbedderBaseConfig],
                                                          dict[str, RegisteredEmbedderClientInfo]] = {}
        self._embedder_client_framework_to_provider: dict[str,
                                                          dict[type[EmbedderBaseConfig],
                                                               RegisteredEmbedderClientInfo]] = {}

        # Evaluators
        self._registered_evaluator_infos: dict[type[EvaluatorBaseConfig], RegisteredEvaluatorInfo] = {}

        # Memory
        self._registered_memory_infos: dict[type[MemoryBaseConfig], RegisteredMemoryInfo] = {}

        # Object Stores
        self._registered_object_store_infos: dict[type[ObjectStoreBaseConfig], RegisteredObjectStoreInfo] = {}

        # Retrievers
        self._registered_retriever_provider_infos: dict[type[RetrieverBaseConfig], RegisteredRetrieverProviderInfo] = {}
        self._retriever_client_provider_to_framework: dict[type[RetrieverBaseConfig],
                                                           dict[str | None, RegisteredRetrieverClientInfo]] = {}
        self._retriever_client_framework_to_provider: dict[str | None,
                                                           dict[type[RetrieverBaseConfig],
                                                                RegisteredRetrieverClientInfo]] = {}

        # Registry Handlers
        self._registered_registry_handler_infos: dict[type[RegistryHandlerBaseConfig],
                                                      RegisteredRegistryHandlerInfo] = {}

        # Tool Wrappers
        self._registered_tool_wrappers: dict[str, RegisteredToolWrapper] = {}

        # TTC Strategies
        self._registered_ttc_strategies: dict[type[TTCStrategyBaseConfig], RegisteredTTCStrategyInfo] = {}

        # Packages
        self._registered_packages: dict[str, RegisteredPackage] = {}

        self._registration_changed_hooks: list[Callable[[], None]] = []
        self._registration_changed_hooks_active: bool = True

        self._registered_channel_map = {}

    def _registration_changed(self):

        if (not self._registration_changed_hooks_active):
            return

        logger.debug("Registration changed. Notifying hooks.")

        for hook in self._registration_changed_hooks:
            hook()

    def add_registration_changed_hook(self, cb: Callable[[], typing.Any]) -> None:

        self._registration_changed_hooks.append(cb)

    @contextmanager
    def pause_registration_changed_hooks(self):

        self._registration_changed_hooks_active = False

        try:
            yield
        finally:
            self._registration_changed_hooks_active = True

            # Ensure that the registration changed hooks are called
            self._registration_changed()

    def register_telemetry_exporter(self, registration: RegisteredTelemetryExporter):

        if (registration.config_type in self._registered_telemetry_exporters):
            raise ValueError(f"A telemetry exporter with the same config type `{registration.config_type}` has already "
                             "been registered.")

        self._registered_telemetry_exporters[registration.config_type] = registration

        self._registration_changed()

    def get_telemetry_exporter(self, config_type: type[TelemetryExporterBaseConfig]) -> RegisteredTelemetryExporter:

        try:
            return self._registered_telemetry_exporters[config_type]
        except KeyError as err:
            raise KeyError(f"Could not find a registered telemetry exporter for config `{config_type}`. "
                           f"Registered configs: {set(self._registered_telemetry_exporters.keys())}") from err

    def get_registered_telemetry_exporters(self) -> list[RegisteredInfo[TelemetryExporterBaseConfig]]:

        return list(self._registered_telemetry_exporters.values())

    def register_logging_method(self, registration: RegisteredLoggingMethod):

        if (registration.config_type in self._registered_logging_methods):
            raise ValueError(f"A logging method with the same config type `{registration.config_type}` has already "
                             "been registered.")

        self._registered_logging_methods[registration.config_type] = registration

        self._registration_changed()

    def get_logging_method(self, config_type: type[LoggingBaseConfig]) -> RegisteredLoggingMethod:
        try:
            return self._registered_logging_methods[config_type]
        except KeyError as err:
            raise KeyError(f"No logging method found for config `{config_type}`. "
                           f"Known: {set(self._registered_logging_methods.keys())}") from err

    def get_registered_logging_method(self) -> list[RegisteredInfo[LoggingBaseConfig]]:

        return list(self._registered_logging_methods.values())

    def register_front_end(self, registration: RegisteredFrontEndInfo):

        if (registration.config_type in self._registered_front_end_infos):
            raise ValueError(f"A front end with the same config type `{registration.config_type}` has already been "
                             "registered.")

        self._registered_front_end_infos[registration.config_type] = registration

        self._registration_changed()

    def get_front_end(self, config_type: type[FrontEndBaseConfig]) -> RegisteredFrontEndInfo:

        try:
            return self._registered_front_end_infos[config_type]
        except KeyError as err:
            raise KeyError(f"Could not find a registered front end for config `{config_type}`. "
                           f"Registered configs: {set(self._registered_front_end_infos.keys())}") from err

    def get_registered_front_ends(self) -> list[RegisteredInfo[FrontEndBaseConfig]]:

        return list(self._registered_front_end_infos.values())

    def register_function(self, registration: RegisteredFunctionInfo):

        if (registration.config_type in self._registered_functions):
            raise ValueError(f"A function with the same config type `{registration.config_type}` has already been "
                             "registered.")

        self._registered_functions[registration.config_type] = registration

        self._registration_changed()

    def get_function(self, config_type: type[FunctionBaseConfig]) -> RegisteredFunctionInfo:

        try:
            return self._registered_functions[config_type]
        except KeyError as err:
            raise KeyError(f"Could not find a registered function for config `{config_type}`. "
                           f"Registered configs: {set(self._registered_functions.keys())}") from err

    def get_registered_functions(self) -> list[RegisteredInfo[FunctionBaseConfig]]:

        return list(self._registered_functions.values())

    def register_function_group(self, registration: RegisteredFunctionGroupInfo):
        """Register a function group with the type registry.

        Args:
            registration: The function group registration information

        Raises:
            ValueError: If a function group with the same config type is already registered
        """
        if (registration.config_type in self._registered_function_groups):
            raise ValueError(
                f"A function group with the same config type `{registration.config_type}` has already been "
                "registered.")

        self._registered_function_groups[registration.config_type] = registration

        self._registration_changed()

    def get_function_group(self, config_type: type[FunctionGroupBaseConfig]) -> RegisteredFunctionGroupInfo:
        """Get a registered function group by its config type.

        Args:
            config_type: The function group configuration type

        Returns:
            RegisteredFunctionGroupInfo: The registered function group information

        Raises:
            KeyError: If no function group is registered for the given config type
        """
        try:
            return self._registered_function_groups[config_type]
        except KeyError as err:
            raise KeyError(f"Could not find a registered function group for config `{config_type}`. "
                           f"Registered configs: {set(self._registered_function_groups.keys())}") from err

    def get_registered_function_groups(self) -> list[RegisteredInfo[FunctionGroupBaseConfig]]:
        """Get all registered function groups.

        Returns:
            list[RegisteredInfo[FunctionGroupBaseConfig]]: List of all registered function groups
        """
        return list(self._registered_function_groups.values())

    def register_llm_provider(self, info: RegisteredLLMProviderInfo):

        if (info.config_type in self._registered_llm_provider_infos):
            raise ValueError(
                f"An LLM provider with the same config type `{info.config_type}` has already been registered.")

        self._registered_llm_provider_infos[info.config_type] = info

        self._registration_changed()

    def get_llm_provider(self, config_type: type[LLMBaseConfig]) -> RegisteredLLMProviderInfo:

        try:
            return self._registered_llm_provider_infos[config_type]
        except KeyError as err:
            raise KeyError(f"Could not find a registered LLM provider for config `{config_type}`. "
                           f"Registered configs: {set(self._registered_llm_provider_infos.keys())}") from err

    def get_registered_llm_providers(self) -> list[RegisteredInfo[LLMBaseConfig]]:
        return list(self._registered_llm_provider_infos.values())

    def register_auth_provider(self, info: RegisteredAuthProviderInfo):

        if (info.config_type in self._registered_auth_provider_infos):
            raise ValueError(
                f"An Authentication Provider with the same config type `{info.config_type}` has already been "
                "registered.")

        self._registered_auth_provider_infos[info.config_type] = info

        self._registration_changed()

    def get_auth_provider(self, config_type: type[AuthProviderBaseConfig]) -> RegisteredAuthProviderInfo:
        try:
            return self._registered_auth_provider_infos[config_type]
        except KeyError as err:
            raise KeyError(f"Could not find a registered Authentication Provider for config `{config_type}`. "
                           f"Registered configs: {set(self._registered_auth_provider_infos.keys())}") from err

    def get_registered_auth_providers(self) -> list[RegisteredInfo[AuthProviderBaseConfig]]:
        return list(self._registered_auth_provider_infos.values())

    def register_llm_client(self, info: RegisteredLLMClientInfo):

        if (info.config_type in self._llm_client_provider_to_framework
                and info.llm_framework in self._llm_client_provider_to_framework[info.config_type]):
            raise ValueError(f"An LLM client with the same config type `{info.config_type}` "
                             f"and LLM framework `{info.llm_framework}` has already been registered.")

        self._llm_client_provider_to_framework.setdefault(info.config_type, {})[info.llm_framework] = info
        self._llm_client_framework_to_provider.setdefault(info.llm_framework, {})[info.config_type] = info

        self._registration_changed()

    def get_llm_client(self, config_type: type[LLMBaseConfig], wrapper_type: str) -> RegisteredLLMClientInfo:

        try:
            client_info = self._llm_client_provider_to_framework[config_type][wrapper_type]
        except KeyError as err:
            raise KeyError(f"An invalid LLM config and wrapper combination was supplied. Config: `{config_type}`, "
                           f"Wrapper: `{wrapper_type}`. The workflow is requesting a {wrapper_type} LLM client but "
                           f"there is no registered conversion from that LLM provider to LLM framework: "
                           f"{wrapper_type}. "
                           f"Please provide an LLM configuration from one of the following providers: "
                           f"{set(self._llm_client_provider_to_framework.keys())}") from err

        return client_info

    def register_embedder_provider(self, info: RegisteredEmbedderProviderInfo):

        if (info.config_type in self._registered_embedder_provider_infos):
            raise ValueError(f"An Embedder provider with the same config type `{info.config_type}` has already been "
                             "registered.")

        self._registered_embedder_provider_infos[info.config_type] = info

        self._registration_changed()

    def get_embedder_provider(self, config_type: type[EmbedderBaseConfig]) -> RegisteredEmbedderProviderInfo:

        try:
            return self._registered_embedder_provider_infos[config_type]
        except KeyError as err:
            raise KeyError(f"Could not find a registered Embedder provider for config `{config_type}`. "
                           f"Registered configs: {set(self._registered_embedder_provider_infos.keys())}") from err

    def get_registered_embedder_providers(self) -> list[RegisteredInfo[EmbedderBaseConfig]]:

        return list(self._registered_embedder_provider_infos.values())

    def register_embedder_client(self, info: RegisteredEmbedderClientInfo):

        if (info.config_type in self._embedder_client_provider_to_framework
                and info.llm_framework in self._embedder_client_provider_to_framework[info.config_type]):
            raise ValueError(f"An Embedder client with the same config type `{info.config_type}` has already been "
                             "registered.")

        self._embedder_client_provider_to_framework.setdefault(info.config_type, {})[info.llm_framework] = info
        self._embedder_client_framework_to_provider.setdefault(info.llm_framework, {})[info.config_type] = info

        self._registration_changed()

    def get_embedder_client(self, config_type: type[EmbedderBaseConfig],
                            wrapper_type: str) -> RegisteredEmbedderClientInfo:

        try:
            client_info = self._embedder_client_provider_to_framework[config_type][wrapper_type]
        except KeyError as err:
            raise KeyError(
                f"An invalid Embedder config and wrapper combination was supplied. Config: `{config_type}`, "
                f"Wrapper: `{wrapper_type}`. The workflow is requesting a {wrapper_type} Embedder client but "
                f"there is no registered conversion from that Embedder provider to LLM framework: {wrapper_type}. "
                "Please provide an Embedder configuration from one of the following providers: "
                f"{set(self._embedder_client_provider_to_framework.keys())}") from err

        return client_info

    def register_evaluator(self, info: RegisteredEvaluatorInfo):

        if (info.config_type in self._registered_evaluator_infos):
            raise ValueError(f"An Evaluator with the same config type `{info.config_type}` has already been "
                             "registered.")

        self._registered_evaluator_infos[info.config_type] = info

        self._registration_changed()

    def get_evaluator(self, config_type: type[EvaluatorBaseConfig]) -> RegisteredEvaluatorInfo:

        try:
            return self._registered_evaluator_infos[config_type]
        except KeyError as err:
            raise KeyError(f"Could not find a registered Evaluator for config `{config_type}`. "
                           f"Registered configs: {set(self._registered_evaluator_infos.keys())}") from err

    def get_registered_evaluators(self) -> list[RegisteredInfo[EvaluatorBaseConfig]]:

        return list(self._registered_evaluator_infos.values())

    def register_memory(self, info: RegisteredMemoryInfo):

        if (info.config_type in self._registered_memory_infos):
            raise ValueError(
                f"A Memory client with the same config type `{info.config_type}` has already been registered.")

        self._registered_memory_infos[info.config_type] = info

        self._registration_changed()

    def get_memory(self, config_type: type[MemoryBaseConfig]) -> RegisteredMemoryInfo:

        try:
            return self._registered_memory_infos[config_type]
        except KeyError as err:
            raise KeyError(f"Could not find a registered Memory client for config `{config_type}`. "
                           f"Registered configs: {set(self._registered_memory_infos.keys())}") from err

    def get_registered_memorys(self) -> list[RegisteredInfo[MemoryBaseConfig]]:

        return list(self._registered_memory_infos.values())

    def register_object_store(self, info: RegisteredObjectStoreInfo):

        if (info.config_type in self._registered_object_store_infos):
            raise ValueError(f"An Object Store with the same config type `{info.config_type}` has already been "
                             "registered.")

        self._registered_object_store_infos[info.config_type] = info

        self._registration_changed()

    def get_object_store(self, config_type: type[ObjectStoreBaseConfig]) -> RegisteredObjectStoreInfo:

        try:
            return self._registered_object_store_infos[config_type]
        except KeyError as err:
            raise KeyError(f"Could not find a registered Object Store for config `{config_type}`. "
                           f"Registered configs: {set(self._registered_object_store_infos.keys())}") from err

    def get_registered_object_stores(self) -> list[RegisteredInfo[ObjectStoreBaseConfig]]:

        return list(self._registered_object_store_infos.values())

    def register_retriever_provider(self, info: RegisteredRetrieverProviderInfo):

        if (info.config_type in self._registered_retriever_provider_infos):
            raise ValueError(
                f"A Retriever provider with the same config type `{info.config_type}` has already been registered")

        self._registered_retriever_provider_infos[info.config_type] = info

        self._registration_changed()

    def get_retriever_provider(self, config_type: type[RetrieverBaseConfig]) -> RegisteredRetrieverProviderInfo:

        try:
            return self._registered_retriever_provider_infos[config_type]
        except KeyError as err:
            raise KeyError(f"Could not find a registered Retriever provider for config `{config_type}`. "
                           f"Registered configs: {set(self._registered_retriever_provider_infos.keys())}") from err

    def get_registered_retriever_providers(self) -> list[RegisteredInfo[RetrieverBaseConfig]]:

        return list(self._registered_retriever_provider_infos.values())

    def register_retriever_client(self, info: RegisteredRetrieverClientInfo):

        if (info.config_type in self._retriever_client_provider_to_framework
                and info.llm_framework in self._retriever_client_provider_to_framework[info.config_type]):
            raise ValueError(f"A Retriever client with the same config type `{info.config_type}` "
                             " and LLM framework `{info.llm_framework}` has already been registered.")

        self._retriever_client_provider_to_framework.setdefault(info.config_type, {})[info.llm_framework] = info
        self._retriever_client_framework_to_provider.setdefault(info.llm_framework, {})[info.config_type] = info

        self._registration_changed()

    def get_retriever_client(self, config_type: type[RetrieverBaseConfig],
                             wrapper_type: str | None) -> RegisteredRetrieverClientInfo:

        try:
            client_info = self._retriever_client_provider_to_framework[config_type][wrapper_type]
        except KeyError as err:
            raise KeyError(
                f"An invalid Retriever config and wrapper combination was supplied. Config: `{config_type}`, "
                f"Wrapper: `{wrapper_type}`. The workflow is requesting a {wrapper_type} Retriever client but "
                f"there is no registered conversion from that Retriever provider to LLM framework: {wrapper_type}. "
                "Please provide a Retriever configuration from one of the following providers: "
                f"{set(self._retriever_client_provider_to_framework.keys())}") from err

        return client_info

    def register_tool_wrapper(self, registration: RegisteredToolWrapper):

        if (registration.llm_framework in self._registered_tool_wrappers):
            raise ValueError(f"A tool wrapper for the LLM framework `{registration.llm_framework}` has already been "
                             "registered.")

        self._registered_tool_wrappers[registration.llm_framework] = registration

        self._registration_changed()

    def get_tool_wrapper(self, llm_framework: str) -> RegisteredToolWrapper:

        try:
            return self._registered_tool_wrappers[llm_framework]
        except KeyError as err:
            raise KeyError(f"Could not find a registered tool wrapper for LLM framework `{llm_framework}`. "
                           f"Registered LLM frameworks: {set(self._registered_tool_wrappers.keys())}") from err

    def register_ttc_strategy(self, info: RegisteredTTCStrategyInfo):
        if (info.config_type in self._registered_ttc_strategies):
            raise ValueError(
                f"An TTC strategy with the same config type `{info.config_type}` has already been registered.")

        self._registered_ttc_strategies[info.config_type] = info

        self._registration_changed()

    def get_ttc_strategy(self, config_type: type[TTCStrategyBaseConfig]) -> RegisteredTTCStrategyInfo:
        try:
            strategy = self._registered_ttc_strategies[config_type]
        except Exception as e:
            raise KeyError(f"Could not find a registered TTC strategy for config `{config_type}`. ") from e
        return strategy

    def get_registered_ttc_strategies(self) -> list[RegisteredInfo[TTCStrategyBaseConfig]]:
        return list(self._registered_ttc_strategies.values())

    def register_registry_handler(self, info: RegisteredRegistryHandlerInfo):

        if (info.config_type in self._registered_memory_infos):
            raise ValueError(
                f"A Registry Handler with the same config type `{info.config_type}` has already been registered.")

        self._registered_registry_handler_infos[info.config_type] = info
        self._registered_channel_map[info.config_type.static_type()] = info

        self._registration_changed()

    def get_registry_handler(self, config_type: type[RegistryHandlerBaseConfig]) -> RegisteredRegistryHandlerInfo:

        try:
            return self._registered_registry_handler_infos[config_type]
        except KeyError as err:
            raise KeyError(f"Could not find a registered Registry Handler for config `{config_type}`. "
                           f"Registered configs: {set(self._registered_registry_handler_infos.keys())}") from err

    def get_registered_registry_handlers(self) -> list[RegisteredInfo[RegistryHandlerBaseConfig]]:

        return list(self._registered_registry_handler_infos.values())

    def register_package(self, package_name: str, package_version: str | None = None):

        discovery_metadata = DiscoveryMetadata.from_package_name(package_name=package_name,
                                                                 package_version=package_version)
        package = RegisteredPackage(discovery_metadata=discovery_metadata, package_name=package_name)
        self._registered_packages[package.package_name] = package

        self._registration_changed()

    def get_infos_by_type(self, component_type: ComponentEnum) -> dict:

        if component_type == ComponentEnum.FRONT_END:
            return self._registered_front_end_infos

        if component_type == ComponentEnum.AUTHENTICATION_PROVIDER:
            return self._registered_auth_provider_infos

        if component_type == ComponentEnum.FUNCTION:
            return self._registered_functions

        if component_type == ComponentEnum.FUNCTION_GROUP:
            return self._registered_function_groups

        if component_type == ComponentEnum.TOOL_WRAPPER:
            return self._registered_tool_wrappers

        if component_type == ComponentEnum.LLM_PROVIDER:
            return self._registered_llm_provider_infos

        if component_type == ComponentEnum.LLM_CLIENT:
            leaf_llm_client_infos = {}
            for framework in self._llm_client_provider_to_framework.values():
                for info in framework.values():
                    leaf_llm_client_infos[info.discovery_metadata.component_name] = info
            return leaf_llm_client_infos

        if component_type == ComponentEnum.EMBEDDER_PROVIDER:
            return self._registered_embedder_provider_infos

        if component_type == ComponentEnum.EMBEDDER_CLIENT:
            leaf_embedder_client_infos = {}
            for framework in self._embedder_client_provider_to_framework.values():
                for info in framework.values():
                    leaf_embedder_client_infos[info.discovery_metadata.component_name] = info
            return leaf_embedder_client_infos

        if component_type == ComponentEnum.RETRIEVER_PROVIDER:
            return self._registered_retriever_provider_infos

        if component_type == ComponentEnum.RETRIEVER_CLIENT:
            leaf_retriever_client_infos = {}
            for framework in self._retriever_client_provider_to_framework.values():
                for info in framework.values():
                    leaf_retriever_client_infos[info.discovery_metadata.component_name] = info
            return leaf_retriever_client_infos

        if component_type == ComponentEnum.EVALUATOR:
            return self._registered_evaluator_infos

        if component_type == ComponentEnum.MEMORY:
            return self._registered_memory_infos

        if component_type == ComponentEnum.OBJECT_STORE:
            return self._registered_object_store_infos

        if component_type == ComponentEnum.REGISTRY_HANDLER:
            return self._registered_registry_handler_infos

        if component_type == ComponentEnum.LOGGING:
            return self._registered_logging_methods

        if component_type == ComponentEnum.TRACING:
            return self._registered_telemetry_exporters

        if component_type == ComponentEnum.PACKAGE:
            return self._registered_packages

        if component_type == ComponentEnum.TTC_STRATEGY:
            return self._registered_ttc_strategies

        raise ValueError(f"Supplied an unsupported component type {component_type}")

    def get_registered_types_by_component_type(self, component_type: ComponentEnum) -> list[str]:

        if component_type == ComponentEnum.FUNCTION:
            return [i.static_type() for i in self._registered_functions]

        if component_type == ComponentEnum.FUNCTION_GROUP:
            return [i.static_type() for i in self._registered_function_groups]

        if component_type == ComponentEnum.TOOL_WRAPPER:
            return list(self._registered_tool_wrappers)

        if component_type == ComponentEnum.LLM_PROVIDER:
            return [i.static_type() for i in self._registered_llm_provider_infos]

        if component_type == ComponentEnum.LLM_CLIENT:
            leaf_client_provider_framework_types = []
            for framework in self._llm_client_provider_to_framework.values():
                for info in framework.values():
                    leaf_client_provider_framework_types.append([info.discovery_metadata.component_name])
            return leaf_client_provider_framework_types

        if component_type == ComponentEnum.EMBEDDER_PROVIDER:
            return [i.static_type() for i in self._registered_embedder_provider_infos]

        if component_type == ComponentEnum.EMBEDDER_CLIENT:
            leaf_embedder_provider_framework_types = []
            for framework in self._embedder_client_provider_to_framework.values():
                for info in framework.values():
                    leaf_embedder_provider_framework_types.append([info.discovery_metadata.component_name])
            return leaf_embedder_provider_framework_types

        if component_type == ComponentEnum.EVALUATOR:
            return [i.static_type() for i in self._registered_evaluator_infos]

        if component_type == ComponentEnum.MEMORY:
            return [i.static_type() for i in self._registered_memory_infos]

        if component_type == ComponentEnum.REGISTRY_HANDLER:
            return [i.static_type() for i in self._registered_registry_handler_infos]

        if component_type == ComponentEnum.LOGGING:
            return [i.static_type() for i in self._registered_logging_methods]

        if component_type == ComponentEnum.TRACING:
            return [i.static_type() for i in self._registered_telemetry_exporters]

        if component_type == ComponentEnum.PACKAGE:
            return list(self._registered_packages)

        if component_type == ComponentEnum.TTC_STRATEGY:
            return [i.static_type() for i in self._registered_ttc_strategies]

        raise ValueError(f"Supplied an unsupported component type {component_type}")

    def get_registered_channel_info_by_channel_type(self, channel_type: str) -> RegisteredRegistryHandlerInfo:
        return self._registered_channel_map[channel_type]

    def _do_compute_annotation(self, cls: type[TypedBaseModelT], registrations: list[RegisteredInfo[TypedBaseModelT]]):

        while (len(registrations) < 2):
            registrations.append(RegisteredInfo[TypedBaseModelT](full_type=f"_ignore/{len(registrations)}",
                                                                 config_type=cls))

        short_names: dict[str, int] = {}
        type_list: list[tuple[str, type[TypedBaseModelT]]] = []

        # For all keys in the list, split the key by / and increment the count of the last element
        for key in registrations:
            short_names[key.local_name] = short_names.get(key.local_name, 0) + 1

            type_list.append((key.full_type, key.config_type))

        # Now loop again and if the short name is unique, then create two entries, for the short and full name
        for key in registrations:

            if (short_names[key.local_name] == 1):
                type_list.append((key.local_name, key.config_type))

        return typing.Union[*tuple(typing.Annotated[x_type, Tag(x_id)] for x_id, x_type in type_list)]

    def compute_annotation(self, cls: type[TypedBaseModelT]):

        if issubclass(cls, AuthProviderBaseConfig):
            return self._do_compute_annotation(cls, self.get_registered_auth_providers())

        if issubclass(cls, EmbedderBaseConfig):
            return self._do_compute_annotation(cls, self.get_registered_embedder_providers())

        if issubclass(cls, EvaluatorBaseConfig):
            return self._do_compute_annotation(cls, self.get_registered_evaluators())

        if issubclass(cls, FrontEndBaseConfig):
            return self._do_compute_annotation(cls, self.get_registered_front_ends())

        if issubclass(cls, FunctionBaseConfig):
            return self._do_compute_annotation(cls, self.get_registered_functions())

        if issubclass(cls, FunctionGroupBaseConfig):
            return self._do_compute_annotation(cls, self.get_registered_function_groups())

        if issubclass(cls, LLMBaseConfig):
            return self._do_compute_annotation(cls, self.get_registered_llm_providers())

        if issubclass(cls, MemoryBaseConfig):
            return self._do_compute_annotation(cls, self.get_registered_memorys())

        if issubclass(cls, ObjectStoreBaseConfig):
            return self._do_compute_annotation(cls, self.get_registered_object_stores())

        if issubclass(cls, RegistryHandlerBaseConfig):
            return self._do_compute_annotation(cls, self.get_registered_registry_handlers())

        if issubclass(cls, RetrieverBaseConfig):
            return self._do_compute_annotation(cls, self.get_registered_retriever_providers())

        if issubclass(cls, TelemetryExporterBaseConfig):
            return self._do_compute_annotation(cls, self.get_registered_telemetry_exporters())

        if issubclass(cls, LoggingBaseConfig):
            return self._do_compute_annotation(cls, self.get_registered_logging_method())

        if issubclass(cls, TTCStrategyBaseConfig):
            return self._do_compute_annotation(cls, self.get_registered_ttc_strategies())

        raise ValueError(f"Supplied an unsupported component type {cls}")


class GlobalTypeRegistry:

    _global_registry: TypeRegistry = TypeRegistry()

    @staticmethod
    def get() -> TypeRegistry:
        return GlobalTypeRegistry._global_registry

    @staticmethod
    @contextmanager
    def push():

        saved = GlobalTypeRegistry._global_registry
        registry = deepcopy(saved)

        try:
            GlobalTypeRegistry._global_registry = registry

            yield registry
        finally:
            GlobalTypeRegistry._global_registry = saved
            GlobalTypeRegistry._global_registry._registration_changed()


# Finally, update the Config object each time the registry changes
GlobalTypeRegistry.get().add_registration_changed_hook(lambda: Config.rebuild_annotations())
