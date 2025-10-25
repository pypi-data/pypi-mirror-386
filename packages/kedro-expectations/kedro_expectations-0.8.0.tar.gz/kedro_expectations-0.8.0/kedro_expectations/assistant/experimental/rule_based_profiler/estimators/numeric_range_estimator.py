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
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Optional

from great_expectations.compatibility.typing_extensions import override
from great_expectations.types import SerializableDictDot
from great_expectations.util import convert_to_json_serializable  # noqa: TID251 # FIXME CoP

if TYPE_CHECKING:
    import numpy as np

    from great_expectations.core.domain import Domain
    from kedro_expectations.assistant.experimental.rule_based_profiler.estimators.numeric_range_estimation_result import (  # noqa: E501 # FIXME CoP
        NumericRangeEstimationResult,
    )
    from kedro_expectations.assistant.experimental.rule_based_profiler.parameter_container import (
        ParameterContainer,
    )
    from great_expectations.types.attributes import Attributes

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class NumericRangeEstimator(ABC, SerializableDictDot):
    """
    Parent class that incorporates the "get_numeric_range_estimate()" interface method, requiring all subclasses to
    implement the "_get_numeric_range_estimate()" method (for encapsulation reasons, the former calls the latter).
    """  # noqa: E501 # FIXME CoP

    def __init__(
        self,
        name: str,
        configuration: Optional[Attributes] = None,
    ) -> None:
        """
        Args:
            name: the name of this estimator, which encodes the choice of the estimation algorithm: "quantiles",
            "bootstrap", "exact" (default - deterministic, incorporating entire observed value range), or "kde"
            (kernel density estimation).
            configuration: attributes needed for the estimation algorithm (subject of the inherited class) to operate.
        """  # noqa: E501 # FIXME CoP
        self._name = name
        self._configuration = configuration

    @property
    def name(self) -> str:
        return self._name

    @property
    def configuration(self) -> Optional[Attributes]:
        return self._configuration

    @configuration.setter
    def configuration(self, value: Optional[Attributes]) -> None:
        self._configuration = value

    def get_numeric_range_estimate(
        self,
        metric_values: np.ndarray,
        domain: Domain,
        variables: Optional[ParameterContainer] = None,
        parameters: Optional[Dict[str, ParameterContainer]] = None,
    ) -> NumericRangeEstimationResult:
        """
        Method that invokes implementation of the estimation algorithm that is the subject of the inherited class.
        Args:
            metric_values: "numpy.ndarray" of "dtype.float" values with elements corresponding to "Batch" data samples.
            domain: "Domain" object that is context for execution of this "NumericRangeEstimator" object.
            variables: attribute name/value pairs
            parameters: Dictionary of "ParameterContainer" objects corresponding to all "Domain" objects in memory.

        Returns:
            "NumericRangeEstimationResult" object, containing computed "value_range" and "estimation_histogram" details.
        """  # noqa: E501 # FIXME CoP
        return self._get_numeric_range_estimate(
            metric_values=metric_values,
            domain=domain,
            variables=variables,
            parameters=parameters,
        )

    @abstractmethod
    def _get_numeric_range_estimate(
        self,
        metric_values: np.ndarray,
        domain: Domain,
        variables: Optional[ParameterContainer] = None,
        parameters: Optional[Dict[str, ParameterContainer]] = None,
    ) -> NumericRangeEstimationResult:
        """
        Essentials of the estimation algorithm (all subclasses must implement this method).
        """
        pass

    @override
    def to_dict(self) -> dict:
        """
        Returns dictionary equivalent of this object.
        """
        dict_obj: dict = (
            self._configuration.to_dict()  # type: ignore[union-attr] # could be None
        )
        dict_obj.update({"name": self._name})
        return dict_obj

    @override
    def to_json_dict(self) -> dict:
        """
        Returns JSON dictionary equivalent of this object.
        """
        return convert_to_json_serializable(data=self.to_dict())
