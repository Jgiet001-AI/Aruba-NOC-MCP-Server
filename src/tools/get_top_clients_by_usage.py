"""
Get Top Clients by Usage - MCP tools for top clients usage analysis in Aruba Central
"""

import json
import logging
from typing import Any

from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import format_bytes

logger = logging.getLogger("aruba-noc-server")


def _format_json(data: dict[str, Any]) -> str:
    """Format JSON data for display"""
    return json.dumps(data, indent=2)

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
    data = await call_aruba_api(
        "/network-monitoring/v1alpha1/clients/usage/topn",
        params=params
    )

    # Step 3: Extract top clients
    top_clients = data.get("items", [])
    time_range = params["time-range"]

    # Calculate totals
    total_bandwidth = sum(c.get("totalBytes", 0) for c in top_clients)

    # Step 4: Create ranked summary
    summary = f"[CLI] Top {len(top_clients)} Bandwidth Consumers ({time_range})\n"
    summary += f"\n[STATS] Combined Usage: {format_bytes(total_bandwidth)}\n"
    summary += "\n[RANK] Rankings:\n"

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

        summary += f"\n{rank_label} {hostname}\n"
        summary += f"    {conn_label} {connection_type} | MAC: {mac} | IP: {ip_address}\n"
        summary += f"    [DATA] Total: {format_bytes(total_bytes)}\n"
        summary += f"    [DN] Down: {format_bytes(download_bytes)} | [UP] Up: {format_bytes(upload_bytes)}\n"
        summary += f"    [LOC] Connected to: {connected_device}\n"

        # Usage warnings
        if total_bytes > 100 * 1024**3:  # > 100 GB
            summary += "    [WARN] Excessive usage - investigate for policy violations\n"

    # Step 5: Return formatted response
    return [TextContent(
        type="text",
        text=f"{summary}\n{_format_json(data)}"
    )]
