"""Stream type classes for tap-checkly."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from tap_checkly.client import ChecklyPaginatedStream, ChecklyStream

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if TYPE_CHECKING:
    from singer_sdk.helpers.types import Context, Record


class AlertChannels(ChecklyPaginatedStream):
    """Alert channels."""

    name = "alert_channels"
    path = "/alert-channels"
    primary_keys = ("id",)
    openapi_ref = "AlertChannel"


class AlertNotifications(ChecklyPaginatedStream):
    """Alert notification.

    Alert notifications that have been sent for your account.
    """

    name = "alert_notifications"
    path = "/alert-notifications"
    primary_keys = ("id",)
    openapi_ref = "AlertNotification"
    replication_key = "timestamp"


class Checks(ChecklyPaginatedStream):
    """Checks."""

    name = "checks"
    path = "/checks"
    primary_keys = ("id",)
    openapi_ref = "Check"

    @override
    def get_child_context(self, record: Record, context: Context | None) -> dict[str, Any]:
        return {"checkId": record["id"]}


class CheckAlerts(ChecklyPaginatedStream):
    """Check alerts."""

    name = "check_alerts"
    path = "/check-alerts"
    primary_keys = ("id",)
    openapi_ref = "CheckAlert"
    replication_key = "created_at"


class CheckGroups(ChecklyPaginatedStream):
    """Check groups."""

    name = "check_groups"
    path = "/check-groups"
    primary_keys = ("id",)
    openapi_ref = "CheckGroup"


class CheckResults(ChecklyPaginatedStream):
    """Check results."""

    name = "check_results"
    path = "/check-results/{checkId}"
    primary_keys = ("id",)
    openapi_ref = "CheckResult"
    replication_key = "created_at"
    parent_stream_type = Checks


class Dashboards(ChecklyPaginatedStream):
    """Dashboards.

    All current dashboards in your account.
    """

    name = "dashboards"
    path = "/dashboards"
    primary_keys = ("dashboardId",)
    openapi_ref = "Dashboard"


class EnvironmentVariables(ChecklyStream):
    """Environment variables.

    Note: Pagination seems to be broken for this endpoint.
    """

    name = "variables"
    path = "/variables"
    primary_keys = ("key",)
    openapi_ref = "EnvironmentVariable"


class Locations(ChecklyStream):
    """Locations."""

    name = "locations"
    path = "/locations"
    primary_keys = ("region",)
    openapi_ref = "Location"


class MaintenanceWindows(ChecklyPaginatedStream):
    """Maintenance windows."""

    name = "maintenance_windows"
    path = "/maintenance-windows"
    primary_keys = ("id",)
    openapi_ref = "MaintenanceWindow"


class PrivateLocations(ChecklyStream):
    """Private locations."""

    name = "private_locations"
    path = "/private-locations"
    primary_keys = ("id",)
    openapi_ref = "privateLocationsSchema"


class Runtimes(ChecklyStream):
    """Runtimes."""

    name = "runtimes"
    path = "/runtimes"
    primary_keys = ("name",)
    openapi_ref = "Runtime"


class Snippets(ChecklyPaginatedStream):
    """Snippets."""

    name = "snippets"
    path = "/snippets"
    primary_keys = ("id",)
    openapi_ref = "Snippet"
