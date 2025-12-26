"""
Firmware - MCP tools for firmware management in Aruba Central
"""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..config import ArubaConfig
from ..api_client import call_aruba_api
from .base import paginated_params, build_filter_params

logger = logging.getLogger("aruba-noc-server")


def register(mcp: FastMCP, config: ArubaConfig):
    """Register firmware-related tools with the MCP server"""

    @mcp.tool()
    async def list_firmware_versions(
        device_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List available firmware versions.

        Args:
            device_type: Filter by device type (ap, switch, gateway)
            limit: Maximum number of versions to return
            offset: Pagination offset

        Returns:
            Dictionary containing firmware versions
        """
        params = build_filter_params(
            paginated_params(limit, offset),
            device_type=device_type,
        )
        return await call_aruba_api(config, "/firmware/v1/versions", params=params)

    @mcp.tool()
    async def get_device_firmware(device_serial: str) -> dict[str, Any]:
        """
        Get current firmware information for a specific device.

        Args:
            device_serial: Serial number of the device

        Returns:
            Device firmware details
        """
        return await call_aruba_api(
            config, f"/firmware/v1/devices/{device_serial}"
        )

    @mcp.tool()
    async def get_firmware_compliance(
        group: str | None = None,
        site: str | None = None,
    ) -> dict[str, Any]:
        """
        Get firmware compliance status across devices.

        Args:
            group: Optional filter by group name
            site: Optional filter by site name

        Returns:
            Firmware compliance summary
        """
        params = build_filter_params({}, group=group, site=site)
        return await call_aruba_api(
            config, "/firmware/v1/compliance", params=params
        )

    @mcp.tool()
    async def get_upgrade_status(
        task_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get status of firmware upgrade tasks.

        Args:
            task_id: Optional specific task ID to check
            limit: Maximum number of tasks to return
            offset: Pagination offset

        Returns:
            Firmware upgrade task status
        """
        if task_id:
            return await call_aruba_api(
                config, f"/firmware/v1/upgrade/status/{task_id}"
            )
        params = paginated_params(limit, offset)
        return await call_aruba_api(
            config, "/firmware/v1/upgrade/status", params=params
        )

    @mcp.tool()
    async def get_firmware_recommendations(
        device_type: str,
    ) -> dict[str, Any]:
        """
        Get recommended firmware versions for a device type.

        Args:
            device_type: Device type (ap, switch, gateway)

        Returns:
            Recommended firmware versions
        """
        params = {"device_type": device_type}
        return await call_aruba_api(
            config, "/firmware/v1/recommendations", params=params
        )
