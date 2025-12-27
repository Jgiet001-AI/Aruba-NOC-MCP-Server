"""
Ping from AP - MCP tools for ping diagnostics from access point in Aruba Central
"""

import json
import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api

logger = logging.getLogger("aruba-noc-server")


def _format_json(data: dict[str, Any]) -> str:
    """Format JSON data for display"""
    return json.dumps(data, indent=2)

async def handle_ping_from_ap(args: dict[str, Any]) -> list[TextContent]:
    """Tool 23: Ping from AP - POST /network-troubleshooting/v1alpha1/aps/{serial}/ping"""

    # Step 1: Validate required parameters
    serial = args.get("serial")
    target = args.get("target")

    if not serial:
        return [TextContent(
            type="text",
            text="[ERR] Parameter 'serial' is required. Provide the AP serial number."
        )]

    if not target:
        return [TextContent(
            type="text",
            text="[ERR] Parameter 'target' is required. Provide the target IP or hostname."
        )]

    # Step 2: Build request payload
    payload = {
        "target": target,
        "count": args.get("count", 5),
        "packetSize": args.get("packet_size", 64)
    }

    # Step 3: Call Aruba API (POST operation)
    try:
        data = await call_aruba_api(
            f"/network-troubleshooting/v1alpha1/aps/{serial}/ping",
            method="POST",
            json_data=payload
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [TextContent(
                type="text",
                text=f"[ERR] AP with serial '{serial}' not found. Verify the serial number."
            )]
        raise

    # Step 4: Extract task information
    task_id = data.get("taskId", "Unknown")
    status = data.get("status", "UNKNOWN")
    ap_name = data.get("apName", serial)

    # Step 5: Create response with polling instructions
    summary = "[PING] Ping Test Initiated\n"
    summary += f"\n[LOC] From: {ap_name} ({serial})\n"
    summary += f"[PING] To: {target}\n"
    summary += f"[DATA] Packets: {payload['count']} x {payload['packetSize']} bytes\n"
    summary += f"\n[ASYNC] Status: {status}\n"
    summary += f"[INFO] Task ID: {task_id}\n"
    summary += "\n[INFO] This is an async operation. Poll for results using:\n"
    summary += f"   get_async_test_result(task_id: '{task_id}')\n"

    return [TextContent(
        type="text",
        text=f"{summary}\n{_format_json(data)}"
    )]
