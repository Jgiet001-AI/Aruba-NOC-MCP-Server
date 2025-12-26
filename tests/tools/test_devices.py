"""
Tests for Device Tools
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from src.config import ArubaConfig
from src.tools.base import paginated_params, build_filter_params


class TestDeviceToolHelpers:
    """Test helper functions used by device tools"""

    def test_paginated_params_defaults(self):
        """Test default pagination parameters"""
        params = paginated_params()
        assert params == {"limit": 100, "offset": 0}

    def test_paginated_params_custom(self):
        """Test custom pagination parameters"""
        params = paginated_params(limit=50, offset=100)
        assert params == {"limit": 50, "offset": 100}

    def test_build_filter_params_excludes_none(self):
        """Test that None values are excluded from filter params"""
        base = {"limit": 100}
        params = build_filter_params(
            base,
            device_type="ap",
            site=None,
            status="up",
        )
        assert params == {"limit": 100, "device_type": "ap", "status": "up"}
        assert "site" not in params

    def test_build_filter_params_all_values(self):
        """Test filter params with all values provided"""
        base = {"limit": 100, "offset": 0}
        params = build_filter_params(
            base,
            device_type="switch",
            site="main",
            group="production",
        )
        assert params == {
            "limit": 100,
            "offset": 0,
            "device_type": "switch",
            "site": "main",
            "group": "production",
        }


class TestListDevices:
    """Test cases for list_devices tool"""

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
    async def test_list_devices_calls_correct_endpoint(self, mock_config):
        """Test that list_devices calls the correct API endpoint"""
        with patch("src.api_client.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"devices": [], "total": 0}

            from src.tools import devices
            from mcp.server.fastmcp import FastMCP

            mcp = MagicMock(spec=FastMCP)
            registered_tools = {}

            def mock_tool():
                def decorator(func):
                    registered_tools[func.__name__] = func
                    return func
                return decorator

            mcp.tool = mock_tool
            devices.register(mcp, mock_config)

            # Call the registered tool
            result = await registered_tools["list_devices"]()

            mock_api.assert_called_once()
            call_args = mock_api.call_args
            assert "/monitoring/v2/devices" in str(call_args)


class TestGetDevice:
    """Test cases for get_device tool"""

    @pytest.mark.asyncio
    async def test_get_device_requires_serial(self):
        """Test that get_device requires a serial number"""
        # This test validates the function signature
        from src.tools import devices
        import inspect

        # Get the register function and verify it defines get_device properly
        source = inspect.getsource(devices.register)
        assert "device_serial: str" in source
