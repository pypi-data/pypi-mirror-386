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
# This file includes code originally from:
#   Great Expectations - https://github.com/great-expectations/great_expectations
# Copied from version: [v1.5.0]
# This functionality was later deprecated and removed from the original project.

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kedro_expectations.assistant.experimental.metric_repository.data_store import DataStore
    from kedro_expectations.assistant.experimental.metric_repository.metrics import MetricRun


class MetricRepository:
    """A repository for storing and retrieving MetricRuns.

    Args:
        data_store: The DataStore to use for storing and retrieving MetricRuns.
    """

    def __init__(self, data_store: DataStore):
        self._data_store = data_store

    def add_metric_run(self, metric_run: MetricRun) -> uuid.UUID:
        return self._data_store.add(value=metric_run)
