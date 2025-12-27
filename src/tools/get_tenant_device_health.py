"""
Get Tenant Device Health - MCP tools for tenant device health monitoring in Aruba Central
"""

import json
import logging
from typing import Any

from mcp.types import TextContent

from src.api_client import call_aruba_api

logger = logging.getLogger("aruba-noc-server")


def _format_json(data: dict[str, Any]) -> str:
    """Format JSON data for display"""
    return json.dumps(data, indent=2)

async def handle_get_tenant_device_health(args: dict[str, Any]) -> list[TextContent]:
    """Tool 7: Get Tenant Device Health - /network-monitoring/v1alpha1/tenant-device-health"""

    # Step 1: Call Aruba API (no parameters needed)
    data = await call_aruba_api(
        "/network-monitoring/v1alpha1/tenant-device-health"
    )

    # Step 2: Extract overall health metrics
    overall_health = data.get("overallHealth", "UNKNOWN").upper()
    health_score = data.get("healthScore", 0)

    # Device totals
    devices = data.get("devices", {})
    total_devices = devices.get("total", 0)
    online_devices = devices.get("online", 0)
    offline_devices = devices.get("offline", 0)

    # Device health distribution
    health_dist = data.get("healthDistribution", {})
    good_count = health_dist.get("good", 0)
    fair_count = health_dist.get("fair", 0)
    poor_count = health_dist.get("poor", 0)

    # Device types
    by_type = devices.get("byType", {})
    ap_count = by_type.get("ACCESS_POINT", 0)
    switch_count = by_type.get("SWITCH", 0)
    gateway_count = by_type.get("GATEWAY", 0)

    # Calculate percentages
    online_pct = (online_devices / total_devices * 100) if total_devices > 0 else 0

    # Step 3: Create executive summary with professional labels
    health_label = {
        "GOOD": "[OK]",
        "FAIR": "[WARN]",
        "POOR": "[CRIT]"
    }.get(overall_health, "[--]")

    summary = "[NET] Organization-Wide Network Health\n"
    summary += f"\n[STATUS] Overall Status: {health_label} {overall_health} ({health_score}%)\n"

    # Total devices
    summary += f"\n[DEV] Total Devices: {total_devices}\n"
    summary += f"  * [UP] Online: {online_devices} ({online_pct:.1f}%)\n"
    summary += f"  * [DN] Offline: {offline_devices}\n"

    # Device types
    summary += "\n[TYPE] By Type:\n"
    summary += f"  * [AP] Access Points: {ap_count}\n"
    summary += f"  * [SW] Switches: {switch_count}\n"
    summary += f"  * [GW] Gateways: {gateway_count}\n"

    # Health distribution
    if good_count or fair_count or poor_count:
        summary += "\n[HEALTH] Health Distribution:\n"
        summary += f"  * [OK] Good: {good_count}\n"
        summary += f"  * [WARN] Fair: {fair_count}\n"
        summary += f"  * [CRIT] Poor: {poor_count}\n"

    # SLA indicators
    if online_pct >= 99:
        summary += f"\n[SLA] SLA Status: [OK] Excellent ({online_pct:.2f}% uptime)\n"
    elif online_pct >= 95:
        summary += f"\n[SLA] SLA Status: [OK] Meeting target ({online_pct:.2f}% uptime)\n"
    else:
        summary += f"\n[WARN] SLA Status: [WARN] Below target ({online_pct:.2f}% uptime)\n"

    # Warnings
    if poor_count > 0:
        summary += f"\n[WARN] Action Required: {poor_count} devices in poor health\n"
    if offline_devices > total_devices * 0.05:
        summary += f"[WARN] Alert: {offline_devices} devices offline (>{5}%)\n"

    # Step 4: Return formatted response
    return [TextContent(
        type="text",
        text=f"{summary}\n{_format_json(data)}"
    )]
