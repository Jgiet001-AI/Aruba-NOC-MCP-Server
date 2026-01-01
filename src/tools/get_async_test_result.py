"""
Get Async Test Result - MCP tools for async test result retrieval in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.verify_facts import store_facts

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

    # Step 4: Format response based on status with verification guardrails
    summary_parts = []

    # Verification checkpoint
    summary_parts.append(
        VerificationGuards.checkpoint(
            {
                "Test type": test_type,
                "Status": status,
                "Target": target,
            }
        )
    )

    if status == "IN_PROGRESS":
        progress_pct = data.get("progressPercent", 0)
        eta = data.get("estimatedCompletionTime", "Unknown")

        summary_parts.append("\n[ASYNC] Test In Progress")
        summary_parts.append(f"\n[TYPE] Type: {test_type}")
        summary_parts.append(f"[DEV] Device: {device_name}")
        summary_parts.append(f"[TGT] Target: {target}")
        summary_parts.append(f"[STATS] Progress: {progress_pct}%")
        summary_parts.append(f"[ETA] ETA: {eta}")
        summary_parts.append("\n[INFO] Poll again in a few seconds to check for completion.")

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

            summary_parts.append("\n[OK] Ping Test Complete")
            summary_parts.append(f"\n[DEV] Device: {device_name}")
            summary_parts.append(f"[TGT] Target: {target}")
            summary_parts.append("\n[DATA] Results:")
            summary_parts.append(f"  [PKT] Sent: {packets_sent} packets | Received: {packets_received} packets")
            summary_parts.append(f"  [LOSS] Packet Loss: {packet_loss}%")
            summary_parts.append(
                f"  [LAT] Latency - Min: {min_latency}ms | Avg: {avg_latency}ms | Max: {max_latency}ms"
            )

            # Health assessment
            if packet_loss == 0 and avg_latency < 50:
                summary_parts.append("\n[OK] Excellent connectivity - no loss, low latency")
            elif packet_loss < 5 and avg_latency < 100:
                summary_parts.append("\n[OK] Good connectivity - minor latency")
            elif packet_loss < 20:
                summary_parts.append("\n[WARN] Degraded connectivity - packet loss detected")
            else:
                summary_parts.append("\n[CRIT] Poor connectivity - high loss or unreachable")

        elif test_type == "TRACEROUTE":
            hops = results.get("hops", [])

            summary_parts.append("\n[OK] Traceroute Complete")
            summary_parts.append(f"\n[DEV] Device: {device_name}")
            summary_parts.append(f"[TGT] Target: {target}")
            summary_parts.append(f"\n[PATH] Path ({len(hops)} hops):")

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

                summary_parts.append(hop_display)

        else:
            # Generic result display
            summary_parts.append("\n[OK] Test Complete")
            summary_parts.append(f"\n[TYPE] Type: {test_type}")
            summary_parts.append(f"[DEV] Device: {device_name}")
            summary_parts.append(f"[TGT] Target: {target}")

    elif status == "FAILED":
        error_msg = data.get("errorMessage", "Unknown error")

        summary_parts.append("\n[ERR] Test Failed")
        summary_parts.append(f"\n[TYPE] Type: {test_type}")
        summary_parts.append(f"[DEV] Device: {device_name}")
        summary_parts.append(f"[TGT] Target: {target}")
        summary_parts.append(f"\n[ERR] Error: {error_msg}")

    else:
        summary_parts.append(f"\n[--] Unknown Status: {status}")

    # Anti-hallucination footer
    summary_parts.append(
        VerificationGuards.anti_hallucination_footer(
            {
                "Status": status,
                "Test type": test_type,
            }
        )
    )

    summary = "\n".join(summary_parts)

    # Step 5: Store facts and return summary (NO raw JSON)
    store_facts(
        "get_async_test_result",
        {
            "Status": status,
            "Test type": test_type,
            "Target": target,
        },
    )

    return [TextContent(type="text", text=summary)]
