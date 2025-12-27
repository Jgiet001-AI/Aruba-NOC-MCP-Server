"""
Get Switch Details - MCP tools for switch details in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import format_json

logger = logging.getLogger("aruba-noc-server")


async def handle_get_switch_details(args: dict[str, Any]) -> list[TextContent]:
    """Tool 7: Get Switch Details - /network-monitoring/v1alpha1/switch/{serial}"""

    # Step 1: Validate required parameter
    serial = args.get("serial")
    if not serial:
        return [
            TextContent(
                type="text", text="[ERR] Parameter 'serial' is required. Please provide the switch serial number."
            )
        ]

    # Step 2: Call Aruba API (path parameter, not query param)
    try:
        data = await call_aruba_api(f"/network-monitoring/v1alpha1/switch/{serial}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [
                TextContent(
                    type="text", text=f"[ERR] Switch with serial '{serial}' not found. Please verify the serial number."
                )
            ]
        raise

    # Step 3: Extract switch details
    device_name = data.get("deviceName", "Unknown")
    model = data.get("model", "Unknown")
    status = data.get("status", "UNKNOWN")
    firmware = data.get("firmwareVersion", "Unknown")
    uptime = data.get("uptime", 0)
    cpu_util = data.get("cpuUtilization", 0)
    mem_util = data.get("memoryUtilization", 0)
    port_count = data.get("totalPorts", 0)
    stack_member = data.get("stackMember", False)
    site_name = data.get("siteName", "Unknown")

    # Step 4: Create detailed summary with professional labels
    status_label = "[UP]" if status == "ONLINE" else "[DN]"

    summary = f"[SW] Switch Details: {device_name}\n"
    summary += f"\n[STATUS] {status_label} {status}\n"
    summary += f"[MODEL] {model}\n"
    summary += f"[SERIAL] {serial}\n"
    summary += f"[FW] Firmware: {firmware}\n"
    summary += f"[UPTIME] {uptime} seconds\n"
    summary += f"[PORTS] {port_count}\n"
    summary += f"[LOC] Location: {site_name}\n"

    if stack_member:
        summary += "[STACK] Stack Member: Yes\n"

    # Performance indicators
    if cpu_util > 80:
        summary += f"\n[WARN] High CPU: {cpu_util}%\n"
    if mem_util > 80:
        summary += f"[WARN] High Memory: {mem_util}%\n"

    # Step 5: Return formatted response
    return [TextContent(type="text", text=f"{summary}\n{format_json(data)}")]
