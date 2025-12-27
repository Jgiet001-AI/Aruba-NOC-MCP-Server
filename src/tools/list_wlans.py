"""
List WLANs - MCP tools for WLAN listing in Aruba Central
"""

import json
import logging
from typing import Any

from mcp.types import TextContent

from src.api_client import call_aruba_api

logger = logging.getLogger("aruba-noc-server")


def _format_json(data: dict[str, Any]) -> str:
    """Format JSON data for display"""
    return json.dumps(data, indent=2)

async def handle_list_wlans(args: dict[str, Any]) -> list[TextContent]:
    """Tool 17: List WLANs - /network-monitoring/v1alpha1/wlans"""

    # Step 1: Extract parameters
    params = {}

    if "site_id" in args:
        params["site-id"] = args["site_id"]
    params["limit"] = args.get("limit", 100)

    # Step 2: Call Aruba API
    data = await call_aruba_api(
        "/network-monitoring/v1alpha1/wlans",
        params=params
    )

    # Step 3: Extract WLAN data
    wlans = data.get("items", [])
    total = data.get("total", len(wlans))

    # Categorize WLANs
    by_security = {}
    enabled_count = 0
    disabled_count = 0
    guest_networks = []

    for wlan in wlans:
        # Security type
        security = wlan.get("securityType", "UNKNOWN")
        by_security[security] = by_security.get(security, 0) + 1

        # Status
        if wlan.get("enabled", False):
            enabled_count += 1
        else:
            disabled_count += 1

        # Guest networks
        if "guest" in wlan.get("wlanName", "").lower():
            guest_networks.append(wlan.get("wlanName"))

    # Step 4: Create summary
    summary = "[WIFI] Wireless Networks (WLANs)\n"
    summary += f"\n[STATS] Total: {total} WLANs | [UP] {enabled_count} enabled | [DN] {disabled_count} disabled\n"
    summary += "\n[SEC] Security Distribution:\n"
    for sec_type, count in sorted(by_security.items(), key=lambda x: x[1], reverse=True):
        summary += f"  * {sec_type}: {count}\n"

    if guest_networks:
        summary += f"\n[GUEST] Guest Networks ({len(guest_networks)}): {', '.join(guest_networks)}\n"

    summary += "\n[LIST] WLAN Details:\n"
    for wlan in wlans:
        wlan_name = wlan.get("wlanName", "Unknown")
        security = wlan.get("securityType", "Unknown")
        vlan = wlan.get("vlanId", "N/A")
        enabled = wlan.get("enabled", False)
        broadcast = wlan.get("ssidBroadcast", True)

        status_label = "[UP]" if enabled else "[DN]"
        broadcast_label = "Broadcast" if broadcast else "Hidden"

        summary += f"\n{status_label} {wlan_name}\n"
        summary += f"   [SEC] {security} | VLAN {vlan} | {broadcast_label}\n"

        # Security warnings
        if security == "OPEN" and enabled:
            summary += "   [WARN] Open network - no encryption!\n"
        if not broadcast and enabled:
            summary += "   [INFO] Hidden SSID - clients must know exact name\n"

    # Step 5: Return formatted response
    return [TextContent(
        type="text",
        text=f"{summary}\n{_format_json(data)}"
    )]
