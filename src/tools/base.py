"""
Base - Shared tool patterns and utilities for Aruba Central MCP tools
"""

import logging
from typing import Any, Callable, TypeVar
from functools import wraps

from mcp.server.fastmcp import FastMCP

from ..config import ArubaConfig
from ..api_client import call_aruba_api

logger = logging.getLogger("aruba-noc-server")

T = TypeVar("T")


def with_error_handling(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to add standardized error handling to tool functions"""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            return {"error": str(e), "success": False}

    return wrapper


def paginated_params(
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Build standard pagination parameters"""
    return {"limit": limit, "offset": offset}


def build_filter_params(
    base_params: dict[str, Any],
    **filters: Any,
) -> dict[str, Any]:
    """Build parameters with optional filters, excluding None values"""
    params = base_params.copy()
    for key, value in filters.items():
        if value is not None:
            params[key] = value
    return params


class ToolRegistry:
    """Registry for managing MCP tool registration"""

    def __init__(self, mcp: FastMCP, config: ArubaConfig):
        self.mcp = mcp
        self.config = config
        self._registered_tools: list[str] = []

    def register(self, func: Callable) -> Callable:
        """Register a function as an MCP tool"""
        decorated = self.mcp.tool()(func)
        self._registered_tools.append(func.__name__)
        logger.debug(f"Registered tool: {func.__name__}")
        return decorated

    @property
    def registered_tools(self) -> list[str]:
        """Get list of registered tool names"""
        return self._registered_tools.copy()
