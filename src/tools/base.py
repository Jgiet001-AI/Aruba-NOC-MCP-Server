"""
Base - Shared utilities for Aruba Central MCP tools

Provides centralized helpers for consistent output formatting across all tools:
- StatusLabels: Professional text-based indicators for status display
- format_bytes: Human-readable byte size formatting
- format_json: JSON serialization helper
- extract_params: Parameter transformation for API calls
- Response builders: Consistent tool response formatting
- validate_input: Pydantic v2 input validation helper
"""

import json
import logging
from typing import Any, TypeVar

from mcp.types import TextContent
from pydantic import BaseModel, ValidationError

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
    OK = "[OK]"  # Healthy, online, success
    WARN = "[WARN]"  # Warning condition
    CRIT = "[CRIT]"  # Critical issue
    ERR = "[ERR]"  # Error state
    INFO = "[INFO]"  # Informational note

    # Online/Offline status
    UP = "[UP]"  # Online, active
    DN = "[DN]"  # Offline, down

    # Connection types
    WIFI = "[WIFI]"  # Wireless connection
    WIRED = "[WIRED]"  # Wired connection

    # Device types
    AP = "[AP]"  # Access Point
    SW = "[SW]"  # Switch
    GW = "[GW]"  # Gateway
    DEV = "[DEV]"  # Generic device

    # Actions/States
    AVAIL = "[AVAIL]"  # Available update
    REQ = "[REQ]"  # Required update
    IDLE = "[IDLE]"  # Idle state
    MORE = "[MORE]"  # More results available (pagination)
    ALERT = "[ALERT]"  # Alert condition
    ASYNC = "[ASYNC]"  # Async operation pending

    # Categories
    SEC = "[SEC]"  # Security-related
    BUG = "[BUG]"  # Bug fix
    FEAT = "[FEAT]"  # Feature release
    HW = "[HW]"  # Hardware
    CLI = "[CLI]"  # Client
    VPN = "[VPN]"  # VPN/Tunnel
    NET = "[NET]"  # Network

    # Data/Stats
    STATS = "[STATS]"  # Statistics
    TREND = "[TREND]"  # Trend data
    DATA = "[DATA]"  # Data metrics
    RANK = "[RANK]"  # Ranking information

    # Deployment
    CLUST = "[CLUST]"  # Clustered deployment
    SOLO = "[SOLO]"  # Standalone deployment

    # Location/Site
    LOC = "[LOC]"  # Location
    SITE = "[SITE]"  # Site

    # Roles
    ROLE = "[ROLE]"  # Role designation
    CFG = "[CFG]"  # Configuration

    # Guest
    GUEST = "[GUEST]"  # Guest network

    # Operations
    PING = "[PING]"  # Ping operation
    TRACE = "[TRACE]"  # Traceroute operation

    # Time
    TIME = "[TIME]"  # Time-related

    # Link
    LINK = "[LINK]"  # Link status

    # List/Details
    LIST = "[LIST]"  # List marker
    DETAIL = "[DETAIL]"  # Detail section

    # Default/Unknown
    UNKNOWN = "[--]"  # Unknown or N/A


# =============================================================================
# INPUT VALIDATION - Pydantic v2 helpers
# =============================================================================

# Type variable for Pydantic models
T = TypeVar("T", bound=BaseModel)


def validate_input(
    model: type[T],
    args: dict[str, Any],
    tool_name: str,
) -> T | list[TextContent]:
    """
    Validate tool input using a Pydantic model.

    Returns the validated model instance on success, or a TextContent
    error response on validation failure.

    Args:
        model: Pydantic model class to validate against
        args: Raw arguments dictionary from MCP
        tool_name: Name of the tool for error messages

    Returns:
        - Validated model instance (T) on success
        - list[TextContent] with error message on failure

    Example:
        validated = validate_input(GetAPDetailsInput, args, "get_ap_details")
        if isinstance(validated, list):
            return validated  # Validation error
        serial = validated.serial_number  # Type-safe access
    """
    try:
        return model.model_validate(args)
    except ValidationError as e:
        # Format user-friendly error messages
        errors = []
        for err in e.errors():
            loc = ".".join(str(x) for x in err["loc"]) if err["loc"] else "input"
            msg = err["msg"]
            errors.append(f"{loc}: {msg}")

        error_text = "; ".join(errors)
        return [
            TextContent(
                type="text",
                text=f"{StatusLabels.ERR} {tool_name} validation failed: {error_text}",
            )
        ]


