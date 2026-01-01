"""
Tests for API Client
"""

from unittest.mock import MagicMock, patch

import pytest


class TestCallArubaApi:
    """Test cases for the call_aruba_api function"""

    @pytest.mark.asyncio
    async def test_call_aruba_api_success(self):
        """Test successful API call"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"devices": []}

        with (
            patch("src.api_client.config") as mock_config,
            patch("src.api_client.httpx.AsyncClient") as mock_client_class,
        ):
            mock_config.access_token = "test_token"
            mock_config.base_url = "https://api.test.com"
            mock_config.get_headers.return_value = {
                "Authorization": "Bearer test_token",
                "Content-Type": "application/json",
            }

            # Setup async context manager mock
            mock_client_instance = MagicMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client_instance
            mock_client_class.return_value.__aexit__.return_value = None

            # Make request() return a coroutine that awaits to the response
            async def mock_request(*args, **kwargs):
                return mock_response

            mock_client_instance.request = mock_request

            from src.api_client import call_aruba_api

            result = await call_aruba_api("/monitoring/v2/devices")
            assert result == {"devices": []}

    @pytest.mark.asyncio
    async def test_call_aruba_api_with_params(self):
        """Test API call with query parameters"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"total": 5}

        with (
            patch("src.api_client.config") as mock_config,
            patch("src.api_client.httpx.AsyncClient") as mock_client_class,
        ):
            mock_config.access_token = "test_token"
            mock_config.base_url = "https://api.test.com"
            mock_config.get_headers.return_value = {"Authorization": "Bearer test_token"}

            mock_client_instance = MagicMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client_instance
            mock_client_class.return_value.__aexit__.return_value = None

            captured_kwargs = {}

            async def mock_request(*args, **kwargs):
                captured_kwargs.update(kwargs)
                return mock_response

            mock_client_instance.request = mock_request

            from src.api_client import call_aruba_api

            result = await call_aruba_api(
                "/monitoring/v2/devices",
                params={"limit": 10, "offset": 0},
            )

            assert result == {"total": 5}
            assert captured_kwargs.get("params") == {"limit": 10, "offset": 0}

    @pytest.mark.asyncio
    async def test_call_aruba_api_token_refresh_on_401(self):
        """Test that API client refreshes token on 401"""
        mock_401_response = MagicMock()
        mock_401_response.status_code = 401

        mock_200_response = MagicMock()
        mock_200_response.status_code = 200
        mock_200_response.json.return_value = {"data": "success"}

        responses = [mock_401_response, mock_200_response]

        with (
            patch("src.api_client.config") as mock_config,
            patch("src.api_client.httpx.AsyncClient") as mock_client_class,
        ):
            mock_config.access_token = "old_token"
            mock_config.base_url = "https://api.test.com"
            mock_config.get_headers.return_value = {"Authorization": "Bearer old_token"}

            async def mock_get_access_token():
                pass

            mock_config.get_access_token = mock_get_access_token

            mock_client_instance = MagicMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client_instance
            mock_client_class.return_value.__aexit__.return_value = None

            call_count = [0]

            async def mock_request(*args, **kwargs):
                response = responses[call_count[0]]
                call_count[0] += 1
                return response

            mock_client_instance.request = mock_request

            from src.api_client import call_aruba_api

            result = await call_aruba_api("/test")
            assert result == {"data": "success"}
            assert call_count[0] == 2  # First 401, then success

    @pytest.mark.asyncio
    async def test_call_aruba_api_auto_token_generation(self):
        """Test that API client works when token exists"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "ok"}

        with (
            patch("src.api_client.config") as mock_config,
            patch("src.api_client.httpx.AsyncClient") as mock_client_class,
        ):
            mock_config.access_token = "valid_token"
            mock_config.base_url = "https://api.test.com"
            mock_config.get_headers.return_value = {"Authorization": "Bearer valid_token"}

            mock_client_instance = MagicMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client_instance
            mock_client_class.return_value.__aexit__.return_value = None

            async def mock_request(*args, **kwargs):
                return mock_response

            mock_client_instance.request = mock_request

            from src.api_client import call_aruba_api

            result = await call_aruba_api("/test")
            assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_call_aruba_api_post_with_json(self):
        """Test POST request with JSON body"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "new_resource"}

        with (
            patch("src.api_client.config") as mock_config,
            patch("src.api_client.httpx.AsyncClient") as mock_client_class,
        ):
            mock_config.access_token = "test_token"
            mock_config.base_url = "https://api.test.com"
            mock_config.get_headers.return_value = {"Authorization": "Bearer test_token"}

            mock_client_instance = MagicMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client_instance
            mock_client_class.return_value.__aexit__.return_value = None

            captured_kwargs = {}

            async def mock_request(*args, **kwargs):
                captured_kwargs.update(kwargs)
                return mock_response

            mock_client_instance.request = mock_request

            from src.api_client import call_aruba_api

            result = await call_aruba_api(
                "/resources",
                method="POST",
                json_data={"name": "test"},
            )

            assert result == {"id": "new_resource"}
            assert captured_kwargs.get("method") == "POST"
            assert captured_kwargs.get("json") == {"name": "test"}
