"""
Observability - Metrics, Tracing, and Logging for Production Monitoring

This module provides OpenTelemetry-based instrumentation for the Aruba NOC MCP Server.
Metrics are exposed via Prometheus format for scraping by monitoring systems.

Key metrics tracked:
- API calls (success/failure rates, latency)
- Circuit breaker state transitions
- Rate limiter utilization
- OAuth2 token refresh events
- Health check status

Usage:
    from src.observability import (
        api_calls_total,
        api_call_duration_seconds,
        circuit_breaker_state_gauge,
        record_api_call,
    )

    # Record API call
    with record_api_call(endpoint="/test", method="GET"):
        result = await call_api()
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Literal

from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger("aruba-noc-server")

# =============================================================================
# OpenTelemetry Setup
# =============================================================================

# Create resource with service information
resource = Resource.create(
    {
        "service.name": "aruba-noc-server",
        "service.version": os.getenv("APP_VERSION", "1.0.0"),
        "deployment.environment": os.getenv("ENVIRONMENT", "production"),
    }
)

# Initialize meter provider with Prometheus exporter
# Metrics will be available at http://localhost:8000/metrics by default
meter_provider = MeterProvider(
    resource=resource,
    metric_readers=[PrometheusMetricReader()],
)

# Set as global meter provider
metrics.set_meter_provider(meter_provider)

# Create meter for this service
meter = metrics.get_meter("aruba-noc-server", "1.0.0")

logger.info("OpenTelemetry metrics initialized with Prometheus exporter")


# =============================================================================
# API Client Metrics
# =============================================================================

api_calls_total = meter.create_counter(
    name="api_calls_total",
    description="Total number of API calls made to Aruba Central",
    unit="calls",
)

api_call_duration_seconds = meter.create_histogram(
    name="api_call_duration_seconds",
    description="Duration of API calls in seconds",
    unit="s",
)

api_retries_total = meter.create_counter(
    name="api_retries_total",
    description="Total number of API call retries",
    unit="retries",
)

# =============================================================================
# OAuth2 Authentication Metrics
# =============================================================================

oauth2_token_refreshes_total = meter.create_counter(
    name="oauth2_token_refreshes_total",
    description="Total number of OAuth2 token refresh attempts",
    unit="refreshes",
)

oauth2_token_refresh_duration_seconds = meter.create_histogram(
    name="oauth2_token_refresh_duration_seconds",
    description="Duration of OAuth2 token refresh requests",
    unit="s",
)

oauth2_concurrent_refresh_prevented = meter.create_counter(
    name="oauth2_concurrent_refresh_prevented",
    description="Number of times concurrent token refresh was prevented by lock",
    unit="events",
)

token_expiry_buffer_seconds = meter.create_gauge(
    name="token_expiry_buffer_seconds",
    description="Seconds until OAuth2 token expires",
    unit="s",
)

# =============================================================================
# Circuit Breaker Metrics
# =============================================================================

circuit_breaker_state_gauge = meter.create_gauge(
    name="circuit_breaker_state",
    description="Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)",
    unit="state",
)

circuit_breaker_failures = meter.create_gauge(
    name="circuit_breaker_failures",
    description="Current consecutive failure count in circuit breaker",
    unit="failures",
)

circuit_breaker_opens_total = meter.create_counter(
    name="circuit_breaker_opens_total",
    description="Total number of times circuit breaker opened",
    unit="opens",
)

circuit_breaker_half_open_success = meter.create_counter(
    name="circuit_breaker_half_open_success",
    description="Successful recovery tests in HALF_OPEN state",
    unit="successes",
)

circuit_breaker_half_open_failure = meter.create_counter(
    name="circuit_breaker_half_open_failure",
    description="Failed recovery tests in HALF_OPEN state",
    unit="failures",
)

# =============================================================================
# Rate Limiter Metrics
# =============================================================================

rate_limiter_tokens_available = meter.create_gauge(
    name="rate_limiter_tokens_available",
    description="Current number of available rate limit tokens",
    unit="tokens",
)

rate_limiter_wait_time_seconds = meter.create_histogram(
    name="rate_limiter_wait_time_seconds",
    description="Time spent waiting for rate limit tokens",
    unit="s",
)

rate_limiter_throttled_requests = meter.create_counter(
    name="rate_limiter_throttled_requests",
    description="Number of requests that had to wait for tokens",
    unit="requests",
)

# =============================================================================
# Health Check Metrics
# =============================================================================

health_check_status = meter.create_gauge(
    name="health_check_status",
    description="Overall server health status (0=unhealthy, 1=healthy)",
    unit="status",
)

health_check_dependencies_up = meter.create_gauge(
    name="health_check_dependencies_up",
    description="Number of dependencies that are healthy",
    unit="dependencies",
)

# =============================================================================
# Helper Functions
# =============================================================================


@asynccontextmanager
async def record_api_call(
    endpoint: str,
    method: str = "GET",
    record_retries: bool = False,
):
    """
    Context manager to record API call metrics.

    Automatically tracks:
    - Call duration
    - Success/failure status
    - Status codes
    - Retries (if record_retries=True)

    Example:
        async with record_api_call("/monitoring/v2/devices", method="GET"):
            result = await call_aruba_api("/monitoring/v2/devices")

    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, etc.)
        record_retries: Whether this is a retry attempt
    """
    start_time = time.time()
    status = "unknown"
    status_code = None

    try:
        yield
        status = "success"
        status_code = "2xx"
    except Exception as e:
        status = "failure"

        # Extract status code if available
        if hasattr(e, "response") and hasattr(e.response, "status_code"):
            status_code = f"{e.response.status_code}"
        else:
            status_code = "error"

        raise
    finally:
        # Record duration
        duration = time.time() - start_time
        api_call_duration_seconds.record(
            duration,
            attributes={
                "endpoint": endpoint,
                "method": method,
                "status": status,
            },
        )

        # Record call count
        api_calls_total.add(
            1,
            attributes={
                "endpoint": endpoint,
                "method": method,
                "status": status,
                "status_code": status_code or "unknown",
            },
        )

        # Record retry if applicable
        if record_retries:
            api_retries_total.add(
                1,
                attributes={
                    "endpoint": endpoint,
                },
            )

        logger.debug(
            f"API call recorded: {method} {endpoint} - {status} "
            f"({duration:.3f}s) [status_code={status_code}]"
        )


def record_token_refresh(duration_seconds: float, success: bool):
    """
    Record OAuth2 token refresh metrics.

    Args:
        duration_seconds: Time taken to refresh token
        success: Whether refresh was successful
    """
    oauth2_token_refreshes_total.add(
        1,
        attributes={
            "status": "success" if success else "failure",
        },
    )

    if success:
        oauth2_token_refresh_duration_seconds.record(duration_seconds)

    logger.debug(f"Token refresh recorded: {'success' if success else 'failure'} ({duration_seconds:.3f}s)")


def update_circuit_breaker_state(
    state: Literal["CLOSED", "OPEN", "HALF_OPEN"],
    failures: int,
):
    """
    Update circuit breaker state metrics.

    Args:
        state: Current circuit breaker state
        failures: Current consecutive failure count
    """
    state_value = {
        "CLOSED": 0,
        "OPEN": 1,
        "HALF_OPEN": 2,
    }[state]

    circuit_breaker_state_gauge.set(state_value)
    circuit_breaker_failures.set(failures)

    logger.debug(f"Circuit breaker state updated: {state} (failures={failures})")


def record_circuit_breaker_open():
    """Record circuit breaker opening event."""
    circuit_breaker_opens_total.add(1)
    logger.warning("Circuit breaker opened - API unavailable")


def record_circuit_breaker_recovery(success: bool):
    """
    Record circuit breaker recovery test result.

    Args:
        success: Whether recovery test succeeded
    """
    if success:
        circuit_breaker_half_open_success.add(1)
        logger.info("Circuit breaker recovery test succeeded - transitioning to CLOSED")
    else:
        circuit_breaker_half_open_failure.add(1)
        logger.warning("Circuit breaker recovery test failed - reopening circuit")


def update_rate_limiter_tokens(tokens_available: int):
    """
    Update rate limiter token availability.

    Args:
        tokens_available: Current number of available tokens
    """
    rate_limiter_tokens_available.set(tokens_available)


@asynccontextmanager
async def record_rate_limit_wait():
    """
    Context manager to record rate limit wait time.

    Example:
        async with record_rate_limit_wait():
            await rate_limiter.acquire()
    """
    start_time = time.time()

    try:
        yield
    finally:
        wait_time = time.time() - start_time

        # Only record if we actually waited
        if wait_time > 0.01:  # 10ms threshold
            rate_limiter_wait_time_seconds.record(wait_time)
            rate_limiter_throttled_requests.add(1)
            logger.debug(f"Rate limit wait recorded: {wait_time:.3f}s")


def update_health_status(healthy: bool, dependencies_up: int = 0):
    """
    Update health check metrics.

    Args:
        healthy: Whether server is healthy overall
        dependencies_up: Number of healthy dependencies
    """
    health_check_status.set(1 if healthy else 0)
    health_check_dependencies_up.set(dependencies_up)

    logger.debug(f"Health status updated: {'healthy' if healthy else 'unhealthy'} (deps={dependencies_up})")


# =============================================================================
# Prometheus Metrics Endpoint
# =============================================================================


def get_prometheus_metrics() -> str:
    """
    Get Prometheus-formatted metrics.

    This is exposed via the /metrics endpoint for scraping.

    Returns:
        Prometheus text format metrics
    """
    # OpenTelemetry's PrometheusMetricReader handles the formatting
    # This function is just a placeholder for integration with web frameworks
    logger.debug("Prometheus metrics requested")
    return "# Metrics available at the configured PrometheusMetricReader endpoint\n"
