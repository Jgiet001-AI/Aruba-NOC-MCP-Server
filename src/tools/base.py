"""
Base - Shared utilities for Aruba Central MCP tools

Provides centralized helpers for consistent output formatting across all tools:
- StatusLabels: Professional text-based indicators for status display
- format_bytes: Human-readable byte size formatting
- format_json: JSON serialization helper
- extract_params: Parameter transformation for API calls
- Response builders: Consistent tool response formatting
"""

import json
import logging
from typing import Any

from mcp.types import TextContent

logger = logging.getLogger("aruba-noc-server")


# =============================================================================
# STATUS LABELS - Professional text-based indicators
# =============================================================================


class StatusLabels:
    """
    Professional text-based status labels for consistent output formatting.

    Use these labels instead of emojis for enterprise-ready tool responses.
    Labels are designed to be clear, concise, and easily parseable.
    """

    # Status indicators
    OK = "[OK]"          # Healthy, online, success
    WARN = "[WARN]"      # Warning condition
    CRIT = "[CRIT]"      # Critical issue
    ERR = "[ERR]"        # Error state
    INFO = "[INFO]"      # Informational note

    # Online/Offline status
    UP = "[UP]"          # Online, active
    DN = "[DN]"          # Offline, down

    # Connection types
    WIFI = "[WIFI]"      # Wireless connection
    WIRED = "[WIRED]"    # Wired connection

    # Device types
    AP = "[AP]"          # Access Point
    SW = "[SW]"          # Switch
    GW = "[GW]"          # Gateway
    DEV = "[DEV]"        # Generic device

    # Actions/States
    AVAIL = "[AVAIL]"    # Available update
    REQ = "[REQ]"        # Required update
    IDLE = "[IDLE]"      # Idle state
    MORE = "[MORE]"      # More results available (pagination)
    ALERT = "[ALERT]"    # Alert condition
    ASYNC = "[ASYNC]"    # Async operation pending

    # Categories
    SEC = "[SEC]"        # Security-related
    BUG = "[BUG]"        # Bug fix
    FEAT = "[FEAT]"      # Feature release
    HW = "[HW]"          # Hardware
    CLI = "[CLI]"        # Client
    VPN = "[VPN]"        # VPN/Tunnel
    NET = "[NET]"        # Network

    # Data/Stats
    STATS = "[STATS]"    # Statistics
    TREND = "[TREND]"    # Trend data
    DATA = "[DATA]"      # Data metrics
    RANK = "[RANK]"      # Ranking information

    # Deployment
    CLUST = "[CLUST]"    # Clustered deployment
    SOLO = "[SOLO]"      # Standalone deployment

    # Location/Site
    LOC = "[LOC]"        # Location
    SITE = "[SITE]"      # Site

    # Roles
    ROLE = "[ROLE]"      # Role designation
    CFG = "[CFG]"        # Configuration

    # Guest
    GUEST = "[GUEST]"    # Guest network

    # Operations
    PING = "[PING]"      # Ping operation
    TRACE = "[TRACE]"    # Traceroute operation

    # Time
    TIME = "[TIME]"      # Time-related

    # Link
    LINK = "[LINK]"      # Link status

    # List/Details
    LIST = "[LIST]"      # List marker
    DETAIL = "[DETAIL]"  # Detail section

    # Default/Unknown
    UNKNOWN = "[--]"     # Unknown or N/A


# =============================================================================
# JSON FORMATTING
# =============================================================================


