"""
Get Gateway Cluster Info - MCP tools for gateway cluster information in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import format_uptime, VerificationGuards
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


async def handle_get_gateway_cluster_info(args: dict[str, Any]) -> list[TextContent]:
    """Tool 20: Get Gateway Cluster Info - /network-monitoring/v1alpha1/clusters/{cluster-name}"""

    # Step 1: Validate required parameter
    cluster_name = args.get("cluster_name")
    if not cluster_name:
        return [TextContent(type="text", text="[ERR] Parameter 'cluster_name' is required. Provide the cluster name.")]

    # Step 2: Call Aruba API
    try:
        data = await call_aruba_api(f"/network-monitoring/v1alpha1/clusters/{cluster_name}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [
                TextContent(type="text", text=f"[ERR] Cluster '{cluster_name}' not found. Verify the cluster name.")
            ]
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

    # Step 4: Create cluster summary with verification guardrails
    status_label = "[OK]" if cluster_status == "HEALTHY" else "[WARN]"
    ha_label = "[OK]" if ha_enabled else "[DN]"

    summary_parts = []
    
    # Verification checkpoint FIRST
    summary_parts.append(VerificationGuards.checkpoint({
        "Total members": f"{len(members)} members",
        "Status": cluster_status,
        "HA enabled": "Yes" if ha_enabled else "No",
    }))
    
    summary_parts.append(f"\n[CLUSTER] Gateway Cluster: {cluster_name}")
    summary_parts.append(f"\n{status_label} Status: {cluster_status}")
    summary_parts.append(f"{ha_label} High Availability: {'Enabled' if ha_enabled else 'Disabled'}")
    summary_parts.append(f"\n[MEMBERS] Cluster Members ({len(members)} total):")

    # Primary gateway
    if primary:
        gw_name = primary.get("gatewayName", "Unknown")
        gw_serial = primary.get("serialNumber", "Unknown")
        gw_status = primary.get("status", "UNKNOWN")
        uptime = primary.get("uptimeSeconds", 0)

        status_icon = "[UP]" if gw_status == "ONLINE" else "[DN]"

        summary_parts.append(f"\n[PRIMARY] {gw_name}")
        summary_parts.append(f"  {status_icon} Status: {gw_status}")
        summary_parts.append(f"  [SERIAL] {gw_serial}")
        summary_parts.append(f"  [UPTIME] {format_uptime(uptime)}")
    else:
        summary_parts.append("\n[WARN] No primary gateway detected!")

    # Backup gateways
    if backups:
        summary_parts.append(f"\n[BACKUP] BACKUP Gateways ({len(backups)}):")
        for backup in backups:
            gw_name = backup.get("gatewayName", "Unknown")
            gw_status = backup.get("status", "UNKNOWN")
            status_icon = "[UP]" if gw_status == "ONLINE" else "[DN]"
            summary_parts.append(f"  {status_icon} {gw_name} - {gw_status}")

    # Standby gateways
    if standby:
        summary_parts.append(f"\n[STANDBY] STANDBY Gateways ({len(standby)}):")
        for sb in standby:
            gw_name = sb.get("gatewayName", "Unknown")
            summary_parts.append(f"  * {gw_name}")

    # Configuration sync status
    summary_parts.append(f"\n[SYNC] Configuration Sync: {sync_status}")
    if sync_status != "IN_SYNC":
        summary_parts.append("  [WARN] Cluster members may have configuration drift")

    # Health analysis
    summary_parts.append("\n[STATS] Health Analysis:")

    if not ha_enabled:
        summary_parts.append("  [WARN] HA is disabled - no automatic failover")

    if not primary:
        summary_parts.append("  [CRIT] No primary gateway - cluster inoperative")
    elif primary.get("status") != "ONLINE":
        summary_parts.append(f"  [CRIT] Primary gateway is {primary.get('status')}")

    if not backups and ha_enabled:
        summary_parts.append("  [WARN] No backup gateways - HA cannot function")

    offline_backups = [b for b in backups if b.get("status") != "ONLINE"]
    if offline_backups:
        summary_parts.append(f"  [WARN] {len(offline_backups)} backup gateway(s) offline")

    if cluster_status == "HEALTHY" and ha_enabled and backups:
        summary_parts.append("  [OK] Cluster is healthy and redundant")

    # Anti-hallucination footer
    summary_parts.append(VerificationGuards.anti_hallucination_footer({
        "Total members": len(members),
        "Status": cluster_status,
        "HA enabled": "Yes" if ha_enabled else "No",
    }))

    summary = "\n".join(summary_parts)

    # Step 5: Store facts and return summary (NO raw JSON)
    store_facts("get_gateway_cluster_info", {
        "Cluster": cluster_name,
        "Total members": len(members),
        "Status": cluster_status,
        "HA enabled": "Yes" if ha_enabled else "No",
    })
    
    return [TextContent(type="text", text=summary)]
