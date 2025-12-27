"""
Tests for API Client
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api_client import call_aruba_api
from src.config import ArubaConfig


class TestCallArubaApi:
    """Test cases for the call_aruba_api function"""

    @pytest.mark.asyncio
    async def test_call_aruba_api_success(self):
        """Test successful API call"""
        config = MagicMock(spec=ArubaConfig)
        config.access_token = "test_token"
        config.base_url = "https://api.test.com"
        config.get_headers.return_value = {
            "Authorization": "Bearer test_token",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"devices": []}
        mock_response.raise_for_status = AsyncMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            result = await call_aruba_api(config, "/monitoring/v2/devices")
            assert result == {"devices": []}

    @pytest.mark.asyncio
    async def test_call_aruba_api_with_params(self):
        """Test API call with query parameters"""
        config = MagicMock(spec=ArubaConfig)
        config.access_token = "test_token"
        config.base_url = "https://api.test.com"
        config.get_headers.return_value = {"Authorization": "Bearer test_token"}

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"total": 5}
        mock_response.raise_for_status = AsyncMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_request = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.request = mock_request

            result = await call_aruba_api(
                config,
                "/monitoring/v2/devices",
                params={"limit": 10, "offset": 0},
            )

            assert result == {"total": 5}
            mock_request.assert_called()

    @pytest.mark.asyncio
    async def test_call_aruba_api_token_refresh_on_401(self):
        """Test that API client refreshes token on 401"""
        config = MagicMock(spec=ArubaConfig)
        config.access_token = "old_token"
        config.base_url = "https://api.test.com"
        config.get_headers.return_value = {"Authorization": "Bearer old_token"}
        config.get_access_token = AsyncMock()

        mock_401_response = AsyncMock()
        mock_401_response.status_code = 401

        mock_200_response = AsyncMock()
        mock_200_response.status_code = 200
        mock_200_response.json.return_value = {"data": "success"}
        mock_200_response.raise_for_status = AsyncMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                side_effect=[mock_401_response, mock_200_response]
            )
            result = await call_aruba_api(config, "/test")
            config.get_access_token.assert_called_once()
            assert result == {"data": "success"}

    @pytest.mark.asyncio
    async def test_call_aruba_api_auto_token_generation(self):
        """Test that API client generates token if none exists"""
        config = MagicMock(spec=ArubaConfig)
        config.access_token = None
        config.base_url = "https://api.test.com"
        config.get_access_token = AsyncMock()
        config.get_headers.return_value = {"Authorization": "Bearer new_token"}

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "ok"}
        mock_response.raise_for_status = AsyncMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            result = await call_aruba_api(config, "/test")
            config.get_access_token.assert_called_once()
            assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_call_aruba_api_post_with_json(self):
        """Test POST request with JSON body"""
        config = MagicMock(spec=ArubaConfig)
        config.access_token = "test_token"
        config.base_url = "https://api.test.com"
        config.get_headers.return_value = {"Authorization": "Bearer test_token"}

        mock_response = AsyncMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "new_resource"}
        mock_response.raise_for_status = AsyncMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_request = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.request = mock_request

            result = await call_aruba_api(
                config,
                "/resources",
                method="POST",
                json_data={"name": "test"},
            )

            assert result == {"id": "new_resource"}
