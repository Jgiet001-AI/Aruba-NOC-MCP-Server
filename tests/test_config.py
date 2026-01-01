"""
Tests for ArubaConfig class
"""

import os
from unittest.mock import AsyncMock, patch

import pytest

from src.config import ArubaConfig


class TestArubaConfig:
    """Test cases for ArubaConfig"""

    def test_config_loads_env_vars(self):
        """Test that config loads environment variables"""
        with patch.dict(
            os.environ,
            {
                "ARUBA_BASE_URL": "https://test.api.com",
                "ARUBA_CLIENT_ID": "test_client_id",
                "ARUBA_CLIENT_SECRET": "test_secret",
                "ARUBA_ACCESS_TOKEN": "test_token",
            },
        ):
            config = ArubaConfig()
            assert config.base_url == "https://test.api.com"
            assert config.client_id == "test_client_id"
            assert config.client_secret == "test_secret"
            assert config.access_token == "test_token"

    def test_config_default_base_url(self):
        """Test that config uses default base URL when not set"""
        with patch.dict(os.environ, {}, clear=True):
            config = ArubaConfig()
            assert config.base_url == "https://us1.api.central.arubanetworks.com"

    def test_get_headers(self):
        """Test that get_headers returns correct auth headers"""
        with patch.dict(os.environ, {"ARUBA_ACCESS_TOKEN": "my_token"}):
            config = ArubaConfig()
            headers = config.get_headers()
            assert headers["Authorization"] == "Bearer my_token"
            assert headers["Content-Type"] == "application/json"
            assert headers["Accept"] == "application/json"

    @pytest.mark.asyncio
    async def test_get_access_token_requires_credentials(self):
        """Test that get_access_token raises error without credentials"""
        with patch.dict(os.environ, {}, clear=True):
            config = ArubaConfig()
            with pytest.raises(ValueError, match="Client ID and Client Secret"):
                await config.get_access_token()

    @pytest.mark.asyncio
    async def test_get_access_token_success(self):
        """Test successful token generation"""
        with patch.dict(
            os.environ,
            {
                "ARUBA_CLIENT_ID": "test_id",
                "ARUBA_CLIENT_SECRET": "test_secret",
            },
        ):
            from unittest.mock import MagicMock

            config = ArubaConfig()

            # Response object with sync json() method
            mock_response = MagicMock()
            mock_response.json.return_value = {"access_token": "new_token"}
            mock_response.raise_for_status = MagicMock()

            # AsyncClient context manager with async post
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value = mock_client_instance
                token = await config.get_access_token()
                assert token == "new_token"
                assert config.access_token == "new_token"
