"""
Get AP Radios - MCP tools for access point radio information in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import format_json

logger = logging.getLogger("aruba-noc-server")


async def handle_get_ap_radios(args: dict[str, Any]) -> list[TextContent]:
    """Tool 19: Get AP Radios - /network-monitoring/v1alpha1/aps/{serial}/radios"""

    # Step 1: Validate required parameter
    serial = args.get("serial")
    if not serial:
        return [TextContent(type="text", text="[ERR] Parameter 'serial' is required. Provide the AP serial number.")]

    # Step 2: Call Aruba API
    try:
        data = await call_aruba_api(f"/network-monitoring/v1alpha1/aps/{serial}/radios")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [
                TextContent(type="text", text=f"[ERR] AP with serial '{serial}' not found. Verify the serial number.")
            ]
        raise

    # Step 3: Extract radio data
    radios = data.get("radios", [])
    ap_name = data.get("apName", serial)

    if not radios:
        return [TextContent(type="text", text=f"[WARN] No radio information available for {ap_name}")]

    # Step 4: Create radio summary
    summary = f"[RADIO] Radio Status: {ap_name}\n"
    summary += f"\n[INFO] {len(radios)} Radio(s) Detected\n"

    for idx, radio in enumerate(radios, 1):
        band = radio.get("band", "Unknown")
        channel = radio.get("channel", "N/A")
        channel_width = radio.get("channelWidth", "N/A")
        tx_power = radio.get("txPower", "N/A")
        clients = radio.get("clientCount", 0)
        utilization = radio.get("utilizationPercent", 0)
        status = radio.get("status", "UNKNOWN")
        noise_floor = radio.get("noiseFloor", "N/A")

        # Band-specific labels
        band_label = {"2.4GHz": "[2.4G]", "5GHz": "[5G]", "6GHz": "[6G]"}.get(band, "[RADIO]")

        status_label = "[UP]" if status == "UP" else "[DN]"

        summary += f"\n{band_label} Radio {idx}: {band}\n"
        summary += f"  {status_label} Status: {status}\n"
        summary += f"  [CH] Channel: {channel} ({channel_width})\n"
        summary += f"  [PWR] TX Power: {tx_power} dBm\n"
        summary += f"  [CLI] Clients: {clients}\n"
        summary += f"  [UTIL] Utilization: {utilization}%\n"
        summary += f"  [NOISE] Noise Floor: {noise_floor} dBm\n"

        # Channel recommendations
        if band == "2.4GHz" and channel not in [1, 6, 11]:
            summary += "  [WARN] Non-standard channel - use 1, 6, or 11 to avoid overlap\n"

        # Utilization warnings
        if utilization >= 80:
            summary += "  [CRIT] Radio heavily utilized - performance degraded\n"
        elif utilization >= 60:
            summary += "  [WARN] High utilization - may impact performance\n"

        # Client load warnings
        if clients > 30:
            summary += "  [WARN] High client count - consider load balancing\n"

        # Noise warnings
        if isinstance(noise_floor, int) and noise_floor > -85:
            summary += "  [WARN] High noise floor - RF interference detected\n"

    # Overall recommendations
    summary += "\n[INFO] Recommendations:\n"

    # Check for channel conflicts
    channels_in_use = [r.get("channel") for r in radios if r.get("channel")]
    if len(channels_in_use) != len(set(channels_in_use)):
        summary += "  * Duplicate channels detected - may cause self-interference\n"

    # Check overall utilization
    avg_util = sum(r.get("utilizationPercent", 0) for r in radios) / len(radios)
    if avg_util > 70:
        summary += "  * Consider adding more APs to distribute load\n"
        summary += "  * Review channel assignments to minimize interference\n"

    # Step 5: Return formatted response
    return [TextContent(type="text", text=f"{summary}\n{format_json(data)}")]
