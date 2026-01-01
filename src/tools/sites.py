"""
Sites - MCP tools for site management in Aruba Central
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


async def handle_get_sites_health(args: dict[str, Any]) -> list[TextContent]:
    """Tool 2: Get Sites Health - /network-monitoring/v1alpha1/sites-health

    Returns health overview for ALL sites with device counts, client counts,
    alerts, and health scores.
    """
    # Step 1: Extract and prepare parameters
    params = {}
    params["limit"] = args.get("limit", 100)
    params["offset"] = args.get("offset", 0)

    # Step 2: Call Aruba API
    data = await call_aruba_api("/network-monitoring/v1alpha1/sites-health", params=params)

    # Step 3: Extract response data
    sites = data.get("items", [])
    total_sites = len(sites)

    # Step 4: Analyze and categorize sites
    by_health = {"Good": 0, "Fair": 0, "Poor": 0, "Unknown": 0}
    total_devices = 0
    total_clients = 0
    total_alerts = 0
    total_online = 0
    total_offline = 0
    sites_with_alerts = []

    for site in sites:
        # Health categorization
        health = site.get("overallHealth", "Unknown").title()
        if health in by_health:
            by_health[health] += 1
        else:
            by_health["Unknown"] += 1

        # Aggregate metrics
        site_devices = site.get("deviceCount", 0)
        total_devices += site_devices
        total_clients += site.get("clientCount", 0)

        # Track device status
        site_online = site.get("onlineDevices", site_devices)
        site_offline = site.get("offlineDevices", 0)
        total_online += site_online
        total_offline += site_offline

        # Track alerts
        alert_count = site.get("alertCount", 0)
        if alert_count > 0:
            total_alerts += alert_count
            sites_with_alerts.append(
                {
                    "name": site.get("siteName", "Unknown"),
                    "id": site.get("siteId", "N/A"),
                    "alerts": alert_count,
                    "health": health,
                    "devices": site_devices,
                    "offline": site_offline,
                }
            )

    # Sort sites by alert count
    sites_with_alerts.sort(key=lambda x: x["alerts"], reverse=True)

    # Step 5: Create human-readable summary with verification guardrails
    summary_parts = []

    # Verification checkpoint FIRST
    summary_parts.append(
        VerificationGuards.checkpoint(
            {
                "Total sites": f"{total_sites} sites",
                "Total devices": f"{total_devices} devices",
                "Online devices": f"{total_online} devices",
                "Offline devices": f"{total_offline} devices",
                "Health scores are NOT device counts": "True",
            }
        )
    )

    summary_parts.append("\n**Network Sites Health Overview**")
    summary_parts.append(f"Total sites analyzed: {total_sites}\n")

    # Health distribution with explicit labels
    summary_parts.append("**Site Health Distribution (by site count, not devices):**")
    health_labels = {"Good": "[OK]", "Fair": "[WARN]", "Poor": "[CRIT]", "Unknown": "[--]"}
    for health, count in by_health.items():
        if count > 0:
            label = health_labels.get(health, "[--]")
            percentage = (count / total_sites * 100) if total_sites > 0 else 0
            summary_parts.append(f"  {label} {health}: {count} sites ({percentage:.1f}% of sites)")

    # Aggregate metrics with explicit device counts
    summary_parts.append("\n**Aggregate Metrics (actual device counts):**")
    summary_parts.append(f"  [DEV] Total devices: {total_devices:,}")
    summary_parts.append(f"  [UP] Online devices: {total_online:,}")
    summary_parts.append(f"  [DN] Offline devices: {total_offline:,}")
    summary_parts.append(f"  [CLI] Total clients: {total_clients:,}")
    summary_parts.append(f"  [ALERT] Total active alerts: {total_alerts}")

    # Top sites with alerts - include device counts
    if sites_with_alerts:
        summary_parts.append("\n**Top Sites with Alerts (with device counts):**")
        for i, site in enumerate(sites_with_alerts[:5], 1):  # Top 5
            health_label = health_labels.get(site["health"], "[--]")
            summary_parts.append(
                f"  {i}. {site['name']}: {site['alerts']} alerts {health_label} | "
                f"Devices: {site['devices']}, Offline: {site['offline']}"
            )

    # Anti-hallucination footer
    summary_parts.append(
        VerificationGuards.anti_hallucination_footer(
            {
                "Total sites": total_sites,
                "Total devices": total_devices,
                "Offline devices": total_offline,
            }
        )
    )

    summary = "\n".join(summary_parts)

    # Step 6: Store facts for verification and return summary (NO raw JSON)
    store_facts(
        "get_sites_health",
        {
            "Total sites": total_sites,
            "Total devices": total_devices,
            "Online devices": total_online,
            "Offline devices": total_offline,
            "Total clients": total_clients,
            "Total alerts": total_alerts,
        },
    )

    return [TextContent(type="text", text=summary)]
