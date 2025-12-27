"""
Get AP Details - MCP tools for access point details retrieval in Aruba Central
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

async def handle_get_ap_details(args: dict[str, Any]) -> list[TextContent]:
    """Tool 4: Get AP Details - /network-monitoring/v1alpha1/aps/{serial-number}"""

    # Step 1: Validate required parameter
    serial_number = args.get("serial_number")
    if not serial_number:
        return [TextContent(
            type="text",
            text="[ERR] Parameter 'serial_number' is required. Please provide the AP serial number."
        )]

    # Step 2: Call Aruba API (path parameter)
    # CRITICAL: API uses hyphenated path: aps/{serial-number}
    try:
        data = await call_aruba_api(
            f"/network-monitoring/v1alpha1/aps/{serial_number}"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [TextContent(
                type="text",
                text=f"[ERR] Access Point with serial '{serial_number}' not found. Please verify the serial number."
            )]
        raise

    # Step 3: Extract AP details
    device_name = data.get("deviceName", "Unknown")
    model = data.get("model", "Unknown")
    status = data.get("status", "UNKNOWN")
    firmware = data.get("firmwareVersion", "Unknown")
    client_count = data.get("clientCount", 0)
    uptime = data.get("uptime", 0)
    cpu_util = data.get("cpuUtilization", 0)
    mem_util = data.get("memoryUtilization", 0)
    site_name = data.get("siteName", "Unknown")

    # Radio information
    radios = data.get("radios", [])
    radio_2_4 = next((r for r in radios if r.get("band") == "2.4GHz"), {})
    radio_5 = next((r for r in radios if r.get("band") == "5GHz"), {})

    # Step 4: Create detailed summary with professional labels
    status_label = "[UP]" if status == "ONLINE" else "[DN]"

    summary = f"[AP] Access Point Details: {device_name}\n"
    summary += f"\n[STATUS] {status_label} {status}\n"
    summary += f"[MODEL] {model}\n"
    summary += f"[SERIAL] {serial_number}\n"
    summary += f"[FW] Firmware: {firmware}\n"
    summary += f"[UPTIME] {uptime} seconds\n"
    summary += f"[CLI] Connected Clients: {client_count}\n"
    summary += f"[LOC] Location: {site_name}\n"

    # Radio details
    if radio_2_4:
        channel_2_4 = radio_2_4.get("channel", "N/A")
        power_2_4 = radio_2_4.get("txPower", "N/A")
        summary += "\n[RADIO] 2.4GHz Radio:\n"
        summary += f"  * Channel: {channel_2_4}\n"
        summary += f"  * Tx Power: {power_2_4} dBm\n"

    if radio_5:
        channel_5 = radio_5.get("channel", "N/A")
        power_5 = radio_5.get("txPower", "N/A")
        summary += "[RADIO] 5GHz Radio:\n"
        summary += f"  * Channel: {channel_5}\n"
        summary += f"  * Tx Power: {power_5} dBm\n"

    # Performance warnings
    if cpu_util > 80:
        summary += f"\n[WARN] High CPU: {cpu_util}%\n"
    if mem_util > 80:
        summary += f"[WARN] High Memory: {mem_util}%\n"
    if client_count > 50:
        summary += f"[WARN] High Client Load: {client_count} clients\n"

    # Step 5: Return formatted response
    return [TextContent(
        type="text",
        text=f"{summary}\n{_format_json(data)}"
    )]
