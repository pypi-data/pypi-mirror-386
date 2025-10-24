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

import typing
from enum import Enum
from pathlib import Path

from pydantic import BaseModel
from pydantic import Discriminator
from pydantic import model_validator

from nat.data_models.common import TypedBaseModel
from nat.data_models.dataset_handler import EvalDatasetConfig
from nat.data_models.dataset_handler import EvalS3Config
from nat.data_models.evaluator import EvaluatorBaseConfig
from nat.data_models.intermediate_step import IntermediateStepType
from nat.data_models.profiler import ProfilerConfig


class JobEvictionPolicy(str, Enum):
    """Policy for evicting old jobs when max_jobs is exceeded."""
    TIME_CREATED = "time_created"
    TIME_MODIFIED = "time_modified"


class EvalCustomScriptConfig(BaseModel):
    # Path to the script to run
    script: Path
    # Keyword arguments to pass to the script
    kwargs: dict[str, str] = {}


class JobManagementConfig(BaseModel):
    # Whether to append a unique job ID to the output directory for each run
    append_job_id_to_output_dir: bool = False
    # Maximum number of jobs to keep in the output directory. Oldest jobs will be evicted.
    # A value of 0 means no limit.
    max_jobs: int = 0
    # Policy for evicting old jobs. Defaults to using time_created.
    eviction_policy: JobEvictionPolicy = JobEvictionPolicy.TIME_CREATED


class EvalOutputConfig(BaseModel):
    # Output directory for the workflow and evaluation results
    dir: Path = Path("./.tmp/nat/examples/default/")
    # S3 prefix for the workflow and evaluation results
    remote_dir: str | None = None
    # Custom function to pre-evaluation process the eval input
    # Format: "module.path.function_name"
    custom_pre_eval_process_function: str | None = None
    # Custom scripts to run after the workflow and evaluation results are saved
    custom_scripts: dict[str, EvalCustomScriptConfig] = {}
    # S3 config for uploading the contents of the output directory
    s3: EvalS3Config | None = None
    # Whether to cleanup the output directory before running the workflow
    cleanup: bool = True
    # Job management configuration (job id, eviction, etc.)
    job_management: JobManagementConfig = JobManagementConfig()
    # Filter for the workflow output steps
    workflow_output_step_filter: list[IntermediateStepType] | None = None


class EvalGeneralConfig(BaseModel):
    max_concurrency: int = 8

    # Workflow alias for displaying in evaluation UI, if not provided,
    # the workflow type will be used
    workflow_alias: str | None = None

    # Output directory for the workflow and evaluation results
    output_dir: Path = Path("./.tmp/nat/examples/default/")

    # If present overrides output_dir
    output: EvalOutputConfig | None = None

    # Dataset for running the workflow and evaluating
    dataset: EvalDatasetConfig | None = None

    # Inference profiler
    profiler: ProfilerConfig | None = None

    # overwrite the output_dir with the output config if present
    @model_validator(mode="before")
    @classmethod
    def override_output_dir(cls, values):
        if values.get("output") and values["output"].get("dir"):
            values["output_dir"] = values["output"]["dir"]
        return values


class EvalConfig(BaseModel):

    # General Evaluation Options
    general: EvalGeneralConfig = EvalGeneralConfig()

    # Evaluators
    evaluators: dict[str, EvaluatorBaseConfig] = {}

    @classmethod
    def rebuild_annotations(cls):

        from nat.cli.type_registry import GlobalTypeRegistry

        type_registry = GlobalTypeRegistry.get()

        EvaluatorsAnnotation = dict[str,
                                    typing.Annotated[type_registry.compute_annotation(EvaluatorBaseConfig),
                                                     Discriminator(TypedBaseModel.discriminator)]]

        should_rebuild = False

        evaluators_field = cls.model_fields.get("evaluators")
        if evaluators_field is not None and evaluators_field.annotation != EvaluatorsAnnotation:
            evaluators_field.annotation = EvaluatorsAnnotation
            should_rebuild = True

        if (should_rebuild):
            cls.model_rebuild(force=True)
