"""
Get AP Details - MCP tools for access point details retrieval in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards, validate_input
from src.tools.models import GetAPDetailsInput
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


async def handle_get_ap_details(args: dict[str, Any]) -> list[TextContent]:
    """Tool 4: Get AP Details - /network-monitoring/v1alpha1/aps/{serial-number}"""

    # Step 1: Validate input with Pydantic
    validated = validate_input(GetAPDetailsInput, args, "get_ap_details")
    if isinstance(validated, list):
        return validated  # Validation error response
    serial_number = validated.serial_number

    # Step 2: Call Aruba API (path parameter)
    # CRITICAL: API uses hyphenated path: aps/{serial-number}
    try:
        data = await call_aruba_api(f"/network-monitoring/v1alpha1/aps/{serial_number}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [
                TextContent(
                    type="text",
                    text=f"[ERR] AP with serial '{serial_number}' not found. Verify the serial number.",
                )
            ]
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

    # Step 4: Create detailed summary with verification guardrails
    summary_parts = []

    # Verification checkpoint FIRST
    summary_parts.append(VerificationGuards.checkpoint({
        "AP Name": device_name,
        "Serial": serial_number,
        "Status": status,
        "Connected clients": f"{client_count} clients",
    }))

    status_label = "[UP]" if status == "ONLINE" else "[DN]"

    summary_parts.append(f"\n[AP] Access Point Details: {device_name}")
    summary_parts.append(f"\n[STATUS] {status_label} {status}")
    summary_parts.append(f"[MODEL] {model}")
    summary_parts.append(f"[SERIAL] {serial_number}")
    summary_parts.append(f"[FW] Firmware: {firmware}")
    summary_parts.append(f"[UPTIME] {uptime} seconds")
    summary_parts.append(f"[CLI] Connected Clients: {client_count} clients")
    summary_parts.append(f"[LOC] Location: {site_name}")

    # Radio details
    if radio_2_4:
        channel_2_4 = radio_2_4.get("channel", "N/A")
        power_2_4 = radio_2_4.get("txPower", "N/A")
        summary_parts.append("\n[RADIO] 2.4GHz Radio:")
        summary_parts.append(f"  * Channel: {channel_2_4}")
        summary_parts.append(f"  * Tx Power: {power_2_4} dBm")

    if radio_5:
        channel_5 = radio_5.get("channel", "N/A")
        power_5 = radio_5.get("txPower", "N/A")
        summary_parts.append("[RADIO] 5GHz Radio:")
        summary_parts.append(f"  * Channel: {channel_5}")
        summary_parts.append(f"  * Tx Power: {power_5} dBm")

    # Performance warnings
    if cpu_util > 80:
        summary_parts.append(f"\n[WARN] High CPU: {cpu_util}%")
    if mem_util > 80:
        summary_parts.append(f"[WARN] High Memory: {mem_util}%")
    if client_count > 50:
        summary_parts.append(f"[WARN] High Client Load: {client_count} clients")

    # Anti-hallucination footer
    summary_parts.append(VerificationGuards.anti_hallucination_footer({
        "AP Name": device_name,
        "Status": status,
        "Clients": client_count,
    }))

    summary = "\n".join(summary_parts)

    # Step 5: Store facts and return summary (NO raw JSON)
    store_facts("get_ap_details", {
        "AP Name": device_name,
        "Serial": serial_number,
        "Status": status,
        "Connected clients": client_count,
        "Site": site_name,
    })

    return [TextContent(type="text", text=summary)]
