"""
Pydantic V2 Input Models for Aruba Central MCP Tools

Provides type-safe input validation for all MCP tool handlers.
These models validate and normalize input before API calls.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

# =============================================================================
# BASE MODELS - Reusable patterns
# =============================================================================


class PaginatedInput(BaseModel):
    """Base model for tools with pagination support."""

    filter: str | None = Field(default=None, description="OData v4.0 filter criteria")
    sort: str | None = Field(default=None, description="Sort order (field direction)")
    limit: int = Field(default=100, ge=1, le=100, description="Maximum results per page")
    next: str | None = Field(default=None, description="Pagination cursor token")


class SerialNumberInput(BaseModel):
    """Base model for tools requiring a device serial number."""

    serial_number: str = Field(..., min_length=5, max_length=30, description="Device serial number")

    @field_validator("serial_number")
    @classmethod
    def normalize_serial(cls, v: str) -> str:
        """Strip whitespace and uppercase serial numbers."""
        return v.strip().upper()


class SerialInput(BaseModel):
    """Base model for tools using 'serial' parameter name."""

    serial: str = Field(..., min_length=5, max_length=30, description="Device serial number")

    @field_validator("serial")
    @classmethod
    def normalize_serial(cls, v: str) -> str:
        """Strip whitespace and uppercase serial numbers."""
        return v.strip().upper()


# =============================================================================
# DEVICE TOOLS - Individual device details
# =============================================================================


class GetAPDetailsInput(SerialNumberInput):
    """Input for get_ap_details tool."""



class GetSwitchDetailsInput(SerialInput):
    """Input for get_switch_details tool."""



class GetGatewayDetailsInput(SerialNumberInput):
    """Input for get_gateway_details tool."""



class GetSiteDetailsInput(BaseModel):
    """Input for get_site_details tool."""

    site_id: str = Field(..., min_length=1, description="Site identifier")

    @field_validator("site_id")
    @classmethod
    def normalize_site_id(cls, v: str) -> str:
        """Strip whitespace from site ID."""
        return v.strip()


class GetWLANDetailsInput(BaseModel):
    """Input for get_wlan_details tool."""

    wlan_name: str = Field(..., min_length=1, description="WLAN/SSID name")


# =============================================================================
# LIST TOOLS - Paginated lists
# =============================================================================


class GetDeviceListInput(PaginatedInput):
    """Input for get_device_list tool."""



class ListAllClientsInput(PaginatedInput):
    """Input for list_all_clients tool."""

    site_id: str | None = Field(default=None, description="Filter by site ID")
    serial_number: str | None = Field(default=None, description="Filter by device serial")
    start_query_time: str | None = Field(default=None, description="Start time (epoch ms)")
    end_query_time: str | None = Field(default=None, description="End time (epoch ms)")


class ListGatewaysInput(PaginatedInput):
    """Input for list_gateways tool."""



class GetFirmwareDetailsInput(PaginatedInput):
    """Input for get_firmware_details tool."""

    search: str | None = Field(default=None, description="Free-text search query")


class GetDeviceInventoryInput(PaginatedInput):
    """Input for get_device_inventory tool."""



class ListWLANsInput(BaseModel):
    """Input for list_wlans tool."""

    site_id: str | None = Field(default=None, description="Filter by site ID")
    limit: int = Field(default=100, ge=1, le=100, description="Maximum results")


class GetSitesHealthInput(BaseModel):
    """Input for get_sites_health tool."""

    limit: int = Field(default=100, ge=1, le=100, description="Maximum sites per page")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


class GetTenantDeviceHealthInput(BaseModel):
    """Input for get_tenant_device_health tool (no parameters)."""



# =============================================================================
# RADIO & PERFORMANCE TOOLS
# =============================================================================


class GetAPRadiosInput(SerialInput):
    """Input for get_ap_radios tool."""



class GetAPCPUUtilizationInput(SerialInput):
    """Input for get_ap_cpu_utilization tool."""

    start_time: str | None = Field(default=None, description="Start time (RFC 3339)")
    end_time: str | None = Field(default=None, description="End time (RFC 3339)")
    interval: Literal["5min", "1hour"] = Field(default="1hour", description="Data interval")


class GetGatewayCPUUtilizationInput(SerialInput):
    """Input for get_gateway_cpu_utilization tool."""

    start_time: str | None = Field(default=None, description="Start time (RFC 3339)")
    end_time: str | None = Field(default=None, description="End time (RFC 3339)")
    interval: Literal["5min", "1hour"] = Field(default="1hour", description="Data interval")


# =============================================================================
# GATEWAY-SPECIFIC TOOLS
# =============================================================================


class GetGatewayClusterInfoInput(BaseModel):
    """Input for get_gateway_cluster_info tool."""

    cluster_name: str = Field(..., min_length=1, description="Gateway cluster name")

    @field_validator("cluster_name")
    @classmethod
    def normalize_cluster_name(cls, v: str) -> str:
        """Strip whitespace from cluster name."""
        return v.strip()


class GetGatewayUplinksInput(SerialNumberInput):
    """Input for get_gateway_uplinks tool."""



class ListGatewayTunnelsInput(SerialNumberInput):
    """Input for list_gateway_tunnels tool."""



# =============================================================================
# SWITCH TOOLS
# =============================================================================


class GetSwitchInterfacesInput(SerialInput):
    """Input for get_switch_interfaces tool."""



class GetStackMembersInput(SerialInput):
    """Input for get_stack_members tool."""



# =============================================================================
# TRENDS & TOP USAGE TOOLS
# =============================================================================


class GetClientTrendsInput(BaseModel):
    """Input for get_client_trends tool."""

    site_id: str | None = Field(default=None, description="Filter by site ID")
    start_time: str | None = Field(default=None, description="Start time (RFC 3339)")
    end_time: str | None = Field(default=None, description="End time (RFC 3339)")
    interval: Literal["5min", "15min", "1hour", "1day"] = Field(
        default="1hour", description="Data interval"
    )


class GetTopAPsByBandwidthInput(BaseModel):
    """Input for get_top_aps_by_bandwidth tool."""

    site_id: str | None = Field(default=None, description="Filter by site ID")
    limit: int = Field(default=100, ge=1, le=100, description="Number of top APs")
    time_range: Literal["1hour", "24hours", "7days", "30days"] = Field(
        default="24hours", description="Analysis time period"
    )


class GetTopClientsByUsageInput(BaseModel):
    """Input for get_top_clients_by_usage tool."""

    site_id: str | None = Field(default=None, description="Filter by site ID")
    limit: int = Field(default=100, ge=1, le=100, description="Number of top clients")
    time_range: Literal["1hour", "24hours", "7days"] = Field(
        default="24hours", description="Analysis time period"
    )
    connection_type: Literal["WIRELESS", "WIRED", "ALL"] = Field(
        default="ALL", description="Connection type filter"
    )


# =============================================================================
# SECURITY TOOLS
# =============================================================================


class ListIDPSThreatsInput(PaginatedInput):
    """Input for list_idps_threats tool."""

    site_id: str | None = Field(default=None, description="Filter by site ID")


class GetFirewallSessionsInput(SerialNumberInput):
    """Input for get_firewall_sessions tool."""

    limit: int = Field(default=100, ge=1, le=100, description="Maximum sessions")


# =============================================================================
# NETWORK DIAGNOSTICS TOOLS
# =============================================================================


class PingFromAPInput(BaseModel):
    """Input for ping_from_ap tool."""

    serial_number: str = Field(..., min_length=5, description="AP serial number")
    target: str = Field(..., min_length=1, description="Target IP or hostname")
    count: int = Field(default=4, ge=1, le=10, description="Number of ping attempts")

    @field_validator("serial_number")
    @classmethod
    def normalize_serial(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("target")
    @classmethod
    def normalize_target(cls, v: str) -> str:
        return v.strip()


class PingFromGatewayInput(BaseModel):
    """Input for ping_from_gateway tool."""

    serial_number: str = Field(..., min_length=5, description="Gateway serial number")
    target: str = Field(..., min_length=1, description="Target IP or hostname")
    count: int = Field(default=4, ge=1, le=10, description="Number of ping attempts")

    @field_validator("serial_number")
    @classmethod
    def normalize_serial(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("target")
    @classmethod
    def normalize_target(cls, v: str) -> str:
        return v.strip()


class TracerouteFromAPInput(BaseModel):
    """Input for traceroute_from_ap tool."""

    serial_number: str = Field(..., min_length=5, description="AP serial number")
    target: str = Field(..., min_length=1, description="Target IP or hostname")
    max_hops: int = Field(default=30, ge=1, le=64, description="Maximum hops")

    @field_validator("serial_number")
    @classmethod
    def normalize_serial(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("target")
    @classmethod
    def normalize_target(cls, v: str) -> str:
        return v.strip()


# =============================================================================
# ASYNC TOOLS
# =============================================================================


class GetAsyncTestResultInput(BaseModel):
    """Input for get_async_test_result tool."""

    task_id: str = Field(..., min_length=1, description="Async task ID")

    @field_validator("task_id")
    @classmethod
    def normalize_task_id(cls, v: str) -> str:
        return v.strip()


# =============================================================================
# VERIFICATION TOOL
# =============================================================================


class VerifyFactsInput(BaseModel):
    """Input for verify_facts tool."""

    tool_name: str | None = Field(default=None, description="Specific tool to verify")
