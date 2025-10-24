# Copyright 2025 Iguazio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import enum

from pydantic.v1 import BaseModel

from mlrun.common.types import StrEnum

from .background_task import BackgroundTaskList


class DeployResponse(BaseModel):
    data: dict
    background_tasks: BackgroundTaskList


class ModelRunnerStepData(StrEnum):
    MODELS = "models"
    MODEL_TO_EXECUTION_MECHANISM = "execution_mechanism_by_model_name"
    MONITORING_DATA = "monitoring_data"


class MonitoringData(StrEnum):
    INPUTS = "inputs"
    OUTPUTS = "outputs"
    INPUT_PATH = "input_path"
    RESULT_PATH = "result_path"
    CREATION_STRATEGY = "creation_strategy"
    LABELS = "labels"
    MODEL_PATH = "model_path"
    MODEL_ENDPOINT_UID = "model_endpoint_uid"
    MODEL_CLASS = "model_class"


class ModelsData(enum.Enum):
    MODEL_CLASS = 0
    MODEL_PARAMETERS = 1


MAX_BATCH_JOB_DURATION = "1w"