# =============================================================================
# VERIFICATION GUARDRAILS - Anti-Hallucination Helpers
# =============================================================================


class VerificationGuards:
    """
    Anti-hallucination guardrails for LLM-friendly output formatting.

    These helpers ensure the LLM cannot confuse different metrics by:
    1. Explicit labeling of metric types (counts vs percentages vs scores)
    2. Verification checkpoints summarizing key facts
    3. Warning blocks for commonly confused metrics
    """

    SEPARATOR = "=" * 50

    @staticmethod
    def checkpoint(facts: dict[str, Any]) -> str:
        """
        Create a verification checkpoint with key facts.

        The LLM should reference these facts before making claims.

        Args:
            facts: Dictionary of fact_name -> fact_value pairs

        Returns:
            Formatted verification checkpoint block
        """
        lines = [
            VerificationGuards.SEPARATOR,
            "[VERIFICATION CHECKPOINT - Cite these facts exactly]",
        ]
        for name, value in facts.items():
            lines.append(f"  {name}: {value}")
        lines.append(VerificationGuards.SEPARATOR)
        return "\n".join(lines)

    @staticmethod
    def device_counts(total: int, online: int, offline: int) -> str:
        """
        Format device counts with explicit labels.

        Prevents confusion between device counts and health scores.
        """
        online_pct = (online / total * 100) if total > 0 else 0
        offline_pct = (offline / total * 100) if total > 0 else 0
        return (
            f"[DEVICE COUNTS - actual devices, not health scores]\n"
            f"  Total: {total} devices\n"
            f"  Online: {online} devices ({online_pct:.1f}% of total devices)\n"
            f"  Offline: {offline} devices ({offline_pct:.1f}% of total devices)"
        )

    @staticmethod
    def health_scores(good: float, fair: float, poor: float) -> str:
        """
        Format health SCORES with explicit warning.

        Health scores are weighted metrics, NOT device percentages.
        """
        return (
            f"[HEALTH SCORES - weighted metrics, NOT device percentages]\n"
            f"  Good: {good:.1f}% (health score)\n"
            f"  Fair: {fair:.1f}% (health score)\n"
            f"  Poor: {poor:.1f}% (health score)\n"
            f"  [!] These percentages are health SCORES, not device counts"
        )

    @staticmethod
    def anti_hallucination_footer(key_facts: dict[str, Any]) -> str:
        """
        Create an anti-hallucination footer with key facts to verify.

        This block reminds the LLM to verify facts before reporting.
        """
        lines = [
            "",
            VerificationGuards.SEPARATOR,
            "[!] BEFORE REPORTING, VERIFY THESE FACTS:",
        ]
        for name, value in key_facts.items():
            lines.append(f"    - {name}: {value}")
        lines.append("    - Health % ≠ Device % (they are different metrics)")
        lines.append("    - Cite actual numbers from this response, do not calculate")
        lines.append(VerificationGuards.SEPARATOR)
        return "\n".join(lines)

    @staticmethod
    def metric_label(value: Any, metric_type: str, unit: str = "") -> str:
        """
        Format a single metric with explicit type label.

        Args:
            value: The metric value
            metric_type: Type like 'count', 'percentage', 'score', 'bytes'
            unit: Optional unit suffix

        Returns:
            Formatted metric string like "150 [count of devices]"
        """
        unit_str = f" {unit}" if unit else ""
        return f"{value}{unit_str} [{metric_type}]"


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
    for unit in ["B", "KB", "MB", "GB", "TB"]:
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


