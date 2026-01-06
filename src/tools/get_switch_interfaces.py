"""
Get Switch Interfaces - MCP tools for switch interfaces retrieval in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.site_helper import get_site_id_for_device
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


async def handle_get_switch_interfaces(args: dict[str, Any]) -> list[TextContent]:
    """Tool 30: Get Switch Interfaces - /network-monitoring/v1alpha1/switch/{serial}/interfaces"""

    # Step 1: Validate required parameter
    serial = args.get("serial")

    if not serial:
        return [
            TextContent(type="text", text="[ERR] Parameter 'serial' is required. Provide the switch serial number.")
        ]

    # Step 2: Get site-id for this device (REQUIRED by API)
    try:
        site_id = await get_site_id_for_device(serial)
        params = {"site-id": site_id}

        # Call Aruba API with site-id parameter
        data = await call_aruba_api(f"/network-monitoring/v1alpha1/switch/{serial}/interfaces", params=params)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [
                TextContent(
                    type="text", text=f"[ERR] Switch with serial '{serial}' not found. Verify the serial number."
                )
            ]
        raise

    # Step 3: Extract interface data
    interfaces = data.get("interfaces", [])
    switch_name = data.get("switchName", serial)
    model = data.get("model", "Unknown")

    if not interfaces:
        return [TextContent(type="text", text=f"[INFO] Switch '{switch_name}' has no interfaces reported.")]

    # Step 4: Filter by status if requested
    status_filter = args.get("status_filter", "ALL")
    if status_filter != "ALL":
        interfaces = [iface for iface in interfaces if iface.get("operStatus") == status_filter]

    # Analyze interfaces
    total_ports = len(data.get("interfaces", []))  # Before filtering
    shown_ports = len(interfaces)  # After filtering
    up_ports = sum(1 for iface in data.get("interfaces", []) if iface.get("operStatus") == "UP")
    down_ports = total_ports - up_ports
    poe_ports = sum(1 for iface in data.get("interfaces", []) if iface.get("poeEnabled"))
    trunk_ports = sum(1 for iface in data.get("interfaces", []) if iface.get("portMode") == "TRUNK")
    access_ports = sum(1 for iface in data.get("interfaces", []) if iface.get("portMode") == "ACCESS")

    # Total PoE power consumption
    total_poe_power = sum(iface.get("poePowerConsumption", 0) for iface in data.get("interfaces", []))

    # Interfaces with errors
    error_ports = [
        iface for iface in data.get("interfaces", []) if iface.get("crcErrors", 0) > 0 or iface.get("collisions", 0) > 0
    ]

    # Step 5: Create interface summary with verification guardrails
    summary_parts = []

    # Verification checkpoint FIRST
    summary_parts.append(
        VerificationGuards.checkpoint(
            {
                "Total ports": f"{total_ports} ports",
                "Ports UP": f"{up_ports} ports",
                "Ports DOWN": f"{down_ports} ports",
                "PoE ports": f"{poe_ports} ports",
            }
        )
    )

    summary_parts.append("\n[PORT] Switch Interface Report")
    summary_parts.append(f"\n[NAME] Switch: {switch_name}")
    summary_parts.append(f"[MODEL] Model: {model}")
    summary_parts.append(f"[SERIAL] Serial: {serial}")

    summary_parts.append("\n[STATS] Port Summary (port counts):")
    summary_parts.append(f"  [PORT] Total Ports: {total_ports} ports")
    summary_parts.append(f"  [UP] UP: {up_ports} ports | [DN] DOWN: {down_ports} ports")
    summary_parts.append(f"  [TRUNK] Trunk: {trunk_ports} ports | [ACCESS] Access: {access_ports} ports")

    if poe_ports > 0:
        summary_parts.append(f"  [POE] PoE Ports: {poe_ports} ports (consuming {total_poe_power:.1f}W)")

    if status_filter != "ALL":
        summary_parts.append(f"\n[FILTER] Filtered: Showing {shown_ports} {status_filter} ports")

    # Port details
    summary_parts.append("\n[PORT] Port Details:")
    for iface in interfaces[:20]:  # Show first 20 ports
        port_name = iface.get("portName", "Unknown")
        oper_status = iface.get("operStatus", "UNKNOWN")
        speed = iface.get("speed", "N/A")
        duplex = iface.get("duplex", "N/A")
        vlan = iface.get("vlan", "N/A")
        port_mode = iface.get("portMode", "N/A")
        poe_enabled = iface.get("poeEnabled", False)
        poe_power = iface.get("poePowerConsumption", 0)
        neighbor = iface.get("lldpNeighbor", "")

        # Status label
        status_label = "[UP]" if oper_status == "UP" else "[DN]"

        # Port line
        port_line = f"  {status_label} {port_name}: {oper_status}"

        if oper_status == "UP":
            port_line += f" | {speed} {duplex}"
            port_line += f" | {port_mode}"
            if port_mode == "ACCESS":
                port_line += f" VLAN {vlan}"

        if poe_enabled and poe_power > 0:
            port_line += f" | [POE]{poe_power:.1f}W"

        if neighbor:
            port_line += f" | [LINK]{neighbor}"

        summary_parts.append(port_line)

    if len(interfaces) > 20:
        summary_parts.append(f"  ... and {len(interfaces) - 20} more ports")

    # Error analysis
    if error_ports:
        summary_parts.append(f"\n[WARN] Ports with Errors ({len(error_ports)}):")
        for iface in error_ports[:5]:
            port_name = iface.get("portName", "Unknown")
            crc = iface.get("crcErrors", 0)
            collisions = iface.get("collisions", 0)
            drops = iface.get("drops", 0)

            error_line = f"  [WARN] {port_name}:"
            if crc > 0:
                error_line += f" CRC={crc}"
            if collisions > 0:
                error_line += f" Collisions={collisions}"
            if drops > 0:
                error_line += f" Drops={drops}"
            summary_parts.append(error_line)

    # Health insights
    summary_parts.append("\n[HEALTH] Health Insights:")

    if down_ports == 0:
        summary_parts.append("  [OK] All ports operational")
    elif down_ports < total_ports * 0.1:
        summary_parts.append(f"  [OK] {down_ports} ports down - normal for unused ports")
    else:
        summary_parts.append(f"  [WARN] {down_ports} ports down - investigate connectivity")

    if error_ports:
        summary_parts.append(f"  [WARN] {len(error_ports)} ports with errors - check cabling")

    if total_poe_power > 0:
        # Assuming 370W budget for typical switch
        poe_budget = 370
        poe_usage_pct = (total_poe_power / poe_budget) * 100

        if poe_usage_pct > 90:
            summary_parts.append(f"  [CRIT] PoE budget critical - {poe_usage_pct:.1f}% used")
        elif poe_usage_pct > 70:
            summary_parts.append(f"  [WARN] PoE budget high - {poe_usage_pct:.1f}% used")
        else:
            summary_parts.append(f"  [OK] PoE budget healthy - {poe_usage_pct:.1f}% used")

    # Anti-hallucination footer
    summary_parts.append(
        VerificationGuards.anti_hallucination_footer(
            {
                "Total ports": total_ports,
                "Ports UP": up_ports,
                "Ports DOWN": down_ports,
            }
        )
    )

    summary = "\n".join(summary_parts)

    # Step 6: Store facts and return summary (NO raw JSON)
    store_facts(
        "get_switch_interfaces",
        {
            "Switch": switch_name,
            "Total ports": total_ports,
            "Ports UP": up_ports,
            "Ports DOWN": down_ports,
            "PoE ports": poe_ports,
        },
    )

    return [TextContent(type="text", text=summary)]
