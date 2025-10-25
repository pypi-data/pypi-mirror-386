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
from typing import TYPE_CHECKING, Dict, List, Optional, Union

if TYPE_CHECKING:
    from great_expectations.core.domain import SemanticDomainTypes


class SemanticTypeFilter(ABC):
    @abstractmethod
    def parse_semantic_domain_type_argument(
        self,
        semantic_types: Optional[
            Union[str, SemanticDomainTypes, List[Union[str, SemanticDomainTypes]]]
        ] = None,
    ) -> List[SemanticDomainTypes]:
        pass

    @property
    @abstractmethod
    def table_column_name_to_inferred_semantic_domain_type_map(
        self,
    ) -> Dict[str, SemanticDomainTypes]:
        pass
