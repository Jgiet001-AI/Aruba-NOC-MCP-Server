"""
Devices - MCP tools for device management in Aruba Central
"""

import json
import logging
from typing import Any

from mcp.types import TextContent

from src.api_client import call_aruba_api

logger = logging.getLogger("aruba-noc-server")


def _format_json(data: dict[str, Any]) -> str:
    """Format JSON data for display"""
    return json.dumps(data, indent=2)


async def handle_get_device_list(args: dict[str, Any]) -> list[TextContent]:
    """Tool 1: Get Device List - /network-monitoring/v1alpha1/devices

    Retrieves comprehensive list of ALL network devices (APs, switches, gateways)
    with filtering, sorting, and pagination support.
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
    data = await call_aruba_api("/network-monitoring/v1alpha1/devices", params=params)

    # Step 3: Extract response data
    total = data.get("total", 0)
    count = data.get("count", 0)
    items = data.get("items", [])
    next_cursor = data.get("next")

    # Step 4: Analyze and categorize devices
    by_type = {}
    by_status = {}
    by_deployment = {}

    for item in items:
        device_type = item.get("deviceType", "UNKNOWN")
        status = item.get("status", "UNKNOWN")
        deployment = item.get("deployment", "UNKNOWN")

        by_type[device_type] = by_type.get(device_type, 0) + 1
        by_status[status] = by_status.get(status, 0) + 1
        by_deployment[deployment] = by_deployment.get(deployment, 0) + 1

    # Step 5: Create human-readable summary
    summary_parts = []
    summary_parts.append("**Device Inventory Summary**")
    summary_parts.append(f"Total devices: {total} (showing {count})\n")

    # Device type breakdown
    if by_type:
        summary_parts.append("**By Device Type:**")
        type_labels = {
            "ACCESS_POINT": "[AP]",
            "SWITCH": "[SW]",
            "GATEWAY": "[GW]",
            "UNKNOWN": "[--]",
        }
        for dtype, dcount in sorted(by_type.items()):
            label = type_labels.get(dtype, "[??]")
            summary_parts.append(f"  {label} {dtype}: {dcount}")

    # Status breakdown
    if by_status:
        summary_parts.append("\n**By Status:**")
        status_labels = {"ONLINE": "[UP]", "OFFLINE": "[DN]", "UNKNOWN": "[--]"}
        for status, scount in sorted(by_status.items()):
            label = status_labels.get(status, "[??]")
            summary_parts.append(f"  {label} {status}: {scount}")

    # Deployment breakdown
    if by_deployment:
        summary_parts.append("\n**By Deployment:**")
        for deployment, dep_count in sorted(by_deployment.items()):
            summary_parts.append(f"  - {deployment}: {dep_count}")

    # Pagination info
    if next_cursor:
        summary_parts.append(
            "\n[PAGINATED] More results available (use next cursor for pagination)"
        )

    summary = "\n".join(summary_parts)

    # Step 6: Return formatted response
    return [TextContent(type="text", text=f"{summary}\n\n{_format_json(data)}")]
