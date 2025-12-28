"""
Get Stack Members - MCP tools for stack members retrieval in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import VerificationGuards
from src.tools.verify_facts import store_facts

logger = logging.getLogger("aruba-noc-server")


async def handle_get_stack_members(args: dict[str, Any]) -> list[TextContent]:
    """Tool 29: Get Stack Members - /network-monitoring/v1alpha1/stack/{stack-id}/members"""

    # Step 1: Validate required parameter
    stack_id = args.get("stack_id")

    if not stack_id:
        return [TextContent(type="text", text="[ERR] Parameter 'stack_id' is required. Provide the stack identifier.")]

    # Step 2: Call Aruba API
    try:
        data = await call_aruba_api(f"/network-monitoring/v1alpha1/stack/{stack_id}/members")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [TextContent(type="text", text=f"[ERR] Stack '{stack_id}' not found. Verify the stack ID or name.")]
        raise

    # Step 3: Extract stack member data
    members = data.get("members", [])
    stack_name = data.get("stackName", stack_id)
    stack_status = data.get("stackStatus", "UNKNOWN")

    if not members:
        return [TextContent(type="text", text=f"[INFO] Stack '{stack_name}' has no members (empty stack).")]

    # Step 4: Analyze stack topology
    commander = None
    standby = None
    regular_members = []
    total_members = len(members)
    up_members = 0
    down_members = 0

    for member in members:
        role = member.get("role", "UNKNOWN")
        status = member.get("status", "UNKNOWN")

        if status == "UP":
            up_members += 1
        else:
            down_members += 1

        if role == "COMMANDER":
            commander = member
        elif role == "STANDBY":
            standby = member
        else:
            regular_members.append(member)

    # Step 5: Create stack topology summary with verification guardrails
    summary_parts = []
    
    # Verification checkpoint FIRST
    summary_parts.append(VerificationGuards.checkpoint({
        "Total members": f"{total_members} members",
        "Members UP": f"{up_members} members",
        "Members DOWN": f"{down_members} members",
    }))
    
    summary_parts.append("\n[STACK] Switch Stack Topology")
    summary_parts.append(f"\n[NAME] Stack: {stack_name}")
    summary_parts.append(f"[STATUS] Status: {stack_status}")
    summary_parts.append(f"\n[MEMBERS] Members: {total_members} total ({up_members} UP, {down_members} DOWN)")

    # Commander details
    if commander:
        summary_parts.append("\n[PRIMARY] Commander:")
        summary_parts.append(f"  [POS] Position: {commander.get('stackPosition', 'N/A')}")
        summary_parts.append(f"  [NAME] Name: {commander.get('deviceName', 'N/A')}")
        summary_parts.append(f"  [SERIAL] Serial: {commander.get('serialNumber', 'N/A')}")
        summary_parts.append(f"  [MODEL] Model: {commander.get('model', 'N/A')}")
        summary_parts.append(f"  [FW] Version: {commander.get('swVersion', 'N/A')}")
        summary_parts.append(f"  [UP] Status: {commander.get('status', 'N/A')}")

    # Standby details
    if standby:
        summary_parts.append("\n[STANDBY] Standby:")
        summary_parts.append(f"  [POS] Position: {standby.get('stackPosition', 'N/A')}")
        summary_parts.append(f"  [NAME] Name: {standby.get('deviceName', 'N/A')}")
        summary_parts.append(f"  [SERIAL] Serial: {standby.get('serialNumber', 'N/A')}")
        summary_parts.append(f"  [MODEL] Model: {standby.get('model', 'N/A')}")
        summary_parts.append(f"  [FW] Version: {standby.get('swVersion', 'N/A')}")
        summary_parts.append(f"  [UP] Status: {standby.get('status', 'N/A')}")

    # Regular members
    if regular_members:
        summary_parts.append(f"\n[MEMBER] Members ({len(regular_members)}):")
        for member in regular_members:
            pos = member.get("stackPosition", "?")
            name = member.get("deviceName", "Unknown")
            status = member.get("status", "UNKNOWN")
            model = member.get("model", "N/A")

            status_label = "[UP]" if status == "UP" else "[DN]"

            summary_parts.append(f"  {status_label} Pos {pos}: {name} ({model}) - {status}")

    # Health assessment
    summary_parts.append("\n[HEALTH] Stack Health:")

    if down_members == 0:
        summary_parts.append("  [OK] All members operational")
    else:
        summary_parts.append(f"  [WARN] {down_members} member(s) DOWN - degraded stack")

    if not commander:
        summary_parts.append("  [CRIT] No commander detected - stack election issue!")

    if not standby and total_members > 1:
        summary_parts.append("  [WARN] No standby configured - no redundancy")

    # Version consistency check
    versions = {member.get("swVersion", "N/A") for member in members}
    if len(versions) > 1:
        summary_parts.append("  [WARN] Mixed software versions detected - recommend upgrade")
        summary_parts.append(f"     Versions: {', '.join(versions)}")
    else:
        summary_parts.append("  [OK] Consistent software version across stack")

    # Anti-hallucination footer
    summary_parts.append(VerificationGuards.anti_hallucination_footer({
        "Total members": total_members,
        "Members UP": up_members,
        "Members DOWN": down_members,
    }))

    summary = "\n".join(summary_parts)

    # Step 6: Store facts and return summary (NO raw JSON)
    store_facts("get_stack_members", {
        "Stack": stack_name,
        "Total members": total_members,
        "Members UP": up_members,
        "Members DOWN": down_members,
    })
    
    return [TextContent(type="text", text=summary)]
