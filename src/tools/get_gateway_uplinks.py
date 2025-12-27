"""
Get Gateway Uplinks - MCP tools for gateway uplinks information in Aruba Central
"""

import json
import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import format_bytes

logger = logging.getLogger("aruba-noc-server")


def _format_json(data: dict[str, Any]) -> str:
    """Format JSON data for display"""
    return json.dumps(data, indent=2)

async def handle_get_gateway_uplinks(args: dict[str, Any]) -> list[TextContent]:
    """Tool 22: Get Gateway Uplinks - /network-monitoring/v1alpha1/gateways/{serial}/uplinks"""

    # Step 1: Validate required parameter
    serial = args.get("serial")
    if not serial:
        return [TextContent(
            type="text",
            text="[ERR] Parameter 'serial' is required. Provide the gateway serial number."
        )]

    # Step 2: Call Aruba API
    try:
        data = await call_aruba_api(
            f"/network-monitoring/v1alpha1/gateways/{serial}/uplinks"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [TextContent(
                type="text",
                text=f"[ERR] Gateway with serial '{serial}' not found. Verify the serial number."
            )]
        raise

    # Step 3: Extract uplink data
    uplinks = data.get("uplinks", [])
    gateway_name = data.get("gatewayName", serial)

    if not uplinks:
        return [TextContent(
            type="text",
            text=f"[WARN] No uplink information available for {gateway_name}"
        )]

    # Step 4: Analyze uplinks
    up_count = sum(1 for u in uplinks if u.get("status") == "UP")
    down_count = len(uplinks) - up_count
    primary_uplink = next((u for u in uplinks if u.get("isPrimary", False)), None)

    # Step 5: Create uplink summary
    summary = f"[NET] WAN Uplinks: {gateway_name}\n"
    summary += f"\n[STATS] Total: {len(uplinks)} uplinks | [UP] {up_count} up | [DN] {down_count} down\n"

    for idx, uplink in enumerate(uplinks, 1):
        interface = uplink.get("interfaceName", f"uplink-{idx}")
        status = uplink.get("status", "UNKNOWN")
        uplink_type = uplink.get("type", "UNKNOWN")
        ip_address = uplink.get("ipAddress", "N/A")
        gateway_ip = uplink.get("gateway", "N/A")
        is_primary = uplink.get("isPrimary", False)
        throughput_mbps = uplink.get("throughputMbps", 0)
        tx_bytes = uplink.get("txBytes", 0)
        rx_bytes = uplink.get("rxBytes", 0)
        tx_errors = uplink.get("txErrors", 0)
        rx_errors = uplink.get("rxErrors", 0)

        # Status indicators
        status_label = "[UP]" if status == "UP" else "[DN]"
        primary_badge = "[PRIMARY]" if is_primary else ""

        # Type label
        type_label = {
            "ETHERNET": "[WIRED]",
            "CELLULAR": "[LTE]",
            "DSL": "[DSL]",
            "FIBER": "[FIBER]"
        }.get(uplink_type, "[NET]")

        summary += f"\n{status_label} {interface} {primary_badge}\n"
        summary += f"  {type_label} Type: {uplink_type} | Status: {status}\n"
        summary += f"  [NET] IP: {ip_address} | Gateway: {gateway_ip}\n"
        summary += f"  [TREND] Throughput: {throughput_mbps} Mbps\n"
        summary += f"  [DATA] TX: {format_bytes(tx_bytes)} | RX: {format_bytes(rx_bytes)}\n"

        # Error analysis
        if tx_errors > 0 or rx_errors > 0:
            summary += f"  [WARN] Errors - TX: {tx_errors:,} | RX: {rx_errors:,}\n"

            error_rate_tx = (tx_errors / max(tx_bytes, 1)) * 100 if tx_bytes > 0 else 0
            error_rate_rx = (rx_errors / max(rx_bytes, 1)) * 100 if rx_bytes > 0 else 0

            if error_rate_tx > 1 or error_rate_rx > 1:
                summary += "  [CRIT] High error rate - link quality issues\n"

        # Status-specific warnings
        if status == "DOWN":
            if is_primary:
                summary += "  [CRIT] Primary uplink is down!\n"
            else:
                summary += "  [WARN] Backup uplink unavailable\n"
        elif status == "UP" and throughput_mbps == 0:
            summary += "  [WARN] No traffic - uplink may be idle\n"

    # Overall health assessment
    summary += "\n[STATS] Health Assessment:\n"

    if up_count == 0:
        summary += "  [CRIT] All uplinks are down - no WAN connectivity!\n"
    elif primary_uplink and primary_uplink.get("status") != "UP":
        summary += "  [WARN] Primary uplink down - using backup path\n"
    elif up_count == len(uplinks):
        summary += "  [OK] All uplinks operational - full redundancy available\n"
    else:
        summary += f"  [WARN] Partial connectivity - {down_count} uplink(s) need attention\n"

    # Multi-WAN recommendations
    if len(uplinks) > 1:
        summary += "\n[INFO] Multi-WAN Status:\n"
        if up_count >= 2:
            summary += "  [OK] Multiple active paths - load balancing/failover ready\n"
        elif up_count == 1:
            summary += "  [WARN] Only one uplink active - no failover available\n"

    # Step 6: Return formatted response
    return [TextContent(
        type="text",
        text=f"{summary}\n{_format_json(data)}"
    )]
