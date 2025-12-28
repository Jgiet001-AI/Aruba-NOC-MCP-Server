"""
List WLANs - MCP tools for WLAN listing in Aruba Central
"""

import logging
from typing import Any

from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")

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

    # Step 4: Create summary with verification guardrails
    summary_parts = []
    
    # Verification checkpoint FIRST
    summary_parts.append(VerificationGuards.checkpoint({
        "Total WLANs": f"{total} WLANs",
        "Enabled": f"{enabled_count} WLANs",
        "Disabled": f"{disabled_count} WLANs",
    }))
    
    summary_parts.append("\n[WIFI] Wireless Networks (WLANs)")
    summary_parts.append(f"\n[STATS] Total: {total} WLANs | [UP] {enabled_count} enabled | [DN] {disabled_count} disabled")
    summary_parts.append("\n[SEC] Security Distribution:")
    for sec_type, count in sorted(by_security.items(), key=lambda x: x[1], reverse=True):
        summary_parts.append(f"  * {sec_type}: {count} WLANs")

    if guest_networks:
        summary_parts.append(f"\n[GUEST] Guest Networks ({len(guest_networks)}): {', '.join(guest_networks)}")

    summary_parts.append("\n[LIST] WLAN Details:")
    for wlan in wlans:
        wlan_name = wlan.get("wlanName", "Unknown")
        security = wlan.get("securityType", "Unknown")
        vlan = wlan.get("vlanId", "N/A")
        enabled = wlan.get("enabled", False)
        broadcast = wlan.get("ssidBroadcast", True)

        status_label = "[UP]" if enabled else "[DN]"
        broadcast_label = "Broadcast" if broadcast else "Hidden"

        summary_parts.append(f"\n{status_label} {wlan_name}")
        summary_parts.append(f"   [SEC] {security} | VLAN {vlan} | {broadcast_label}")

        # Security warnings
        if security == "OPEN" and enabled:
            summary_parts.append("   [WARN] Open network - no encryption!")
        if not broadcast and enabled:
            summary_parts.append("   [INFO] Hidden SSID - clients must know exact name")

    # Anti-hallucination footer
    summary_parts.append(VerificationGuards.anti_hallucination_footer({
        "Total WLANs": total,
        "Enabled": enabled_count,
        "Disabled": disabled_count,
    }))

    summary = "\n".join(summary_parts)

    # Step 5: Store facts and return summary (NO raw JSON)
    store_facts("list_wlans", {
        "Total WLANs": total,
        "Enabled": enabled_count,
        "Disabled": disabled_count,
        "Security types": by_security,
    })
    
    return [TextContent(type="text", text=summary)]