def count_by_field(items: list[dict], field: str) -> dict[str, int]:
    """
    Count items by a specific field value.

    Args:
        items: List of dictionaries to count
        field: Field name to group by

    Returns:
        Dictionary mapping field values to counts

    Example:
        count_by_field([{"status": "UP"}, {"status": "DOWN"}], "status")
        # Returns: {"UP": 1, "DOWN": 1}
    """
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(field, "Unknown"))
        counts[value] = counts.get(value, 0) + 1
    return counts


def build_summary_response(
    title: str,
    total: int,
    breakdowns: dict[str, dict[str, int]] | None = None,
    preview_items: list[dict] | None = None,
    preview_fields: list[str] | None = None,
    filter_hints: list[str] | None = None,
    next_cursor: str | None = None,
) -> str:
    """
    Build a context-efficient summary response.

    Returns a compact summary with stats, preview items, and actionable hints
    instead of raw JSON, reducing context window usage by ~95%.

    Args:
        title: Response title (e.g., "Device Inventory")
        total: Total count of items
        breakdowns: Stats by category (e.g., {"By Status": {"ONLINE": 100}})
        preview_items: First few items to show as preview
        preview_fields: Fields to include in preview (default: first 3 fields)
        filter_hints: Suggested filters for the user
        next_cursor: Pagination cursor if more results available

    Returns:
        Formatted summary string

    Example:
        build_summary_response(
            title="Device Inventory",
            total=8642,
            breakdowns={"By Status": {"ONLINE": 7609, "OFFLINE": 1033}},
            filter_hints=["status eq OFFLINE"]
        )
    """
    lines = [f"**{title}** | Total: {total:,}"]

    # Add breakdowns
    if breakdowns:
        lines.append("")
        for category, counts in breakdowns.items():
            # Sort by count descending, format as compact line
            sorted_counts = sorted(counts.items(), key=lambda x: -x[1])
            parts = [f"{k}: {v:,}" for k, v in sorted_counts[:5]]  # Top 5
            if len(sorted_counts) > 5:
                parts.append(f"+{len(sorted_counts) - 5} more")
            lines.append(f"**{category}:** {' | '.join(parts)}")

    # Add preview items
    if preview_items:
        lines.append("")
        lines.append(f"**Preview** (showing {len(preview_items)} of {total:,}):")
        for i, item in enumerate(preview_items[:5], 1):
            # Use specified fields or first 3 fields
            fields = preview_fields or list(item.keys())[:3]
            parts = [f"{k}={item.get(k, 'N/A')}" for k in fields if k in item]
            lines.append(f"  {i}. {' | '.join(parts)}")

    # Add filter hints
    if filter_hints:
        lines.append("")
        lines.append(f"{StatusLabels.INFO} Filter hints: " + ", ".join(filter_hints))

    # Add pagination notice
    if next_cursor:
        lines.append(f"{StatusLabels.MORE} More results available (next={next_cursor})")

    # Add verbose hint
    lines.append("")
    lines.append(f"{StatusLabels.INFO} Add verbose=true for full JSON output")

    return "\n".join(lines)


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


# =============================================================================
# ERROR HANDLING DECORATOR
# =============================================================================


def handle_tool_errors(tool_name: str):
    """
    Decorator for consistent error handling in tool handlers.

    Wraps async tool handlers to catch common exceptions and return
    user-friendly error responses.

    Args:
        tool_name: Name of the tool for error reporting

    Returns:
        Decorated function

    Example:
        @handle_tool_errors("get_device_list")
        async def handle_get_device_list(args):
            ...
    """
    import functools

    import httpx

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status == 404:
                    return [TextContent(type="text", text=f"{StatusLabels.ERR} {tool_name}: Resource not found")]
                if status == 401:
                    return [TextContent(type="text", text=f"{StatusLabels.ERR} {tool_name}: Authentication failed")]
                if status == 403:
                    return [TextContent(type="text", text=f"{StatusLabels.ERR} {tool_name}: Access denied")]
                return build_error_response(f"HTTP {status}: {e.response.text[:200]}", tool_name)
            except httpx.TimeoutException:
                return [TextContent(type="text", text=f"{StatusLabels.ERR} {tool_name}: Request timed out")]
            except Exception as e:
                return build_error_response(str(e), tool_name)

        return wrapper

    return decorator
