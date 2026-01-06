# Production Monitoring Plan - Aruba NOC MCP Server

## Executive Summary

This document outlines a comprehensive production monitoring strategy for the Aruba NOC MCP Server, focusing on observability, resilience patterns, and proactive alerting to ensure high availability and optimal performance.

## 1. Key Metrics to Monitor

### 1.1 API Client Metrics

| Metric | Type | Purpose | Alert Threshold |
|--------|------|---------|-----------------|
| `api_calls_total` | Counter | Total API calls made | N/A (trending) |
| `api_calls_success` | Counter | Successful API calls | Success rate < 95% |
| `api_calls_failure` | Counter | Failed API calls by status code | 5xx error rate > 5% |
| `api_call_duration_seconds` | Histogram | API call latency distribution | P95 > 5s |
| `api_retries_total` | Counter | Retry attempts per endpoint | > 10/min |

### 1.2 Authentication Metrics

| Metric | Type | Purpose | Alert Threshold |
|--------|------|---------|-----------------|
| `oauth2_token_refreshes_total` | Counter | Token refresh attempts | > 1/hour (normal: 1/3600s) |
| `oauth2_token_refresh_failures` | Counter | Failed token refreshes | > 0 (critical) |
| `oauth2_token_refresh_duration_seconds` | Histogram | OAuth2 request latency | P95 > 2s |
| `oauth2_concurrent_refresh_prevented` | Counter | Duplicate refreshes prevented by lock | Trending (indicates concurrency) |
| `token_expiry_buffer_seconds` | Gauge | Time until token expires | < 120s (warning) |

### 1.3 Circuit Breaker Metrics

| Metric | Type | Purpose | Alert Threshold |
|--------|------|---------|-----------------|
| `circuit_breaker_state` | Gauge | Current state (0=CLOSED, 1=OPEN, 2=HALF_OPEN) | > 0 (critical) |
| `circuit_breaker_failures` | Counter | Consecutive failures | >= 4 (warning, 5 triggers) |
| `circuit_breaker_opens_total` | Counter | Times circuit opened | > 0 (critical) |
| `circuit_breaker_half_open_success` | Counter | Successful recovery tests | Trending |
| `circuit_breaker_half_open_failure` | Counter | Failed recovery tests | > 3 consecutive |

### 1.4 Rate Limiter Metrics

| Metric | Type | Purpose | Alert Threshold |
|--------|------|---------|-----------------|
| `rate_limiter_tokens_available` | Gauge | Current token count | < 10% capacity |
| `rate_limiter_wait_time_seconds` | Histogram | Time spent waiting for tokens | P95 > 1s |
| `rate_limiter_throttled_requests` | Counter | Requests that had to wait | Trending |

### 1.5 Health Check Metrics

| Metric | Type | Purpose | Alert Threshold |
|--------|------|---------|-----------------|
| `health_check_status` | Gauge | Overall health (0=unhealthy, 1=healthy) | = 0 (critical) |
| `health_check_dependencies_up` | Gauge | Dependency availability | < 1.0 (warning) |

## 2. Alerting Rules

### 2.1 Critical Alerts (Page On-Call)

```yaml
# Circuit Breaker Open
- alert: CircuitBreakerOpen
  expr: circuit_breaker_state > 0
  for: 1m
  severity: critical
  description: "Circuit breaker is OPEN - API unavailable"
  action: "Check Aruba Central API status, verify credentials"

# OAuth2 Token Refresh Failure
- alert: OAuth2TokenRefreshFailed
  expr: oauth2_token_refresh_failures > 0
  for: 0s
  severity: critical
  description: "Unable to refresh OAuth2 token - check credentials"
  action: "Verify ARUBA_CLIENT_ID and ARUBA_CLIENT_SECRET"

# High API Failure Rate
- alert: HighAPIFailureRate
  expr: (api_calls_failure / api_calls_total) > 0.10
  for: 5m
  severity: critical
  description: "API failure rate above 10% for 5 minutes"
  action: "Check API logs, verify Aruba Central service status"

# Health Check Failed
- alert: HealthCheckFailed
  expr: health_check_status == 0
  for: 2m
  severity: critical
  description: "MCP server health check failing"
  action: "Check server logs, verify dependencies"
```

