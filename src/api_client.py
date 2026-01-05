"""
API Client - API calling function for Aruba Central

Features:
- Automatic retry with exponential backoff for transient failures
- Token refresh on 401 Unauthorized
- Configurable timeout
- Rate limiting to prevent API throttling
- Circuit breaker for resilience
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
from src.resilience import CircuitBreaker, CircuitBreakerError, RateLimiter

logger = logging.getLogger("aruba-noc-server")

# Configurable timeout (default: 30 seconds)
API_TIMEOUT = float(os.getenv("ARUBA_API_TIMEOUT", "30.0"))

# Rate limiter (100 requests per minute - adjust based on your API tier)
# Aruba Central rate limits vary by subscription level
rate_limiter = RateLimiter(
    max_requests=int(os.getenv("ARUBA_RATE_LIMIT_REQUESTS", "100")),
    window_seconds=int(os.getenv("ARUBA_RATE_LIMIT_WINDOW", "60")),
)

# Circuit breaker (5 failures triggers open, 60s timeout)
circuit_breaker = CircuitBreaker(
    failure_threshold=int(os.getenv("ARUBA_CIRCUIT_BREAKER_THRESHOLD", "5")),
    timeout_seconds=int(os.getenv("ARUBA_CIRCUIT_BREAKER_TIMEOUT", "60")),
)


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
    """
    Make an authenticated API call to Aruba Central with resilience patterns.

    This function provides:
    - Rate limiting to prevent API throttling
    - Circuit breaker to fail fast when API is down
    - Automatic retry with exponential backoff
    - Token refresh on 401 Unauthorized

    Args:
        endpoint: API endpoint path (e.g., "/monitoring/v2/devices")
        method: HTTP method (default: GET)
        params: Query parameters
        json_data: JSON body for POST/PUT requests

    Returns:
        API response as dictionary

    Raises:
        CircuitBreakerError: If circuit breaker is open
        httpx.HTTPStatusError: For non-retryable HTTP errors
        httpx.TimeoutException: If request times out
    """
    # Check circuit breaker first (fail fast if API is down)
    try:
        circuit_breaker.check()
    except CircuitBreakerError:
        logger.warning(f"Circuit breaker prevented API call to {endpoint}")
        raise

    # Acquire rate limit token (wait if necessary)
    await rate_limiter.acquire()

    # Auto-generate token if not available
    if not config.access_token:
        logger.info("No access token found, generating via OAuth2...")
        await config.get_access_token()

    url = f"{config.base_url}{endpoint}"

    try:
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

            # Record success for circuit breaker
            await circuit_breaker.record_success()

            return response.json()

    except httpx.HTTPStatusError as e:
        # Record failure for circuit breaker (only for 5xx errors)
        if e.response.status_code >= 500:
            await circuit_breaker.record_failure()
            logger.warning(
                f"Server error {e.response.status_code} from {endpoint} "
                f"(circuit breaker: {circuit_breaker.failures}/{circuit_breaker.failure_threshold})"
            )
        raise

    except Exception:
        # Other errors (timeout, connection, etc.)
        logger.exception(f"API call to {endpoint} failed")
        raise
