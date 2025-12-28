"""
Ping from AP - MCP tools for ping diagnostics from access point in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


async def handle_ping_from_ap(args: dict[str, Any]) -> list[TextContent]:
    """Tool 23: Ping from AP - POST /network-troubleshooting/v1alpha1/aps/{serial}/ping"""

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
    payload = {"target": target, "count": args.get("count", 5), "packetSize": args.get("packet_size", 64)}

    # Step 3: Call Aruba API (POST operation)
    try:
        data = await call_aruba_api(
            f"/network-troubleshooting/v1alpha1/aps/{serial}/ping", method="POST", json_data=payload
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

    # Step 5: Create response with verification guardrails
    summary_parts = []
    
    summary_parts.append(VerificationGuards.checkpoint({
        "Task ID": task_id,
        "Status": status,
        "Target": target,
    }))
    
    summary_parts.append("\n[PING] Ping Test Initiated")
    summary_parts.append(f"\n[LOC] From: {ap_name} ({serial})")
    summary_parts.append(f"[PING] To: {target}")
    summary_parts.append(f"[DATA] Packets: {payload['count']} x {payload['packetSize']} bytes")
    summary_parts.append(f"\n[ASYNC] Status: {status}")
    summary_parts.append(f"[INFO] Task ID: {task_id}")
    summary_parts.append("\n[INFO] This is an async operation. Poll for results using:")
    summary_parts.append(f"   get_async_test_result(task_id: '{task_id}')")
    
    summary_parts.append(VerificationGuards.anti_hallucination_footer({
        "Task ID": task_id,
        "Status": status,
    }))

    summary = "\n".join(summary_parts)
    
    store_facts("ping_from_ap", {
        "Task ID": task_id,
        "Status": status,
        "Target": target,
    })

    return [TextContent(type="text", text=summary)]
