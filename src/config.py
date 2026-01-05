"""
ArubaConfig - Configuration class for Aruba Central API authentication

Supports multiple secret sources for security:
1. Docker Secrets (production - most secure)
2. Environment variables (development - backward compatible)
3. File-based secrets (Kubernetes/custom deployments)
"""

import logging
import os
from pathlib import Path

import httpx

logger = logging.getLogger("aruba-noc-server")


class ArubaConfig:
    """Configuration and authentication manager for Aruba Central API"""

    def __init__(self):
        self.token_url = "https://sso.common.cloud.hpe.com/as/token.oauth2"
        self.base_url = os.getenv("ARUBA_BASE_URL", "https://us1.api.central.arubanetworks.com")

        # Load credentials from secure sources
        self.client_id = self._load_secret("ARUBA_CLIENT_ID", "aruba_client_id")
        self.client_secret = self._load_secret("ARUBA_CLIENT_SECRET", "aruba_client_secret")
        self.access_token = self._load_secret("ARUBA_ACCESS_TOKEN", "aruba_access_token")

        # Validate credentials (but don't log sensitive values!)
        self._validate_credentials()

    def _load_secret(self, env_var: str, secret_name: str) -> str | None:
        """
        Load secret from multiple sources with priority order:
        1. Docker Secrets (/run/secrets/<secret_name>)
        2. File-based secrets (/secrets/<secret_name>)
        3. Environment variables (backward compatibility)

        Args:
            env_var: Environment variable name
            secret_name: Docker secret name

        Returns:
            Secret value or None if not found
        """
        # Priority 1: Docker Secrets (production)
        docker_secret = Path(f"/run/secrets/{secret_name}")
        if docker_secret.exists():
            try:
                value = docker_secret.read_text().strip()
                if value:
                    logger.info(f"Loaded {env_var} from Docker secret")
                    return value
            except Exception as e:
                logger.warning(f"Failed to read Docker secret {secret_name}: {e}")

        # Priority 2: File-based secrets (Kubernetes, custom)
        file_secret = Path(f"/secrets/{secret_name}")
        if file_secret.exists():
            try:
                value = file_secret.read_text().strip()
                if value:
                    logger.info(f"Loaded {env_var} from file secret")
                    return value
            except Exception as e:
                logger.warning(f"Failed to read file secret {secret_name}: {e}")

        # Priority 3: Environment variables (backward compatibility, development)
        env_value = os.getenv(env_var)
        if env_value:
            logger.info(f"Loaded {env_var} from environment variable")
            return env_value

        return None

    def _validate_credentials(self) -> None:
        """Validate that credentials are properly configured."""
        # Check for placeholder values
        placeholders = ["your_client_id", "your_client_secret", "your_access_token", ""]

        if self.client_id in placeholders:
            self.client_id = None
        if self.client_secret in placeholders:
            self.client_secret = None
        if self.access_token in placeholders:
            self.access_token = None

        # Warn if no credentials found
        if not self.access_token and not (self.client_id and self.client_secret):
            logger.warning(
                "No authentication credentials found. "
                "Please provide credentials via Docker Secrets or environment variables."
            )
            return

        # Validate OAuth2 credentials if present
        if self.client_id and not self.client_secret:
            logger.error("ARUBA_CLIENT_ID provided but ARUBA_CLIENT_SECRET is missing")
        elif self.client_secret and not self.client_id:
            logger.error("ARUBA_CLIENT_SECRET provided but ARUBA_CLIENT_ID is missing")
        elif self.client_id and self.client_secret:
            logger.info("OAuth2 credentials loaded successfully")

    def get_headers(self) -> dict[str, str]:
        """
        Get HTTP headers with authentication.

        Raises:
            ValueError: If no access token is available

        Returns:
            Dictionary of HTTP headers
        """
        if not self.access_token:
            raise ValueError(
                "Access token not available. "
                "Call get_access_token() first or provide ARUBA_ACCESS_TOKEN."
            )

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def get_access_token(self) -> str:
        """
        Generate OAuth2 access token from client credentials.

        This method uses the OAuth2 client credentials flow to obtain
        an access token from the HPE SSO service.

        Returns:
            The access token string

        Raises:
            ValueError: If credentials are missing or token generation fails
            httpx.HTTPStatusError: If the OAuth2 request fails
        """
        if not (self.client_id and self.client_secret):
            raise ValueError(
                "Client ID and Client Secret are required to generate an access token. "
                "Provide via Docker Secrets or environment variables."
            )

        logger.info("Requesting new OAuth2 access token from HPE SSO")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()

            token_data = response.json()
            if "access_token" not in token_data:
                raise ValueError("Access token not found in OAuth2 response")

            self.access_token = token_data["access_token"]

            # Log success without exposing token (security best practice)
            expires_in = token_data.get("expires_in", "unknown")
            logger.info(
                f"OAuth2 access token acquired successfully (expires in {expires_in}s)"
            )

            return self.access_token


config = ArubaConfig()
