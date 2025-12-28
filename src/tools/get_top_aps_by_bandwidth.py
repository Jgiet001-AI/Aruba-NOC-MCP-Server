"""
Get Top APs by Bandwidth - MCP tools for top access points bandwidth analysis in Aruba Central
"""

import logging
from typing import Any

from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import format_bytes, VerificationGuards
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")

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

    # Step 4: Create ranked summary with verification guardrails
    summary_parts = []
    
    # Verification checkpoint FIRST
    summary_parts.append(VerificationGuards.checkpoint({
        "Total APs": f"{len(top_aps)} APs",
        "Total bandwidth": format_bytes(total_bandwidth),
        "Total clients": f"{total_clients} clients",
    }))
    
    summary_parts.append(f"\n[STATS] Top {len(top_aps)} APs by Bandwidth Usage ({time_range})")
    summary_parts.append(f"\n[TREND] Total: {format_bytes(total_bandwidth)} | [CLI] {total_clients} clients")
    summary_parts.append("\n[RANK] Rankings:")

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

        summary_parts.append(f"\n{rank_label} {ap_name} ({serial})")
        summary_parts.append(f"    [DATA] Total: {format_bytes(total_bytes)}")
        summary_parts.append(f"    [DN] Down: {format_bytes(download_bytes)} | [UP] Up: {format_bytes(upload_bytes)}")
        summary_parts.append(f"    [CLI] Clients: {clients} clients | [UTIL] Utilization: {utilization}%")

        # Warnings
        if utilization > 80:
            summary_parts.append("    [WARN] High utilization - consider capacity upgrade")
        if clients > 50:
            summary_parts.append("    [WARN] High client count - may need load balancing")

    # Anti-hallucination footer
    summary_parts.append(VerificationGuards.anti_hallucination_footer({
        "Total APs": len(top_aps),
        "Total bandwidth": format_bytes(total_bandwidth),
        "Total clients": total_clients,
    }))

    summary = "\n".join(summary_parts)

    # Step 5: Store facts and return summary (NO raw JSON)
    store_facts("get_top_aps_by_bandwidth", {
        "Total APs": len(top_aps),
        "Total bandwidth": format_bytes(total_bandwidth),
        "Total clients": total_clients,
    })
    
    return [TextContent(type="text", text=summary)]
