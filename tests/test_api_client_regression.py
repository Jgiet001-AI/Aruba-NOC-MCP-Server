"""
Regression tests for API client module.

These tests verify the CURRENT WORKING BEHAVIOR of the call_aruba_api
function before applying lint fixes. Focus on testing request formation,
parameter handling, and response processing.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCallArubaApiBasicPatterns:
    """Test call_aruba_api function basic behavior."""

    @pytest.mark.asyncio
    async def test_api_call_returns_dict(self):
        """Verify API call returns dictionary response."""
        from src.api_client import call_aruba_api

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": [], "total": 0}
        mock_response.raise_for_status = MagicMock()

        with patch("src.api_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch("src.api_client.config") as mock_config:
                mock_config.base_url = "https://test.api.com"
                mock_config.get_headers.return_value = {"Authorization": "Bearer test"}

                result = await call_aruba_api("/test/endpoint")

        assert isinstance(result, dict)
        assert "items" in result

    @pytest.mark.asyncio
    async def test_api_call_uses_request_method(self):
        """Verify client.request is called with correct method."""
        from src.api_client import call_aruba_api

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status = MagicMock()

        with patch("src.api_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch("src.api_client.config") as mock_config:
                mock_config.base_url = "https://test.api.com"
                mock_config.get_headers.return_value = {}

                await call_aruba_api("/test/endpoint")

        # Verify request was called
        mock_client.request.assert_called_once()
        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["method"] == "GET"

    @pytest.mark.asyncio
    async def test_api_call_constructs_full_url(self):
        """Verify endpoint is appended to base URL."""
        from src.api_client import call_aruba_api

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()

        with patch("src.api_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch("src.api_client.config") as mock_config:
                mock_config.base_url = "https://api.example.com"
                mock_config.get_headers.return_value = {}

                await call_aruba_api("/my/endpoint")

        # Check URL construction
        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["url"] == "https://api.example.com/my/endpoint"


class TestCallArubaApiParameterHandling:
    """Test parameter passing to API calls."""

    @pytest.mark.asyncio
    async def test_api_call_passes_params(self):
        """Verify query parameters are passed to request."""
        from src.api_client import call_aruba_api

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()

        test_params = {"limit": 50, "filter": "type:AP"}

        with patch("src.api_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch("src.api_client.config") as mock_config:
                mock_config.base_url = "https://test.api.com"
                mock_config.get_headers.return_value = {}

                await call_aruba_api("/test", params=test_params)

        # Verify params were passed
        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["params"] == test_params

    @pytest.mark.asyncio
    async def test_api_call_passes_headers(self):
        """Verify headers from config are passed to request."""
        from src.api_client import call_aruba_api

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()

        expected_headers = {
            "Authorization": "Bearer test_token",
            "Content-Type": "application/json",
        }

        with patch("src.api_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch("src.api_client.config") as mock_config:
                mock_config.base_url = "https://test.api.com"
                mock_config.get_headers.return_value = expected_headers

                await call_aruba_api("/test")

        # Verify headers were passed
        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["headers"] == expected_headers


class TestCallArubaApiResponseHandling:
    """Test response processing."""

    @pytest.mark.asyncio
    async def test_api_call_calls_raise_for_status(self):
        """Verify response.raise_for_status() is called."""
        from src.api_client import call_aruba_api

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()

        with patch("src.api_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch("src.api_client.config") as mock_config:
                mock_config.base_url = "https://test.api.com"
                mock_config.get_headers.return_value = {}

                await call_aruba_api("/test")

        # Verify raise_for_status was called
        mock_response.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_api_call_returns_json_content(self):
        """Verify JSON response is parsed and returned."""
        from src.api_client import call_aruba_api

        expected_data = {
            "items": [{"id": 1, "name": "Test"}],
            "total": 1,
            "metadata": {"page": 1},
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_data
        mock_response.raise_for_status = MagicMock()

        with patch("src.api_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch("src.api_client.config") as mock_config:
                mock_config.base_url = "https://test.api.com"
                mock_config.get_headers.return_value = {}

                result = await call_aruba_api("/test")

        assert result == expected_data
        assert result["items"] == [{"id": 1, "name": "Test"}]
        assert result["total"] == 1


class TestCallArubaApiPostMethod:
    """Test POST method support."""

    @pytest.mark.asyncio
    async def test_api_call_with_post_method(self):
        """Verify POST method can be specified."""
        from src.api_client import call_aruba_api

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"result": "created"}
        mock_response.raise_for_status = MagicMock()

        with patch("src.api_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch("src.api_client.config") as mock_config:
                mock_config.base_url = "https://test.api.com"
                mock_config.get_headers.return_value = {}

                result = await call_aruba_api("/test", method="POST")

        assert result["result"] == "created"
        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["method"] == "POST"


class TestCallArubaApiTokenRefresh:
    """Test token refresh on 401."""

    @pytest.mark.asyncio
    async def test_api_refreshes_token_on_401(self):
        """Verify token is refreshed when 401 is received."""
        from src.api_client import call_aruba_api

        # First response is 401, second is success
        mock_response_401 = MagicMock()
        mock_response_401.status_code = 401

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"success": True}
        mock_response_200.raise_for_status = MagicMock()

        with patch("src.api_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(side_effect=[mock_response_401, mock_response_200])
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch("src.api_client.config") as mock_config:
                mock_config.base_url = "https://test.api.com"
                mock_config.get_headers.return_value = {}
                mock_config.get_access_token = AsyncMock()

                result = await call_aruba_api("/test")

        # Verify token refresh was called
        mock_config.get_access_token.assert_called_once()
        assert result["success"] is True
