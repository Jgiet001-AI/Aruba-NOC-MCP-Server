"""
Base Tool Handler - Consistent error handling and logging for all MCP tools

This module provides a base class that all tool handlers should inherit from.
It ensures consistent error handling, logging, and response formatting across
all tools in the Aruba NOC MCP Server.

Usage:
    class MyToolHandler(BaseToolHandler):
        def __init__(self):
            super().__init__("my_tool_name")

        async def execute(self, args: dict[str, Any]) -> list[TextContent]:
            # Your tool logic here
            return [TextContent(type="text", text="Result")]

    # Register handler
    handle_my_tool = MyToolHandler()
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx
from mcp.types import TextContent

from src.tools.base import StatusLabels

logger = logging.getLogger("aruba-noc-server")


class BaseToolHandler(ABC):
    """
    Base class for all MCP tool handlers.

    Provides:
    - Consistent error handling for HTTP errors
    - Structured logging
    - Timeout handling
    - User-friendly error messages

    Subclasses must implement the `execute()` method.
    """

    def __init__(self, tool_name: str):
        """
        Initialize the tool handler.

        Args:
            tool_name: Name of the tool (e.g., "get_device_list")
        """
        self.tool_name = tool_name
        self.logger = logging.getLogger(f"aruba-noc-server.{tool_name}")

    @abstractmethod
    async def execute(self, args: dict[str, Any]) -> list[TextContent]:
        """
        Execute the tool logic.

        Subclasses must implement this method with their specific logic.

        Args:
            args: Tool arguments from MCP client

        Returns:
            List of TextContent responses

        Raises:
            Any exceptions will be caught and handled by __call__
        """
        ...

    async def __call__(self, args: dict[str, Any]) -> list[TextContent]:
        """
        Handle tool execution with consistent error handling.

        This is called by the MCP server when the tool is invoked.
        It wraps the execute() method with error handling.

        Args:
            args: Tool arguments from MCP client

        Returns:
            List of TextContent responses
        """
        try:
            self.logger.info(f"Executing {self.tool_name}", extra={"args": args})
            result = await self.execute(args)
        except httpx.HTTPStatusError as e:
            self.logger.warning(
                f"{self.tool_name} HTTP error",
                extra={"status_code": e.response.status_code, "endpoint": str(e.request.url)},
            )
            return self._handle_http_error(e)

        except httpx.TimeoutException as e:
            self.logger.warning(f"{self.tool_name} request timed out", extra={"error": str(e)})
            return [
                TextContent(
                    type="text",
                    text=(
                        f"{StatusLabels.ERR} {self.tool_name}: Request timed out\n\n"
                        "The Aruba Central API did not respond in time. "
                        "This may indicate network issues or API overload. "
                        "Please retry in a few moments."
                    ),
                )
            ]

        except Exception as e:
            self.logger.exception(f"{self.tool_name} failed with unexpected error")
            return [
                TextContent(
                    type="text",
                    text=(
                        f"{StatusLabels.ERR} {self.tool_name} failed: {e!s}\n\n"
                        "An unexpected error occurred. Please check the logs for details."
                    ),
                )
            ]
        else:
            self.logger.info(f"{self.tool_name} completed successfully")
            return result

    def _handle_http_error(self, e: httpx.HTTPStatusError) -> list[TextContent]:
        """
        Handle HTTP errors with context-aware messages.

        Provides helpful guidance based on the specific HTTP status code.

        Args:
            e: The HTTP status error

        Returns:
            List containing error TextContent
        """
        status = e.response.status_code

        # Map status codes to user-friendly messages
        error_messages = {
            400: (
                "Bad request - parameters may be invalid or missing.\n\n"
                "Common causes:\n"
                "• Missing required time range parameters\n"
                "• Invalid filter syntax\n"
                "• Insufficient API scopes/permissions\n\n"
                "Check the API documentation for parameter requirements."
            ),
            401: (
                "Authentication failed - access token may be expired.\n\n"
                "The server will automatically refresh the token and retry. "
                "If this persists, check your OAuth2 credentials."
            ),
            403: (
                "Access denied - insufficient permissions.\n\n"
                "Your API application may not have the required scopes:\n"
                "• monitoring:read - For client/network monitoring\n"
                "• analytics:read - For bandwidth/usage analytics\n"
                "• security:read - For IDS/IPS and firewall data\n\n"
                "Add these scopes in: Aruba Central > API Gateway > My Apps & Tokens"
            ),
            404: (
                "Resource not found.\n\n"
                "Possible causes:\n"
                "• Invalid device serial number\n"
                "• Site ID does not exist\n"
                "• API endpoint not available in your region\n\n"
                "Verify the resource identifier and try again."
            ),
            429: (
                "Rate limit exceeded.\n\n"
                "You've made too many requests in a short time. "
                "Please wait 60 seconds and retry. "
                "Consider reducing request frequency or implementing caching."
            ),
            500: (
                "Aruba Central API server error.\n\n"
                "This is a temporary issue with the Aruba infrastructure. "
                "The request will automatically retry with exponential backoff. "
                "If the issue persists, contact Aruba support."
            ),
            503: (
                "Aruba Central API is temporarily unavailable.\n\n"
                "The API service may be undergoing maintenance. "
                "Please retry in a few minutes. "
                "Check https://status.arubanetworks.com for service status."
            ),
        }

        message = error_messages.get(status, f"HTTP {status} error - an unexpected status code was returned.")

        # Try to extract error details from response
        try:
            error_body = e.response.json()
            if "error_description" in error_body:
                message += f"\n\nAPI Details: {error_body['error_description']}"
            elif "message" in error_body:
                message += f"\n\nAPI Details: {error_body['message']}"
        except Exception:
            # Response body not JSON or missing error details
            pass

        return [
            TextContent(
                type="text",
                text=f"{StatusLabels.ERR} {self.tool_name}: {message}",
            )
        ]


# Example usage:
"""
from src.tools.base_handler import BaseToolHandler
from src.tools.base import extract_params
from src.api_client import call_aruba_api

class DeviceListHandler(BaseToolHandler):
    def __init__(self):
        super().__init__("get_device_list")

    async def execute(self, args: dict[str, Any]) -> list[TextContent]:
        # Extract and validate parameters
        params = extract_params(
            args,
            param_map={"site_id": "site-id"},
            defaults={"limit": 100}
        )

        # Call API
        data = await call_aruba_api("/network-monitoring/v1alpha1/devices", params=params)

        # Process response
        total = data.get("total", 0)
        items = data.get("items", [])

        # Build summary
        summary = f"Found {total} devices, showing {len(items)}"

        return [TextContent(type="text", text=summary)]

# Register handler
handle_get_device_list = DeviceListHandler()
"""