### 2.2 Warning Alerts (Slack/Email)

```yaml
# Token Expiring Soon (No Refresh)
- alert: TokenExpiringSoon
  expr: token_expiry_buffer_seconds < 120
  for: 1m
  severity: warning
  description: "OAuth2 token expires in < 2 minutes but not refreshing"
  action: "Check token refresh logic, verify credentials"

# High Retry Rate
- alert: HighRetryRate
  expr: rate(api_retries_total[5m]) > 10
  for: 5m
  severity: warning
  description: "API retry rate elevated - possible connectivity issues"
  action: "Check network connectivity to Aruba Central"

# Rate Limiter Pressure
- alert: RateLimiterPressure
  expr: rate_limiter_tokens_available < 10
  for: 2m
  severity: warning
  description: "Rate limiter tokens nearly exhausted"
  action: "Consider increasing rate limit or scaling workload"
```

## 3. Metrics Collection Implementation

### 3.1 Recommended Approach: OpenTelemetry + Prometheus

**Why OpenTelemetry?**
- Vendor-neutral, future-proof instrumentation
- Built-in support for metrics, traces, and logs
- Native Python support via `opentelemetry-api` and `opentelemetry-sdk`
- Easy integration with Prometheus, Grafana, Datadog, etc.

**Architecture**:
```
Aruba MCP Server → OpenTelemetry Collector → Prometheus → Grafana
                                           ↓
                                     Alertmanager
```

### 3.2 Code Structure

Create `src/observability.py`:
```python
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader

# Initialize meter provider
meter_provider = MeterProvider(
    metric_readers=[PrometheusMetricReader()]
)
metrics.set_meter_provider(meter_provider)

# Create meter for this service
meter = metrics.get_meter("aruba-noc-server")

# Define metrics
api_calls_total = meter.create_counter(
    "api_calls_total",
    description="Total API calls made",
    unit="calls"
)

circuit_breaker_state = meter.create_gauge(
    "circuit_breaker_state",
    description="Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)",
    unit="state"
)
```

### 3.3 Instrumentation Points

**In `src/api_client.py`**:
```python
from src.observability import api_calls_total, api_call_duration_seconds

async def call_aruba_api(...):
    start_time = time.time()

    try:
        # ... API call logic ...
        api_calls_total.add(1, {"endpoint": endpoint, "status": "success"})
        return result
    except httpx.HTTPStatusError as e:
        api_calls_total.add(1, {"endpoint": endpoint, "status": f"{e.response.status_code}"})
        raise
    finally:
        duration = time.time() - start_time
        api_call_duration_seconds.record(duration, {"endpoint": endpoint})
```

**In `src/resilience.py`**:
```python
from src.observability import circuit_breaker_state

async def record_failure(self):
    async with self.lock:
        self.failures += 1
        # ... state transition logic ...

        # Update metric
        state_value = {
            CircuitState.CLOSED: 0,
            CircuitState.OPEN: 1,
            CircuitState.HALF_OPEN: 2
        }[self.state]
        circuit_breaker_state.set(state_value)
```

## 4. Health Check Endpoint

### 4.1 MCP Tool: `check_server_health`

