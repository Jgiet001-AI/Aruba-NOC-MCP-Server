"""
Gateways - MCP tools for gateway management in Aruba Central
"""

import json
import logging
from typing import Any

from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


def _format_json(data: dict[str, Any]) -> str:
    """Format JSON data for display"""
    return json.dumps(data, indent=2)


async def handle_list_gateways(args: dict[str, Any]) -> list[TextContent]:
    """Tool 5: List Gateways - /network-monitoring/v1alpha1/gateways

    Retrieves comprehensive list of ALL gateways with deployment details.
    """
    # Step 1: Extract and prepare parameters
    params = {}

    if "filter" in args:
        params["filter"] = args["filter"]
    if "sort" in args:
        params["sort"] = args["sort"]
    params["limit"] = args.get("limit", 100)
    if "next" in args:
        params["next"] = args["next"]

    # Step 2: Call Aruba API
    data = await call_aruba_api("/network-monitoring/v1alpha1/gateways", params=params)

    # Step 3: Extract response data
    gateways = data.get("items", [])
    total = data.get("total", 0)
    count = len(gateways)
    next_cursor = data.get("next")

    # Step 4: Analyze and categorize gateways
    by_status = {"ONLINE": 0, "OFFLINE": 0}
    by_deployment = {"Standalone": 0, "Clustered": 0}
    by_model = {}
    offline_gateways = []

    for gw in gateways:
        # Status tracking
        status = gw.get("status", "UNKNOWN")
        if status == "ONLINE":
            by_status["ONLINE"] += 1
        elif status == "OFFLINE":
            by_status["OFFLINE"] += 1
            offline_gateways.append(
                {
                    "name": gw.get("deviceName", "Unknown"),
                    "serial": gw.get("serialNumber", "N/A"),
                    "site": gw.get("siteName", "Unknown"),
                }
            )

        # Deployment type
        deployment = gw.get("deployment", "Unknown")
        if deployment in by_deployment:
            by_deployment[deployment] += 1
        elif deployment != "Unknown":
            by_deployment[deployment] = 1

        # Model tracking
        model = gw.get("model", "Unknown")
        by_model[model] = by_model.get(model, 0) + 1

    # Step 5: Create human-readable summary with verification guardrails
    summary_parts = []
    
    # Verification checkpoint FIRST
    summary_parts.append(VerificationGuards.checkpoint({
        "Total gateways": f"{total} gateways",
        "Online gateways": f"{by_status.get('ONLINE', 0)} gateways",
        "Offline gateways": f"{by_status.get('OFFLINE', 0)} gateways",
    }))
    
    summary_parts.append("\n**Gateway Inventory Overview**")
    summary_parts.append(f"Total gateways: {total} (showing {count})\n")

    # Status breakdown
    summary_parts.append("**By Status (actual gateway counts):**")
    online = by_status.get("ONLINE", 0)
    offline = by_status.get("OFFLINE", 0)
    summary_parts.append(f"  [UP] ONLINE: {online} gateways")
    summary_parts.append(f"  [DN] OFFLINE: {offline} gateways")
    if total > 0:
        uptime_pct = online / total * 100
        summary_parts.append(f"  [AVAIL] Availability: {uptime_pct:.1f}%")

    # Deployment breakdown
    summary_parts.append("\n**By Deployment Type:**")
    for deployment, count_val in sorted(by_deployment.items()):
        label = "[CLUST]" if deployment == "Clustered" else "[SOLO]"
        summary_parts.append(f"  {label} {deployment}: {count_val} gateways")

    # Model inventory
    if by_model:
        summary_parts.append("\n**By Model:**")
        for model, count_val in sorted(by_model.items()):
            summary_parts.append(f"  [HW] {model}: {count_val} gateways")

    # Offline gateways (critical info)
    if offline_gateways:
        summary_parts.append(f"\n[ALERT] **Offline Gateways ({len(offline_gateways)} gateways):**")
        for i, gw in enumerate(offline_gateways[:10], 1):  # Top 10
            summary_parts.append(f"  {i}. {gw['name']} ({gw['serial']}) at {gw['site']}")
        if len(offline_gateways) > 10:
            summary_parts.append(f"  ... and {len(offline_gateways) - 10} more offline")

    # Pagination info
    if next_cursor:
        summary_parts.append("\n[MORE] Results available (use next cursor)")

    # Anti-hallucination footer
    summary_parts.append(VerificationGuards.anti_hallucination_footer({
        "Total gateways": total,
        "Online": online,
        "Offline": offline,
    }))

    summary = "\n".join(summary_parts)

    # Step 6: Store facts and return summary (NO raw JSON)
    store_facts("list_gateways", {
        "Total gateways": total,
        "Online gateways": online,
        "Offline gateways": offline,
    })
    
    return [TextContent(type="text", text=summary)]
