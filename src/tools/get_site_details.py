"""
Get Site Details - MCP tools for site details retrieval in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


async def handle_get_site_details(args: dict[str, Any]) -> list[TextContent]:
    """Tool 6: Get Site Details - /network-monitoring/v1alpha1/site-health/{site-id}"""

    # Step 1: Validate required parameter
    site_id = args.get("site_id")
    if not site_id:
        return [TextContent(type="text", text="[ERR] Parameter 'site_id' is required. Please provide the site ID.")]

    # Step 2: Call Aruba API (path parameter)
    # CRITICAL: API uses hyphenated path: site-health/{site-id}
    try:
        data = await call_aruba_api(f"/network-monitoring/v1alpha1/site-health/{site_id}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [
                TextContent(type="text", text=f"[ERR] Site with ID '{site_id}' not found. Please verify the site ID.")
            ]
        raise

    # Step 3: Extract site details
    site_name = data.get("siteName", "Unknown")
    health = data.get("overallHealth", "UNKNOWN").upper()

    # Device statistics
    devices = data.get("devices", {})
    total_devices = devices.get("total", 0)
    online_devices = devices.get("online", 0)
    offline_devices = devices.get("offline", 0)
    devices_by_type = devices.get("byType", {})

    # Client statistics
    clients = data.get("clients", {})
    total_clients = clients.get("total", 0)
    wireless_clients = clients.get("wireless", 0)
    wired_clients = clients.get("wired", 0)

    # Alert statistics
    alerts = data.get("alerts", {})
    critical_alerts = alerts.get("critical", 0)
    warning_alerts = alerts.get("warning", 0)
    total_alerts = critical_alerts + warning_alerts

    # Bandwidth
    bandwidth = data.get("bandwidthUsage", {})
    download_mbps = bandwidth.get("downloadMbps", 0)
    upload_mbps = bandwidth.get("uploadMbps", 0)

    # Step 4: Create detailed summary with verification guardrails
    summary_parts = []

    # Verification checkpoint FIRST
    summary_parts.append(
        VerificationGuards.checkpoint(
            {
                "Site": site_name,
                "Health": health,
                "Total devices": f"{total_devices} devices",
                "Online devices": f"{online_devices} devices",
                "Offline devices": f"{offline_devices} devices",
                "Total clients": f"{total_clients} clients",
            }
        )
    )

    health_label = {"GOOD": "[OK]", "FAIR": "[WARN]", "POOR": "[CRIT]"}.get(health, "[--]")

    summary_parts.append(f"\n[SITE] Site Details: {site_name} (ID: {site_id})")
    summary_parts.append(f"\n[STATS] Health: {health_label} {health}")

    # Devices
    summary_parts.append(f"\n[DEV] Devices: {total_devices} devices total")
    summary_parts.append(f"  * [UP] Online: {online_devices} devices")
    summary_parts.append(f"  * [DN] Offline: {offline_devices} devices")
    if devices_by_type:
        summary_parts.append("  * By Type:")
        for dtype, dcount in devices_by_type.items():
            summary_parts.append(f"    - {dtype}: {dcount} devices")

    # Clients
    summary_parts.append(f"\n[CLI] Clients: {total_clients} clients connected")
    summary_parts.append(f"  * [WIFI] Wireless: {wireless_clients} clients")
    summary_parts.append(f"  * [WIRED] Wired: {wired_clients} clients")

    # Alerts
    if total_alerts > 0:
        summary_parts.append(f"\n[ALERT] Alerts: {total_alerts} active")
        if critical_alerts > 0:
            summary_parts.append(f"  * [CRIT] Critical: {critical_alerts}")
        if warning_alerts > 0:
            summary_parts.append(f"  * [WARN] Warning: {warning_alerts}")
    else:
        summary_parts.append("\n[OK] No active alerts")

    # Bandwidth
    if download_mbps or upload_mbps:
        summary_parts.append("\n[TREND] Bandwidth Usage:")
        summary_parts.append(f"  * [DN] Download: {download_mbps:.2f} Mbps")
        summary_parts.append(f"  * [UP] Upload: {upload_mbps:.2f} Mbps")

    # Warnings
    if offline_devices > total_devices * 0.2:
        summary_parts.append(f"\n[WARN] {offline_devices} devices offline (>{20}%)")
    if critical_alerts > 0:
        summary_parts.append(f"[WARN] Action Required: {critical_alerts} critical alerts")

    # Anti-hallucination footer
    summary_parts.append(
        VerificationGuards.anti_hallucination_footer(
            {
                "Site": site_name,
                "Total devices": total_devices,
                "Online": online_devices,
                "Offline": offline_devices,
                "Total clients": total_clients,
            }
        )
    )

    summary = "\n".join(summary_parts)

    # Step 5: Store facts and return summary (NO raw JSON)
    store_facts(
        "get_site_details",
        {
            "Site": site_name,
            "Health": health,
            "Total devices": total_devices,
            "Online devices": online_devices,
            "Offline devices": offline_devices,
            "Total clients": total_clients,
        },
    )

    return [TextContent(type="text", text=summary)]
