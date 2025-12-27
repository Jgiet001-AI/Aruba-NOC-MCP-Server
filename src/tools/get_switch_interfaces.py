"""
Get Switch Interfaces - MCP tools for switch interfaces retrieval in Aruba Central
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

async def handle_get_switch_interfaces(args: dict[str, Any]) -> list[TextContent]:
    """Tool 30: Get Switch Interfaces - /network-monitoring/v1alpha1/switch/{serial}/interfaces"""

    # Step 1: Validate required parameter
    serial = args.get("serial")

    if not serial:
        return [TextContent(
            type="text",
            text="[ERR] Parameter 'serial' is required. Provide the switch serial number."
        )]

    # Step 2: Call Aruba API
    try:
        data = await call_aruba_api(
            f"/network-monitoring/v1alpha1/switch/{serial}/interfaces"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [TextContent(
                type="text",
                text=f"[ERR] Switch with serial '{serial}' not found. Verify the serial number."
            )]
        raise

    # Step 3: Extract interface data
    interfaces = data.get("interfaces", [])
    switch_name = data.get("switchName", serial)
    model = data.get("model", "Unknown")

    if not interfaces:
        return [TextContent(
            type="text",
            text=f"[INFO] Switch '{switch_name}' has no interfaces reported."
        )]

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
    error_ports = [iface for iface in data.get("interfaces", [])
                   if iface.get("crcErrors", 0) > 0 or iface.get("collisions", 0) > 0]

    # Step 5: Create interface summary
    summary = "[PORT] Switch Interface Report\n"
    summary += f"\n[NAME] Switch: {switch_name}\n"
    summary += f"[MODEL] Model: {model}\n"
    summary += f"[SERIAL] Serial: {serial}\n"

    summary += "\n[STATS] Port Summary:\n"
    summary += f"  [PORT] Total Ports: {total_ports}\n"
    summary += f"  [UP] UP: {up_ports} | [DN] DOWN: {down_ports}\n"
    summary += f"  [TRUNK] Trunk: {trunk_ports} | [ACCESS] Access: {access_ports}\n"

    if poe_ports > 0:
        summary += f"  [POE] PoE Ports: {poe_ports} (consuming {total_poe_power:.1f}W)\n"

    if status_filter != "ALL":
        summary += f"\n[FILTER] Filtered: Showing {shown_ports} {status_filter} ports\n"

    # Port details
    summary += "\n[PORT] Port Details:\n"
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

        summary += f"{port_line}\n"

    if len(interfaces) > 20:
        summary += f"  ... and {len(interfaces) - 20} more ports\n"

    # Error analysis
    if error_ports:
        summary += f"\n[WARN] Ports with Errors ({len(error_ports)}):\n"
        for iface in error_ports[:5]:
            port_name = iface.get("portName", "Unknown")
            crc = iface.get("crcErrors", 0)
            collisions = iface.get("collisions", 0)
            drops = iface.get("drops", 0)

            summary += f"  [WARN] {port_name}:"
            if crc > 0:
                summary += f" CRC={crc}"
            if collisions > 0:
                summary += f" Collisions={collisions}"
            if drops > 0:
                summary += f" Drops={drops}"
            summary += "\n"

    # Health insights
    summary += "\n[HEALTH] Health Insights:\n"

    if down_ports == 0:
        summary += "  [OK] All ports operational\n"
    elif down_ports < total_ports * 0.1:
        summary += f"  [OK] {down_ports} ports down - normal for unused ports\n"
    else:
        summary += f"  [WARN] {down_ports} ports down - investigate connectivity\n"

    if error_ports:
        summary += f"  [WARN] {len(error_ports)} ports with errors - check cabling\n"

    if total_poe_power > 0:
        # Assuming 370W budget for typical switch
        poe_budget = 370
        poe_usage_pct = (total_poe_power / poe_budget) * 100

        if poe_usage_pct > 90:
            summary += f"  [CRIT] PoE budget critical - {poe_usage_pct:.1f}% used\n"
        elif poe_usage_pct > 70:
            summary += f"  [WARN] PoE budget high - {poe_usage_pct:.1f}% used\n"
        else:
            summary += f"  [OK] PoE budget healthy - {poe_usage_pct:.1f}% used\n"

    # Step 6: Return formatted response
    return [TextContent(
        type="text",
        text=f"{summary}\n{_format_json(data)}"
    )]
