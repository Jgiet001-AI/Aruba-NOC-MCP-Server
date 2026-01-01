"""
Get AP CPU Utilization - MCP tools for access point CPU utilization monitoring in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


async def handle_get_ap_cpu_utilization(args: dict[str, Any]) -> list[TextContent]:
    """Tool 15: Get AP CPU Utilization - /network-monitoring/v1alpha1/aps/{serial}/cpu-utilization-trends"""

    # Step 1: Validate required parameter
    serial = args.get("serial")
    if not serial:
        return [TextContent(type="text", text="[ERR] Parameter 'serial' is required. Provide the AP serial number.")]

    # Step 2: Build query parameters
    params = {}
    if "start_time" in args:
        params["start-time"] = args["start_time"]
    if "end_time" in args:
        params["end-time"] = args["end_time"]
    params["interval"] = args.get("interval", "1hour")

    # Step 3: Call Aruba API
    try:
        data = await call_aruba_api(f"/network-monitoring/v1alpha1/aps/{serial}/cpu-utilization-trends", params=params)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [
                TextContent(type="text", text=f"[ERR] AP with serial '{serial}' not found. Verify the serial number.")
            ]
        raise

    # Step 4: Extract trend data
    trends = data.get("trends", [])
    ap_name = data.get("apName", serial)
    interval = params["interval"]

    if trends:
        cpu_values = [t.get("cpuUtilization", 0) for t in trends]
        avg_cpu = sum(cpu_values) / len(cpu_values)
        max_cpu = max(cpu_values)
        min_cpu = min(cpu_values)

        # Find peak time
        peak_index = cpu_values.index(max_cpu)
        peak_time = trends[peak_index].get("timestamp", "Unknown")

        # Current value (last in series)
        current_cpu = cpu_values[-1] if cpu_values else 0
    else:
        avg_cpu = max_cpu = min_cpu = current_cpu = 0
        peak_time = "No data"

    # Step 5: Create performance summary with verification guardrails
    summary_parts = []

    # Verification checkpoint FIRST
    summary_parts.append(
        VerificationGuards.checkpoint(
            {
                "Current CPU": f"{current_cpu}%",
                "Average CPU": f"{avg_cpu:.1f}%",
                "Peak CPU": f"{max_cpu}%",
            }
        )
    )

    summary_parts.append(f"\n[CPU] CPU Utilization: {ap_name}")
    summary_parts.append(f"\n[STATS] Current: {current_cpu}%")
    summary_parts.append(f"\n[TREND] Statistics ({len(trends)} data points @ {interval}):")
    summary_parts.append(f"  * [PEAK] Peak: {max_cpu}% @ {peak_time}")
    summary_parts.append(f"  * [LOW] Minimum: {min_cpu}%")
    summary_parts.append(f"  * [AVG] Average: {avg_cpu:.1f}%")

    # Performance health indicators
    if max_cpu >= 90:
        summary_parts.append(f"\n[CRIT] CPU usage reached {max_cpu}% - AP is severely overloaded")
    elif max_cpu >= 80:
        summary_parts.append(f"\n[WARN] CPU usage reached {max_cpu}% - AP is under heavy load")
    elif avg_cpu >= 70:
        summary_parts.append(f"\n[WARN] Average CPU at {avg_cpu:.1f}% - monitor for performance issues")
    else:
        summary_parts.append("\n[OK] Healthy: CPU utilization is normal")

    # Trend analysis
    if len(cpu_values) >= 5:
        recent_avg = sum(cpu_values[-5:]) / 5
        older_avg = sum(cpu_values[:5]) / 5

        if recent_avg > older_avg * 1.2:
            summary_parts.append("[TREND] Increasing - CPU load is rising")
        elif recent_avg < older_avg * 0.8:
            summary_parts.append("[TREND] Decreasing - CPU load is dropping")

    # Recommendations
    if max_cpu >= 80:
        summary_parts.append("\n[INFO] Recommendation: Consider reducing client load or upgrading AP hardware")

    # Anti-hallucination footer
    summary_parts.append(
        VerificationGuards.anti_hallucination_footer(
            {
                "Current CPU": f"{current_cpu}%",
                "Average CPU": f"{avg_cpu:.1f}%",
                "Peak CPU": f"{max_cpu}%",
            }
        )
    )

    summary = "\n".join(summary_parts)

    # Step 6: Store facts and return summary (NO raw JSON)
    store_facts(
        "get_ap_cpu_utilization",
        {
            "AP": ap_name,
            "Current CPU": f"{current_cpu}%",
            "Average CPU": f"{avg_cpu:.1f}%",
            "Peak CPU": f"{max_cpu}%",
        },
    )

    return [TextContent(type="text", text=summary)]
