"""
Get Gateway Details - MCP tools for gateway details retrieval in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import format_json

logger = logging.getLogger("aruba-noc-server")


async def handle_get_gateway_details(args: dict[str, Any]) -> list[TextContent]:
    """Tool 11: Get Gateway Details - /network-monitoring/v1alpha1/gateways/{serial-number}"""

    # Step 1: Validate required parameter
    serial_number = args.get("serial_number")
    if not serial_number:
        return [
            TextContent(
                type="text",
                text="[ERR] Parameter 'serial_number' is required. Please provide the gateway serial number.",
            )
        ]

    # Step 2: Call Aruba API (path parameter)
    # CRITICAL: API uses hyphenated path: gateways/{serial-number}
    try:
        data = await call_aruba_api(f"/network-monitoring/v1alpha1/gateways/{serial_number}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [
                TextContent(
                    type="text",
                    text=f"[ERR] Gateway with serial '{serial_number}' not found. Please verify the serial number.",
                )
            ]
        raise

    # Step 3: Extract gateway details
    device_name = data.get("deviceName", "Unknown")
    model = data.get("model", "Unknown")
    status = data.get("status", "UNKNOWN")
    firmware = data.get("firmwareVersion", "Unknown")
    uptime = data.get("uptime", 0)
    cpu_util = data.get("cpuUtilization", 0)
    mem_util = data.get("memoryUtilization", 0)
    site_name = data.get("siteName", "Unknown")

    # Cluster information
    cluster_name = data.get("clusterName")
    cluster_role = data.get("clusterRole", "Standalone")
    deployment = data.get("deployment", "Standalone")

    # Tunnel information
    tunnel_count = data.get("activeTunnels", 0)

    # Uplink information
    uplinks = data.get("uplinks", [])
    uplinks_up = sum(1 for u in uplinks if u.get("status") == "UP")
    uplinks_total = len(uplinks)

    # Throughput
    throughput = data.get("throughput", {})
    download_mbps = throughput.get("downloadMbps", 0)
    upload_mbps = throughput.get("uploadMbps", 0)

    # Step 4: Create detailed summary with professional labels
    status_label = "[UP]" if status == "ONLINE" else "[DN]"

    summary = f"[GW] Gateway Details: {device_name}\n"
    summary += f"\n[STATUS] {status_label} {status}\n"
    summary += f"[MODEL] {model}\n"
    summary += f"[SERIAL] {serial_number}\n"
    summary += f"[FW] Firmware: {firmware}\n"
    summary += f"[UPTIME] {uptime} seconds\n"
    summary += f"[LOC] Location: {site_name}\n"

    # Deployment and clustering
    summary += f"\n[CFG] Deployment: {deployment}\n"
    if cluster_name:
        summary += f"[CLUSTER] {cluster_name}\n"
        summary += f"[ROLE] {cluster_role}\n"

    # Uplinks
    if uplinks_total > 0:
        summary += f"\n[LINK] Uplinks: {uplinks_up}/{uplinks_total} up\n"
        for uplink in uplinks:
            uplink_name = uplink.get("name", "Unknown")
            uplink_status = uplink.get("status", "UNKNOWN")
            uplink_label = "[UP]" if uplink_status == "UP" else "[DN]"
            summary += f"  * {uplink_label} {uplink_name}: {uplink_status}\n"

    # Tunnels
    if tunnel_count > 0:
        summary += f"\n[VPN] VPN Tunnels: {tunnel_count} active\n"
    else:
        summary += "\n[VPN] VPN Tunnels: None active\n"

    # Throughput
    if download_mbps or upload_mbps:
        summary += "\n[TREND] Throughput:\n"
        summary += f"  * [DN] Download: {download_mbps:.2f} Mbps\n"
        summary += f"  * [UP] Upload: {upload_mbps:.2f} Mbps\n"

    # Performance indicators
    if cpu_util > 80:
        summary += f"\n[WARN] High CPU: {cpu_util}%\n"
    if mem_util > 80:
        summary += f"[WARN] High Memory: {mem_util}%\n"

    # Warnings
    if uplinks_total > 0 and uplinks_up < uplinks_total:
        summary += f"[WARN] {uplinks_total - uplinks_up} uplink(s) down\n"
    if uplinks_up == 0:
        summary += "[CRIT] All uplinks down - no WAN connectivity\n"

    # Step 5: Return formatted response
    return [TextContent(type="text", text=f"{summary}\n{format_json(data)}")]
