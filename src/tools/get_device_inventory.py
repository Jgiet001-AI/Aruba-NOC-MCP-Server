"""
Get Device Inventory - MCP tools for device inventory management in Aruba Central
"""

import logging
from typing import Any

from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


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

    # Step 5: Create summary with verification guardrails
    summary_parts = []
    
    # Verification checkpoint FIRST
    summary_parts.append(VerificationGuards.checkpoint({
        "Total devices": f"{total} devices",
        "Showing in response": f"{count} devices",
    }))
    
    summary_parts.append(f"\n[INV] Hardware Inventory: {total} devices (showing {count})")
    
    summary_parts.append("\n[MODEL] By Model (device counts):")
    for model, model_count in sorted(by_model.items(), key=lambda x: x[1], reverse=True)[:5]:
        summary_parts.append(f"  * {model}: {model_count} devices")
    
    summary_parts.append(f"\n[TYPE] By Type:")
    for dtype, type_count in sorted(by_type.items()):
        summary_parts.append(f"  * {dtype}: {type_count} devices")
    
    summary_parts.append(f"\n[SUB] By Subscription:")
    for sub, sub_count in sorted(by_subscription.items()):
        summary_parts.append(f"  * {sub}: {sub_count} devices")

    # Anti-hallucination footer
    summary_parts.append(VerificationGuards.anti_hallucination_footer({
        "Total devices": total,
        "Showing": count,
    }))

    summary = "\n".join(summary_parts)

    # Step 6: Store facts and return summary (NO raw JSON)
    store_facts("get_device_inventory", {
        "Total devices": total,
        "By type": by_type,
        "By model (top 5)": dict(sorted(by_model.items(), key=lambda x: x[1], reverse=True)[:5]),
    })
    
    return [TextContent(type="text", text=summary)]
