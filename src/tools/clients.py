"""
Clients - MCP tools for wireless client management in Aruba Central
"""

import json
import logging
from typing import Any

from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.site_helper import ensure_site_id
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


def _format_json(data: dict[str, Any]) -> str:
    """Format JSON data for display"""
    return json.dumps(data, indent=2)


async def handle_list_all_clients(args: dict[str, Any]) -> list[TextContent]:
    """Tool 3: List All Clients - /network-monitoring/v1alpha1/clients

    Retrieves ALL connected/recent clients with connection details.
    Note: API uses hyphenated parameter names!
    """
    # Step 1: Extract and prepare parameters
    # IMPORTANT: API uses hyphenated names (site-id, serial-number, etc.)
    params = {}

    if "site_id" in args:
        params["site-id"] = args["site_id"]  # Note the hyphen!
    if "serial_number" in args:
        params["serial-number"] = args["serial_number"]  # Note the hyphen!
    if "start_query_time" in args:
        params["start-query-time"] = args["start_query_time"]  # Note the hyphen!
    if "end_query_time" in args:
        params["end-query-time"] = args["end_query_time"]  # Note the hyphen!
    if "filter" in args:
        params["filter"] = args["filter"]
    if "sort" in args:
        params["sort"] = args["sort"]
    params["limit"] = args.get("limit", 100)
    if "next" in args:
        params["next"] = args["next"]

    # ✅ FIX: Auto-fetch site-id if not provided (REQUIRED by API)
    params = await ensure_site_id(params)

    # Step 2: Call Aruba API
    data = await call_aruba_api("/network-monitoring/v1alpha1/clients", params=params)

    # Step 3: Extract response data
    clients = data.get("items", [])
    total = data.get("total", 0)
    count = len(clients)
    next_cursor = data.get("next")

    # Step 4: Analyze and categorize clients
    by_type = {"Wired": 0, "Wireless": 0, "Unknown": 0}
    by_status = {}
    by_experience = {"Good": 0, "Fair": 0, "Poor": 0, "Unknown": 0}

    for client in clients:
        # Connection type
        conn_type = client.get("type", "Unknown")
        if conn_type in by_type:
            by_type[conn_type] += 1
        else:
            by_type["Unknown"] += 1

        # Status
        status = client.get("status", "Unknown")
        by_status[status] = by_status.get(status, 0) + 1

        # Experience
        experience = client.get("experience", "Unknown")
        if experience in by_experience:
            by_experience[experience] += 1
        else:
            by_experience["Unknown"] += 1

    # Step 5: Create human-readable summary with verification guardrails
    summary_parts = []

    # Verification checkpoint FIRST
    summary_parts.append(
        VerificationGuards.checkpoint(
            {
                "Total clients": f"{total} clients",
                "Showing in response": f"{count} clients",
                "Wireless clients": f"{by_type.get('Wireless', 0)} clients",
                "Wired clients": f"{by_type.get('Wired', 0)} clients",
            }
        )
    )

    summary_parts.append("\n**Network Clients Overview**")
    summary_parts.append(f"Total clients: {total} (showing {count})\n")

    # Connection type breakdown
    summary_parts.append("**By Connection Type (actual counts):**")
    type_labels = {"Wireless": "[WIFI]", "Wired": "[WIRED]", "Unknown": "[--]"}
    for ctype, cnt in by_type.items():
        if cnt > 0:
            label = type_labels.get(ctype, "[--]")
            summary_parts.append(f"  {label} {ctype}: {cnt} clients")

    # Status breakdown
    if by_status:
        summary_parts.append("\n**By Status:**")
        status_labels = {"Connected": "[OK]", "Disconnected": "[X]", "Idle": "[IDLE]"}
        for status, cnt in sorted(by_status.items()):
            label = status_labels.get(status, "[--]")
            summary_parts.append(f"  {label} {status}: {cnt} clients")

    # Experience breakdown
    summary_parts.append("\n**By Experience:**")
    exp_labels = {"Good": "[OK]", "Fair": "[WARN]", "Poor": "[CRIT]", "Unknown": "[--]"}
    for exp, cnt in by_experience.items():
        if cnt > 0:
            label = exp_labels.get(exp, "[--]")
            summary_parts.append(f"  {label} {exp}: {cnt} clients")

    # Pagination info
    if next_cursor:
        summary_parts.append("\n[MORE] Results available (use next cursor)")

    # Anti-hallucination footer
    summary_parts.append(
        VerificationGuards.anti_hallucination_footer(
            {
                "Total clients": total,
                "Wireless": by_type.get("Wireless", 0),
                "Wired": by_type.get("Wired", 0),
            }
        )
    )

    summary = "\n".join(summary_parts)

    # Step 6: Store facts and return summary (NO raw JSON)
    store_facts(
        "list_all_clients",
        {
            "Total clients": total,
            "Wireless clients": by_type.get("Wireless", 0),
            "Wired clients": by_type.get("Wired", 0),
            "Good experience": by_experience.get("Good", 0),
            "Poor experience": by_experience.get("Poor", 0),
        },
    )

    return [TextContent(type="text", text=summary)]
