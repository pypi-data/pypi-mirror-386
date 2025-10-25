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

import abc
import uuid
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from great_expectations.data_context import CloudDataContext

T = TypeVar("T")


class DataStore(abc.ABC, Generic[T]):
    """Abstract base class for all DataStore implementations."""

    def __init__(self, context: CloudDataContext):
        self._context = context

    @abc.abstractmethod
    def add(self, value: T) -> uuid.UUID:
        """Add a value to the DataStore.

        Args:
            value: Value to add to the DataStore.

        Returns:
            id of the created resource.
        """
        raise NotImplementedError