def format_json(data: dict[str, Any], indent: int = 2) -> str:
    """
    Format JSON data for display in tool responses.

    Args:
        data: Dictionary to format
        indent: Indentation level (default: 2)

    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=indent)


# =============================================================================
# PARAMETER HELPERS
# =============================================================================


def extract_params(
    args: dict[str, Any],
    param_map: dict[str, str] | None = None,
    defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Extract and transform parameters from tool arguments.

    Handles conversion from snake_case to hyphenated API parameters.

    Args:
        args: Tool arguments dictionary
        param_map: Mapping of arg names to API param names (e.g., {"site_id": "site-id"})
        defaults: Default values for parameters

    Returns:
        Dictionary of API parameters

    Example:
        params = extract_params(
            args={"site_id": "123", "limit": 50},
            param_map={"site_id": "site-id"},
            defaults={"limit": 100}
        )
        # Returns: {"site-id": "123", "limit": 50}
    """
    params = {}
    param_map = param_map or {}
    defaults = defaults or {}

    # Apply defaults first
    for key, value in defaults.items():
        api_key = param_map.get(key, key)
        params[api_key] = value

    # Override with provided args
    for key, value in args.items():
        if value is not None:
            api_key = param_map.get(key, key)
            params[api_key] = value

    return params


# =============================================================================
# DATA FORMATTING HELPERS
# =============================================================================


def format_bytes(bytes_val: int) -> str:
    """
    Format bytes to human-readable size (e.g., 1024 -> "1.00 KB").

    Args:
        bytes_val: Number of bytes to format

    Returns:
        Human-readable string with appropriate unit (B, KB, MB, GB, TB, PB)
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"


def format_uptime(seconds: int) -> str:
    """
    Format uptime in seconds to human-readable duration.

    Args:
        seconds: Uptime in seconds

    Returns:
        Human-readable string (e.g., "5d 3h 20m" or "45m 30s")
    """
    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m {seconds % 60}s"

    hours = minutes // 60
    if hours < 24:
        return f"{hours}h {minutes % 60}m"

    days = hours // 24
    return f"{days}d {hours % 24}h {minutes % 60}m"


def format_percentage(value: float, threshold_warn: float = 70, threshold_crit: float = 90) -> str:
    """
    Format a percentage with status indicator based on thresholds.

    Args:
        value: Percentage value (0-100)
        threshold_warn: Warning threshold (default: 70%)
        threshold_crit: Critical threshold (default: 90%)

    Returns:
        Formatted string with status label (e.g., "[WARN] 75.5%")
    """
    if value >= threshold_crit:
        return f"{StatusLabels.CRIT} {value:.1f}%"
    if value >= threshold_warn:
        return f"{StatusLabels.WARN} {value:.1f}%"
    return f"{StatusLabels.OK} {value:.1f}%"


# =============================================================================
# SUMMARY HELPERS
# =============================================================================


def safe_get(data: dict[str, Any], key: str, default: Any = "Unknown") -> Any:
    """
    Safely get a value from a dictionary with a default.

    Args:
        data: Dictionary to extract from
        key: Key to look up
        default: Default value if key not found or value is None

    Returns:
        Value or default
    """
    value = data.get(key)
    return value if value is not None else default


def get_status_label(status: str, label_map: dict[str, str]) -> str:
    """
    Get a text label for a status value.

    Args:
        status: Status value to look up
        label_map: Mapping of status values to labels

    Returns:
        Label string or StatusLabels.UNKNOWN if not found
    """
    return label_map.get(status, StatusLabels.UNKNOWN)


def format_pagination_message(has_more: bool) -> str | None:
    """
    Generate pagination message if more results are available.

    Args:
        has_more: Whether more results exist

    Returns:
        Pagination message or None
    """
    if has_more:
        return f"\n{StatusLabels.MORE} Results available (use next cursor)"
    return None


# =============================================================================
# RESPONSE BUILDERS
# =============================================================================


def build_text_response(summary: str, data: dict[str, Any]) -> list[TextContent]:
    """
    Build a standard tool response with summary and JSON data.

    Args:
        summary: Human-readable summary text
        data: Raw API response data

    Returns:
        List containing a single TextContent with combined output
    """
    return [TextContent(type="text", text=f"{summary}\n\n{format_json(data)}")]


def build_error_response(error: str, tool_name: str = "tool") -> list[TextContent]:
    """
    Build an error response for failed tool execution.

    Args:
        error: Error message
        tool_name: Name of the tool that failed

    Returns:
        List containing a single TextContent with error details
    """
    logger.error(f"Error in {tool_name}: {error}")
    return [TextContent(type="text", text=f"[ERROR] {tool_name} failed: {error}")]
