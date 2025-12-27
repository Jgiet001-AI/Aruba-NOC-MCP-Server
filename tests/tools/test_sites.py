"""
Tests for Site Tools
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.tools.sites import handle_get_sites_health


class TestHandleGetSitesHealth:
    """Test cases for handle_get_sites_health."""

    @pytest.mark.asyncio
    async def test_get_sites_health_success(self, mock_sites_health_response):
        """Test successful sites health retrieval."""
        with patch("src.tools.sites.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_sites_health_response

            result = await handle_get_sites_health({})

            assert len(result) == 1
            assert result[0].type == "text"
            assert "Sites Health Overview" in result[0].text
            assert "Total sites analyzed: 2" in result[0].text

    @pytest.mark.asyncio
    async def test_get_sites_health_breakdown(self, mock_sites_health_response):
        """Test health status breakdown."""
        with patch("src.tools.sites.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_sites_health_response

            result = await handle_get_sites_health({})

            # Should show health breakdown
            assert "Health Distribution" in result[0].text

    @pytest.mark.asyncio
    async def test_get_sites_health_device_counts(self, mock_sites_health_response):
        """Test that device counts are included."""
        with patch("src.tools.sites.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_sites_health_response

            result = await handle_get_sites_health({})

            # Should include device information
            assert "device" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_get_sites_health_alerts(self, mock_sites_health_response):
        """Test that alerts are shown for sites with issues."""
        with patch("src.tools.sites.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_sites_health_response

            result = await handle_get_sites_health({})

            # Should show sites with alerts
            assert "alert" in result[0].text.lower() or "Alert" in result[0].text

    @pytest.mark.asyncio
    async def test_get_sites_health_empty_response(self):
        """Test handling empty response."""
        with patch("src.tools.sites.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"items": [], "total": 0}

            result = await handle_get_sites_health({})

            assert len(result) == 1
            assert "Total sites analyzed: 0" in result[0].text

    @pytest.mark.asyncio
    async def test_get_sites_health_pagination(self):
        """Test pagination handling."""
        with patch("src.tools.sites.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                "items": [{"siteName": "Site1", "overallHealth": "Good"}],
                "total": 200,
            }

            result = await handle_get_sites_health({"limit": 100})

            # Check response received
            assert len(result) == 1
