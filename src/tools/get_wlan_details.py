"""
Get WLAN Details - MCP tools for WLAN details retrieval in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import format_bytes, VerificationGuards
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


async def handle_get_wlan_details(args: dict[str, Any]) -> list[TextContent]:
    """Tool 18: Get WLAN Details - /network-monitoring/v1alpha1/wlans/{wlan-name}"""

    # Step 1: Validate required parameter
    wlan_name = args.get("wlan_name")
    if not wlan_name:
        return [TextContent(type="text", text="[ERR] Parameter 'wlan_name' is required. Provide the WLAN/SSID name.")]

    # Step 2: Call Aruba API
    try:
        data = await call_aruba_api(f"/network-monitoring/v1alpha1/wlans/{wlan_name}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [
                TextContent(
                    type="text", text=f"[ERR] WLAN '{wlan_name}' not found. Verify the WLAN name and try again."
                )
            ]
        raise

    # Step 3: Extract WLAN configuration
    ssid = data.get("ssid", wlan_name)
    security_type = data.get("securityType", "Unknown")
    auth_method = data.get("authenticationMethod", "N/A")
    vlan_id = data.get("vlanId", "N/A")
    enabled = data.get("enabled", False)
    broadcast = data.get("ssidBroadcast", True)
    band_steering = data.get("bandSteering", False)
    max_clients = data.get("maxClients", "Unlimited")
    current_clients = data.get("connectedClients", 0)

    # Performance stats
    throughput_mbps = data.get("throughputMbps", 0)
    total_bytes = data.get("totalBytes", 0)

    # Step 4: Create detailed summary with verification guardrails
    status_label = "[UP] ENABLED" if enabled else "[DN] DISABLED"

    summary_parts = []
    
    # Verification checkpoint FIRST
    summary_parts.append(VerificationGuards.checkpoint({
        "Status": "Enabled" if enabled else "Disabled",
        "Security": security_type,
        "Connected clients": f"{current_clients} clients",
    }))
    
    summary_parts.append(f"\n[WIFI] WLAN Details: {wlan_name}")
    summary_parts.append(f"\n{status_label}")
    summary_parts.append(f"\nSSID: {ssid}")

    summary_parts.append("\n[SEC] Security Configuration:")
    summary_parts.append(f"  * Type: {security_type}")
    summary_parts.append(f"  * Authentication: {auth_method}")
    if security_type == "OPEN":
        summary_parts.append("  [WARN] Open network - no encryption!")

    summary_parts.append("\n[NET] Network Settings:")
    summary_parts.append(f"  * VLAN ID: {vlan_id}")
    summary_parts.append(f"  * SSID Broadcast: {'Yes' if broadcast else 'Hidden'}")
    summary_parts.append(f"  * Band Steering: {'[OK] Enabled' if band_steering else '[--] Disabled'}")
    summary_parts.append(f"  * Max Clients: {max_clients}")

    summary_parts.append("\n[CLI] Current Usage:")
    summary_parts.append(f"  * Connected Clients: {current_clients} clients")
    if isinstance(max_clients, int) and current_clients >= max_clients * 0.9:
        summary_parts.append("  [WARN] Near capacity limit!")

    summary_parts.append(f"  * Throughput: {throughput_mbps} Mbps")
    summary_parts.append(f"  * Total Data: {format_bytes(total_bytes)}")

    # Configuration recommendations
    summary_parts.append("\n[INFO] Recommendations:")
    if security_type == "OPEN" and enabled:
        summary_parts.append("  * [WARN] Enable WPA2/WPA3 encryption for security")
    if not band_steering:
        summary_parts.append("  * Consider enabling band steering for better performance")
    if not broadcast:
        summary_parts.append("  * Hidden SSIDs reduce usability without significant security gain")
    if security_type == "WPA2-PERSONAL":
        summary_parts.append("  * Consider upgrading to WPA3 for enhanced security")

    # Anti-hallucination footer
    summary_parts.append(VerificationGuards.anti_hallucination_footer({
        "Status": "Enabled" if enabled else "Disabled",
        "Security": security_type,
        "Connected clients": current_clients,
    }))

    summary = "\n".join(summary_parts)

    # Step 5: Store facts and return summary (NO raw JSON)
    store_facts("get_wlan_details", {
        "WLAN": wlan_name,
        "Status": "Enabled" if enabled else "Disabled",
        "Security": security_type,
        "Connected clients": current_clients,
    })
    
    return [TextContent(type="text", text=summary)]
