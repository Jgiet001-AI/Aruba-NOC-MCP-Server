"""
Sites - MCP tools for site management in Aruba Central
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
    sites_with_alerts = []

    for site in sites:
        # Health categorization
        health = site.get("overallHealth", "Unknown").title()
        if health in by_health:
            by_health[health] += 1
        else:
            by_health["Unknown"] += 1

        # Aggregate metrics
        total_devices += site.get("deviceCount", 0)
        total_clients += site.get("clientCount", 0)

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
                }
            )

    # Sort sites by alert count
    sites_with_alerts.sort(key=lambda x: x["alerts"], reverse=True)

    # Step 5: Create human-readable summary
    summary_parts = []
    summary_parts.append("**Network Sites Health Overview**")
    summary_parts.append(f"Total sites analyzed: {total_sites}\n")

    # Health distribution
    summary_parts.append("**Site Health Distribution:**")
    health_labels = {"Good": "[OK]", "Fair": "[WARN]", "Poor": "[CRIT]", "Unknown": "[--]"}
    for health, count in by_health.items():
        if count > 0:
            label = health_labels.get(health, "[--]")
            percentage = (count / total_sites * 100) if total_sites > 0 else 0
            summary_parts.append(f"  {label} {health}: {count} ({percentage:.1f}%)")

    # Aggregate metrics
    summary_parts.append("\n**Aggregate Metrics:**")
    summary_parts.append(f"  [DEV] Total devices: {total_devices:,}")
    summary_parts.append(f"  [CLI] Total clients: {total_clients:,}")
    summary_parts.append(f"  [ALERT] Total active alerts: {total_alerts}")

    # Top sites with alerts
    if sites_with_alerts:
        summary_parts.append("\n**Top Sites with Critical Alerts:**")
        for i, site in enumerate(sites_with_alerts[:5], 1):  # Top 5
            health_label = health_labels.get(site["health"], "[--]")
            summary_parts.append(
                f"  {i}. {site['name']} (ID: {site['id']}): {site['alerts']} alerts {health_label}"
            )

    summary = "\n".join(summary_parts)

    # Step 6: Return formatted response
    return [TextContent(type="text", text=f"{summary}\n\n{_format_json(data)}")]
