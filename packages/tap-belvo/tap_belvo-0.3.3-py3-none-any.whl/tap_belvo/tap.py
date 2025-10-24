"""Belvo tap class."""

from __future__ import annotations

import sys

import singer_sdk
from singer_sdk import typing as th

from tap_belvo.streams import banking, core, enrichment, fiscal

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class TapBelvo(singer_sdk.Tap):
    """Singer tap for Belvo."""

    name = "tap-belvo"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "secret_id",
            th.StringType,
            description="Belvo API secret ID.",
            required=True,
            secret=True,
        ),
        th.Property(
            "password",
            th.StringType,
            description="Belvo API password.",
            required=True,
            secret=True,
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            description="Earliest datetime to get data from",
        ),
        th.Property(
            "base_url",
            th.StringType,
            description="Base URL for the Belvo API",
            default="https://development.belvo.com",
        ),
    ).to_dict()

    @override
    def discover_streams(self) -> list[singer_sdk.Stream]:
        # TODO(edgarrmondragon): Add tax declarations and tax returns
        # https://github.com/reservoir-data/tap-belvo/issues/76
        return [
            core.Links(self),
            core.Institutions(self),
            # TODO(edgarrmondragon): The `document_number` field seems to be incorrectly
            # marked as required?
            # https://developers.belvo.com/apis/belvoopenapispec/consents/listconsents
            # core.Consents(self),  # noqa: ERA001
            banking.Accounts(self),
            banking.Transactions(self),
            banking.Owners(self),
            # banking.InvestmentPortfolios(self),  # noqa: ERA001
            # banking.ReceivableTransactions(self),  # noqa: ERA001
            enrichment.Incomes(self),
            enrichment.RecurringExpenses(self),
            enrichment.RiskInsights(self),
            fiscal.Invoices(self),
            fiscal.TaxComplianceStatuses(self),
            fiscal.TaxRetentions(self),
            fiscal.TaxStatuses(self),
        ]
