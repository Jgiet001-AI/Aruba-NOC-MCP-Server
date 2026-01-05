"""
Regression tests for config module.

These tests verify the CURRENT WORKING BEHAVIOR of the ArubaConfig class
before applying lint fixes. Focus on testing initialization, header
generation, and environment variable handling.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestArubaConfigInitialization:
    """Test ArubaConfig class initialization patterns."""

    def test_config_uses_environment_variables(self):
        """Verify config reads from environment variables."""
        with patch.dict(
            os.environ,
            {
                "ARUBA_BASE_URL": "https://custom.api.test.com",
                "ARUBA_CLIENT_ID": "test_id",
                "ARUBA_CLIENT_SECRET": "test_secret",
                "ARUBA_ACCESS_TOKEN": "test_token",
            },
        ):
            # Import fresh to pick up patched env vars
            from importlib import reload

            import src.config

            reload(src.config)

            config = src.config.ArubaConfig()

            assert config.base_url == "https://custom.api.test.com"
            assert config.client_id == "test_id"
            assert config.client_secret == "test_secret"
            assert config.access_token == "test_token"

    def test_config_default_base_url(self):
        """Verify default base URL when not provided."""
        with patch.dict(
            os.environ,
            {
                "ARUBA_ACCESS_TOKEN": "test_token",
            },
            clear=True,
        ):
            from importlib import reload

            import src.config

            reload(src.config)

            config = src.config.ArubaConfig()

            # Default should be US1 API URL
            assert "api.central.arubanetworks.com" in config.base_url

    def test_config_token_url_is_set(self):
        """Verify token URL is properly set."""
        with patch.dict(
            os.environ,
            {
                "ARUBA_ACCESS_TOKEN": "test_token",
            },
        ):
            from importlib import reload

            import src.config

            reload(src.config)

            config = src.config.ArubaConfig()

            assert config.token_url == "https://sso.common.cloud.hpe.com/as/token.oauth2"


class TestArubaConfigHeaders:
    """Test get_headers method."""

    def test_headers_include_authorization(self):
        """Verify headers include Bearer token."""
        with patch.dict(
            os.environ,
            {
                "ARUBA_ACCESS_TOKEN": "my_test_token",
            },
        ):
            from importlib import reload

            import src.config

            reload(src.config)

            config = src.config.ArubaConfig()
            headers = config.get_headers()

            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer my_test_token"

    def test_headers_include_content_type(self):
        """Verify headers include Content-Type."""
        with patch.dict(
            os.environ,
            {
                "ARUBA_ACCESS_TOKEN": "test_token",
            },
        ):
            from importlib import reload

            import src.config

            reload(src.config)

            config = src.config.ArubaConfig()
            headers = config.get_headers()

            assert headers.get("Content-Type") == "application/json"

    def test_headers_include_accept(self):
        """Verify headers include Accept."""
        with patch.dict(
            os.environ,
            {
                "ARUBA_ACCESS_TOKEN": "test_token",
            },
        ):
            from importlib import reload

            import src.config

            reload(src.config)

            config = src.config.ArubaConfig()
            headers = config.get_headers()

            assert headers.get("Accept") == "application/json"

    def test_headers_returns_dict(self):
        """Verify get_headers returns a dict."""
        with patch.dict(
            os.environ,
            {
                "ARUBA_ACCESS_TOKEN": "test_token",
            },
        ):
            from importlib import reload

            import src.config

            reload(src.config)

            config = src.config.ArubaConfig()
            headers = config.get_headers()

            assert isinstance(headers, dict)


class TestArubaConfigGetAccessToken:
    """Test get_access_token async method."""

    @pytest.mark.asyncio
    async def test_get_access_token_requires_credentials(self):
        """Verify error is raised without client credentials."""
        with patch.dict(os.environ, {}, clear=True):
            from importlib import reload

            import src.config

            reload(src.config)

            config = src.config.ArubaConfig()
            config.client_id = None
            config.client_secret = None

            with pytest.raises(ValueError) as exc_info:
                await config.get_access_token()

            assert "Client ID and Client Secret are required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_access_token_makes_post_request(self):
        """Verify token request uses POST method."""
        with patch.dict(
            os.environ,
            {
                "ARUBA_CLIENT_ID": "test_id",
                "ARUBA_CLIENT_SECRET": "test_secret",
            },
        ):
            from importlib import reload

            import src.config

            reload(src.config)

            config = src.config.ArubaConfig()

            mock_response = MagicMock()
            mock_response.json.return_value = {"access_token": "new_token"}
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post.return_value = mock_response

            with patch("httpx.AsyncClient", return_value=mock_client):
                token = await config.get_access_token()

            # Verify token was returned
            assert token == "new_token"
            # Verify access_token was updated on config
            assert config.access_token == "new_token"

    @pytest.mark.asyncio
    async def test_get_access_token_raises_on_missing_token(self):
        """Verify error is raised if response lacks access_token."""
        with patch.dict(
            os.environ,
            {
                "ARUBA_CLIENT_ID": "test_id",
                "ARUBA_CLIENT_SECRET": "test_secret",
            },
        ):
            from importlib import reload

            import src.config

            reload(src.config)

            config = src.config.ArubaConfig()

            mock_response = MagicMock()
            mock_response.json.return_value = {"error": "invalid_grant"}  # No access_token!
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post.return_value = mock_response

            with patch("httpx.AsyncClient", return_value=mock_client):
                with pytest.raises(ValueError) as exc_info:
                    await config.get_access_token()

            assert "Access token not found in OAuth2 response" in str(exc_info.value)


class TestModuleLevelConfig:
    """Test the module-level config singleton."""

    def test_module_config_exists(self):
        """Verify module exports a config instance."""
        with patch.dict(
            os.environ,
            {
                "ARUBA_ACCESS_TOKEN": "test_token",
            },
        ):
            from importlib import reload

            import src.config

            reload(src.config)

            assert hasattr(src.config, "config")
            assert src.config.config is not None

    def test_module_config_is_aruba_config_instance(self):
        """Verify module config is an ArubaConfig instance."""
        with patch.dict(
            os.environ,
            {
                "ARUBA_ACCESS_TOKEN": "test_token",
            },
        ):
            from importlib import reload

            import src.config

            reload(src.config)

            assert isinstance(src.config.config, src.config.ArubaConfig)
