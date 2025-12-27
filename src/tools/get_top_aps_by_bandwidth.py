"""
Get Top APs by Bandwidth - MCP tools for top access points bandwidth analysis in Aruba Central
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

async def handle_get_top_aps_by_bandwidth(args: dict[str, Any]) -> list[TextContent]:
    """Tool 13: Get Top APs by Bandwidth - /network-monitoring/v1alpha1/top-aps-by-wireless-usage"""

    # Step 1: Extract parameters
    params = {}

    if "site_id" in args:
        params["site-id"] = args["site_id"]
    params["limit"] = args.get("limit", 10)
    params["time-range"] = args.get("time_range", "24hours")

    # Step 2: Call Aruba API
    data = await call_aruba_api(
        "/network-monitoring/v1alpha1/top-aps-by-wireless-usage",
        params=params
    )

    # Step 3: Extract top APs
    top_aps = data.get("items", [])
    time_range = params["time-range"]

    # Calculate totals
    total_bandwidth = sum(ap.get("totalBytes", 0) for ap in top_aps)
    total_clients = sum(ap.get("clientCount", 0) for ap in top_aps)

    # Step 4: Create ranked summary
    summary = f"[STATS] Top {len(top_aps)} APs by Bandwidth Usage ({time_range})\n"
    summary += f"\n[TREND] Total: {format_bytes(total_bandwidth)} | [CLI] {total_clients} clients\n"
    summary += "\n[RANK] Rankings:\n"

    for idx, ap in enumerate(top_aps[:10], 1):
        ap_name = ap.get("apName", "Unknown")
        serial = ap.get("serialNumber", "Unknown")
        total_bytes = ap.get("totalBytes", 0)
        download_bytes = ap.get("downloadBytes", 0)
        upload_bytes = ap.get("uploadBytes", 0)
        clients = ap.get("clientCount", 0)
        utilization = ap.get("utilizationPercent", 0)

        # Rank labels for top 3
        rank_label = {1: "#1", 2: "#2", 3: "#3"}.get(idx, f"#{idx}")

        summary += f"\n{rank_label} {ap_name} ({serial})\n"
        summary += f"    [DATA] Total: {format_bytes(total_bytes)}\n"
        summary += f"    [DN] Down: {format_bytes(download_bytes)} | [UP] Up: {format_bytes(upload_bytes)}\n"
        summary += f"    [CLI] Clients: {clients} | [UTIL] Utilization: {utilization}%\n"

        # Warnings
        if utilization > 80:
            summary += "    [WARN] High utilization - consider capacity upgrade\n"
        if clients > 50:
            summary += "    [WARN] High client count - may need load balancing\n"

    # Step 5: Return formatted response
    return [TextContent(
        type="text",
        text=f"{summary}\n{_format_json(data)}"
    )]
