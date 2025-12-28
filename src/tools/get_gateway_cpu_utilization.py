"""
Get Gateway CPU Utilization - MCP tools for gateway CPU utilization monitoring in Aruba Central
"""

import logging
from typing import Any

from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


async def handle_get_gateway_cpu_utilization(args: dict[str, Any]) -> list[TextContent]:
    """Get Gateway CPU Utilization - Retrieves CPU utilization trends for a specific gateway.

    Returns time-series data showing CPU usage percentages at different intervals,
    average CPU load, peak utilization, and performance trend indicators.
    """
    # Step 1: Validate required parameter
    serial = args.get("serial")

    if not serial:
        return [
            TextContent(type="text", text="[ERR] Parameter 'serial' is required. Provide the gateway serial number.")
        ]

    # Step 2: Extract optional parameters
    params = {}

    params["interval"] = args.get("interval", "1hour")

    if "start_time" in args:
        params["start-time"] = args["start_time"]
    if "end_time" in args:
        params["end-time"] = args["end_time"]

    # Step 3: Call Aruba API
    data = await call_aruba_api(f"/network-monitoring/v1alpha1/gateways/{serial}/cpu-utilization", params=params)

    # Step 4: Extract and analyze data
    samples = data.get("samples", [])
    total_samples = len(samples)

    if total_samples == 0:
        summary = f"[INFO] No CPU data available for gateway {serial}\n"
        return [TextContent(type="text", text=summary)]

    # Calculate statistics
    cpu_values = [s.get("cpuPercent", 0) for s in samples]
    avg_cpu = sum(cpu_values) / total_samples
    max_cpu = max(cpu_values)
    min_cpu = min(cpu_values)

    # Step 5: Create human-readable summary with verification guardrails
    summary_parts = []
    
    # Verification checkpoint FIRST
    summary_parts.append(VerificationGuards.checkpoint({
        "Average CPU": f"{avg_cpu:.1f}%",
        "Min CPU": f"{min_cpu:.1f}%",
        "Max CPU": f"{max_cpu:.1f}%",
    }))
    
    summary_parts.append(f"\n[GW] Gateway CPU Utilization: {serial}")
    summary_parts.append(f"\n[STATS] Statistics ({total_samples} samples):")

    # Format with status indicators based on thresholds
    if avg_cpu >= 90:
        avg_label = "[CRIT]"
    elif avg_cpu >= 70:
        avg_label = "[WARN]"
    else:
        avg_label = "[OK]"

    summary_parts.append(f"  {avg_label} Average: {avg_cpu:.1f}%")
    summary_parts.append(f"  [DATA] Min: {min_cpu:.1f}% | Max: {max_cpu:.1f}%")

    # Health assessment
    if max_cpu >= 90:
        summary_parts.append("\n[WARN] Peak utilization exceeded 90% - monitor for capacity issues")
    elif avg_cpu >= 70:
        summary_parts.append("\n[INFO] Elevated average CPU - consider load distribution")
    else:
        summary_parts.append("\n[OK] CPU utilization within normal range")

    # Anti-hallucination footer
    summary_parts.append(VerificationGuards.anti_hallucination_footer({
        "Average CPU": f"{avg_cpu:.1f}%",
        "Min CPU": f"{min_cpu:.1f}%",
        "Max CPU": f"{max_cpu:.1f}%",
    }))

    summary = "\n".join(summary_parts)

    # Step 6: Store facts and return summary (NO raw JSON)
    store_facts("get_gateway_cpu_utilization", {
        "Gateway": serial,
        "Average CPU": f"{avg_cpu:.1f}%",
        "Min CPU": f"{min_cpu:.1f}%",
        "Max CPU": f"{max_cpu:.1f}%",
    })
    
    return [TextContent(type="text", text=summary)]
