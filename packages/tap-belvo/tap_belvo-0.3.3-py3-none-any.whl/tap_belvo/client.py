"""REST client handling, including BelvoStream base class."""

from __future__ import annotations

import sys
from abc import ABCMeta, abstractmethod
from copy import deepcopy
from importlib import resources
from typing import TYPE_CHECKING, Any
from urllib.parse import ParseResult, parse_qsl

from requests.auth import HTTPBasicAuth
from requests_cache import install_cache
from singer_sdk import OpenAPISchema, RESTStream
from singer_sdk.pagination import BaseHATEOASPaginator

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if TYPE_CHECKING:
    from requests import Response
    from singer_sdk.helpers.types import Context


PAGE_SIZE = 1000
OPENAPI = OpenAPISchema(resources.files("tap_belvo") / "openapi.json")

install_cache("tap_belvo_cache", backend="sqlite", expire_after=3600)


def _handle_schema_nullable(schema: dict[str, Any]) -> dict[str, Any]:
    """Resolve x-nullable properties to standard JSON Schema nullable type.

    Args:
        schema: A JSON Schema dictionary.

    Returns:
        A new JSON Schema dictionary with 'x-nullable' resolved to [<type>, "null"].
    """
    result = deepcopy(schema)

    if "object" in result["type"]:
        for prop, prop_schema in result.get("properties", {}).items():
            prop_type: str | list[str] = prop_schema.get("type", [])
            types = [prop_type] if isinstance(prop_type, str) else prop_type
            nullable: bool = prop_schema.get("nullable", False)

            if nullable:
                prop_schema["type"] = [*types, "null"]

            result["properties"][prop] = _handle_schema_nullable(prop_schema)

    elif "array" in result["type"]:
        result["items"] = _handle_schema_nullable(result["items"])

    if "enum" in result and None not in result["enum"]:
        result["enum"].append(None)

    return result


class BelvoPaginator(BaseHATEOASPaginator):
    """Belvo API paginator class."""

    @override
    def get_next_url(self, response: Response) -> str | None:
        """Get the next URL from the response."""
        return response.json().get("next")  # type: ignore[no-any-return]


class BelvoStream(RESTStream[ParseResult], metaclass=ABCMeta):
    """Belvo stream class."""

    records_jsonpath = "$.results[*]"  # Or override `parse_response`.

    @override
    @property
    def url_base(self) -> str:
        return self.config["base_url"]  # type: ignore[no-any-return]

    @override
    @property
    def authenticator(self) -> HTTPBasicAuth:
        return HTTPBasicAuth(self.config["secret_id"], self.config["password"])

    @override
    def get_new_paginator(self) -> BelvoPaginator:
        return BelvoPaginator()

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: ParseResult | None,
    ) -> dict[str, Any]:
        """Get URL query parameters."""
        params: dict[str, Any] = {
            "page": 1,
            "page_size": PAGE_SIZE,
        }

        if next_page_token:
            params.update(parse_qsl(next_page_token.query))

        if (
            self.replication_key  # Only if the stream is running incrementally
            and (start_date := self.get_starting_timestamp(context))
        ):
            params[f"{self.replication_key}__gte"] = start_date.date().isoformat()

        return params

    @override
    @property
    def schema(self) -> dict[str, Any]:
        return _handle_schema_nullable(OPENAPI.fetch_schema(self.openapi_ref))

    @property
    @abstractmethod
    def openapi_ref(self) -> str:
        """OpenAPI component name for this stream."""
