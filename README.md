# Aruba NOC MCP Server

An MCP (Model Context Protocol) server for integrating with Aruba Central API, enabling AI assistants to manage and monitor Aruba network infrastructure.

## Features

- **38 Production Tools**: Comprehensive coverage of network monitoring and management
- **Device Management**: List, query, and deep-dive diagnostics for APs, switches, and gateways
- **Site Management**: Manage sites and retrieve site-specific health information
- **Client Monitoring**: Track wireless clients, bandwidth usage, and connection trends
- **Gateway Operations**: Monitor uplinks, VPN tunnels, CPU utilization, and cluster health
- **Network Diagnostics**: Ping and traceroute operations from APs and gateways
- **Security Monitoring**: IDS/IPS threat detection and firewall session analysis
- **Professional Output**: Enterprise-ready text-based status labels (no emojis)
- **OAuth2 Authentication**: Automatic token management with HPE SSO

## Project Structure

```
aruba-noc-mcp-server/
├── src/
│   ├── __init__.py
│   ├── config.py              # ArubaConfig class
│   ├── api_client.py          # call_aruba_api helper
│   ├── server.py              # MCP server initialization
│   └── tools/
│       ├── __init__.py
│       ├── base.py            # StatusLabels + shared utilities
│       ├── devices.py         # Device listing
│       ├── sites.py           # Site health
│       ├── clients.py         # Client monitoring
│       ├── gateways.py        # Gateway listing
│       ├── firmware.py        # Firmware compliance
│       ├── get_ap_*.py        # AP deep-dive tools (4 files)
│       ├── get_gateway_*.py   # Gateway deep-dive tools (5 files)
│       ├── get_switch_*.py    # Switch deep-dive tools (3 files)
│       ├── get_site_*.py      # Site details
│       ├── get_client_*.py    # Client analytics
│       ├── get_tenant_*.py    # Org-wide health
│       ├── list_*.py          # List tools (WLANs, tunnels, threats)
│       ├── ping_from_*.py     # Ping diagnostics
│       └── traceroute_*.py    # Traceroute diagnostics
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_api_client.py
│   └── tools/
│       ├── test_devices.py
│       └── test_sites.py
├── scripts/
│   └── test_connection.py
├── Dockerfile
├── docker-compose.yaml
├── mcp_config.json
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/aruba-noc-mcp-server.git
   cd aruba-noc-mcp-server
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   # Production only
   pip install -r requirements.txt

   # With development tools
   pip install -r requirements-dev.txt
   ```

4. Configure environment:

   ```bash
   cp .env.example .env
   # Edit .env with your Aruba Central credentials
   ```

## Configuration

Set the following environment variables in your `.env` file:

| Variable | Required | Description |
|----------|----------|-------------|
| `ARUBA_BASE_URL` | No | Aruba Central API URL (defaults to US1) |
| `ARUBA_CLIENT_ID` | Yes* | OAuth2 Client ID |
| `ARUBA_CLIENT_SECRET` | Yes* | OAuth2 Client Secret |
| `ARUBA_ACCESS_TOKEN` | Yes* | Pre-generated access token |

*Either `ARUBA_ACCESS_TOKEN` or both `ARUBA_CLIENT_ID` and `ARUBA_CLIENT_SECRET` are required.

## Running the Server

### Local Development

```bash
python -m src.server
```

### Docker (Recommended)

**One-command deployment:**

```bash
./deploy.sh
```

The deploy script will:

1. Check Docker prerequisites
2. Verify `.env` configuration
3. Stop any existing container
4. Build and start the container
5. Verify deployment health

**Manual Docker commands:**

```bash
# Build and start
docker compose up -d --build

# View logs
docker logs aruba-noc-mcp-server -f

# Stop
docker compose down

# Restart
docker compose restart
```

### MCP Client Configuration

Add to your `mcp_config.json`:

```json
{
  "mcpServers": {
    "aruba-noc": {
      "command": "docker",
      "args": ["exec", "-i", "aruba-noc-mcp-server", "python", "-m", "src.server"]
    }
  }
}
```

### Running Tests

```bash
# Run all tests (133 tests)
pytest tests/ -v

# Quick test run
pytest tests/ -q
```

## Available Tools (38 Total)

### Core Device Tools

| Tool | Description |
|------|-------------|
| `get_device_list` | List all network devices with filtering, sorting, pagination |
| `get_device_inventory` | Device inventory summary by model and type |

### Access Point (AP) Tools

