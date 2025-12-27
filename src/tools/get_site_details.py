"""
Get Site Details - MCP tools for site details retrieval in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import format_json

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

    # Step 4: Create detailed summary with professional labels
    health_label = {"GOOD": "[OK]", "FAIR": "[WARN]", "POOR": "[CRIT]"}.get(health, "[--]")

    summary = f"[SITE] Site Details: {site_name} (ID: {site_id})\n"
    summary += f"\n[STATS] Health: {health_label} {health}\n"

    # Devices
    summary += f"\n[DEV] Devices: {total_devices} total\n"
    summary += f"  * [UP] Online: {online_devices}\n"
    summary += f"  * [DN] Offline: {offline_devices}\n"
    if devices_by_type:
        summary += f"  * By Type: {dict(devices_by_type)}\n"

    # Clients
    summary += f"\n[CLI] Clients: {total_clients} connected\n"
    summary += f"  * [WIFI] Wireless: {wireless_clients}\n"
    summary += f"  * [WIRED] Wired: {wired_clients}\n"

    # Alerts
    if total_alerts > 0:
        summary += f"\n[ALERT] Alerts: {total_alerts} active\n"
        if critical_alerts > 0:
            summary += f"  * [CRIT] Critical: {critical_alerts}\n"
        if warning_alerts > 0:
            summary += f"  * [WARN] Warning: {warning_alerts}\n"
    else:
        summary += "\n[OK] No active alerts\n"

    # Bandwidth
    if download_mbps or upload_mbps:
        summary += "\n[TREND] Bandwidth Usage:\n"
        summary += f"  * [DN] Download: {download_mbps:.2f} Mbps\n"
        summary += f"  * [UP] Upload: {upload_mbps:.2f} Mbps\n"

    # Warnings
    if offline_devices > total_devices * 0.2:
        summary += f"\n[WARN] {offline_devices} devices offline (>{20}%)\n"
    if critical_alerts > 0:
        summary += f"[WARN] Action Required: {critical_alerts} critical alerts\n"

    # Step 5: Return formatted response
    return [TextContent(type="text", text=f"{summary}\n{format_json(data)}")]
