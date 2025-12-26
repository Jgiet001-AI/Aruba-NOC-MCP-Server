"""
Tests for Site Tools
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from src.config import ArubaConfig


class TestListSites:
    """Test cases for list_sites tool"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock ArubaConfig"""
        config = MagicMock(spec=ArubaConfig)
        config.access_token = "test_token"
        config.base_url = "https://api.test.com"
        config.get_headers.return_value = {
            "Authorization": "Bearer test_token",
        }
        return config

    @pytest.mark.asyncio
    async def test_list_sites_calls_correct_endpoint(self, mock_config):
        """Test that list_sites calls the correct API endpoint"""
        with patch("src.api_client.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"sites": [], "total": 0}

            from src.tools import sites
            from mcp.server.fastmcp import FastMCP

            mcp = MagicMock(spec=FastMCP)
            registered_tools = {}

            def mock_tool():
                def decorator(func):
                    registered_tools[func.__name__] = func
                    return func
                return decorator

            mcp.tool = mock_tool
            sites.register(mcp, mock_config)

            # Call the registered tool
            result = await registered_tools["list_sites"]()

            mock_api.assert_called_once()
            call_args = mock_api.call_args
            assert "/central/v2/sites" in str(call_args)


class TestGetSite:
    """Test cases for get_site tool"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock ArubaConfig"""
        config = MagicMock(spec=ArubaConfig)
        config.access_token = "test_token"
        config.base_url = "https://api.test.com"
        config.get_headers.return_value = {
            "Authorization": "Bearer test_token",
        }
        return config

    @pytest.mark.asyncio
    async def test_get_site_includes_site_id_in_path(self, mock_config):
        """Test that get_site includes site_id in the API path"""
        with patch("src.api_client.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"site_id": "123", "name": "HQ"}

            from src.tools import sites
            from mcp.server.fastmcp import FastMCP

            mcp = MagicMock(spec=FastMCP)
            registered_tools = {}

            def mock_tool():
                def decorator(func):
                    registered_tools[func.__name__] = func
                    return func
                return decorator

            mcp.tool = mock_tool
            sites.register(mcp, mock_config)

            # Call the registered tool with a site_id
            await registered_tools["get_site"](site_id="123")

            mock_api.assert_called_once()
            call_args = mock_api.call_args
            assert "123" in str(call_args)


class TestGetSiteDevices:
    """Test cases for get_site_devices tool"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock ArubaConfig"""
        config = MagicMock(spec=ArubaConfig)
        config.access_token = "test_token"
        config.base_url = "https://api.test.com"
        config.get_headers.return_value = {
            "Authorization": "Bearer test_token",
        }
        return config

    @pytest.mark.asyncio
    async def test_get_site_devices_with_filter(self, mock_config):
        """Test that get_site_devices applies device_type filter"""
        with patch("src.api_client.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"devices": []}

            from src.tools import sites
            from mcp.server.fastmcp import FastMCP

            mcp = MagicMock(spec=FastMCP)
            registered_tools = {}

            def mock_tool():
                def decorator(func):
                    registered_tools[func.__name__] = func
                    return func
                return decorator

            mcp.tool = mock_tool
            sites.register(mcp, mock_config)

            # Call with device_type filter
            await registered_tools["get_site_devices"](
                site_id="123",
                device_type="ap",
            )

            mock_api.assert_called_once()
            call_args = mock_api.call_args
            # Verify the params include device_type
            assert "device_type" in str(call_args)
