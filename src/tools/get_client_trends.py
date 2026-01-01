"""
Get Client Trends - MCP tools for client trends analysis in Aruba Central
"""

import logging
from typing import Any

from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


async def handle_get_client_trends(args: dict[str, Any]) -> list[TextContent]:
    """Tool 9: Get Client Trends - /network-monitoring/v1alpha1/clients/trends"""

    # Step 1: Extract and prepare parameters
    params = {}

    # Note: API uses hyphenated parameter names
    if "site_id" in args:
        params["site-id"] = args["site_id"]
    if "start_time" in args:
        params["start-time"] = args["start_time"]
    if "end_time" in args:
        params["end-time"] = args["end_time"]
    if "interval" in args:
        params["interval"] = args["interval"]

    # Step 2: Call Aruba API
    data = await call_aruba_api("/network-monitoring/v1alpha1/clients/trends", params=params)

    # Step 3: Extract trend data
    trends = data.get("trends", [])
    data.get("summary", {})

    # Calculate statistics from trends
    if trends:
        total_counts = [t.get("totalClients", 0) for t in trends]
        wireless_counts = [t.get("wirelessClients", 0) for t in trends]
        wired_counts = [t.get("wiredClients", 0) for t in trends]

        max_clients = max(total_counts) if total_counts else 0
        min_clients = min(total_counts) if total_counts else 0
        avg_clients = sum(total_counts) / len(total_counts) if total_counts else 0

        # Find peak time
        peak_index = total_counts.index(max_clients) if total_counts else 0
        peak_time = trends[peak_index].get("timestamp", "Unknown") if trends else "Unknown"

        # Average breakdown
        avg_wireless = sum(wireless_counts) / len(wireless_counts) if wireless_counts else 0
        avg_wired = sum(wired_counts) / len(wired_counts) if wired_counts else 0
    else:
        max_clients = min_clients = avg_clients = 0
        avg_wireless = avg_wired = 0
        peak_time = "No data"

    # Step 4: Create trend summary with verification guardrails
    summary_parts = []
    interval = params.get("interval", "1hour")
    data_points = len(trends)

    # Verification checkpoint FIRST
    summary_parts.append(
        VerificationGuards.checkpoint(
            {
                "Data points": f"{data_points} data points",
                "Peak clients": f"{max_clients} clients",
                "Average clients": f"{avg_clients:.1f} clients",
                "Min clients": f"{min_clients} clients",
            }
        )
    )

    summary_parts.append("\n[TREND] Client Connection Trends")
    summary_parts.append(f"\n[TIME] Time Period: {data_points} data points at {interval} intervals")

    # Statistics
    summary_parts.append("\n[STATS] Statistics (client counts):")
    summary_parts.append(f"  * [PEAK] Peak: {max_clients} clients")
    summary_parts.append(f"  * [LOW] Minimum: {min_clients} clients")
    summary_parts.append(f"  * [AVG] Average: {avg_clients:.1f} clients")
    summary_parts.append(f"  * [TIME] Peak Time: {peak_time}")

    # Breakdown
    summary_parts.append("\n[DATA] Average Breakdown:")
    summary_parts.append(f"  * [WIFI] Wireless: {avg_wireless:.1f} clients")
    summary_parts.append(f"  * [WIRED] Wired: {avg_wired:.1f} clients")

    # Trend indicators
    if len(total_counts) >= 2:
        recent_avg = sum(total_counts[-5:]) / min(5, len(total_counts))
        older_avg = sum(total_counts[:5]) / min(5, len(total_counts))

        if recent_avg > older_avg * 1.1:
            summary_parts.append(f"\n[TREND] [UP] Increasing (+{((recent_avg / older_avg - 1) * 100):.1f}%)")
        elif recent_avg < older_avg * 0.9:
            summary_parts.append(f"\n[TREND] [DN] Decreasing ({((recent_avg / older_avg - 1) * 100):.1f}%)")
        else:
            summary_parts.append("\n[TREND] Stable")

    # Capacity warnings
    if max_clients > avg_clients * 1.5:
        summary_parts.append("\n[WARN] Peak usage is 50% above average - consider capacity planning")

    # Anti-hallucination footer
    summary_parts.append(
        VerificationGuards.anti_hallucination_footer(
            {
                "Peak clients": max_clients,
                "Average clients": f"{avg_clients:.1f}",
                "Data points": data_points,
            }
        )
    )

    summary = "\n".join(summary_parts)

    # Step 5: Store facts and return summary (NO raw JSON)
    store_facts(
        "get_client_trends",
        {
            "Peak clients": max_clients,
            "Average clients": avg_clients,
            "Min clients": min_clients,
            "Avg wireless": avg_wireless,
            "Avg wired": avg_wired,
        },
    )

    return [TextContent(type="text", text=summary)]
