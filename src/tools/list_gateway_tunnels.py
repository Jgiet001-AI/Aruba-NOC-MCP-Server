"""
List Gateway Tunnels - MCP tools for gateway tunnel listing in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


async def handle_list_gateway_tunnels(args: dict[str, Any]) -> list[TextContent]:
    """Tool 21: List Gateway Tunnels - /network-monitoring/v1alpha1/clusters/{cluster-name}/tunnels"""

    # Step 1: Validate required parameter
    cluster_name = args.get("cluster_name")
    if not cluster_name:
        return [TextContent(type="text", text="[ERR] Parameter 'cluster_name' is required. Provide the cluster name.")]

    # Step 2: Build query parameters
    params = {}
    params["limit"] = args.get("limit", 100)

    # Step 3: Call Aruba API
    try:
        data = await call_aruba_api(f"/network-monitoring/v1alpha1/clusters/{cluster_name}/tunnels", params=params)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [
                TextContent(type="text", text=f"[ERR] Cluster '{cluster_name}' not found. Verify the cluster name.")
            ]
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

    # Step 5: Create tunnel summary with verification guardrails
    up_count = by_status.get("UP", 0)
    down_count = by_status.get("DOWN", 0)

    summary_parts = []
    
    # Verification checkpoint FIRST
    summary_parts.append(VerificationGuards.checkpoint({
        "Total tunnels": f"{total} tunnels",
        "Tunnels UP": f"{up_count} tunnels",
        "Tunnels DOWN": f"{down_count} tunnels",
    }))
    
    summary_parts.append(f"\n[VPN] VPN Tunnels: {cluster_name}")
    summary_parts.append(f"\n[STATS] Total: {total} tunnels | [UP] {up_count} up | [DN] {down_count} down")

    if by_type:
        summary_parts.append("\n[TYPE] Tunnel Types:")
        for ttype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            summary_parts.append(f"  * {ttype}: {count} tunnels")

    if down_tunnels:
        summary_parts.append(f"\n[WARN] Tunnels DOWN ({len(down_tunnels)}): {', '.join(down_tunnels)}")

    summary_parts.append("\n[LIST] Tunnel Details:")

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

        summary_parts.append(f"\n{status_label} {tunnel_name}")
        summary_parts.append(f"  {type_label} Type: {tunnel_type} | [ENC] {encryption}")
        summary_parts.append(f"  [NET] {local_endpoint} <-> {remote_endpoint}")
        summary_parts.append(f"  [DATA] Throughput: {throughput_mbps} Mbps")
        summary_parts.append(f"  [PKT] TX: {tx_packets:,} | RX: {rx_packets:,} packets")

        # Tunnel health warnings
        if status == "DOWN":
            summary_parts.append("  [CRIT] Tunnel is down - connectivity lost")
        elif throughput_mbps == 0 and status == "UP":
            summary_parts.append("  [WARN] No traffic - tunnel may be idle or broken")

        # Encryption warnings
        if encryption in ["DES", "3DES", "None"]:
            summary_parts.append("  [WARN] Weak or no encryption - security risk")

    # Overall health assessment
    if down_count == 0:
        summary_parts.append("\n[OK] All tunnels operational")
    elif down_count == total:
        summary_parts.append("\n[CRIT] All tunnels are down!")
    else:
        summary_parts.append(f"\n[WARN] {down_count}/{total} tunnels need attention")

    # Anti-hallucination footer
    summary_parts.append(VerificationGuards.anti_hallucination_footer({
        "Total tunnels": total,
        "Tunnels UP": up_count,
        "Tunnels DOWN": down_count,
    }))

    summary = "\n".join(summary_parts)

    # Step 6: Store facts and return summary (NO raw JSON)
    store_facts("list_gateway_tunnels", {
        "Cluster": cluster_name,
        "Total tunnels": total,
        "Tunnels UP": up_count,
        "Tunnels DOWN": down_count,
    })
    
    return [TextContent(type="text", text=summary)]
