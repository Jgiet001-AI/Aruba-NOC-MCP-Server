"""
Health Check Tool - Server and Dependency Status Monitoring

This MCP tool provides comprehensive health check capabilities for the Aruba NOC MCP Server.
It checks:
- OAuth2 authentication status and token expiration
- Circuit breaker state
- Rate limiter capacity
- Aruba Central API connectivity

Usage:
    Claude can call this tool to diagnose server issues:
    "Check server health" -> Calls check_server_health tool

    External monitoring can also invoke this via MCP protocol.
"""

import json
import logging
from datetime import UTC, datetime

import httpx
from mcp import types

from src.resilience import CircuitState

logger = logging.getLogger("aruba-noc-server")


async def handle_check_server_health() -> list[types.TextContent]:
    """
    Check MCP server health status including dependencies and resilience state.

    This tool provides a comprehensive health report that includes:
    - Overall status: healthy, degraded, or unhealthy
    - Authentication: Token status and expiration
    - Circuit breaker: Current state and failure count
    - Rate limiter: Token availability and utilization
    - Aruba API: Connectivity test

    Returns:
        Health status report in JSON format

    Example Response:
        {
          "status": "healthy",
          "timestamp": "2025-01-05T12:00:00Z",
          "components": {
            "auth": {
              "status": "healthy",
              "token_expires_in_seconds": 3542
            },
            "circuit_breaker": {
              "status": "healthy",
              "state": "closed",
              "failures": 0,
              "threshold": 5
            },
            "rate_limiter": {
              "status": "healthy",
              "tokens_available": 95,
              "max_tokens": 100,
              "utilization_percentage": 5.0
            },
            "aruba_api": {
              "status": "healthy",
              "response_code": 200,
              "latency_ms": 145
            }
          }
        }
    """
    from src.api_client import circuit_breaker, rate_limiter
    from src.config import config
    from src.observability import update_health_status

    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "1.0.0",
        "components": {},
    }

    dependencies_up = 0
    total_dependencies = 4  # auth, circuit_breaker, rate_limiter, aruba_api

    # ==========================================================================
    # Check OAuth2 Authentication
    # ==========================================================================

    try:
        if not config.access_token:
            health_status["components"]["auth"] = {
                "status": "degraded",
                "message": "No access token - will generate on first API call",
                "requires_credentials": bool(config.client_id and config.client_secret),
            }
            logger.warning("Health check: No access token available")

        elif config._is_token_expired():
            health_status["components"]["auth"] = {
                "status": "degraded",
                "message": "Token expired - will refresh proactively on next call",
            }
            logger.warning("Health check: Token expired")

        else:
            # Token is valid
            if config._token_expiry:
                expiry_seconds = (config._token_expiry - datetime.now(UTC)).total_seconds()
                health_status["components"]["auth"] = {
                    "status": "healthy",
                    "token_expires_in_seconds": int(expiry_seconds),
                    "expires_at": config._token_expiry.isoformat(),
                }
                dependencies_up += 1
            else:
                # Token exists but no expiry tracking
                health_status["components"]["auth"] = {
                    "status": "healthy",
                    "message": "Token available (expiry unknown)",
                }
                dependencies_up += 1

    except Exception as e:
        health_status["components"]["auth"] = {
            "status": "unhealthy",
            "error": str(e),
            "error_type": type(e).__name__,
        }
        health_status["status"] = "unhealthy"
        logger.error(f"Health check: Auth component error - {e}")

    # ==========================================================================
    # Check Circuit Breaker
    # ==========================================================================

    try:
        state_str = circuit_breaker.state.value
        failure_percentage = (circuit_breaker.failures / circuit_breaker.failure_threshold) * 100

        component_status = {
            "state": state_str,
            "failures": circuit_breaker.failures,
            "threshold": circuit_breaker.failure_threshold,
            "failure_percentage": round(failure_percentage, 2),
        }

        if circuit_breaker.state == CircuitState.CLOSED:
            component_status["status"] = "healthy"
            dependencies_up += 1
        elif circuit_breaker.state == CircuitState.HALF_OPEN:
            component_status["status"] = "degraded"
            component_status["message"] = "Testing recovery - one test request allowed"
        else:  # OPEN
            component_status["status"] = "unhealthy"
            component_status["message"] = "Circuit open - API calls blocked"

            # Calculate time until recovery test
            if circuit_breaker.last_failure_time:
                time_since_failure = (datetime.now(UTC) - circuit_breaker.last_failure_time).total_seconds()
                timeout_seconds = circuit_breaker.timeout.total_seconds()
                retry_in = max(0, timeout_seconds - time_since_failure)

                component_status["retry_in_seconds"] = int(retry_in)

            health_status["status"] = "degraded"  # Degraded, not unhealthy (will recover)

        health_status["components"]["circuit_breaker"] = component_status

    except Exception as e:
        health_status["components"]["circuit_breaker"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "unhealthy"
        logger.error(f"Health check: Circuit breaker component error - {e}")

    # ==========================================================================
    # Check Rate Limiter
    # ==========================================================================

    try:
        tokens_percentage = (rate_limiter.tokens / rate_limiter.max_requests) * 100

        component_status = {
            "tokens_available": int(rate_limiter.tokens),
            "max_tokens": rate_limiter.max_requests,
            "utilization_percentage": round(100 - tokens_percentage, 2),
        }

        # Status based on token availability
        if tokens_percentage > 50:
            component_status["status"] = "healthy"
            dependencies_up += 1
        elif tokens_percentage > 10:
            component_status["status"] = "degraded"
            component_status["message"] = "Token capacity below 50%"
        else:
            component_status["status"] = "degraded"
            component_status["message"] = "Token capacity critically low"
            health_status["status"] = "degraded"

        health_status["components"]["rate_limiter"] = component_status

    except Exception as e:
        health_status["components"]["rate_limiter"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "unhealthy"
        logger.error(f"Health check: Rate limiter component error - {e}")

    # ==========================================================================
    # Check Aruba API Connectivity
    # ==========================================================================

    try:
        # Quick connectivity test with timeout
        # Use a lightweight endpoint that doesn't require heavy processing
        start_time = datetime.now(UTC)

        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try a simple GET to the base URL (should return 401 or redirect, but confirms connectivity)
            response = await client.get(
                config.base_url,
                follow_redirects=False,
            )

            latency_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            component_status = {
                "response_code": response.status_code,
                "latency_ms": latency_ms,
            }

            # We expect 401 (no auth), 301/302 (redirect), or 403 (forbidden without path)
            # Anything but 5xx indicates API is reachable
            if response.status_code < 500:
                component_status["status"] = "healthy"
                dependencies_up += 1

                if latency_ms > 2000:
                    component_status["message"] = "High latency detected"
                    component_status["status"] = "degraded"

            else:
                component_status["status"] = "unhealthy"
                component_status["message"] = f"Server error: {response.status_code}"
                health_status["status"] = "degraded"

            health_status["components"]["aruba_api"] = component_status

    except httpx.TimeoutException:
        health_status["components"]["aruba_api"] = {
            "status": "unhealthy",
            "error": "Connection timeout (>5s)",
            "error_type": "TimeoutException",
        }
        health_status["status"] = "unhealthy"
        logger.error("Health check: Aruba API connectivity timeout")

    except Exception as e:
        health_status["components"]["aruba_api"] = {
            "status": "unhealthy",
            "error": str(e),
            "error_type": type(e).__name__,
        }
        health_status["status"] = "unhealthy"
        logger.error(f"Health check: Aruba API connectivity error - {e}")

    # ==========================================================================
    # Calculate Overall Health
    # ==========================================================================

    health_status["dependencies"] = {
        "healthy": dependencies_up,
        "total": total_dependencies,
        "percentage": round((dependencies_up / total_dependencies) * 100, 2),
    }

    # Update observability metrics
    update_health_status(
        healthy=(health_status["status"] == "healthy"),
        dependencies_up=dependencies_up,
    )

    logger.info(
        f"Health check completed: {health_status['status']} "
        f"({dependencies_up}/{total_dependencies} dependencies healthy)"
    )

    return [
        types.TextContent(
            type="text",
            text=json.dumps(health_status, indent=2),
        )
    ]
