"""
List IDPS Threats - MCP tools for IDPS threats listing in Aruba Central
"""

import logging
from typing import Any

from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")

async def handle_list_idps_threats(args: dict[str, Any]) -> list[TextContent]:
    """Tool 27: List IDPS Threats - /network-monitoring/v1alpha1/threats"""

    # Step 1: Build query parameters
    params = {}

    if "severity" in args:
        params["severity"] = args["severity"]
    if "gateway_serial" in args:
        params["gatewaySerial"] = args["gateway_serial"]
    if "start_time" in args:
        params["startTime"] = args["start_time"]
    if "end_time" in args:
        params["endTime"] = args["end_time"]
    if "limit" in args:
        params["limit"] = args["limit"]

    # Step 2: Call Aruba API
    data = await call_aruba_api(
        "/network-monitoring/v1alpha1/threats",
        params=params
    )

    # Step 3: Extract threat data
    threats = data.get("items", [])
    total = data.get("total", len(threats))

    if not threats:
        return [TextContent(
            type="text",
            text="[OK] No security threats detected in the specified time period."
        )]

    # Step 4: Analyze threats
    by_severity = {}
    by_type = {}
    by_action = {}
    recent_threats = []

    for threat in threats:
        severity = threat.get("severity", "UNKNOWN")
        threat_type = threat.get("threatType", "UNKNOWN")
        action = threat.get("action", "UNKNOWN")

        by_severity[severity] = by_severity.get(severity, 0) + 1
        by_type[threat_type] = by_type.get(threat_type, 0) + 1
        by_action[action] = by_action.get(action, 0) + 1

        # Track recent critical/high threats
        if severity in ["CRITICAL", "HIGH"]:
            recent_threats.append(threat)

    # Step 5: Create threat summary with verification guardrails
    summary_parts = []
    
    # Verification checkpoint FIRST
    summary_parts.append(VerificationGuards.checkpoint({
        "Total threats": f"{total} threats",
        "Critical": f"{by_severity.get('CRITICAL', 0)} threats",
        "High": f"{by_severity.get('HIGH', 0)} threats",
        "Blocked": f"{by_action.get('BLOCKED', 0)} threats",
    }))
    
    summary_parts.append("\n[SEC] Security Threat Report")
    summary_parts.append(f"\n[STATS] Total Threats: {total} (showing {len(threats)})")

    # Severity breakdown
    summary_parts.append("\n[SEV] By Severity (threat counts):")
    severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    for sev in severity_order:
        count = by_severity.get(sev, 0)
        if count > 0:
            label = {
                "CRITICAL": "[CRIT]",
                "HIGH": "[HIGH]",
                "MEDIUM": "[MED]",
                "LOW": "[LOW]"
            }.get(sev, "[--]")
            summary_parts.append(f"  {label} {sev}: {count} threats")

    # Type breakdown
    summary_parts.append("\n[TYPE] By Type:")
    for threat_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:5]:
        summary_parts.append(f"  * {threat_type}: {count} threats")

    # Action breakdown
    summary_parts.append("\n[ACT] Mitigation Actions:")
    for action, count in by_action.items():
        action_label = {
            "BLOCKED": "[BLOCKED]",
            "ALLOWED": "[ALLOWED]",
            "LOGGED": "[LOGGED]"
        }.get(action, "[--]")
        summary_parts.append(f"  {action_label} {action}: {count} threats")

    # Recent critical/high threats
    if recent_threats:
        summary_parts.append("\n[CRIT] Recent Critical/High Threats (top 5):")
        for threat in recent_threats[:5]:
            threat_name = threat.get("threatName", "Unknown")
            severity = threat.get("severity", "UNKNOWN")
            source_ip = threat.get("sourceIp", "N/A")
            dest_ip = threat.get("destinationIp", "N/A")
            timestamp = threat.get("timestamp", "N/A")
            action = threat.get("action", "N/A")

            severity_label = "[CRIT]" if severity == "CRITICAL" else "[HIGH]"

            summary_parts.append(f"\n  {severity_label} {threat_name} ({severity})")
            summary_parts.append(f"    {source_ip} -> {dest_ip}")
            summary_parts.append(f"    [TIME] {timestamp} | Action: {action}")

    # Security posture assessment
    critical_count = by_severity.get("CRITICAL", 0)
    high_count = by_severity.get("HIGH", 0)
    blocked_count = by_action.get("BLOCKED", 0)

    summary_parts.append("\n[STATS] Security Posture:")

    if critical_count > 0:
        summary_parts.append(f"  [CRIT] {critical_count} critical threats require immediate attention!")

    if high_count > 5:
        summary_parts.append(f"  [WARN] {high_count} high-severity threats detected")

    if total > 0:
        block_rate = (blocked_count / total) * 100
        if block_rate > 90:
            summary_parts.append(f"  [OK] Excellent threat mitigation - {block_rate:.1f}% blocked")
        elif block_rate > 70:
            summary_parts.append(f"  [OK] Good threat mitigation - {block_rate:.1f}% blocked")
        else:
            summary_parts.append(f"  [WARN] Review mitigation policies - only {block_rate:.1f}% blocked")

    # Anti-hallucination footer
    summary_parts.append(VerificationGuards.anti_hallucination_footer({
        "Total threats": total,
        "Critical": critical_count,
        "High": high_count,
        "Blocked": blocked_count,
    }))

    summary = "\n".join(summary_parts)

    # Step 6: Store facts and return summary (NO raw JSON)
    store_facts("list_idps_threats", {
        "Total threats": total,
        "Critical": critical_count,
        "High": high_count,
        "Blocked": blocked_count,
    })
    
    return [TextContent(type="text", text=summary)]
