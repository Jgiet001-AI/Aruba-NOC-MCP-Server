"""
Firmware - MCP tools for firmware management in Aruba Central
"""

import json
import logging
from typing import Any

from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


def _format_json(data: dict[str, Any]) -> str:
    """Format JSON data for display"""
    return json.dumps(data, indent=2)


async def handle_get_firmware_details(args: dict[str, Any]) -> list[TextContent]:
    """Tool 4: Get Firmware Details - /network-services/v1alpha1/firmware-details

    Retrieves firmware status for ALL devices with version info and compliance.
    """
    # Step 1: Extract and prepare parameters
    params = {}

    if "filter" in args:
        params["filter"] = args["filter"]
    if "sort" in args:
        params["sort"] = args["sort"]
    if "search" in args:
        params["search"] = args["search"]
    params["limit"] = args.get("limit", 100)
    if "next" in args:
        params["next"] = args["next"]

    # Step 2: Call Aruba API
    data = await call_aruba_api("/network-services/v1alpha1/firmware-details", params=params)

    # Step 3: Extract response data
    devices = data.get("items", [])
    total_devices = data.get("total", len(devices))
    next_cursor = data.get("next")

    # Step 4: Analyze firmware status
    by_upgrade_status = {"Up To Date": 0, "Update Available": 0, "Update Required": 0, "Unknown": 0}
    by_classification = {}
    by_device_type = {}
    devices_needing_updates = []

    for device in devices:
        # Upgrade status
        upgrade_status = device.get("upgradeStatus") or "Unknown"
        if upgrade_status in by_upgrade_status:
            by_upgrade_status[upgrade_status] += 1
        else:
            by_upgrade_status["Unknown"] += 1

        # Classification (handle None values from API)
        classification = device.get("firmwareClassification") or "Unknown"
        by_classification[classification] = by_classification.get(classification, 0) + 1

        # Device type
        device_type = device.get("deviceType") or "Unknown"
        by_device_type[device_type] = by_device_type.get(device_type, 0) + 1

        # Track devices needing updates
        if upgrade_status in ["Update Available", "Update Required"]:
            devices_needing_updates.append(
                {
                    "name": device.get("deviceName") or "Unknown",
                    "serial": device.get("serialNumber") or "N/A",
                    "current": device.get("softwareVersion") or "Unknown",
                    "recommended": device.get("recommendedVersion") or "N/A",
                    "status": upgrade_status,
                    "classification": classification,
                }
            )

    # Sort devices by upgrade priority (Required > Available)
    devices_needing_updates.sort(key=lambda x: (x["status"] != "Update Required", x["name"]))

    # Step 5: Create human-readable summary with verification guardrails
    summary_parts = []

    # Verification checkpoint FIRST
    summary_parts.append(
        VerificationGuards.checkpoint(
            {
                "Total devices analyzed": f"{total_devices} devices",
                "Up to date": f"{by_upgrade_status.get('Up To Date', 0)} devices",
                "Update available": f"{by_upgrade_status.get('Update Available', 0)} devices",
                "Update required": f"{by_upgrade_status.get('Update Required', 0)} devices",
            }
        )
    )

    summary_parts.append("\n**Firmware Status Overview**")
    summary_parts.append(f"Total devices analyzed: {total_devices}\n")

    # Upgrade status breakdown
    summary_parts.append("**By Upgrade Status (actual device counts):**")
    status_labels = {
        "Up To Date": "[OK]",
        "Update Available": "[AVAIL]",
        "Update Required": "[REQ]",
        "Unknown": "[--]",
    }
    for status, count in by_upgrade_status.items():
        if count > 0:
            label = status_labels.get(status, "[--]")
            percentage = (count / total_devices * 100) if total_devices > 0 else 0
            summary_parts.append(f"  {label} {status}: {count} devices ({percentage:.1f}%)")

    # Device type breakdown
    if by_device_type:
        summary_parts.append("\n**By Device Type:**")
        for dtype, count in sorted(by_device_type.items()):
            summary_parts.append(f"  [DEV] {dtype}: {count} devices")

    # Classification breakdown
    if by_classification:
        summary_parts.append("\n**By Classification:**")
        class_labels = {"Security Patch": "[SEC]", "Bug Fix": "[BUG]", "Feature Release": "[FEAT]"}
        for classification, count in sorted(by_classification.items()):
            label = class_labels.get(classification, "[--]")
            summary_parts.append(f"  {label} {classification}: {count} devices")

    # Devices needing updates (top priority)
    if devices_needing_updates:
        summary_parts.append(f"\n**Devices Needing Updates ({len(devices_needing_updates)} devices):**")
        for i, device in enumerate(devices_needing_updates[:10], 1):  # Top 10
            priority = "[REQ]" if device["status"] == "Update Required" else "[AVAIL]"
            summary_parts.append(
                f"  {i}. {priority} {device['name']} ({device['serial']}): "
                f"{device['current']} -> {device['recommended']}"
            )
        if len(devices_needing_updates) > 10:
            summary_parts.append(f"  ... and {len(devices_needing_updates) - 10} more devices")

    # Pagination info
    if next_cursor:
        summary_parts.append("\n[MORE] Results available (use next cursor)")

    # Anti-hallucination footer
    summary_parts.append(
        VerificationGuards.anti_hallucination_footer(
            {
                "Total devices": total_devices,
                "Up to date": by_upgrade_status.get("Up To Date", 0),
                "Needs update": len(devices_needing_updates),
            }
        )
    )

    summary = "\n".join(summary_parts)

    # Step 6: Store facts and return summary (NO raw JSON)
    store_facts(
        "get_firmware_details",
        {
            "Total devices": total_devices,
            "Up to date": by_upgrade_status.get("Up To Date", 0),
            "Update available": by_upgrade_status.get("Update Available", 0),
            "Update required": by_upgrade_status.get("Update Required", 0),
        },
    )

    return [TextContent(type="text", text=summary)]
