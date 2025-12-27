"""
List IDPS Threats - MCP tools for IDPS threats listing in Aruba Central
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

    # Step 5: Create threat summary
    summary = "[SEC] Security Threat Report\n"
    summary += f"\n[STATS] Total Threats: {total} (showing {len(threats)})\n"

    # Severity breakdown
    summary += "\n[SEV] By Severity:\n"
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
            summary += f"  {label} {sev}: {count}\n"

    # Type breakdown
    summary += "\n[TYPE] By Type:\n"
    for threat_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:5]:
        summary += f"  * {threat_type}: {count}\n"

    # Action breakdown
    summary += "\n[ACT] Mitigation Actions:\n"
    for action, count in by_action.items():
        action_label = {
            "BLOCKED": "[BLOCKED]",
            "ALLOWED": "[ALLOWED]",
            "LOGGED": "[LOGGED]"
        }.get(action, "[--]")
        summary += f"  {action_label} {action}: {count}\n"

    # Recent critical/high threats
    if recent_threats:
        summary += "\n[CRIT] Recent Critical/High Threats (top 5):\n"
        for threat in recent_threats[:5]:
            threat_name = threat.get("threatName", "Unknown")
            severity = threat.get("severity", "UNKNOWN")
            source_ip = threat.get("sourceIp", "N/A")
            dest_ip = threat.get("destinationIp", "N/A")
            timestamp = threat.get("timestamp", "N/A")
            action = threat.get("action", "N/A")

            severity_label = "[CRIT]" if severity == "CRITICAL" else "[HIGH]"

            summary += f"\n  {severity_label} {threat_name} ({severity})\n"
            summary += f"    {source_ip} -> {dest_ip}\n"
            summary += f"    [TIME] {timestamp} | Action: {action}\n"

    # Security posture assessment
    critical_count = by_severity.get("CRITICAL", 0)
    high_count = by_severity.get("HIGH", 0)
    blocked_count = by_action.get("BLOCKED", 0)

    summary += "\n[STATS] Security Posture:\n"

    if critical_count > 0:
        summary += f"  [CRIT] {critical_count} critical threats require immediate attention!\n"

    if high_count > 5:
        summary += f"  [WARN] {high_count} high-severity threats detected\n"

    if total > 0:
        block_rate = (blocked_count / total) * 100
        if block_rate > 90:
            summary += f"  [OK] Excellent threat mitigation - {block_rate:.1f}% blocked\n"
        elif block_rate > 70:
            summary += f"  [OK] Good threat mitigation - {block_rate:.1f}% blocked\n"
        else:
            summary += f"  [WARN] Review mitigation policies - only {block_rate:.1f}% blocked\n"

    # Step 6: Return formatted response
    return [TextContent(
        type="text",
        text=f"{summary}\n{_format_json(data)}"
    )]
