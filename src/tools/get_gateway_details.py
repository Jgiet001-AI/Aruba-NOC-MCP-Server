"""
Get Gateway Details - MCP tools for gateway details retrieval in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards, validate_input
from src.tools.models import GetGatewayDetailsInput
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


async def handle_get_gateway_details(args: dict[str, Any]) -> list[TextContent]:
    """Tool 11: Get Gateway Details - /network-monitoring/v1alpha1/gateways/{serial-number}"""

    # Step 1: Validate input with Pydantic
    validated = validate_input(GetGatewayDetailsInput, args, "get_gateway_details")
    if isinstance(validated, list):
        return validated  # Validation error response
    serial_number = validated.serial_number

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

    # Step 4: Create detailed summary with verification guardrails
    summary_parts = []

    # Verification checkpoint FIRST
    summary_parts.append(VerificationGuards.checkpoint({
        "Gateway Name": device_name,
        "Serial": serial_number,
        "Status": status,
        "Active tunnels": f"{tunnel_count} tunnels",
        "Uplinks": f"{uplinks_up}/{uplinks_total} up",
    }))

    status_label = "[UP]" if status == "ONLINE" else "[DN]"

    summary_parts.append(f"\n[GW] Gateway Details: {device_name}")
    summary_parts.append(f"\n[STATUS] {status_label} {status}")
    summary_parts.append(f"[MODEL] {model}")
    summary_parts.append(f"[SERIAL] {serial_number}")
    summary_parts.append(f"[FW] Firmware: {firmware}")
    summary_parts.append(f"[UPTIME] {uptime} seconds")
    summary_parts.append(f"[LOC] Location: {site_name}")

    # Deployment and clustering
    summary_parts.append(f"\n[CFG] Deployment: {deployment}")
    if cluster_name:
        summary_parts.append(f"[CLUSTER] {cluster_name}")
        summary_parts.append(f"[ROLE] {cluster_role}")

    # Uplinks
    if uplinks_total > 0:
        summary_parts.append(f"\n[LINK] Uplinks: {uplinks_up}/{uplinks_total} up")
        for uplink in uplinks:
            uplink_name = uplink.get("name", "Unknown")
            uplink_status = uplink.get("status", "UNKNOWN")
            uplink_label = "[UP]" if uplink_status == "UP" else "[DN]"
            summary_parts.append(f"  * {uplink_label} {uplink_name}: {uplink_status}")

    # Tunnels
    if tunnel_count > 0:
        summary_parts.append(f"\n[VPN] VPN Tunnels: {tunnel_count} active")
    else:
        summary_parts.append("\n[VPN] VPN Tunnels: None active")

    # Throughput
    if download_mbps or upload_mbps:
        summary_parts.append("\n[TREND] Throughput:")
        summary_parts.append(f"  * [DN] Download: {download_mbps:.2f} Mbps")
        summary_parts.append(f"  * [UP] Upload: {upload_mbps:.2f} Mbps")

    # Performance indicators
    if cpu_util > 80:
        summary_parts.append(f"\n[WARN] High CPU: {cpu_util}%")
    if mem_util > 80:
        summary_parts.append(f"[WARN] High Memory: {mem_util}%")

    # Warnings
    if uplinks_total > 0 and uplinks_up < uplinks_total:
        summary_parts.append(f"[WARN] {uplinks_total - uplinks_up} uplink(s) down")
    if uplinks_up == 0:
        summary_parts.append("[CRIT] All uplinks down - no WAN connectivity")

    # Anti-hallucination footer
    summary_parts.append(VerificationGuards.anti_hallucination_footer({
        "Gateway": device_name,
        "Status": status,
        "Tunnels": tunnel_count,
    }))

    summary = "\n".join(summary_parts)

    # Step 5: Store facts and return summary (NO raw JSON)
    store_facts("get_gateway_details", {
        "Gateway Name": device_name,
        "Serial": serial_number,
        "Status": status,
        "Active tunnels": tunnel_count,
        "Uplinks up": uplinks_up,
        "Site": site_name,
    })

    return [TextContent(type="text", text=summary)]
