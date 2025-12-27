"""
Tests for clients.py tool handlers
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.tools.clients import handle_list_all_clients


class TestHandleListAllClients:
    """Test cases for handle_list_all_clients."""

    @pytest.mark.asyncio
    async def test_list_all_clients_success(self, mock_clients_response):
        """Test successful client listing."""
        with patch("src.tools.clients.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_clients_response

            result = await handle_list_all_clients({})

            assert len(result) == 1
            assert result[0].type == "text"
            assert "Network Clients Overview" in result[0].text
            assert "Total clients: 2" in result[0].text

    @pytest.mark.asyncio
    async def test_list_all_clients_with_site_filter(self, mock_clients_response):
        """Test client listing with site filter."""
        with patch("src.tools.clients.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_clients_response

            await handle_list_all_clients({"site_id": "site-001"})

            # Verify API was called with hyphenated param
            call_args = mock_api.call_args
            assert "site-id" in call_args.kwargs.get("params", {})

    @pytest.mark.asyncio
    async def test_list_all_clients_categorization(self, mock_clients_response):
        """Test that clients are categorized correctly."""
        with patch("src.tools.clients.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_clients_response

            result = await handle_list_all_clients({})

            # Should show connection type breakdown
            assert "[WIFI]" in result[0].text or "Wireless" in result[0].text
            assert "[WIRED]" in result[0].text or "Wired" in result[0].text

    @pytest.mark.asyncio
    async def test_list_all_clients_experience_breakdown(self, mock_clients_response):
        """Test experience score breakdown."""
        with patch("src.tools.clients.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_clients_response

            result = await handle_list_all_clients({})

            # Should show experience breakdown
            assert "By Experience" in result[0].text

    @pytest.mark.asyncio
    async def test_list_all_clients_empty_response(self):
        """Test handling empty response."""
        with patch("src.tools.clients.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"items": [], "total": 0}

            result = await handle_list_all_clients({})

            assert len(result) == 1
            assert "Total clients: 0" in result[0].text

    @pytest.mark.asyncio
    async def test_list_all_clients_pagination(self):
        """Test pagination cursor handling."""
        with patch("src.tools.clients.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                "items": [{"type": "Wireless", "status": "Connected", "experience": "Good"}],
                "total": 100,
                "next": "cursor_token_123",
            }

            result = await handle_list_all_clients({})

            assert "[MORE]" in result[0].text

    @pytest.mark.asyncio
    async def test_list_all_clients_default_limit(self):
        """Test that default limit is applied."""
        with patch("src.tools.clients.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"items": [], "total": 0}

            await handle_list_all_clients({})

            call_args = mock_api.call_args
            params = call_args.kwargs.get("params", {})
            assert params.get("limit") == 100
