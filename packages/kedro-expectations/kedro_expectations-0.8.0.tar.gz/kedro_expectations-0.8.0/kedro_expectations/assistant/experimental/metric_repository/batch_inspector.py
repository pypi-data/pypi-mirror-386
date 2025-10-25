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
from typing import TYPE_CHECKING, List, Optional

from kedro_expectations.assistant.experimental.metric_repository.metrics import (
    Metric,
    MetricRun,
    MetricTypes,
)

if TYPE_CHECKING:
    from great_expectations.data_context import AbstractDataContext
    from great_expectations.datasource.fluent.interfaces import BatchRequest
    from kedro_expectations.assistant.experimental.metric_repository.metric_retriever import (
        MetricRetriever,
    )


class BatchInspector:
    """A BatchInspector is responsible for computing metrics for a batch of data.

    It uses MetricRetriever objects to retrieve metrics.
    """

    def __init__(self, context: AbstractDataContext, metric_retrievers: list[MetricRetriever]):
        self._context = context
        self._metric_retrievers = metric_retrievers

    def compute_metric_list_run(
        self,
        data_asset_id: uuid.UUID,
        batch_request: BatchRequest,
        metric_list: Optional[List[MetricTypes]],
    ) -> MetricRun:
        """Method that computes a MetricRun for a list of metrics.
        Called by GX Agent to compute a MetricRun as part of a RunMetricsEvent.
        Args:
            data_asset_id (uuid.UUID): current data asset id.
            batch_request (BatchRequest): BatchRequest for current batch.
            metrics_list (Optional[List[MetricTypes]]): List of metrics to compute.
        Returns:
            MetricRun: _description_
        """
        # TODO: eventually we will keep this and retire `compute_metric_run`.
        metrics: list[Metric] = []
        for metric_retriever in self._metric_retrievers:
            metrics.extend(
                metric_retriever.get_metrics(batch_request=batch_request, metric_list=metric_list)
            )
        return MetricRun(data_asset_id=data_asset_id, metrics=metrics)

    def compute_metric_run(
        self, data_asset_id: uuid.UUID, batch_request: BatchRequest
    ) -> MetricRun:
        metrics: list[Metric] = []
        for metric_retriever in self._metric_retrievers:
            metrics.extend(metric_retriever.get_metrics(batch_request=batch_request))

        return MetricRun(data_asset_id=data_asset_id, metrics=metrics)

    def _generate_run_id(self) -> uuid.UUID:
        return uuid.uuid4()
