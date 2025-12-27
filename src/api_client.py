"""
API Client - API calling function for Aruba Central

Features:
- Automatic retry with exponential backoff for transient failures
- Token refresh on 401 Unauthorized
- Configurable timeout
"""

import logging
import os
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import config

logger = logging.getLogger("aruba-noc-server")

# Configurable timeout (default: 30 seconds)
API_TIMEOUT = float(os.getenv("ARUBA_API_TIMEOUT", "30.0"))


def _retry_on_transient_errors():
    """Retry decorator for transient network errors."""
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError)),
        reraise=True,
    )


@_retry_on_transient_errors()
async def call_aruba_api(
    endpoint: str,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    json_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make an authenticated API call to Aruba Central.

    Args:
        endpoint: API endpoint path (e.g., "/monitoring/v2/devices")
        method: HTTP method (default: GET)
        params: Query parameters
        json_data: JSON body for POST/PUT requests

    Returns:
        API response as dictionary

    Raises:
        httpx.HTTPStatusError: For non-retryable HTTP errors
    """
    url = f"{config.base_url}{endpoint}"

    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
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
