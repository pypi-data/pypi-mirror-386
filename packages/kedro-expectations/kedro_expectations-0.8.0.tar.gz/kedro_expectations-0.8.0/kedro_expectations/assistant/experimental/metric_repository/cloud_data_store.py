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

import urllib.parse
import uuid
import weakref
from typing import TYPE_CHECKING, Any, Dict, TypeVar

from great_expectations.compatibility.pydantic import BaseModel
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.http import create_session
from kedro_expectations.assistant.experimental.metric_repository.data_store import DataStore
from kedro_expectations.assistant.experimental.metric_repository.metrics import MetricRun

if TYPE_CHECKING:
    import requests
    from typing_extensions import TypeAlias

    from great_expectations.data_context import CloudDataContext

# When more types are storable, convert StorableTypes to a Union and add them to the type alias:
StorableTypes: TypeAlias = MetricRun

T = TypeVar("T", bound=StorableTypes)


def orjson_dumps(v, *, default):
    import orjson  # Import here since this is only installed in the cloud environment

    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(
        v,
        default=default,
        option=orjson.OPT_SERIALIZE_NUMPY,
    ).decode()


def orjson_loads(v, *args, **kwargs):
    import orjson  # Import here since this is only installed in the cloud environment

    return orjson.loads(v)


class Payload(BaseModel):
    data: Dict[str, Any]

    class Config:
        extra = "forbid"
        json_dumps = orjson_dumps
        json_loads = orjson_loads


class CloudDataStore(DataStore[StorableTypes]):
    """DataStore implementation for GX Cloud.

    Uses JSON:API https://jsonapi.org/
    """

    @override
    def __init__(self, context: CloudDataContext):
        super().__init__(context=context)
        assert context.ge_cloud_config is not None
        assert self._context.ge_cloud_config is not None
        self._session = create_session(
            access_token=context.ge_cloud_config.access_token,
            retry_count=0,  # Do not retry on authentication errors
        )
        # Finalizer to close the session when the object is garbage collected.
        # https://docs.python.org/3.11/library/weakref.html#weakref.finalize
        self._finalizer = weakref.finalize(self, close_session, self._session)

    def _build_payload(self, value: StorableTypes) -> str:
        payload = Payload(data=value.dict(exclude={"metrics": {"__all__": {"__orig_class__"}}}))
        return payload.json()

    def _build_url(self, value: StorableTypes) -> str:
        assert self._context.ge_cloud_config is not None
        config = self._context.ge_cloud_config
        return urllib.parse.urljoin(
            config.base_url,
            f"api/v1/organizations/{config.organization_id}/metric-runs",
        )

    @override
    def add(self, value: T) -> uuid.UUID:
        """Add a value to the DataStore.

        Args:
            value: Value to add to the DataStore. Must be one of StorableTypes.

        Returns:
            id of the created resource.
        """
        url = self._build_url(value)
        payload = self._build_payload(value)
        response = self._session.post(url=url, data=payload)
        response.raise_for_status()

        response_json = response.json()
        return uuid.UUID(response_json["id"])


def close_session(session: requests.Session):
    """Close the session.
    Used by a finalizer to close the session when the CloudDataStore is garbage collected.

    This is not a bound method on the CloudDataStore class because of this note
    in the Python docs (https://docs.python.org/3.11/library/weakref.html#weakref.finalize):
    Note It is important to ensure that func, args and kwargs do not own any references to obj,
    either directly or indirectly, since otherwise obj will never be garbage collected.
    In particular, func should not be a bound method of obj.

    """
    session.close()
