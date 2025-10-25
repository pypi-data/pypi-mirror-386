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

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from great_expectations.core.batch import Batch, BatchRequestBase  # noqa: TC001 # FIXME CoP
from great_expectations.core.domain import Domain  # noqa: TC001 # FIXME CoP
from great_expectations.core.metric_domain_types import (
    MetricDomainTypes,  # noqa: TC001 # FIXME CoP
)
from kedro_expectations.assistant.experimental.rule_based_profiler.builder import Builder
from kedro_expectations.assistant.experimental.rule_based_profiler.helpers.util import (
    get_batch_ids as get_batch_ids_from_batch_list_or_batch_request,
)
from kedro_expectations.assistant.experimental.rule_based_profiler.helpers.util import (
    get_resolved_metrics_by_key,
)
from kedro_expectations.assistant.experimental.rule_based_profiler.helpers.util import (
    get_validator as get_validator_using_batch_list_or_batch_request,
)
from kedro_expectations.assistant.experimental.rule_based_profiler.parameter_container import (
    ParameterContainer,  # noqa: TC001 # FIXME CoP
)
from great_expectations.validator.computed_metric import MetricValue  # noqa: TC001 # FIXME CoP
from great_expectations.validator.metric_configuration import MetricConfiguration

if TYPE_CHECKING:
    from great_expectations.data_context.data_context.abstract_data_context import (
        AbstractDataContext,
    )
    from great_expectations.validator.validator import Validator


class DomainBuilder(ABC, Builder):
    """
    A DomainBuilder provides methods to get domains based on one or more batches of data.
    """

    def __init__(
        self,
        data_context: Optional[AbstractDataContext] = None,
    ) -> None:
        """
        Args:
            data_context: AbstractDataContext associated with DomainBuilder
        """
        super().__init__(data_context=data_context)

    def get_domains(
        self,
        rule_name: str,
        variables: Optional[ParameterContainer] = None,
        batch_list: Optional[List[Batch]] = None,
        batch_request: Optional[Union[BatchRequestBase, dict]] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> List[Domain]:
        """
        Args:
            rule_name: name of Rule object, for which "Domain" objects are obtained.
            variables: attribute name/value pairs
            batch_list: Explicit list of Batch objects to supply data at runtime.
            batch_request: Explicit batch_request used to supply data at runtime.
            runtime_configuration: Additional run-time settings (see "Validator.DEFAULT_RUNTIME_CONFIGURATION").

        Returns:
            List of Domain objects.

        Note: Please do not overwrite the public "get_domains()" method.  If a child class needs to check parameters,
        then please do so in its implementation of the (private) "_get_domains()" method, or in a utility method.
        """  # noqa: E501 # FIXME CoP
        self.set_batch_list_if_null_batch_request(
            batch_list=batch_list,
            batch_request=batch_request,
        )

        return self._get_domains(
            rule_name=rule_name,
            variables=variables,
            runtime_configuration=runtime_configuration,
        )

    @property
    @abstractmethod
    def domain_type(self) -> MetricDomainTypes:
        pass

    @abstractmethod
    def _get_domains(
        self,
        rule_name: str,
        variables: Optional[ParameterContainer] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> List[Domain]:
        """
        _get_domains is the primary workhorse for the DomainBuilder
        """

        pass

    def get_table_row_counts(
        self,
        validator: Optional[Validator] = None,
        batch_ids: Optional[List[str]] = None,
        variables: Optional[ParameterContainer] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> Dict[str, int]:
        if validator is None:
            validator = self.get_validator(variables=variables)

        if batch_ids is None:
            batch_ids = self.get_batch_ids(variables=variables)

        batch_id: str

        metric_configurations_by_batch_id: Dict[str, List[MetricConfiguration]] = {
            batch_id: [
                MetricConfiguration(
                    metric_name="table.row_count",
                    metric_domain_kwargs={
                        "batch_id": batch_id,
                    },
                    metric_value_kwargs={
                        "include_nested": True,
                    },
                )
            ]
            for batch_id in batch_ids  # type: ignore[union-attr] # could be None
        }

        resolved_metrics_by_batch_id: Dict[str, Dict[Tuple[str, str, str], MetricValue]] = (
            get_resolved_metrics_by_key(
                validator=validator,  # type: ignore[arg-type] # could be None
                metric_configurations_by_key=metric_configurations_by_batch_id,
                runtime_configuration=runtime_configuration,
            )
        )

        resolved_metrics: Dict[Tuple[str, str, str], MetricValue]
        metric_value: Any
        table_row_count_lists_by_batch_id: Dict[str, List[int]] = {
            batch_id: [metric_value for metric_value in resolved_metrics.values()]  # type: ignore[misc] # incompatible values
            for batch_id, resolved_metrics in resolved_metrics_by_batch_id.items()
        }
        table_row_counts_by_batch_id: Dict[str, int] = {
            batch_id: metric_value[0]
            for batch_id, metric_value in table_row_count_lists_by_batch_id.items()
        }

        return table_row_counts_by_batch_id

    def get_validator(
        self,
        variables: Optional[ParameterContainer] = None,
    ) -> Optional[Validator]:
        return get_validator_using_batch_list_or_batch_request(
            purpose="domain_builder",
            data_context=self.data_context,
            batch_list=self.batch_list,
            batch_request=self.batch_request,
            domain=None,
            variables=variables,
            parameters=None,
        )

    def get_batch_ids(
        self,
        variables: Optional[ParameterContainer] = None,
    ) -> Optional[List[str]]:
        return get_batch_ids_from_batch_list_or_batch_request(
            data_context=self.data_context,
            batch_list=self.batch_list,
            batch_request=self.batch_request,
            domain=None,
            variables=variables,
            parameters=None,
        )
