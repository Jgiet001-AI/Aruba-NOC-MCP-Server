"""
Get Gateway Cluster Info - MCP tools for gateway cluster information in Aruba Central
"""

import json
import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import format_uptime

logger = logging.getLogger("aruba-noc-server")


def _format_json(data: dict[str, Any]) -> str:
    """Format JSON data for display"""
    return json.dumps(data, indent=2)

async def handle_get_gateway_cluster_info(args: dict[str, Any]) -> list[TextContent]:
    """Tool 20: Get Gateway Cluster Info - /network-monitoring/v1alpha1/clusters/{cluster-name}"""

    # Step 1: Validate required parameter
    cluster_name = args.get("cluster_name")
    if not cluster_name:
        return [TextContent(
            type="text",
            text="[ERR] Parameter 'cluster_name' is required. Provide the cluster name."
        )]

    # Step 2: Call Aruba API
    try:
        data = await call_aruba_api(
            f"/network-monitoring/v1alpha1/clusters/{cluster_name}"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [TextContent(
                type="text",
                text=f"[ERR] Cluster '{cluster_name}' not found. Verify the cluster name."
            )]
        raise

    # Step 3: Extract cluster data
    data.get("clusterId", cluster_name)
    members = data.get("members", [])
    cluster_status = data.get("status", "UNKNOWN")
    ha_enabled = data.get("haEnabled", False)
    sync_status = data.get("configSyncStatus", "UNKNOWN")

    # Identify roles
    primary = None
    backups = []
    standby = []

    for member in members:
        role = member.get("role", "UNKNOWN")
        if role == "PRIMARY":
            primary = member
        elif role == "BACKUP":
            backups.append(member)
        elif role == "STANDBY":
            standby.append(member)

    # Step 4: Create cluster summary
    status_label = "[OK]" if cluster_status == "HEALTHY" else "[WARN]"
    ha_label = "[OK]" if ha_enabled else "[DN]"

    summary = f"[CLUSTER] Gateway Cluster: {cluster_name}\n"
    summary += f"\n{status_label} Status: {cluster_status}\n"
    summary += f"{ha_label} High Availability: {'Enabled' if ha_enabled else 'Disabled'}\n"
    summary += f"\n[MEMBERS] Cluster Members ({len(members)} total):\n"

    # Primary gateway
    if primary:
        gw_name = primary.get("gatewayName", "Unknown")
        gw_serial = primary.get("serialNumber", "Unknown")
        gw_status = primary.get("status", "UNKNOWN")
        uptime = primary.get("uptimeSeconds", 0)

        status_icon = "[UP]" if gw_status == "ONLINE" else "[DN]"

        summary += f"\n[PRIMARY] {gw_name}\n"
        summary += f"  {status_icon} Status: {gw_status}\n"
        summary += f"  [SERIAL] {gw_serial}\n"
        summary += f"  [UPTIME] {format_uptime(uptime)}\n"
    else:
        summary += "\n[WARN] No primary gateway detected!\n"

    # Backup gateways
    if backups:
        summary += f"\n[BACKUP] BACKUP Gateways ({len(backups)}):\n"
        for backup in backups:
            gw_name = backup.get("gatewayName", "Unknown")
            gw_status = backup.get("status", "UNKNOWN")
            status_icon = "[UP]" if gw_status == "ONLINE" else "[DN]"
            summary += f"  {status_icon} {gw_name} - {gw_status}\n"

    # Standby gateways
    if standby:
        summary += f"\n[STANDBY] STANDBY Gateways ({len(standby)}):\n"
        for sb in standby:
            gw_name = sb.get("gatewayName", "Unknown")
            summary += f"  * {gw_name}\n"

    # Configuration sync status
    summary += f"\n[SYNC] Configuration Sync: {sync_status}\n"
    if sync_status != "IN_SYNC":
        summary += "  [WARN] Cluster members may have configuration drift\n"

    # Health analysis
    summary += "\n[STATS] Health Analysis:\n"

    if not ha_enabled:
        summary += "  [WARN] HA is disabled - no automatic failover\n"

    if not primary:
        summary += "  [CRIT] No primary gateway - cluster inoperative\n"
    elif primary.get("status") != "ONLINE":
        summary += f"  [CRIT] Primary gateway is {primary.get('status')}\n"

    if not backups and ha_enabled:
        summary += "  [WARN] No backup gateways - HA cannot function\n"

    offline_backups = [b for b in backups if b.get("status") != "ONLINE"]
    if offline_backups:
        summary += f"  [WARN] {len(offline_backups)} backup gateway(s) offline\n"

    if cluster_status == "HEALTHY" and ha_enabled and backups:
        summary += "  [OK] Cluster is healthy and redundant\n"

    # Step 5: Return formatted response
    return [TextContent(
        type="text",
        text=f"{summary}\n{_format_json(data)}"
    )]
