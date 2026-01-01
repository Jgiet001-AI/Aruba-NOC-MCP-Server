"""
Get Gateway Uplinks - MCP tools for gateway uplinks information in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards, format_bytes
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


async def handle_get_gateway_uplinks(args: dict[str, Any]) -> list[TextContent]:
    """Tool 22: Get Gateway Uplinks - /network-monitoring/v1alpha1/gateways/{serial}/uplinks"""

    # Step 1: Validate required parameter
    serial = args.get("serial")
    if not serial:
        return [
            TextContent(type="text", text="[ERR] Parameter 'serial' is required. Provide the gateway serial number.")
        ]

    # Step 2: Call Aruba API
    try:
        data = await call_aruba_api(f"/network-monitoring/v1alpha1/gateways/{serial}/uplinks")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [
                TextContent(
                    type="text", text=f"[ERR] Gateway with serial '{serial}' not found. Verify the serial number."
                )
            ]
        raise

    # Step 3: Extract uplink data
    uplinks = data.get("uplinks", [])
    gateway_name = data.get("gatewayName", serial)

    if not uplinks:
        return [TextContent(type="text", text=f"[WARN] No uplink information available for {gateway_name}")]

    # Step 4: Analyze uplinks
    up_count = sum(1 for u in uplinks if u.get("status") == "UP")
    down_count = len(uplinks) - up_count
    primary_uplink = next((u for u in uplinks if u.get("isPrimary", False)), None)

    # Step 5: Create uplink summary with verification guardrails
    summary_parts = []

    # Verification checkpoint FIRST
    summary_parts.append(
        VerificationGuards.checkpoint(
            {
                "Total uplinks": f"{len(uplinks)} uplinks",
                "Uplinks UP": f"{up_count} uplinks",
                "Uplinks DOWN": f"{down_count} uplinks",
            }
        )
    )

    summary_parts.append(f"\n[NET] WAN Uplinks: {gateway_name}")
    summary_parts.append(f"\n[STATS] Total: {len(uplinks)} uplinks | [UP] {up_count} up | [DN] {down_count} down")

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
        type_label = {"ETHERNET": "[WIRED]", "CELLULAR": "[LTE]", "DSL": "[DSL]", "FIBER": "[FIBER]"}.get(
            uplink_type, "[NET]"
        )

        summary_parts.append(f"\n{status_label} {interface} {primary_badge}")
        summary_parts.append(f"  {type_label} Type: {uplink_type} | Status: {status}")
        summary_parts.append(f"  [NET] IP: {ip_address} | Gateway: {gateway_ip}")
        summary_parts.append(f"  [TREND] Throughput: {throughput_mbps} Mbps")
        summary_parts.append(f"  [DATA] TX: {format_bytes(tx_bytes)} | RX: {format_bytes(rx_bytes)}")

        # Error analysis
        if tx_errors > 0 or rx_errors > 0:
            summary_parts.append(f"  [WARN] Errors - TX: {tx_errors:,} | RX: {rx_errors:,}")

            error_rate_tx = (tx_errors / max(tx_bytes, 1)) * 100 if tx_bytes > 0 else 0
            error_rate_rx = (rx_errors / max(rx_bytes, 1)) * 100 if rx_bytes > 0 else 0

            if error_rate_tx > 1 or error_rate_rx > 1:
                summary_parts.append("  [CRIT] High error rate - link quality issues")

        # Status-specific warnings
        if status == "DOWN":
            if is_primary:
                summary_parts.append("  [CRIT] Primary uplink is down!")
            else:
                summary_parts.append("  [WARN] Backup uplink unavailable")
        elif status == "UP" and throughput_mbps == 0:
            summary_parts.append("  [WARN] No traffic - uplink may be idle")

    # Overall health assessment
    summary_parts.append("\n[STATS] Health Assessment:")

    if up_count == 0:
        summary_parts.append("  [CRIT] All uplinks are down - no WAN connectivity!")
    elif primary_uplink and primary_uplink.get("status") != "UP":
        summary_parts.append("  [WARN] Primary uplink down - using backup path")
    elif up_count == len(uplinks):
        summary_parts.append("  [OK] All uplinks operational - full redundancy available")
    else:
        summary_parts.append(f"  [WARN] Partial connectivity - {down_count} uplink(s) need attention")

    # Multi-WAN recommendations
    if len(uplinks) > 1:
        summary_parts.append("\n[INFO] Multi-WAN Status:")
        if up_count >= 2:
            summary_parts.append("  [OK] Multiple active paths - load balancing/failover ready")
        elif up_count == 1:
            summary_parts.append("  [WARN] Only one uplink active - no failover available")

    # Anti-hallucination footer
    summary_parts.append(
        VerificationGuards.anti_hallucination_footer(
            {
                "Total uplinks": len(uplinks),
                "Uplinks UP": up_count,
                "Uplinks DOWN": down_count,
            }
        )
    )

    summary = "\n".join(summary_parts)

    # Step 6: Store facts and return summary (NO raw JSON)
    store_facts(
        "get_gateway_uplinks",
        {
            "Gateway": gateway_name,
            "Total uplinks": len(uplinks),
            "Uplinks UP": up_count,
            "Uplinks DOWN": down_count,
        },
    )

    return [TextContent(type="text", text=summary)]
