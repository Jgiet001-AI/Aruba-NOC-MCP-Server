"""
Get Top Clients by Usage - MCP tools for top clients usage analysis in Aruba Central
"""

import logging
from typing import Any

from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards, format_bytes
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


async def handle_get_top_clients_by_usage(args: dict[str, Any]) -> list[TextContent]:
    """Tool 14: Get Top Clients by Usage - /network-monitoring/v1alpha1/clients/usage/topn"""

    # Step 1: Extract parameters
    params = {}

    if "site_id" in args:
        params["site-id"] = args["site_id"]
    params["limit"] = args.get("limit", 10)
    params["time-range"] = args.get("time_range", "24hours")
    if "connection_type" in args and args["connection_type"] != "ALL":
        params["connection-type"] = args["connection_type"]

    # Step 2: Call Aruba API
    data = await call_aruba_api("/network-monitoring/v1alpha1/clients/usage/topn", params=params)

    # Step 3: Extract top clients
    top_clients = data.get("items", [])
    time_range = params["time-range"]

    # Calculate totals
    total_bandwidth = sum(c.get("totalBytes", 0) for c in top_clients)

    # Step 4: Create ranked summary with verification guardrails
    summary_parts = []

    # Verification checkpoint FIRST
    summary_parts.append(
        VerificationGuards.checkpoint(
            {
                "Top clients shown": f"{len(top_clients)} clients",
                "Combined bandwidth": format_bytes(total_bandwidth),
            }
        )
    )

    summary_parts.append(f"\n[CLI] Top {len(top_clients)} Bandwidth Consumers ({time_range})")
    summary_parts.append(f"\n[STATS] Combined Usage: {format_bytes(total_bandwidth)}")
    summary_parts.append("\n[RANK] Rankings:")

    for idx, client in enumerate(top_clients[:10], 1):
        hostname = client.get("hostname", "Unknown")
        mac = client.get("macAddress", "Unknown")
        total_bytes = client.get("totalBytes", 0)
        download_bytes = client.get("downloadBytes", 0)
        upload_bytes = client.get("uploadBytes", 0)
        connection_type = client.get("connectionType", "UNKNOWN")
        connected_device = client.get("connectedDevice", "Unknown")
        ip_address = client.get("ipAddress", "Unknown")

        # Rank labels
        rank_label = {1: "#1", 2: "#2", 3: "#3"}.get(idx, f"#{idx}")
        conn_label = "[WIFI]" if connection_type == "WIRELESS" else "[WIRED]"

        summary_parts.append(f"\n{rank_label} {hostname}")
        summary_parts.append(f"    {conn_label} {connection_type} | MAC: {mac} | IP: {ip_address}")
        summary_parts.append(f"    [DATA] Total: {format_bytes(total_bytes)}")
        summary_parts.append(f"    [DN] Down: {format_bytes(download_bytes)} | [UP] Up: {format_bytes(upload_bytes)}")
        summary_parts.append(f"    [LOC] Connected to: {connected_device}")

        # Usage warnings
        if total_bytes > 100 * 1024**3:  # > 100 GB
            summary_parts.append("    [WARN] Excessive usage - investigate for policy violations")

    # Anti-hallucination footer
    summary_parts.append(
        VerificationGuards.anti_hallucination_footer(
            {
                "Top clients": len(top_clients),
                "Combined bandwidth": format_bytes(total_bandwidth),
            }
        )
    )

    summary = "\n".join(summary_parts)

    # Step 5: Store facts and return summary (NO raw JSON)
    store_facts(
        "get_top_clients_by_usage",
        {
            "Top clients": len(top_clients),
            "Combined bandwidth": format_bytes(total_bandwidth),
        },
    )

    return [TextContent(type="text", text=summary)]
