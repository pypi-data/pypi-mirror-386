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

import logging
from typing import TYPE_CHECKING, Dict, Optional

import numpy as np

from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.domain import Domain  # noqa: TC001 # FIXME CoP
from kedro_expectations.assistant.experimental.rule_based_profiler.estimators.numeric_range_estimation_result import (  # noqa: E501 # FIXME CoP
    NumericRangeEstimationResult,  # noqa: TC001 # FIXME CoP
)
from kedro_expectations.assistant.experimental.rule_based_profiler.estimators.numeric_range_estimator import (
    NumericRangeEstimator,
)
from kedro_expectations.assistant.experimental.rule_based_profiler.helpers.util import (
    build_numeric_range_estimation_result,
    datetime_semantic_domain_type,
)
from kedro_expectations.assistant.experimental.rule_based_profiler.parameter_container import (
    ParameterContainer,  # noqa: TC001 # FIXME CoP
)
from great_expectations.util import convert_ndarray_to_datetime_dtype_best_effort

if TYPE_CHECKING:
    from numbers import Number

    import numpy.typing as npt

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ExactNumericRangeEstimator(NumericRangeEstimator):
    """
    Implements deterministic, incorporating entire observed value range, computation.
    """

    def __init__(
        self,
    ) -> None:
        super().__init__(
            name="exact",
            configuration=None,
        )

    @override
    def _get_numeric_range_estimate(
        self,
        metric_values: npt.NDArray,
        domain: Domain,
        variables: Optional[ParameterContainer] = None,
        parameters: Optional[Dict[str, ParameterContainer]] = None,
    ) -> NumericRangeEstimationResult:
        datetime_detected: bool = datetime_semantic_domain_type(domain=domain)
        metric_values_converted: npt.NDArray
        (
            _,
            _,
            metric_values_converted,
        ) = convert_ndarray_to_datetime_dtype_best_effort(
            data=metric_values,
            datetime_detected=datetime_detected,
            parse_strings_as_datetimes=True,
            fuzzy=False,
        )
        min_value: Number = np.amin(a=metric_values_converted)
        max_value: Number = np.amax(a=metric_values_converted)
        return build_numeric_range_estimation_result(
            metric_values=metric_values_converted,
            min_value=min_value,
            max_value=max_value,
        )
