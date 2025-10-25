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

from typing import TYPE_CHECKING, List, Optional

from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.domain import Domain
from great_expectations.core.metric_domain_types import MetricDomainTypes
from kedro_expectations.assistant.experimental.rule_based_profiler.domain_builder import DomainBuilder
from kedro_expectations.assistant.experimental.rule_based_profiler.helpers.util import (
    get_parameter_value_and_validate_return_type,
)
from kedro_expectations.assistant.experimental.rule_based_profiler.parameter_container import (
    VARIABLES_KEY,
    ParameterContainer,
)

if TYPE_CHECKING:
    from great_expectations.data_context.data_context.abstract_data_context import (
        AbstractDataContext,
    )


class TableDomainBuilder(DomainBuilder):
    def __init__(
        self,
        data_context: Optional[AbstractDataContext] = None,
    ) -> None:
        """
        Args:
            data_context: AbstractDataContext associated with this DomainBuilder
        """
        super().__init__(data_context=data_context)

    @property
    @override
    def domain_type(self) -> MetricDomainTypes:
        return MetricDomainTypes.TABLE

    """
    The interface method of TableDomainBuilder emits a single Domain object, corresponding to the implied Batch (table).

    Note that for appropriate use-cases, it should be readily possible to build a multi-batch implementation, where a
    separate Domain object is emitted for each individual Batch (using its respective batch_id).  (This is future work.)
    """  # noqa: E501 # FIXME CoP

    @override
    def _get_domains(
        self,
        rule_name: str,
        variables: Optional[ParameterContainer] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> List[Domain]:
        other_table_name: Optional[str]
        try:
            # Obtain table from "rule state" (i.e., variables and parameters); from instance variable otherwise.  # noqa: E501 # FIXME CoP
            other_table_name = get_parameter_value_and_validate_return_type(
                domain=None,
                parameter_reference=f"{VARIABLES_KEY}table",
                expected_return_type=None,
                variables=variables,
                parameters=None,
            )
        except KeyError:
            other_table_name = None

        domains: List[Domain]
        if other_table_name:
            domains = [
                Domain(
                    domain_type=self.domain_type,
                    domain_kwargs={
                        "table": other_table_name,
                    },
                    rule_name=rule_name,
                ),
            ]
        else:
            domains = [
                Domain(
                    domain_type=self.domain_type,
                    rule_name=rule_name,
                ),
            ]

        return domains
