"""
Traceroute from AP - MCP tools for traceroute diagnostics from access point in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import format_json

logger = logging.getLogger("aruba-noc-server")


async def handle_traceroute_from_ap(args: dict[str, Any]) -> list[TextContent]:
    """Tool 25: Traceroute from AP - POST /network-troubleshooting/v1alpha1/aps/{serial}/traceroute"""

    # Step 1: Validate required parameters
    serial = args.get("serial")
    target = args.get("target")

    if not serial:
        return [TextContent(type="text", text="[ERR] Parameter 'serial' is required. Provide the AP serial number.")]

    if not target:
        return [
            TextContent(type="text", text="[ERR] Parameter 'target' is required. Provide the target IP or hostname.")
        ]

    # Step 2: Build request payload
    payload = {"target": target, "maxHops": args.get("max_hops", 30)}

    # Step 3: Call Aruba API (POST operation)
    try:
        data = await call_aruba_api(
            f"/network-troubleshooting/v1alpha1/aps/{serial}/traceroute", method="POST", json_data=payload
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [
                TextContent(type="text", text=f"[ERR] AP with serial '{serial}' not found. Verify the serial number.")
            ]
        raise

    # Step 4: Extract task information
    task_id = data.get("taskId", "Unknown")
    status = data.get("status", "UNKNOWN")
    ap_name = data.get("apName", serial)

    # Step 5: Create response with polling instructions
    summary = "[TRACE] Traceroute Test Initiated\n"
    summary += f"\n[LOC] From: {ap_name} ({serial})\n"
    summary += f"[TRACE] To: {target}\n"
    summary += f"[CFG] Max Hops: {payload['maxHops']}\n"
    summary += f"\n[ASYNC] Status: {status}\n"
    summary += f"[INFO] Task ID: {task_id}\n"
    summary += "\n[INFO] This is an async operation. Poll for results using:\n"
    summary += f"   get_async_test_result(task_id: '{task_id}')\n"
    summary += "\n[INFO] Traceroute may take 30-60 seconds to complete depending on path length.\n"

    return [TextContent(type="text", text=f"{summary}\n{format_json(data)}")]
