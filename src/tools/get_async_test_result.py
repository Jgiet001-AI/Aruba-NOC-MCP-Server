"""
Get Async Test Result - MCP tools for async test result retrieval in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import format_json

logger = logging.getLogger("aruba-noc-server")


async def handle_get_async_test_result(args: dict[str, Any]) -> list[TextContent]:
    """Tool 26: Get Async Test Result - GET /network-troubleshooting/v1alpha1/*/async-operations/{task-id}"""

    # Step 1: Validate required parameter
    task_id = args.get("task_id")

    if not task_id:
        return [
            TextContent(
                type="text", text="[ERR] Parameter 'task_id' is required. Provide the task ID from the initial test."
            )
        ]

    # Step 2: Call Aruba API
    # Note: Endpoint uses wildcard (*) for device type - API routes based on task_id
    try:
        data = await call_aruba_api(f"/network-troubleshooting/v1alpha1/async-operations/{task_id}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [
                TextContent(
                    type="text", text=f"[ERR] Task '{task_id}' not found. Verify the task ID or it may have expired."
                )
            ]
        raise

    # Step 3: Extract status and results
    status = data.get("status", "UNKNOWN")
    test_type = data.get("testType", "Unknown")
    device_name = data.get("deviceName", "Unknown")
    target = data.get("target", "N/A")

    # Step 4: Format response based on status
    if status == "IN_PROGRESS":
        progress_pct = data.get("progressPercent", 0)
        eta = data.get("estimatedCompletionTime", "Unknown")

        summary = "[ASYNC] Test In Progress\n"
        summary += f"\n[TYPE] Type: {test_type}\n"
        summary += f"[DEV] Device: {device_name}\n"
        summary += f"[TGT] Target: {target}\n"
        summary += f"[STATS] Progress: {progress_pct}%\n"
        summary += f"[ETA] ETA: {eta}\n"
        summary += "\n[INFO] Poll again in a few seconds to check for completion.\n"

    elif status == "COMPLETED":
        # Extract test-specific results
        results = data.get("results", {})

        if test_type == "PING":
            packets_sent = results.get("packetsSent", 0)
            packets_received = results.get("packetsReceived", 0)
            packet_loss = results.get("packetLossPercent", 0)
            min_latency = results.get("minLatencyMs", 0)
            avg_latency = results.get("avgLatencyMs", 0)
            max_latency = results.get("maxLatencyMs", 0)

            summary = "[OK] Ping Test Complete\n"
            summary += f"\n[DEV] Device: {device_name}\n"
            summary += f"[TGT] Target: {target}\n"
            summary += "\n[DATA] Results:\n"
            summary += f"  [PKT] Sent: {packets_sent} | Received: {packets_received}\n"
            summary += f"  [LOSS] Packet Loss: {packet_loss}%\n"
            summary += f"  [LAT] Latency - Min: {min_latency}ms | Avg: {avg_latency}ms | Max: {max_latency}ms\n"

            # Health assessment
            if packet_loss == 0 and avg_latency < 50:
                summary += "\n[OK] Excellent connectivity - no loss, low latency\n"
            elif packet_loss < 5 and avg_latency < 100:
                summary += "\n[OK] Good connectivity - minor latency\n"
            elif packet_loss < 20:
                summary += "\n[WARN] Degraded connectivity - packet loss detected\n"
            else:
                summary += "\n[CRIT] Poor connectivity - high loss or unreachable\n"

        elif test_type == "TRACEROUTE":
            hops = results.get("hops", [])

            summary = "[OK] Traceroute Complete\n"
            summary += f"\n[DEV] Device: {device_name}\n"
            summary += f"[TGT] Target: {target}\n"
            summary += f"\n[PATH] Path ({len(hops)} hops):\n"

            for hop in hops:
                hop_num = hop.get("hop", 0)
                ip = hop.get("ip", "*.*.*.*")
                hostname = hop.get("hostname", "")
                latency = hop.get("latency", "*")

                hop_display = f"  {hop_num:2d}. {ip:15s}"
                if hostname:
                    hop_display += f" ({hostname})"
                if latency != "*":
                    hop_display += f" - {latency}ms"

                summary += f"{hop_display}\n"

        else:
            # Generic result display
            summary = "[OK] Test Complete\n"
            summary += f"\n[TYPE] Type: {test_type}\n"
            summary += f"[DEV] Device: {device_name}\n"
            summary += f"[TGT] Target: {target}\n"

    elif status == "FAILED":
        error_msg = data.get("errorMessage", "Unknown error")

        summary = "[ERR] Test Failed\n"
        summary += f"\n[TYPE] Type: {test_type}\n"
        summary += f"[DEV] Device: {device_name}\n"
        summary += f"[TGT] Target: {target}\n"
        summary += f"\n[ERR] Error: {error_msg}\n"

    else:
        summary = f"[--] Unknown Status: {status}\n"

    # Step 5: Return formatted response
    return [TextContent(type="text", text=f"{summary}\n{format_json(data)}")]
