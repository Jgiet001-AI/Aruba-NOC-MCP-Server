"""
Get Device Inventory - MCP tools for device inventory management in Aruba Central
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

async def handle_get_device_inventory(args: dict[str, Any]) -> list[TextContent]:
    """Tool 6: Get Device Inventory - /network-monitoring/v1alpha1/device-inventory"""

    # Step 1: Extract and prepare parameters
    params = {}
    if "filter" in args:
        params["filter"] = args["filter"]
    if "sort" in args:
        params["sort"] = args["sort"]
    if "limit" in args:
        params["limit"] = args["limit"]
    if "next" in args:
        params["next"] = args["next"]

    # Step 2: Call Aruba API
    data = await call_aruba_api(
        "/network-monitoring/v1alpha1/device-inventory",
        params=params
    )

    # Step 3: Extract inventory data
    total = data.get("total", 0)
    count = data.get("count", 0)
    items = data.get("items", [])

    # Step 4: Analyze inventory
    by_model = {}
    by_type = {}
    by_subscription = {}

    for item in items:
        model = item.get("model", "UNKNOWN")
        device_type = item.get("deviceType", "UNKNOWN")
        subscription = item.get("subscriptionTier", "UNKNOWN")

        by_model[model] = by_model.get(model, 0) + 1
        by_type[device_type] = by_type.get(device_type, 0) + 1
        by_subscription[subscription] = by_subscription.get(subscription, 0) + 1

    # Step 5: Create summary with professional labels
    summary = f"[INV] Hardware Inventory: {total} devices (showing {count})\n"
    summary += "\n[MODEL] By Model:\n"
    for model, count in sorted(by_model.items(), key=lambda x: x[1], reverse=True)[:5]:
        summary += f"  * {model}: {count}\n"
    summary += f"\n[TYPE] By Type: {dict(by_type)}\n"
    summary += f"[SUB] By Subscription: {dict(by_subscription)}"

    # Step 6: Return formatted response
    return [TextContent(
        type="text",
        text=f"{summary}\n\n{_format_json(data)}"
    )]
