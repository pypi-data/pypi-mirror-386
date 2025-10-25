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

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, List, Union

from great_expectations.compatibility.typing_extensions import override
from great_expectations.types import DictDot
from great_expectations.util import convert_to_json_serializable  # noqa: TID251 # FIXME CoP

if TYPE_CHECKING:
    import numpy as np

NUM_HISTOGRAM_BINS: int = (
    10  # Equal to "numpy.histogram()" default (can be turned into configurable argument).
)


@dataclass(frozen=True)
class NumericRangeEstimationResult(DictDot):
    """
    NumericRangeEstimationResult is a "dataclass" object, designed to hold results of executing numeric range estimator
    for multidimensional datasets, which consist of "estimation_histogram" and "value_range" for each numeric dimension.

    In particular, "estimation_histogram" is "numpy.ndarray" of shape [2, NUM_HISTOGRAM_BINS + 1], containing
    [0] "histogram": (integer array of dimension [NUM_HISTOGRAM_BINS + 1] padded with 0 at right edge) histogram values;
    [1] "bin_edges": (float array of dimension [NUM_HISTOGRAM_BINS + 1]) binning edges.
    """  # noqa: E501 # FIXME CoP

    estimation_histogram: np.ndarray
    value_range: Union[np.ndarray, List[np.float64]]

    @override
    def to_dict(self) -> dict:
        """Returns: this NumericRangeEstimationResult as a dictionary"""
        return asdict(self)

    def to_json_dict(self) -> dict:
        """Returns: this NumericRangeEstimationResult as a JSON dictionary"""
        return convert_to_json_serializable(data=self.to_dict())
