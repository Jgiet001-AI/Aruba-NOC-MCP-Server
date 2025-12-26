"""
Sites - MCP tools for site management in Aruba Central
"""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..config import ArubaConfig
from ..api_client import call_aruba_api
from .base import paginated_params, build_filter_params

logger = logging.getLogger("aruba-noc-server")


def register(mcp: FastMCP, config: ArubaConfig):
    """Register site-related tools with the MCP server"""

    @mcp.tool()
    async def list_sites(
        calculate_total: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List all sites from Aruba Central.

        Args:
            calculate_total: Include total count in response
            limit: Maximum number of sites to return
            offset: Pagination offset

        Returns:
            Dictionary containing site list and metadata
        """
        params = build_filter_params(
            paginated_params(limit, offset),
            calculate_total=calculate_total,
        )
        return await call_aruba_api(config, "/central/v2/sites", params=params)

    @mcp.tool()
    async def get_site(site_id: str) -> dict[str, Any]:
        """
        Get details for a specific site.

        Args:
            site_id: ID of the site

        Returns:
            Site details dictionary
        """
        return await call_aruba_api(config, f"/central/v2/sites/{site_id}")

    @mcp.tool()
    async def get_site_devices(
        site_id: str,
        device_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get all devices at a specific site.

        Args:
            site_id: ID of the site
            device_type: Optional filter by device type
            limit: Maximum number of devices to return
            offset: Pagination offset

        Returns:
            List of devices at the site
        """
        params = build_filter_params(
            paginated_params(limit, offset),
            device_type=device_type,
        )
        return await call_aruba_api(
            config, f"/central/v2/sites/{site_id}/devices", params=params
        )

    @mcp.tool()
    async def get_site_health(site_id: str) -> dict[str, Any]:
        """
        Get health summary for a specific site.

        Args:
            site_id: ID of the site

        Returns:
            Site health metrics
        """
        return await call_aruba_api(config, f"/central/v2/sites/{site_id}/health")
