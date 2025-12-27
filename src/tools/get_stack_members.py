"""
Get Stack Members - MCP tools for stack members retrieval in Aruba Central
"""

import logging
from typing import Any

import httpx
from mcp.types import TextContent

from src.api_client import call_aruba_api
from src.tools.base import format_json

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

    # Step 5: Create stack topology summary
    summary = "[STACK] Switch Stack Topology\n"
    summary += f"\n[NAME] Stack: {stack_name}\n"
    summary += f"[STATUS] Status: {stack_status}\n"
    summary += f"\n[MEMBERS] Members: {total_members} total ({up_members} UP, {down_members} DOWN)\n"

    # Commander details
    if commander:
        summary += "\n[PRIMARY] Commander:\n"
        summary += f"  [POS] Position: {commander.get('stackPosition', 'N/A')}\n"
        summary += f"  [NAME] Name: {commander.get('deviceName', 'N/A')}\n"
        summary += f"  [SERIAL] Serial: {commander.get('serialNumber', 'N/A')}\n"
        summary += f"  [MODEL] Model: {commander.get('model', 'N/A')}\n"
        summary += f"  [FW] Version: {commander.get('swVersion', 'N/A')}\n"
        summary += f"  [UP] Status: {commander.get('status', 'N/A')}\n"

    # Standby details
    if standby:
        summary += "\n[STANDBY] Standby:\n"
        summary += f"  [POS] Position: {standby.get('stackPosition', 'N/A')}\n"
        summary += f"  [NAME] Name: {standby.get('deviceName', 'N/A')}\n"
        summary += f"  [SERIAL] Serial: {standby.get('serialNumber', 'N/A')}\n"
        summary += f"  [MODEL] Model: {standby.get('model', 'N/A')}\n"
        summary += f"  [FW] Version: {standby.get('swVersion', 'N/A')}\n"
        summary += f"  [UP] Status: {standby.get('status', 'N/A')}\n"

    # Regular members
    if regular_members:
        summary += f"\n[MEMBER] Members ({len(regular_members)}):\n"
        for member in regular_members:
            pos = member.get("stackPosition", "?")
            name = member.get("deviceName", "Unknown")
            status = member.get("status", "UNKNOWN")
            model = member.get("model", "N/A")

            status_label = "[UP]" if status == "UP" else "[DN]"

            summary += f"  {status_label} Pos {pos}: {name} ({model}) - {status}\n"

    # Health assessment
    summary += "\n[HEALTH] Stack Health:\n"

    if down_members == 0:
        summary += "  [OK] All members operational\n"
    else:
        summary += f"  [WARN] {down_members} member(s) DOWN - degraded stack\n"

    if not commander:
        summary += "  [CRIT] No commander detected - stack election issue!\n"

    if not standby and total_members > 1:
        summary += "  [WARN] No standby configured - no redundancy\n"

    # Version consistency check
    versions = {member.get("swVersion", "N/A") for member in members}
    if len(versions) > 1:
        summary += "  [WARN] Mixed software versions detected - recommend upgrade\n"
        summary += f"     Versions: {', '.join(versions)}\n"
    else:
        summary += "  [OK] Consistent software version across stack\n"

    # Step 6: Return formatted response
    return [TextContent(type="text", text=f"{summary}\n{format_json(data)}")]
