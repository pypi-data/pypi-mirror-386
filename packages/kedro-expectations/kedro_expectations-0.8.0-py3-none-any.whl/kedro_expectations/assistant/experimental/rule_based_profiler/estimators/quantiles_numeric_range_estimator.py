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
from typing import TYPE_CHECKING, Dict, Final, Optional

from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.domain import Domain  # noqa: TC001 # FIXME CoP
from kedro_expectations.assistant.experimental.rule_based_profiler.estimators.numeric_range_estimation_result import (  # noqa: E501 # FIXME CoP
    NumericRangeEstimationResult,  # noqa: TC001 # FIXME CoP
)
from kedro_expectations.assistant.experimental.rule_based_profiler.estimators.numeric_range_estimator import (
    NumericRangeEstimator,
)
from kedro_expectations.assistant.experimental.rule_based_profiler.helpers.util import (
    compute_quantiles,
    datetime_semantic_domain_type,
    get_false_positive_rate_from_rule_state,
    get_quantile_statistic_interpolation_method_from_rule_state,
)
from kedro_expectations.assistant.experimental.rule_based_profiler.parameter_container import (
    ParameterContainer,  # noqa: TC001 # FIXME CoP
)
from great_expectations.types.attributes import Attributes  # noqa: TC001 # FIXME CoP
from great_expectations.util import convert_ndarray_to_datetime_dtype_best_effort

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_QUANTILES_QUANTILE_STATISTIC_INTERPOLATION_METHOD: Final[str] = "nearest"


class QuantilesNumericRangeEstimator(NumericRangeEstimator):
    """
    Implements "quantiles" computation.

    This nonparameteric estimator calculates quantiles given a MetricValues vector of length N, the q-th quantile of
        the vector is the value q of the way from the minimum to the maximum in a sorted copy of the MetricValues.
    """  # noqa: E501 # FIXME CoP

    def __init__(
        self,
        configuration: Optional[Attributes] = None,
    ) -> None:
        super().__init__(
            name="quantiles",
            configuration=configuration,
        )

    @override
    def _get_numeric_range_estimate(
        self,
        metric_values: np.ndarray,
        domain: Domain,
        variables: Optional[ParameterContainer] = None,
        parameters: Optional[Dict[str, ParameterContainer]] = None,
    ) -> NumericRangeEstimationResult:
        false_positive_rate: np.float64 = get_false_positive_rate_from_rule_state(  # type: ignore[assignment] # could be float
            false_positive_rate=self.configuration.false_positive_rate,  # type: ignore[union-attr] # configuration could be None
            domain=domain,
            variables=variables,
            parameters=parameters,
        )
        quantile_statistic_interpolation_method: str = get_quantile_statistic_interpolation_method_from_rule_state(  # noqa: E501 # FIXME CoP
            quantile_statistic_interpolation_method=self.configuration.quantile_statistic_interpolation_method,  # type: ignore[union-attr] # configuration could be None
            round_decimals=self.configuration.round_decimals,  # type: ignore[union-attr] # configuration could be None
            domain=domain,
            variables=variables,
            parameters=parameters,
        )
        if quantile_statistic_interpolation_method is None:
            quantile_statistic_interpolation_method = (
                DEFAULT_QUANTILES_QUANTILE_STATISTIC_INTERPOLATION_METHOD
            )

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
        return compute_quantiles(
            metric_values=metric_values_converted,
            false_positive_rate=false_positive_rate,
            quantile_statistic_interpolation_method=quantile_statistic_interpolation_method,
        )
