"""
List Gateway Tunnels - MCP tools for gateway tunnel listing in Aruba Central
"""

import json
import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api

logger = logging.getLogger("aruba-noc-server")


def _format_json(data: dict[str, Any]) -> str:
    """Format JSON data for display"""
    return json.dumps(data, indent=2)

async def handle_list_gateway_tunnels(args: dict[str, Any]) -> list[TextContent]:
    """Tool 21: List Gateway Tunnels - /network-monitoring/v1alpha1/clusters/{cluster-name}/tunnels"""

    # Step 1: Validate required parameter
    cluster_name = args.get("cluster_name")
    if not cluster_name:
        return [TextContent(
            type="text",
            text="[ERR] Parameter 'cluster_name' is required. Provide the cluster name."
        )]

    # Step 2: Build query parameters
    params = {}
    params["limit"] = args.get("limit", 100)

    # Step 3: Call Aruba API
    try:
        data = await call_aruba_api(
            f"/network-monitoring/v1alpha1/clusters/{cluster_name}/tunnels",
            params=params
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [TextContent(
                type="text",
                text=f"[ERR] Cluster '{cluster_name}' not found. Verify the cluster name."
            )]
        raise

    # Step 4: Extract tunnel data
    tunnels = data.get("items", [])
    total = data.get("total", len(tunnels))

    # Categorize tunnels
    by_status = {}
    by_type = {}
    down_tunnels = []

    for tunnel in tunnels:
        status = tunnel.get("status", "UNKNOWN")
        tunnel_type = tunnel.get("type", "UNKNOWN")

        by_status[status] = by_status.get(status, 0) + 1
        by_type[tunnel_type] = by_type.get(tunnel_type, 0) + 1

        if status == "DOWN":
            down_tunnels.append(tunnel.get("tunnelName", "Unknown"))

    # Step 5: Create tunnel summary
    up_count = by_status.get("UP", 0)
    down_count = by_status.get("DOWN", 0)

    summary = f"[VPN] VPN Tunnels: {cluster_name}\n"
    summary += f"\n[STATS] Total: {total} tunnels | [UP] {up_count} up | [DN] {down_count} down\n"

    if by_type:
        summary += "\n[TYPE] Tunnel Types:\n"
        for ttype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            summary += f"  * {ttype}: {count}\n"

    if down_tunnels:
        summary += f"\n[WARN] Tunnels DOWN ({len(down_tunnels)}): {', '.join(down_tunnels)}\n"

    summary += "\n[LIST] Tunnel Details:\n"

    for tunnel in tunnels:
        tunnel_name = tunnel.get("tunnelName", "Unknown")
        status = tunnel.get("status", "UNKNOWN")
        tunnel_type = tunnel.get("type", "UNKNOWN")
        local_endpoint = tunnel.get("localEndpoint", "N/A")
        remote_endpoint = tunnel.get("remoteEndpoint", "N/A")
        encryption = tunnel.get("encryption", "N/A")
        throughput_mbps = tunnel.get("throughputMbps", 0)
        tx_packets = tunnel.get("txPackets", 0)
        rx_packets = tunnel.get("rxPackets", 0)

        status_label = "[UP]" if status == "UP" else "[DN]"
        type_label = "[IPSEC]" if tunnel_type == "IPsec" else "[VPN]"

        summary += f"\n{status_label} {tunnel_name}\n"
        summary += f"  {type_label} Type: {tunnel_type} | [ENC] {encryption}\n"
        summary += f"  [NET] {local_endpoint} <-> {remote_endpoint}\n"
        summary += f"  [DATA] Throughput: {throughput_mbps} Mbps\n"
        summary += f"  [PKT] TX: {tx_packets:,} | RX: {rx_packets:,} packets\n"

        # Tunnel health warnings
        if status == "DOWN":
            summary += "  [CRIT] Tunnel is down - connectivity lost\n"
        elif throughput_mbps == 0 and status == "UP":
            summary += "  [WARN] No traffic - tunnel may be idle or broken\n"

        # Encryption warnings
        if encryption in ["DES", "3DES", "None"]:
            summary += "  [WARN] Weak or no encryption - security risk\n"

    # Overall health assessment
    if down_count == 0:
        summary += "\n[OK] All tunnels operational\n"
    elif down_count == total:
        summary += "\n[CRIT] All tunnels are down!\n"
    else:
        summary += f"\n[WARN] {down_count}/{total} tunnels need attention\n"

    # Step 6: Return formatted response
    return [TextContent(
        type="text",
        text=f"{summary}\n{_format_json(data)}"
    )]