Create `src/tools/health.py`:
```python
async def handle_check_server_health() -> list[types.TextContent]:
    """
    Check MCP server health status including dependencies and resilience state.

    Returns:
        Health status with metrics and dependency checks
    """
    from src.api_client import circuit_breaker, rate_limiter
    from src.config import config

    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "components": {}
    }

    # Check OAuth2 token
    try:
        if not config.access_token:
            health_status["components"]["auth"] = {
                "status": "degraded",
                "message": "No access token - will generate on first API call"
            }
        elif config._is_token_expired():
            health_status["components"]["auth"] = {
                "status": "degraded",
                "message": "Token expired - will refresh on next call"
            }
        else:
            expiry_seconds = (config._token_expiry - datetime.now(UTC)).total_seconds()
            health_status["components"]["auth"] = {
                "status": "healthy",
                "token_expires_in_seconds": int(expiry_seconds)
            }
    except Exception as e:
        health_status["components"]["auth"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"

    # Check circuit breaker
    health_status["components"]["circuit_breaker"] = {
        "status": "healthy" if circuit_breaker.state == CircuitState.CLOSED else "degraded",
        "state": circuit_breaker.state.value,
        "failures": circuit_breaker.failures,
        "threshold": circuit_breaker.failure_threshold
    }

    if circuit_breaker.state == CircuitState.OPEN:
        health_status["status"] = "degraded"

    # Check rate limiter
    tokens_percentage = (rate_limiter.tokens / rate_limiter.max_requests) * 100
    health_status["components"]["rate_limiter"] = {
        "status": "healthy" if tokens_percentage > 10 else "degraded",
        "tokens_available": int(rate_limiter.tokens),
        "max_tokens": rate_limiter.max_requests,
        "utilization_percentage": round(100 - tokens_percentage, 2)
    }

    # Check Aruba API connectivity
    try:
        # Quick connectivity test (with timeout)
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{config.base_url}/platform/licensing/v1/customer/licenses")
            health_status["components"]["aruba_api"] = {
                "status": "healthy" if response.status_code < 500 else "degraded",
                "response_code": response.status_code
            }
    except Exception as e:
        health_status["components"]["aruba_api"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"

    return [types.TextContent(
        type="text",
        text=json.dumps(health_status, indent=2)
    )]
```

### 4.2 Register in `src/server.py`:

```python
@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""

    if name == "check_server_health":
        from src.tools.health import handle_check_server_health
        return await handle_check_server_health()

    # ... existing tool handlers ...
```

## 5. Grafana Dashboard Layout

### 5.1 Overview Panel

- **Server Health Status**: Binary indicator (green/red)
- **API Success Rate**: Gauge (target: > 99%)
- **Circuit Breaker State**: Indicator with color coding
- **Active API Calls**: Current in-flight requests

### 5.2 Performance Panel

- **API Latency (P50, P95, P99)**: Line graph over time
- **Throughput (req/min)**: Line graph
- **Error Rate by Status Code**: Stacked bar chart

### 5.3 Resilience Panel

- **Circuit Breaker Timeline**: State changes over time
- **Rate Limiter Tokens**: Gauge with threshold line
- **Retry Distribution**: Heatmap

### 5.4 Authentication Panel

- **Token Refresh Events**: Event markers on timeline
- **Token Expiry Countdown**: Gauge
- **OAuth2 Latency**: Line graph

## 6. Implementation Roadmap

### Phase 1: Core Metrics (Week 1)
- [ ] Create `src/observability.py` with OpenTelemetry setup
- [ ] Instrument `call_aruba_api()` with success/failure counters
- [ ] Instrument circuit breaker state transitions
- [ ] Add Prometheus exporter on `/metrics` endpoint
- [ ] Deploy Prometheus scraper configuration

### Phase 2: Health Checks (Week 1)
- [ ] Implement `check_server_health` MCP tool
- [ ] Add dependency checks (Aruba API connectivity)
- [ ] Create automated health check tests

### Phase 3: Alerting (Week 2)
- [ ] Deploy Prometheus Alertmanager
- [ ] Configure critical alerts (circuit breaker, OAuth2 failures)
- [ ] Configure warning alerts (high retry rate, token expiry)
- [ ] Set up PagerDuty/Slack/email integrations

### Phase 4: Dashboards (Week 2)
- [ ] Create Grafana dashboard with recommended panels
- [ ] Configure retention policies (30 days high-res, 1 year aggregated)
- [ ] Set up dashboard access controls

### Phase 5: Advanced Observability (Week 3+)
- [ ] Add distributed tracing (OpenTelemetry traces)
- [ ] Implement structured logging with correlation IDs
- [ ] Create runbooks for common alert scenarios
- [ ] Set up SLO/SLI tracking (99.9% availability)

## 7. Cost Optimization

