"""
ArubaConfig - Configuration class for Aruba Central API authentication
"""

import os
import logging
import httpx

logger = logging.getLogger("aruba-noc-server")


class ArubaConfig:
    """Configuration and authentication manager for Aruba Central API"""

    def __init__(self):
        self.token_url = "https://sso.common.cloud.hpe.com/as/token.oauth2"
        self.base_url = os.getenv(
            "ARUBA_BASE_URL", "https://us1.api.central.arubanetworks.com"
        )
        self.client_id = os.getenv("ARUBA_CLIENT_ID")
        self.client_secret = os.getenv("ARUBA_CLIENT_SECRET")
        self.access_token = os.getenv("ARUBA_ACCESS_TOKEN")

        if not self.access_token and not (self.client_id and self.client_secret):
            logger.warning(
                "No authentication credentials found. "
                "Please provide ARUBA_ACCESS_TOKEN or ARUBA_CLIENT_ID and ARUBA_CLIENT_SECRET"
            )
        pass

    def get_headers(self) -> dict[str, str]:
        """Get HTTP headers with authentication"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        pass

    async def get_access_token(self) -> str:
        """Generate OAuth2 access token from client credentials"""
        if not (self.client_id and self.client_secret):
            raise ValueError(
                "Client ID and Client Secret are required to generate an access token"
            )

        async with httpx.AsyncClient() as client:
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
                raise ValueError("Access token not found in response")
            self.access_token = token_data["access_token"]
            logger.info("Access token generated successfully")  
            return self.access_token
        pass

    
config = ArubaConfig()