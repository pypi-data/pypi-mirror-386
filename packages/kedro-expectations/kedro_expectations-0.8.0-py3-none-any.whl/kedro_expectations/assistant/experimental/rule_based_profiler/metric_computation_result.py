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

from dataclasses import make_dataclass
from typing import Any, Dict, List, Set, Tuple, Union

from great_expectations.validator.computed_metric import MetricValue

MetricValues = Union[MetricValue, List[MetricValue], Set[MetricValue], Tuple[MetricValue, ...]]
MetricComputationDetails = Dict[str, Any]
MetricComputationResult = make_dataclass(
    "MetricComputationResult", ["attributed_resolved_metrics", "details"]
)
