"""
Gateways - MCP tools for gateway management in Aruba Central
"""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..config import ArubaConfig
from ..api_client import call_aruba_api
from .base import paginated_params, build_filter_params

logger = logging.getLogger("aruba-noc-server")


def register(mcp: FastMCP, config: ArubaConfig):
    """Register gateway-related tools with the MCP server"""

    @mcp.tool()
    async def list_gateways(
        site: str | None = None,
        group: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List all gateways from Aruba Central.

        Args:
            site: Filter by site name
            group: Filter by group name
            status: Filter by status (up, down)
            limit: Maximum number of gateways to return
            offset: Pagination offset

        Returns:
            Dictionary containing gateway list and metadata
        """
        params = build_filter_params(
            paginated_params(limit, offset),
            site=site,
            group=group,
            status=status,
        )
        return await call_aruba_api(config, "/monitoring/v2/gateways", params=params)

    @mcp.tool()
    async def get_gateway(gateway_serial: str) -> dict[str, Any]:
        """
        Get details for a specific gateway.

        Args:
            gateway_serial: Serial number of the gateway

        Returns:
            Gateway details dictionary
        """
        return await call_aruba_api(
            config, f"/monitoring/v1/gateways/{gateway_serial}"
        )

    @mcp.tool()
    async def get_gateway_uplinks(gateway_serial: str) -> dict[str, Any]:
        """
        Get uplink information for a specific gateway.

        Args:
            gateway_serial: Serial number of the gateway

        Returns:
            Gateway uplink details
        """
        return await call_aruba_api(
            config, f"/monitoring/v1/gateways/{gateway_serial}/uplinks"
        )

    @mcp.tool()
    async def get_gateway_tunnels(gateway_serial: str) -> dict[str, Any]:
        """
        Get VPN tunnel information for a specific gateway.

        Args:
            gateway_serial: Serial number of the gateway

        Returns:
            Gateway tunnel details
        """
        return await call_aruba_api(
            config, f"/monitoring/v1/gateways/{gateway_serial}/tunnels"
        )

    @mcp.tool()
    async def get_gateway_health(gateway_serial: str) -> dict[str, Any]:
        """
        Get health metrics for a specific gateway.

        Args:
            gateway_serial: Serial number of the gateway

        Returns:
            Gateway health metrics
        """
        return await call_aruba_api(
            config, f"/monitoring/v1/gateways/{gateway_serial}/health"
        )

    @mcp.tool()
    async def get_gateway_stats(
        gateway_serial: str,
        duration: str = "3h",
    ) -> dict[str, Any]:
        """
        Get statistics for a specific gateway.

        Args:
            gateway_serial: Serial number of the gateway
            duration: Time duration (e.g., 3h, 1d, 7d)

        Returns:
            Gateway statistics
        """
        params = {"duration": duration}
        return await call_aruba_api(
            config, f"/monitoring/v1/gateways/{gateway_serial}/stats", params=params
        )
