"""
Get Tenant Device Health - MCP tools for tenant device health monitoring in Aruba Central
"""

import logging
from typing import Any

from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


async def handle_get_tenant_device_health(args: dict[str, Any]) -> list[TextContent]:
    """Tool 7: Get Tenant Device Health - /network-monitoring/v1alpha1/tenant-device-health"""

    # Step 1: Call Aruba API (no parameters needed)
    data = await call_aruba_api("/network-monitoring/v1alpha1/tenant-device-health")

    # Step 2: Extract overall health metrics
    overall_health = data.get("overallHealth", "UNKNOWN").upper()
    health_score = data.get("healthScore", 0)

    # Device totals
    devices = data.get("devices", {})
    total_devices = devices.get("total", 0)
    online_devices = devices.get("online", 0)
    offline_devices = devices.get("offline", 0)

    # Device health distribution (NOTE: these are DEVICE COUNTS, not percentages)
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

    # Step 3: Create executive summary with verification guardrails
    summary_parts = []
    
    # CRITICAL: Verification checkpoint FIRST
    summary_parts.append(VerificationGuards.checkpoint({
        "Total devices": f"{total_devices} devices",
        "Online devices": f"{online_devices} devices",
        "Offline devices": f"{offline_devices} devices",
        "Health score": f"{health_score}% (this is a SCORE, not device count)",
        "Devices in poor health": f"{poor_count} devices (this is device COUNT)",
    }))
    
    health_label = {"GOOD": "[OK]", "FAIR": "[WARN]", "POOR": "[CRIT]"}.get(overall_health, "[--]")

    summary_parts.append("\n[NET] Organization-Wide Network Health")
    summary_parts.append(f"\n[STATUS] Overall Status: {health_label} {overall_health}")
    summary_parts.append(f"  Health Score: {health_score}% (weighted score, NOT device percentage)")

    # Total devices with explicit counts
    summary_parts.append(f"\n[DEV] Total Devices: {total_devices} devices")
    summary_parts.append(f"  * [UP] Online: {online_devices} devices ({online_pct:.1f}% of total)")
    summary_parts.append(f"  * [DN] Offline: {offline_devices} devices")

    # Device types
    summary_parts.append("\n[TYPE] By Type (device counts):")
    summary_parts.append(f"  * [AP] Access Points: {ap_count} devices")
    summary_parts.append(f"  * [SW] Switches: {switch_count} devices")
    summary_parts.append(f"  * [GW] Gateways: {gateway_count} devices")

    # Health distribution - CRITICAL: These are device COUNTS, not percentages
    if good_count or fair_count or poor_count:
        summary_parts.append("\n[HEALTH] Health Distribution (DEVICE COUNTS, not percentages):")
        summary_parts.append(f"  * [OK] Good health: {good_count} devices")
        summary_parts.append(f"  * [WARN] Fair health: {fair_count} devices")
        summary_parts.append(f"  * [CRIT] Poor health: {poor_count} devices")
        summary_parts.append("  [!] These are actual device counts, not health score percentages")

    # SLA indicators
    if online_pct >= 99:
        summary_parts.append(f"\n[SLA] SLA Status: [OK] Excellent ({online_pct:.2f}% uptime)")
    elif online_pct >= 95:
        summary_parts.append(f"\n[SLA] SLA Status: [OK] Meeting target ({online_pct:.2f}% uptime)")
    else:
        summary_parts.append(f"\n[WARN] SLA Status: [WARN] Below target ({online_pct:.2f}% uptime)")

    # Warnings
    if poor_count > 0:
        summary_parts.append(f"\n[WARN] Action Required: {poor_count} devices in poor health")
    if offline_devices > total_devices * 0.05:
        summary_parts.append(f"[WARN] Alert: {offline_devices} devices offline (>{5}%)")

    # Anti-hallucination footer
    summary_parts.append(VerificationGuards.anti_hallucination_footer({
        "Total devices": total_devices,
        "Online devices": online_devices,
        "Offline devices": offline_devices,
        "Poor health devices": poor_count,
    }))

    summary = "\n".join(summary_parts)

    # Step 4: Store facts and return summary (NO raw JSON)
    store_facts("get_tenant_device_health", {
        "Total devices": total_devices,
        "Online devices": online_devices,
        "Offline devices": offline_devices,
        "Health score (%)": health_score,
        "Poor health devices": poor_count,
        "Fair health devices": fair_count,
        "Good health devices": good_count,
    })
    
    return [TextContent(type="text", text=summary)]
