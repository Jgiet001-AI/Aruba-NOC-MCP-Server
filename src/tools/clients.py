"""
Clients - MCP tools for wireless client management in Aruba Central
"""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..config import ArubaConfig
from ..api_client import call_aruba_api
from .base import paginated_params, build_filter_params

logger = logging.getLogger("aruba-noc-server")


def register(mcp: FastMCP, config: ArubaConfig):
    """Register client-related tools with the MCP server"""

    @mcp.tool()
    async def list_clients(
        site: str | None = None,
        group: str | None = None,
        label: str | None = None,
        network: str | None = None,
        os_type: str | None = None,
        connection_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List wireless clients from Aruba Central.

        Args:
            site: Filter by site name
            group: Filter by group name
            label: Filter by label
            network: Filter by network/SSID
            os_type: Filter by client OS type
            connection_type: Filter by connection type (wired, wireless)
            limit: Maximum number of clients to return
            offset: Pagination offset

        Returns:
            Dictionary containing client list and metadata
        """
        params = build_filter_params(
            paginated_params(limit, offset),
            site=site,
            group=group,
            label=label,
            network=network,
            os_type=os_type,
            connection_type=connection_type,
        )
        return await call_aruba_api(config, "/monitoring/v1/clients", params=params)

    @mcp.tool()
    async def get_client(client_mac: str) -> dict[str, Any]:
        """
        Get details for a specific client by MAC address.

        Args:
            client_mac: MAC address of the client

        Returns:
            Client details dictionary
        """
        return await call_aruba_api(config, f"/monitoring/v1/clients/{client_mac}")

    @mcp.tool()
    async def get_client_count(
        site: str | None = None,
        group: str | None = None,
    ) -> dict[str, Any]:
        """
        Get client count summary.

        Args:
            site: Optional filter by site name
            group: Optional filter by group name

        Returns:
            Client count metrics
        """
        params = build_filter_params({}, site=site, group=group)
        return await call_aruba_api(
            config, "/monitoring/v1/clients/count", params=params
        )

    @mcp.tool()
    async def get_client_bandwidth(
        client_mac: str,
        duration: str = "3h",
    ) -> dict[str, Any]:
        """
        Get bandwidth usage for a specific client.

        Args:
            client_mac: MAC address of the client
            duration: Time duration (e.g., 3h, 1d, 7d)

        Returns:
            Client bandwidth metrics
        """
        params = {"duration": duration}
        return await call_aruba_api(
            config, f"/monitoring/v1/clients/{client_mac}/bandwidth", params=params
        )

    @mcp.tool()
    async def get_wireless_clients_summary(
        site: str | None = None,
        duration: str = "3h",
    ) -> dict[str, Any]:
        """
        Get wireless clients summary with connection statistics.

        Args:
            site: Optional filter by site name
            duration: Time duration (e.g., 3h, 1d, 7d)

        Returns:
            Wireless clients summary
        """
        params = build_filter_params({"duration": duration}, site=site)
        return await call_aruba_api(
            config, "/monitoring/v1/clients/wireless/summary", params=params
        )
