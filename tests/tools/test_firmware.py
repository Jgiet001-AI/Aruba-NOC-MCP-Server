"""
Tests for firmware.py tool handlers
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.tools.firmware import handle_get_firmware_details


class TestHandleGetFirmwareDetails:
    """Test cases for handle_get_firmware_details."""

    @pytest.mark.asyncio
    async def test_get_firmware_details_success(self, mock_firmware_response):
        """Test successful firmware details retrieval."""
        with patch("src.tools.firmware.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_firmware_response

            result = await handle_get_firmware_details({})

            assert len(result) == 1
            assert result[0].type == "text"
            assert "Firmware Status Overview" in result[0].text
            assert "Total devices analyzed: 2" in result[0].text

    @pytest.mark.asyncio
    async def test_get_firmware_upgrade_status_breakdown(self, mock_firmware_response):
        """Test upgrade status breakdown."""
        with patch("src.tools.firmware.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_firmware_response

            result = await handle_get_firmware_details({})

            # Should show upgrade status breakdown
            assert "By Upgrade Status" in result[0].text
            assert "Up To Date" in result[0].text or "[OK]" in result[0].text

    @pytest.mark.asyncio
    async def test_get_firmware_devices_needing_updates(self, mock_firmware_response):
        """Test that devices needing updates are listed."""
        with patch("src.tools.firmware.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_firmware_response

            result = await handle_get_firmware_details({})

            # Should show devices needing updates
            assert "Devices Needing Updates" in result[0].text
            assert "AP-Floor1-01" in result[0].text

    @pytest.mark.asyncio
    async def test_get_firmware_classification_breakdown(self, mock_firmware_response):
        """Test classification breakdown."""
        with patch("src.tools.firmware.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_firmware_response

            result = await handle_get_firmware_details({})

            # Should show classification breakdown
            assert "By Classification" in result[0].text

    @pytest.mark.asyncio
    async def test_get_firmware_device_type_breakdown(self, mock_firmware_response):
        """Test device type breakdown."""
        with patch("src.tools.firmware.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_firmware_response

            result = await handle_get_firmware_details({})

            # Should show device type breakdown
            assert "By Device Type" in result[0].text

    @pytest.mark.asyncio
    async def test_get_firmware_empty_response(self):
        """Test handling empty response."""
        with patch("src.tools.firmware.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"items": [], "total": 0}

            result = await handle_get_firmware_details({})

            assert len(result) == 1
            assert "Total devices analyzed: 0" in result[0].text

    @pytest.mark.asyncio
    async def test_get_firmware_with_filter(self):
        """Test firmware details with filter parameter."""
        with patch("src.tools.firmware.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"items": [], "total": 0}

            await handle_get_firmware_details({"filter": "upgradeStatus eq Update Required"})

            call_args = mock_api.call_args
            params = call_args.kwargs.get("params", {})
            assert params.get("filter") == "upgradeStatus eq Update Required"

    @pytest.mark.asyncio
    async def test_get_firmware_version_display(self, mock_firmware_response):
        """Test that current and recommended versions are shown."""
        with patch("src.tools.firmware.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_firmware_response

            result = await handle_get_firmware_details({})

            # Should show version transition
            assert "8.10.0.0" in result[0].text
            assert "8.11.0.0" in result[0].text
            assert "->" in result[0].text
