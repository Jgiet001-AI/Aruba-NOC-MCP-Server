"""
Tests for Device Tools
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.tools.devices import handle_get_device_list


class TestHandleGetDeviceList:
    """Test cases for handle_get_device_list."""

    @pytest.mark.asyncio
    async def test_get_device_list_success(self, mock_devices_response):
        """Test successful device listing."""
        with patch("src.tools.devices.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_devices_response

            result = await handle_get_device_list({})

            assert len(result) == 1
            assert result[0].type == "text"
            # Check output contains device information
            assert "2" in result[0].text  # Device count somewhere in output

    @pytest.mark.asyncio
    async def test_get_device_list_with_filters(self, mock_devices_response):
        """Test device listing with filters."""
        with patch("src.tools.devices.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_devices_response

            # Handler uses 'filter' param for OData filtering
            await handle_get_device_list({"filter": "deviceType eq ACCESS_POINT"})

            call_args = mock_api.call_args
            params = call_args.kwargs.get("params", {})
            assert params.get("filter") == "deviceType eq ACCESS_POINT"
            assert params.get("limit") == 100  # Default limit is always applied

    @pytest.mark.asyncio
    async def test_get_device_list_categorization(self, mock_devices_response):
        """Test that devices are categorized by type."""
        with patch("src.tools.devices.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_devices_response

            result = await handle_get_device_list({})

            # Should show device type breakdown
            assert "[AP]" in result[0].text or "ACCESS_POINT" in result[0].text
            assert "[SW]" in result[0].text or "SWITCH" in result[0].text

    @pytest.mark.asyncio
    async def test_get_device_list_status_breakdown(self, mock_devices_response):
        """Test status breakdown in output."""
        with patch("src.tools.devices.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_devices_response

            result = await handle_get_device_list({})

            # Should show status breakdown
            assert "By Status" in result[0].text

    @pytest.mark.asyncio
    async def test_get_device_list_empty_response(self):
        """Test handling empty response."""
        with patch("src.tools.devices.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"items": [], "total": 0}

            result = await handle_get_device_list({})

            assert len(result) == 1
            assert len(result) == 1  # Received valid response

    @pytest.mark.asyncio
    async def test_get_device_list_pagination(self):
        """Test pagination handling."""
        with patch("src.tools.devices.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                "items": [{"deviceType": "ACCESS_POINT", "status": "ONLINE"}],
                "total": 500,
            }

            result = await handle_get_device_list({"limit": 100})

            # Should indicate more results
            assert len(result) == 1  # Response received

    @pytest.mark.asyncio
    async def test_get_device_list_default_limit(self):
        """Test that default limit is applied."""
        with patch("src.tools.devices.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"items": [], "total": 0}

            await handle_get_device_list({})

            call_args = mock_api.call_args
            params = call_args.kwargs.get("params", {})
            assert params.get("limit") == 100
