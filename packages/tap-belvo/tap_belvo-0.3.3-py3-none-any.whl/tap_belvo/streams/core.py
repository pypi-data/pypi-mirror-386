"""Stream type classes for tap-belvo."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from tap_belvo.client import BelvoStream

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if TYPE_CHECKING:
    from singer_sdk.helpers.types import Context


class Links(BelvoStream):
    """Links stream."""

    name = "links"
    path = "/api/links"
    primary_keys = ("id",)
    replication_key = "created_at"
    openapi_ref = "Link"

    @override
    def get_child_context(
        self,
        record: dict[str, Any],
        context: Context | None,
    ) -> dict[Any, Any]:
        return {"link_id": record["id"]}


class Institutions(BelvoStream):
    """Institutions stream."""

    name = "institutions"
    path = "/api/institutions"
    primary_keys = ("id",)
    replication_key = None
    openapi_ref = "InstitutionPublicApi"


class Consents(BelvoStream):
    """Consents stream."""

    name = "consents"
    path = "/api/consents"
    primary_keys = ("id",)
    replication_key = None
    openapi_ref = "Consents"
