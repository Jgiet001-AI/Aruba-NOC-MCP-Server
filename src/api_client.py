"""
API Client - API calling function for Aruba Central
"""

import logging
from typing import Any

import httpx

from src.config import config

logger = logging.getLogger("aruba-noc-server")


async def call_aruba_api(
    endpoint: str,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    json_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make an authenticated API call to Aruba Central"""

    url = f"{config.base_url}{endpoint}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(
            method=method,
            url=url,
            headers=config.get_headers(),
            params=params,
            json=json_data,
        )

        # Handle token refresh on 401
        if response.status_code == 401:
            logger.info("Access token expired, refreshing...")
            await config.get_access_token()
            response = await client.request(
                method=method,
                url=url,
                headers=config.get_headers(),
                params=params,
                json=json_data,
            )

        response.raise_for_status()
        return response.json()
