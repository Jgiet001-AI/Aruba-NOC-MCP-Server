"""
Get Switch Details - MCP tools for switch details in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards, validate_input
from src.tools.models import GetSwitchDetailsInput
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


async def handle_get_switch_details(args: dict[str, Any]) -> list[TextContent]:
    """Tool 7: Get Switch Details - /network-monitoring/v1alpha1/switch/{serial}"""

    # Step 1: Validate input with Pydantic
    validated = validate_input(GetSwitchDetailsInput, args, "get_switch_details")
    if isinstance(validated, list):
        return validated  # Validation error response
    serial = validated.serial

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

    # Step 4: Create detailed summary with verification guardrails
    summary_parts = []

    # Verification checkpoint FIRST
    summary_parts.append(VerificationGuards.checkpoint({
        "Switch Name": device_name,
        "Serial": serial,
        "Status": status,
        "Total ports": f"{port_count} ports",
    }))

    status_label = "[UP]" if status == "ONLINE" else "[DN]"

    summary_parts.append(f"\n[SW] Switch Details: {device_name}")
    summary_parts.append(f"\n[STATUS] {status_label} {status}")
    summary_parts.append(f"[MODEL] {model}")
    summary_parts.append(f"[SERIAL] {serial}")
    summary_parts.append(f"[FW] Firmware: {firmware}")
    summary_parts.append(f"[UPTIME] {uptime} seconds")
    summary_parts.append(f"[PORTS] {port_count} ports")
    summary_parts.append(f"[LOC] Location: {site_name}")

    if stack_member:
        summary_parts.append("[STACK] Stack Member: Yes")

    # Performance indicators
    if cpu_util > 80:
        summary_parts.append(f"\n[WARN] High CPU: {cpu_util}%")
    if mem_util > 80:
        summary_parts.append(f"[WARN] High Memory: {mem_util}%")

    # Anti-hallucination footer
    summary_parts.append(VerificationGuards.anti_hallucination_footer({
        "Switch": device_name,
        "Status": status,
        "Ports": port_count,
    }))

    summary = "\n".join(summary_parts)

    # Step 5: Store facts and return summary (NO raw JSON)
    store_facts("get_switch_details", {
        "Switch Name": device_name,
        "Serial": serial,
        "Status": status,
        "Total ports": port_count,
        "Site": site_name,
    })

    return [TextContent(type="text", text=summary)]
