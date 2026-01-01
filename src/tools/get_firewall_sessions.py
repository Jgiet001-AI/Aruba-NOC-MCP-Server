"""
Get Firewall Sessions - MCP tools for firewall sessions retrieval in Aruba Central
"""

import logging
from typing import Any

from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


async def handle_get_firewall_sessions(args: dict[str, Any]) -> list[TextContent]:
    """Tool 28: Get Firewall Sessions - /network-monitoring/v1alpha1/site-firewall-sessions"""

    # Step 1: Build query parameters
    params = {}

    if "site_id" in args:
        params["siteId"] = args["site_id"]
    if "status" in args:
        params["status"] = args["status"]
    if "protocol" in args:
        params["protocol"] = args["protocol"]
    if "limit" in args:
        params["limit"] = args["limit"]

    # Step 2: Call Aruba API
    data = await call_aruba_api("/network-monitoring/v1alpha1/site-firewall-sessions", params=params)

    # Step 3: Extract session data
    sessions = data.get("items", [])
    total = data.get("total", len(sessions))

    if not sessions:
        return [TextContent(type="text", text="[INFO] No firewall sessions found matching the specified criteria.")]

    # Step 4: Analyze sessions
    by_status = {}
    by_protocol = {}
    by_rule = {}
    blocked_sessions = []
    top_talkers = {}

    for session in sessions:
        status = session.get("status", "UNKNOWN")
        protocol = session.get("protocol", "UNKNOWN")
        rule = session.get("ruleName", "UNKNOWN")
        source_ip = session.get("sourceIp", "N/A")

        by_status[status] = by_status.get(status, 0) + 1
        by_protocol[protocol] = by_protocol.get(protocol, 0) + 1
        by_rule[rule] = by_rule.get(rule, 0) + 1

        # Track blocked sessions
        if status == "BLOCKED":
            blocked_sessions.append(session)

        # Track top talkers by source IP
        top_talkers[source_ip] = top_talkers.get(source_ip, 0) + 1

    # Step 5: Create session summary with verification guardrails
    summary_parts = []

    # Verification checkpoint FIRST
    summary_parts.append(
        VerificationGuards.checkpoint(
            {
                "Total sessions": f"{total} sessions",
                "Active": f"{by_status.get('ACTIVE', 0)} sessions",
                "Blocked": f"{len(blocked_sessions)} sessions",
            }
        )
    )

    summary_parts.append("\n[FW] Firewall Session Report")
    summary_parts.append(f"\n[STATS] Total Sessions: {total} (showing {len(sessions)})")

    # Status breakdown
    summary_parts.append("\n[STATUS] By Status (session counts):")
    for status, count in by_status.items():
        status_label = {"ACTIVE": "[OK]", "CLOSED": "[CLOSED]", "BLOCKED": "[BLOCKED]"}.get(status, "[--]")
        summary_parts.append(f"  {status_label} {status}: {count} sessions")

    # Protocol breakdown
    summary_parts.append("\n[PROTO] By Protocol:")
    for protocol, count in sorted(by_protocol.items(), key=lambda x: x[1], reverse=True):
        protocol_label = {"TCP": "[TCP]", "UDP": "[UDP]", "ICMP": "[ICMP]"}.get(protocol, "[NET]")
        summary_parts.append(f"  {protocol_label} {protocol}: {count} sessions")

    # Top firewall rules
    summary_parts.append("\n[RULES] Top Firewall Rules:")
    for rule, count in sorted(by_rule.items(), key=lambda x: x[1], reverse=True)[:5]:
        summary_parts.append(f"  * {rule}: {count} sessions")

    # Blocked traffic analysis
    if blocked_sessions:
        summary_parts.append(f"\n[BLOCKED] Blocked Traffic ({len(blocked_sessions)} sessions):")

        # Show top 5 blocked
        for session in blocked_sessions[:5]:
            source_ip = session.get("sourceIp", "N/A")
            source_port = session.get("sourcePort", "N/A")
            dest_ip = session.get("destinationIp", "N/A")
            dest_port = session.get("destinationPort", "N/A")
            protocol = session.get("protocol", "N/A")
            rule = session.get("ruleName", "N/A")
            app = session.get("application", "Unknown")

            summary_parts.append(f"\n  [BLOCKED] {source_ip}:{source_port} -> {dest_ip}:{dest_port} ({protocol})")
            summary_parts.append(f"    [RULE] {rule} | App: {app}")

    # Top talkers
    if top_talkers:
        summary_parts.append("\n[TOP] Top Source IPs:")
        for ip, count in sorted(top_talkers.items(), key=lambda x: x[1], reverse=True)[:5]:
            summary_parts.append(f"  * {ip}: {count} sessions")

    # Security insights
    blocked_count = by_status.get("BLOCKED", 0)
    active_count = by_status.get("ACTIVE", 0)

    summary_parts.append("\n[INFO] Insights:")

    if blocked_count > 0:
        block_rate = (blocked_count / total) * 100
        if block_rate > 50:
            summary_parts.append(f"  [WARN] High block rate ({block_rate:.1f}%) - review firewall rules")
        elif block_rate > 20:
            summary_parts.append(f"  [OK] Moderate blocking ({block_rate:.1f}%) - normal activity")
        else:
            summary_parts.append(f"  [OK] Low block rate ({block_rate:.1f}%) - mostly allowed traffic")

    if active_count > 100:
        summary_parts.append("  [INFO] High session count - busy network traffic")

    # Anti-hallucination footer
    summary_parts.append(
        VerificationGuards.anti_hallucination_footer(
            {
                "Total sessions": total,
                "Active": active_count,
                "Blocked": blocked_count,
            }
        )
    )

    summary = "\n".join(summary_parts)

    # Step 6: Store facts and return summary (NO raw JSON)
    store_facts(
        "get_firewall_sessions",
        {
            "Total sessions": total,
            "Active": active_count,
            "Blocked": blocked_count,
        },
    )

    return [TextContent(type="text", text=summary)]
