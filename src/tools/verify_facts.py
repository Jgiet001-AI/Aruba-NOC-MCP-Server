"""
Verify Facts - A verification tool that must be called before making claims

This tool provides a structured way for the LLM to verify facts from previous
tool calls before reporting them to the user. It helps prevent hallucinations
by requiring explicit fact verification.
"""

import logging
from typing import Any

from mcp.types import TextContent

logger = logging.getLogger("aruba-noc-server")


# In-memory fact store (stores facts from the most recent tool calls)
_fact_store: dict[str, Any] = {}


def store_facts(tool_name: str, facts: dict[str, Any]) -> None:
    """
    Store verified facts from a tool call.
    
    Called by other tools to register their key facts for verification.
    
    Args:
        tool_name: Name of the tool that generated the facts
        facts: Dictionary of fact_name -> fact_value pairs
    """
    _fact_store[tool_name] = {
        "facts": facts,
        "verified": False,
    }


def get_stored_facts() -> dict[str, Any]:
    """Get all stored facts from previous tool calls."""
    return _fact_store.copy()


def clear_facts() -> None:
    """Clear all stored facts (called after verification or new session)."""
    _fact_store.clear()


async def handle_verify_facts(args: dict[str, Any]) -> list[TextContent]:
    """
    Verify Facts Tool - Must be called before making claims about data
    
    This tool returns all verified facts from previous tool calls.
    The LLM MUST call this tool and cite the returned facts before
    making any claims to the user.
    
    Args:
        tool_name: (optional) Specific tool to verify facts from
        
    Returns:
        Formatted list of verified facts that can be safely cited
    """
    tool_name = args.get("tool_name")
    
    if not _fact_store:
        return [TextContent(
            type="text",
            text=(
                "[VERIFICATION ERROR]\n"
                "No facts available to verify.\n"
                "You must call a data-gathering tool first before verification."
            )
        )]
    
    lines = []
    lines.append("=" * 60)
    lines.append("[VERIFIED FACTS - Safe to cite to user]")
    lines.append("=" * 60)
    
    if tool_name and tool_name in _fact_store:
        # Verify facts from specific tool
        facts = _fact_store[tool_name]["facts"]
        _fact_store[tool_name]["verified"] = True
        lines.append(f"\nFrom {tool_name}:")
        for name, value in facts.items():
            lines.append(f"  ✓ {name}: {value}")
    else:
        # Verify all facts
        for source_tool, data in _fact_store.items():
            data["verified"] = True
            lines.append(f"\nFrom {source_tool}:")
            for name, value in data["facts"].items():
                lines.append(f"  ✓ {name}: {value}")
    
    lines.append("")
    lines.append("=" * 60)
    lines.append("[INSTRUCTIONS FOR LLM]")
    lines.append("1. ONLY cite the facts listed above")
    lines.append("2. Do NOT calculate or derive new numbers")
    lines.append("3. Do NOT estimate or approximate")
    lines.append("4. If asked about something not listed, say 'I need to query that data'")
    lines.append("=" * 60)
    
    return [TextContent(type="text", text="\n".join(lines))]