- **Prometheus**: Self-hosted (free), ~50GB storage for 30 days
- **Grafana**: Self-hosted (free) or Grafana Cloud (free tier)
- **OpenTelemetry**: Free, open-source
- **Total estimated cost**: $0 - $50/month (depending on scale)

## 8. Best Practices

### 8.1 Metric Naming Conventions

Follow Prometheus naming conventions:
- Counter suffix: `_total` (e.g., `api_calls_total`)
- Histogram suffix: `_seconds` (e.g., `api_call_duration_seconds`)
- Gauge: descriptive name (e.g., `circuit_breaker_state`)

### 8.2 Label Cardinality

⚠️ **Avoid high-cardinality labels** (e.g., user IDs, timestamps)

✅ **Good labels**:
- `endpoint`: Limited set of API endpoints
- `status_code`: HTTP status codes (200, 401, 500, etc.)
- `method`: HTTP methods (GET, POST)

❌ **Bad labels**:
- `request_id`: Unique per request (unbounded)
- `timestamp`: Unique per metric (use built-in time)

### 8.3 Alert Fatigue Prevention

- Use `for:` duration to prevent flapping alerts
- Set appropriate thresholds based on baseline data
- Aggregate alerts (don't alert on every single failure)
- Include runbook links in alert descriptions

## 9. Runbook Examples

### Circuit Breaker Opened

**Symptom**: `CircuitBreakerOpen` alert firing

**Diagnosis**:
1. Check Grafana dashboard for API error rate
2. Review Aruba Central status page: https://status.central.arubanetworks.com
3. Examine recent API error logs

**Remediation**:
1. If Aruba Central is down: Wait for service recovery
2. If credentials invalid: Rotate OAuth2 credentials
3. If transient: Circuit will auto-recover in 60s
4. Manual reset: Use health check endpoint to verify, then restart if needed

### OAuth2 Token Refresh Failure

**Symptom**: `OAuth2TokenRefreshFailed` alert firing

**Diagnosis**:
1. Verify `ARUBA_CLIENT_ID` and `ARUBA_CLIENT_SECRET` environment variables
2. Check Docker secrets are mounted correctly
3. Test credentials manually using OAuth2 token endpoint

**Remediation**:
1. Rotate credentials via Aruba Central dashboard
2. Update Docker secrets
3. Restart MCP server to pick up new credentials

## 10. Security Considerations

- **Never log sensitive metrics**: Don't include tokens, secrets in metrics
- **Restrict metrics endpoint**: Use authentication for `/metrics` in production
- **Encrypt metric traffic**: Use TLS for Prometheus scraping
- **Audit access**: Monitor who accesses metrics and dashboards

## 11. LangSmith Integration (Tool Usage Analytics)

### 11.1 Overview

**LangSmith** is now integrated alongside OpenTelemetry/Prometheus for comprehensive observability. While Prometheus monitors **infrastructure health** (API status, circuit breaker, rate limits), LangSmith tracks **application behavior** (how Claude uses MCP tools).

### 11.2 What LangSmith Monitors

LangSmith provides insights into Claude's tool usage patterns:

| Metric | Description | Use Case |
|--------|-------------|----------|
| **Tool Call Volume** | Number of times each tool is called | Identify most popular tools |
| **Success Rate** | Percentage of successful vs failed calls | Detect problematic tools |
| **Latency** | P50/P95/P99 latency per tool | Find slow tools |
| **Error Patterns** | Common failure reasons | Debug recurring issues |
| **Session Flows** | Multi-tool workflows | Understand user patterns |

### 11.3 Configuration

LangSmith is **already configured** and ready to use:

```bash
# .env (configured with your API key)
LANGSMITH_API_KEY=lsv2_pt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx_xxxxxxxxxxxx
LANGSMITH_PROJECT=aruba-noc-server
LANGSMITH_TRACING=true
```

**Dashboard URL**: https://smith.langchain.com/o/default/projects/p/aruba-noc-server

### 11.4 What You'll See in LangSmith

#### Dashboard View:
- **Tool Call Volume**: Bar chart showing usage of each MCP tool
- **Success Rate**: Percentage by tool (e.g., `get_device_details`: 98.5%)
- **P95 Latency**: Latency distribution (e.g., `list_all_clients`: 1.2s)
- **Error Breakdown**: Common failure reasons (401, 500, timeouts)

#### Trace View (Waterfall):
```
Session: Claude helping with device diagnostics
├─ check_server_health (250ms) ✅
├─ get_sites_health (1.2s) ✅
│  └─ API Call: /monitoring/v2/sites (980ms)
├─ get_device_details [serial=ABC123] (850ms) ✅
│  └─ API Call: /monitoring/v2/devices/ABC123 (720ms)
└─ ping_from_ap [serial=ABC123, target=8.8.8.8] (2.1s) ✅
   └─ API Call: /troubleshooting/v1/ping (1.9s)
```

### 11.5 LangSmith vs Prometheus

**Complementary, Not Redundant**:

| Question | Answer Source |
|----------|--------------|
| "Which tools does Claude use most?" | **LangSmith** |
| "Is `get_device_details` slow?" | **LangSmith** (latency) |
| "Why did this tool call fail?" | **LangSmith** (error trace) |
| "Is the circuit breaker open?" | **Prometheus** |
| "Are we hitting rate limits?" | **Prometheus** |
| "When does the OAuth2 token expire?" | **Prometheus** |
| "Should we page on-call?" | **Prometheus** (alerts) |

**Example Scenario**:
- **Prometheus**: "Circuit breaker opened 3 times today (infrastructure issue)"
- **LangSmith**: "Claude called `get_device_details` 100 times today with 95% success (application usage)"

Both are valuable for different perspectives on the same system.

### 11.6 Accessing LangSmith

1. **Open Dashboard**: https://smith.langchain.com
2. **Navigate to Project**: "aruba-noc-server"
3. **View Traces**: See individual tool calls
4. **View Metrics**: See aggregated success rates and latency

### 11.7 Typical Queries

**"Which tools are most popular?"**
- Navigate to: Dashboard → "aruba-noc-server" → Metrics
- View: Tool call volume bar chart

**"Why did this tool call fail?"**
- Navigate to: Dashboard → "aruba-noc-server" → Traces
- Filter by: Status = Failed
- Click trace to see: Full error details, stack trace, arguments

**"How fast is `list_all_clients`?"**
- Navigate to: Dashboard → "aruba-noc-server" → Metrics
- View: Latency distribution by tool
- See: P50/P95/P99 percentiles

### 11.8 Cost

**LangSmith Pricing**:
- **Free Tier**: 5,000 traces/month (sufficient for most use cases)
- **Pro Tier**: $39/month for 100,000 traces/month
- **Enterprise**: Custom pricing

**Current Usage**: With your API key configured, all tool calls are automatically traced at no cost until you exceed the free tier.

### 11.9 Privacy & Security

✅ **What's Sent to LangSmith**:
- Tool name
- Tool arguments
- Execution time
- Success/failure status
- Error messages (if any)

❌ **What's NOT Sent**:
- Aruba OAuth2 tokens or credentials
- Full API responses (only success/failure)
- User identifying information (unless in tool args)

**Best Practices**:
- Don't log sensitive data in tool arguments
- Audit LangSmith access (who can view traces)
- Review traces periodically for sensitive data leaks

---

## 12. Appendix: Metric Types Reference

| Type | When to Use | Example |
|------|-------------|---------|
| **Counter** | Monotonically increasing value | API calls, errors, retries |
| **Gauge** | Current state that can go up/down | Tokens available, concurrent requests |
| **Histogram** | Distribution of values | Latency, request sizes |
| **Summary** | Similar to histogram but client-side | Less common, prefer histogram |

---

**Document Version**: 1.1
**Last Updated**: 2026-01-05
**Owner**: Infrastructure Team
**Review Cycle**: Quarterly
**Changelog**:
- v1.1 (2026-01-05): Added LangSmith integration documentation
- v1.0 (2026-01-05): Initial release
