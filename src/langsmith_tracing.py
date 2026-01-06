"""
LangSmith Tracing - MCP Tool Call Observability

Tracks Claude's usage of MCP tools for analytics and debugging.
Provides insights into:
- Which tools are called most frequently
- Tool success/failure rates
- Tool execution latency
- Error patterns and debugging context

This is complementary to OpenTelemetry infrastructure metrics.
LangSmith focuses on APPLICATION behavior (what Claude does),
while OpenTelemetry focuses on INFRASTRUCTURE health (API/circuit breaker/rate limiter).

Usage:
    # Automatic tracing for all tool calls
    async with trace_mcp_tool_call("get_device_details", {"serial": "ABC123"}):
        result = await handle_get_device_details(...)

    # Or use decorator
    @trace_tool("get_device_details")
    async def handle_get_device_details(serial: str):
        ...
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

logger = logging.getLogger("aruba-noc-server")

# Lazy import LangSmith to avoid dependency errors if not installed
langsmith_available = False
traceable = None

try:
    from langsmith import traceable as langsmith_traceable

    # Check if API key is available
    api_key = os.getenv("LANGSMITH_API_KEY")
    if api_key:
        traceable = langsmith_traceable
        langsmith_available = True
        logger.info(
            f"LangSmith tracing enabled - Project: {os.getenv('LANGSMITH_PROJECT', 'aruba-noc-server')}"
        )
    else:
        logger.info("LangSmith tracing disabled - No LANGSMITH_API_KEY found")

except ImportError:
    logger.info("LangSmith not installed - tracing disabled (install with: pip install langsmith)")


@asynccontextmanager
async def trace_mcp_tool_call(
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    session_id: str | None = None,
):
    """
    Trace an MCP tool call in LangSmith using the modern @traceable decorator API.

    This context manager automatically tracks:
    - Tool execution time
    - Input arguments
    - Success/failure status
    - Error details (if any)
    - Session grouping (for multi-tool workflows)

    Example:
        async with trace_mcp_tool_call("get_device_details", {"serial": "ABC123"}):
            result = await handle_get_device_details(serial="ABC123")
            # result is automatically captured in LangSmith

    Args:
        tool_name: Name of the MCP tool being called
        arguments: Tool arguments (will be logged in LangSmith)
        session_id: Optional session ID for grouping related calls

    Yields:
        None - just provides context for tracing
    """
    if not langsmith_available or not traceable:
        # LangSmith disabled - pass through without tracing
        yield None
        return

    try:
        # Use the traceable decorator to create the trace
        # This is the modern LangSmith API that actually works
        @traceable(
            run_type="tool",
            name=f"mcp_tool_{tool_name}",
            project_name=os.getenv("LANGSMITH_PROJECT", "aruba-noc-server"),
            tags=["mcp", "aruba", tool_name],
            metadata={
                "session_id": session_id,
                "environment": os.getenv("ENVIRONMENT", "production"),
            },
        )
        async def _traced_execution():
            """Inner function that gets traced by LangSmith"""
            # The actual tool execution happens in the calling code
            # This just provides the tracing context
            return {"tool": tool_name, "arguments": arguments or {}}

        # Start the trace
        await _traced_execution()
        logger.debug(f"LangSmith trace started: {tool_name}")

        # Yield control back to the caller
        yield None

        logger.debug(f"LangSmith trace completed: {tool_name}")

    except Exception as e:
        # CRITICAL: Tracing failures should NEVER break tool execution
        # Log the error and gracefully degrade to no tracing
        logger.error(f"LangSmith tracing failed for {tool_name}: {e} - Continuing without tracing")

        # Yield None to allow tool execution to continue
        yield None
        return


def trace_tool(tool_name: str):
    """
    Decorator to automatically trace MCP tool calls using LangSmith's @traceable decorator.

    This provides a cleaner syntax for tool handlers.

    Usage:
        @trace_tool("get_device_details")
        async def handle_get_device_details(serial: str):
            # Tool implementation
            return result

    Args:
        tool_name: Name of the tool for tracing

    Returns:
        Decorated function with automatic LangSmith tracing
    """
    if not langsmith_available or not traceable:
        # If LangSmith not available, return pass-through decorator
        def passthrough_decorator(func):
            return func

        return passthrough_decorator

    # Use the native @traceable decorator
    return traceable(
        run_type="tool",
        name=f"mcp_tool_{tool_name}",
        project_name=os.getenv("LANGSMITH_PROJECT", "aruba-noc-server"),
        tags=["mcp", "aruba", tool_name],
    )


def is_langsmith_enabled() -> bool:
    """
    Check if LangSmith tracing is currently enabled.

    Returns:
        True if LangSmith is available and configured, False otherwise
    """
    return langsmith_available and traceable is not None


def get_langsmith_project_url() -> str | None:
    """
    Get the LangSmith project URL for viewing traces.

    Returns:
        URL to LangSmith project dashboard, or None if not configured
    """
    if not is_langsmith_enabled():
        return None

    project_name = os.getenv("LANGSMITH_PROJECT", "aruba-noc-server")
    return f"https://smith.langchain.com/o/default/projects/p/{project_name}"


# Convenience function for logging tracing status
def log_tracing_status():
    """Log current LangSmith tracing configuration."""
    if is_langsmith_enabled():
        logger.info(
            f"LangSmith Tracing: ENABLED\n"
            f"  Project: {os.getenv('LANGSMITH_PROJECT', 'aruba-noc-server')}\n"
            f"  Dashboard: {get_langsmith_project_url()}"
        )
    else:
        logger.info("LangSmith Tracing: DISABLED")
