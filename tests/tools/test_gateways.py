"""
Tests for gateways.py tool handlers
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.tools.gateways import handle_list_gateways


class TestHandleListGateways:
    """Test cases for handle_list_gateways."""

    @pytest.mark.asyncio
    async def test_list_gateways_success(self, mock_gateways_response):
        """Test successful gateway listing."""
        with patch("src.tools.gateways.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_gateways_response

            result = await handle_list_gateways({})

            assert len(result) == 1
            assert result[0].type == "text"
            assert "Gateway Inventory Overview" in result[0].text
            assert "Total gateways: 2" in result[0].text

    @pytest.mark.asyncio
    async def test_list_gateways_status_breakdown(self, mock_gateways_response):
        """Test status breakdown in output."""
        with patch("src.tools.gateways.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_gateways_response

            result = await handle_list_gateways({})

            # Should show status breakdown
            assert "[UP]" in result[0].text or "ONLINE" in result[0].text
            assert "[DN]" in result[0].text or "OFFLINE" in result[0].text

    @pytest.mark.asyncio
    async def test_list_gateways_offline_alert(self, mock_gateways_response):
        """Test that offline gateways are highlighted."""
        with patch("src.tools.gateways.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_gateways_response

            result = await handle_list_gateways({})

            # Should show offline gateway details
            assert "Offline Gateways" in result[0].text
            assert "GW-Branch" in result[0].text

    @pytest.mark.asyncio
    async def test_list_gateways_deployment_breakdown(self, mock_gateways_response):
        """Test deployment type breakdown."""
        with patch("src.tools.gateways.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_gateways_response

            result = await handle_list_gateways({})

            # Should show deployment types
            assert "By Deployment Type" in result[0].text

    @pytest.mark.asyncio
    async def test_list_gateways_model_breakdown(self, mock_gateways_response):
        """Test model breakdown."""
        with patch("src.tools.gateways.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_gateways_response

            result = await handle_list_gateways({})

            # Should show model inventory
            assert "By Model" in result[0].text

    @pytest.mark.asyncio
    async def test_list_gateways_availability_percentage(self, mock_gateways_response):
        """Test availability percentage calculation."""
        with patch("src.tools.gateways.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_gateways_response

            result = await handle_list_gateways({})

            # With 1 online and 1 offline, should show 50%
            assert "50.0%" in result[0].text or "Availability" in result[0].text

    @pytest.mark.asyncio
    async def test_list_gateways_empty_response(self):
        """Test handling empty response."""
        with patch("src.tools.gateways.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"items": [], "total": 0}

            result = await handle_list_gateways({})

            assert len(result) == 1
            assert "Total gateways: 0" in result[0].text

    @pytest.mark.asyncio
    async def test_list_gateways_with_filter(self):
        """Test gateway listing with filter parameter."""
        with patch("src.tools.gateways.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"items": [], "total": 0}

            await handle_list_gateways({"filter": "status eq ONLINE"})

            call_args = mock_api.call_args
            params = call_args.kwargs.get("params", {})
            assert params.get("filter") == "status eq ONLINE"
