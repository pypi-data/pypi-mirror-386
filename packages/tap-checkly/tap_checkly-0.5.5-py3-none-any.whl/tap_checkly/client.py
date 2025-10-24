"""REST client handling, including ChecklyStream base class."""

from __future__ import annotations

import importlib.resources
import sys
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any

from singer_sdk import OpenAPISchema, RESTStream, StreamSchema
from singer_sdk.authenticators import BearerTokenAuthenticator

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if TYPE_CHECKING:
    from singer_sdk.helpers.types import Context

PAGE_SIZE = 100
OPENAPI_SCHEMA = OpenAPISchema(importlib.resources.files("tap_checkly") / "openapi.json")


class ChecklySchema(StreamSchema):
    """Checkly schema class."""

    @override
    def get_stream_schema(self, stream: ChecklyStream, stream_class: type[ChecklyStream]) -> dict[str, Any]:  # type: ignore[override]
        return self.schema_source.get_schema(stream.openapi_ref)


class ChecklyStream(RESTStream[int], metaclass=ABCMeta):
    """Checkly stream class."""

    url_base = "https://api.checklyhq.com/v1"
    records_jsonpath = "$[*]"  # Or override `parse_response`.

    schema = ChecklySchema(OPENAPI_SCHEMA)

    @override
    @property
    def authenticator(self) -> BearerTokenAuthenticator:
        return BearerTokenAuthenticator(token=self.config["token"])

    @override
    @property
    def http_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "X-Checkly-Account": self.config["account_id"],
        }

    @override
    def get_url_params(self, context: Context | None, _: Any | None) -> dict[str, Any]:
        params: dict[str, Any] = {}

        if self.replication_key:
            start_date = self.get_starting_timestamp(context)
            if start_date:
                params["from"] = start_date.timestamp()

        return params

    @property
    @abstractmethod
    def openapi_ref(self) -> str:
        """Return the OpenAPI component name for this stream.

        Returns:
            The OpenAPI reference for this stream.
        """
        ...


class ChecklyPaginatedStream(ChecklyStream):
    """Checkly paginated stream class."""

    @override
    def get_url_params(self, context: Context | None, next_page_token: int | None) -> dict[str, Any]:
        params = super().get_url_params(context, next_page_token)
        params["page"] = next_page_token
        params["limit"] = PAGE_SIZE
        return params
