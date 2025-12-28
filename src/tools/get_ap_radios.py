"""
Get AP Radios - MCP tools for access point radio information in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.verify_facts import store_facts

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

    # Step 4: Create radio summary with verification guardrails
    summary_parts = []
    
    # Verification checkpoint FIRST
    summary_parts.append(VerificationGuards.checkpoint({
        "AP Name": ap_name,
        "Total radios": f"{len(radios)} radios",
    }))
    
    summary_parts.append(f"\n[RADIO] Radio Status: {ap_name}")
    summary_parts.append(f"\n[INFO] {len(radios)} Radio(s) Detected")

    total_clients = 0
    for idx, radio in enumerate(radios, 1):
        band = radio.get("band", "Unknown")
        channel = radio.get("channel", "N/A")
        channel_width = radio.get("channelWidth", "N/A")
        tx_power = radio.get("txPower", "N/A")
        clients = radio.get("clientCount", 0)
        total_clients += clients
        utilization = radio.get("utilizationPercent", 0)
        status = radio.get("status", "UNKNOWN")
        noise_floor = radio.get("noiseFloor", "N/A")

        # Band-specific labels
        band_label = {"2.4GHz": "[2.4G]", "5GHz": "[5G]", "6GHz": "[6G]"}.get(band, "[RADIO]")

        status_label = "[UP]" if status == "UP" else "[DN]"

        summary_parts.append(f"\n{band_label} Radio {idx}: {band}")
        summary_parts.append(f"  {status_label} Status: {status}")
        summary_parts.append(f"  [CH] Channel: {channel} ({channel_width})")
        summary_parts.append(f"  [PWR] TX Power: {tx_power} dBm")
        summary_parts.append(f"  [CLI] Clients: {clients} clients")
        summary_parts.append(f"  [UTIL] Utilization: {utilization}%")
        summary_parts.append(f"  [NOISE] Noise Floor: {noise_floor} dBm")

        # Channel recommendations
        if band == "2.4GHz" and channel not in [1, 6, 11]:
            summary_parts.append("  [WARN] Non-standard channel - use 1, 6, or 11 to avoid overlap")

        # Utilization warnings
        if utilization >= 80:
            summary_parts.append("  [CRIT] Radio heavily utilized - performance degraded")
        elif utilization >= 60:
            summary_parts.append("  [WARN] High utilization - may impact performance")

        # Client load warnings
        if clients > 30:
            summary_parts.append("  [WARN] High client count - consider load balancing")

        # Noise warnings
        if isinstance(noise_floor, int) and noise_floor > -85:
            summary_parts.append("  [WARN] High noise floor - RF interference detected")

    # Overall recommendations
    summary_parts.append("\n[INFO] Recommendations:")

    # Check for channel conflicts
    channels_in_use = [r.get("channel") for r in radios if r.get("channel")]
    if len(channels_in_use) != len(set(channels_in_use)):
        summary_parts.append("  * Duplicate channels detected - may cause self-interference")

    # Check overall utilization
    avg_util = sum(r.get("utilizationPercent", 0) for r in radios) / len(radios)
    if avg_util > 70:
        summary_parts.append("  * Consider adding more APs to distribute load")
        summary_parts.append("  * Review channel assignments to minimize interference")

    # Anti-hallucination footer
    summary_parts.append(VerificationGuards.anti_hallucination_footer({
        "AP Name": ap_name,
        "Total radios": len(radios),
        "Total clients across radios": total_clients,
    }))

    summary = "\n".join(summary_parts)

    # Step 5: Store facts and return summary (NO raw JSON)
    store_facts("get_ap_radios", {
        "AP Name": ap_name,
        "Total radios": len(radios),
        "Total clients": total_clients,
    })
    
    return [TextContent(type="text", text=summary)]
