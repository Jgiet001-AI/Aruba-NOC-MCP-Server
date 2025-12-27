"""
Get WLAN Details - MCP tools for WLAN details retrieval in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import format_bytes, format_json

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

    # Step 4: Create detailed summary
    status_label = "[UP] ENABLED" if enabled else "[DN] DISABLED"

    summary = f"[WIFI] WLAN Details: {wlan_name}\n"
    summary += f"\n{status_label}\n"
    summary += f"\nSSID: {ssid}\n"

    summary += "\n[SEC] Security Configuration:\n"
    summary += f"  * Type: {security_type}\n"
    summary += f"  * Authentication: {auth_method}\n"
    if security_type == "OPEN":
        summary += "  [WARN] Open network - no encryption!\n"

    summary += "\n[NET] Network Settings:\n"
    summary += f"  * VLAN ID: {vlan_id}\n"
    summary += f"  * SSID Broadcast: {'Yes' if broadcast else 'Hidden'}\n"
    summary += f"  * Band Steering: {'[OK] Enabled' if band_steering else '[--] Disabled'}\n"
    summary += f"  * Max Clients: {max_clients}\n"

    summary += "\n[CLI] Current Usage:\n"
    summary += f"  * Connected Clients: {current_clients}\n"
    if isinstance(max_clients, int) and current_clients >= max_clients * 0.9:
        summary += "  [WARN] Near capacity limit!\n"

    summary += f"  * Throughput: {throughput_mbps} Mbps\n"
    summary += f"  * Total Data: {format_bytes(total_bytes)}\n"

    # Configuration recommendations
    summary += "\n[INFO] Recommendations:\n"
    if security_type == "OPEN" and enabled:
        summary += "  * [WARN] Enable WPA2/WPA3 encryption for security\n"
    if not band_steering:
        summary += "  * Consider enabling band steering for better performance\n"
    if not broadcast:
        summary += "  * Hidden SSIDs reduce usability without significant security gain\n"
    if security_type == "WPA2-PERSONAL":
        summary += "  * Consider upgrading to WPA3 for enhanced security\n"

    # Step 5: Return formatted response
    return [TextContent(type="text", text=f"{summary}\n{format_json(data)}")]
