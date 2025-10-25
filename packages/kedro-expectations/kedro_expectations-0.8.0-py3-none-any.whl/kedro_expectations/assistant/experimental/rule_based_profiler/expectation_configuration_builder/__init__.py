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

from kedro_expectations.assistant.experimental.rule_based_profiler.expectation_configuration_builder.expectation_configuration_builder import (  # isort:skip  # noqa: E501 # FIXME CoP
    ExpectationConfigurationBuilder,
    init_rule_expectation_configuration_builders,
)
from kedro_expectations.assistant.experimental.rule_based_profiler.expectation_configuration_builder.default_expectation_configuration_builder import (  # isort:skip  # noqa: E501 # FIXME CoP
    DefaultExpectationConfigurationBuilder,
)