| Tool | Description |
|------|-------------|
| `get_ap_details` | Deep-dive AP details with health analysis |
| `get_ap_cpu_utilization` | AP CPU trends with threshold-based recommendations |
| `get_ap_radios` | Radio status, channel, power, utilization per band |
| `ping_from_ap` | Initiate ping from AP (async operation) |
| `traceroute_from_ap` | Initiate traceroute from AP (async operation) |

### Gateway Tools

| Tool | Description |
|------|-------------|
| `list_gateways` | List all gateways with deployment type inventory |
| `get_gateway_details` | Deep-dive gateway details with performance metrics |
| `get_gateway_uplinks` | Uplink status, throughput, and health warnings |
| `get_gateway_cpu_utilization` | Gateway CPU trends and utilization analysis |
| `get_gateway_cluster_info` | Cluster topology, failover status, member health |
| `list_gateway_tunnels` | VPN tunnel status, encryption, traffic statistics |
| `ping_from_gateway` | Initiate ping from gateway (async operation) |

### Switch Tools

| Tool | Description |
|------|-------------|
| `get_switch_details` | Deep-dive switch details with port summary |
| `get_switch_interfaces` | Port status, PoE, VLAN, error details |
| `get_stack_members` | Stack topology, roles, health assessment |

### Client & Wireless Tools

| Tool | Description |
|------|-------------|
| `list_all_clients` | List all connected clients with experience breakdown |
| `get_client_trends` | Client connection trends over time |
| `get_top_clients_by_usage` | Top bandwidth consumers with usage statistics |
| `list_wlans` | List WLANs with security and client counts |
| `get_wlan_details` | WLAN configuration, security, performance |

### Site & Organization Tools

| Tool | Description |
|------|-------------|
| `get_sites_health` | Site health overview with device counts, alerts |
| `get_site_details` | Deep-dive site info with health breakdown |
| `get_tenant_device_health` | Organization-wide network health and SLA |
| `get_top_aps_by_bandwidth` | Top bandwidth-consuming APs with recommendations |

### Security Tools

| Tool | Description |
|------|-------------|
| `list_idps_threats` | IDS/IPS threat detection with severity breakdown |
| `get_firewall_sessions` | Firewall session analysis and rule statistics |

### Firmware Tools

| Tool | Description |
|------|-------------|
| `get_firmware_details` | Firmware compliance with upgrade recommendations |

### Async Operations

| Tool | Description |
|------|-------------|
| `get_async_test_result` | Poll async operation status (ping/traceroute) |

## Status Labels Reference

All tools use professional text-based status labels for enterprise-ready output:

### Status Indicators

| Label | Meaning |
|-------|---------|
| `[OK]` | Healthy, online, success |
| `[WARN]` | Warning condition |
| `[CRIT]` | Critical issue |
| `[ERR]` | Error state |
| `[INFO]` | Informational note |
| `[UP]` | Online, active |
| `[DN]` | Offline, down |

### Device Types

| Label | Meaning |
|-------|---------|
| `[AP]` | Access Point |
| `[SW]` | Switch |
| `[GW]` | Gateway |
| `[DEV]` | Generic device |

### Data Categories

| Label | Meaning |
|-------|---------|
| `[STATS]` | Statistics section |
| `[TREND]` | Trend data |
| `[DATA]` | Data metrics |
| `[NET]` | Network information |
| `[VPN]` | VPN/Tunnel |
| `[SEC]` | Security-related |

### Example Output

```
[NET] Tenant Device Health Report
[STATUS] Network Health: [OK] Healthy | 98.5% Uptime

[DEV] Device Summary
  [AP] Access Points: 45 total | 43 [UP] | 2 [DN]
  [SW] Switches: 12 total | 12 [UP] | 0 [DN]
  [GW] Gateways: 4 total | 4 [UP] | 0 [DN]

[HEALTH] SLA Compliance: [OK] 99.2%
```

## Development

### Code Quality

```bash
# Linting
ruff check src/ tests/

# Auto-fix issues
ruff check src/ tests/ --fix

# Formatting
ruff format src/ tests/

# Type checking
mypy src/
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Validate syntax
python -m py_compile src/**/*.py
```

### Adding New Tools

1. Create tool file in `src/tools/` following existing patterns
2. Import `StatusLabels` from `base.py` for consistent output
3. Use `format_bytes`, `format_uptime` helpers as needed
4. Register handler in `src/server.py`
5. Add tests in `tests/tools/`

## License

MIT License - see LICENSE file for details.
