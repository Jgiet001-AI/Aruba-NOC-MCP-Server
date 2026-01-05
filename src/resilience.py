"""
Resilience Patterns - Rate Limiting and Circuit Breaker for API calls

This module provides production-grade resilience patterns for the Aruba Central API client:
- Token Bucket Rate Limiter: Prevents API throttling
- Circuit Breaker: Fails fast when API is down

Both patterns use pure Python async without external dependencies.
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import TypeVar

logger = logging.getLogger("aruba-noc-server")

T = TypeVar("T")


# =============================================================================
# RATE LIMITER - Token Bucket Algorithm
# =============================================================================


class RateLimiter:
    """
    Token bucket rate limiter for API calls.

    The token bucket algorithm allows:
    - Smooth rate limiting over time
    - Burst capacity for short periods
    - Fair distribution of requests

    Example:
        limiter = RateLimiter(max_requests=100, window_seconds=60)

        async def make_api_call():
            await limiter.acquire()  # Wait for token
            # Make API call
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize the rate limiter.

        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.tokens = max_requests  # Start with full bucket
        self.last_refill = datetime.now(UTC)
        self.lock = asyncio.Lock()

        logger.info(f"Rate limiter initialized: {max_requests} requests per {window_seconds}s")

    async def acquire(self):
        """
        Acquire a token, waiting if necessary.

        This method blocks until a token is available, then consumes it.
        """
        async with self.lock:
            await self._refill_tokens()

            # Wait if no tokens available
            while self.tokens < 1:
                logger.debug("Rate limit reached, waiting for token...")
                await asyncio.sleep(0.1)
                await self._refill_tokens()

            # Consume one token
            self.tokens -= 1
            logger.debug(f"Token acquired ({self.tokens} remaining)")

    async def _refill_tokens(self):
        """Refill tokens based on elapsed time."""
        now = datetime.now(UTC)
        elapsed = (now - self.last_refill).total_seconds()

        # Calculate refill rate (tokens per second)
        refill_rate = self.max_requests / self.window.total_seconds()

        # Add tokens proportional to time elapsed
        tokens_to_add = int(elapsed * refill_rate)

        if tokens_to_add > 0:
            self.tokens = min(self.max_requests, self.tokens + tokens_to_add)
            self.last_refill = now


# =============================================================================
# CIRCUIT BREAKER - Fail Fast Pattern
# =============================================================================


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit broken, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""


class CircuitBreaker:
    """
    Circuit breaker pattern for API resilience.

    Prevents cascading failures by:
    - Detecting repeated failures
    - Opening circuit to fail fast
    - Testing recovery periodically

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject all requests
    - HALF_OPEN: Testing if service recovered

    Example:
        breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=60)

        try:
            breaker.check()  # Raises if circuit is open
            result = await api_call()
            breaker.record_success()
        except APIError:
            breaker.record_failure()
            raise
    """

    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        """
        Initialize the circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Time to wait before testing recovery
        """
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.failures = 0
        self.last_failure_time: datetime | None = None
        self.state = CircuitState.CLOSED
        self.lock = asyncio.Lock()

        logger.info(f"Circuit breaker initialized: threshold={failure_threshold}, timeout={timeout_seconds}s")

    def check(self):
        """
        Check if request should be attempted.

        Raises:
            CircuitBreakerError: If circuit is open
        """
        if self.state == CircuitState.CLOSED:
            return  # Normal operation

        if self.state == CircuitState.OPEN:
            # Check if timeout elapsed
            if self.last_failure_time and datetime.now(UTC) - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker: OPEN → HALF_OPEN (testing recovery)")
                return  # Allow one test request

            # Circuit still open
            raise CircuitBreakerError(
                f"Circuit breaker OPEN - API unavailable. Retry in {self.timeout.total_seconds()}s."
            )

        # HALF_OPEN - allow test request
        return

    async def record_success(self):
        """Record successful API call."""
        async with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                # Service recovered!
                self.state = CircuitState.CLOSED
                self.failures = 0
                logger.info("Circuit breaker: HALF_OPEN → CLOSED (service recovered)")
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failures = 0

    async def record_failure(self):
        """Record failed API call."""
        async with self.lock:
            self.failures += 1
            self.last_failure_time = datetime.now(UTC)

            if self.state == CircuitState.HALF_OPEN:
                # Test failed, reopen circuit
                self.state = CircuitState.OPEN
                logger.warning("Circuit breaker: HALF_OPEN → OPEN (recovery test failed)")

            elif self.failures >= self.failure_threshold:
                # Too many failures, open circuit
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker: CLOSED → OPEN ({self.failures} consecutive failures)")

    async def reset(self):
        """Manually reset circuit breaker."""
        async with self.lock:
            self.failures = 0
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker: Manually reset to CLOSED")


# =============================================================================
# COMBINED RESILIENT WRAPPER
# =============================================================================


async def with_resilience(
    func: Callable[[], T],
    rate_limiter: RateLimiter | None = None,
    circuit_breaker: CircuitBreaker | None = None,
) -> T:
    """
    Execute a function with rate limiting and circuit breaker protection.

    Args:
        func: Async function to execute
        rate_limiter: Optional rate limiter
        circuit_breaker: Optional circuit breaker

    Returns:
        Function result

    Raises:
        CircuitBreakerError: If circuit breaker is open
        Any exceptions from func
    """
    # Check circuit breaker first
    if circuit_breaker:
        circuit_breaker.check()

    # Acquire rate limit token
    if rate_limiter:
        await rate_limiter.acquire()

    # Execute function
    try:
        result = await func()
    except Exception as e:
        # Record failure (only for 5xx errors, not client errors)
        if circuit_breaker:
            # Check if it's a server error (5xx)
            import httpx

            if isinstance(e, httpx.HTTPStatusError) and e.response.status_code >= 500:
                await circuit_breaker.record_failure()

        raise
    else:
        # Record success
        if circuit_breaker:
            await circuit_breaker.record_success()

        return result
