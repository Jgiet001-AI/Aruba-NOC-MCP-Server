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

## Quick Start

### One-Command Deployment

```bash
./deploy.sh
```

The interactive deployment script will:

1. ✅ Check Docker prerequisites
2. ✅ Prompt for your Aruba Central region (13 regions supported)
3. ✅ Securely collect your API credentials
4. ✅ Build and start the Docker container
5. ✅ Verify deployment health

### Supported Regions

| Region | API Endpoint |
|--------|--------------|
| **Americas** | |
| US-1 | us1.api.central.arubanetworks.com |
| US-2 | us2.api.central.arubanetworks.com |
| US-WEST-4 | us4.api.central.arubanetworks.com |
| US-WEST-5 | us5.api.central.arubanetworks.com |
| US-East1 | us6.api.central.arubanetworks.com |
| Canada-1 | ca1.api.central.arubanetworks.com |
| **Europe** | |
| EU-1 | de1.api.central.arubanetworks.com |
| EU-Central2 | de2.api.central.arubanetworks.com |
| EU-Central3 | de3.api.central.arubanetworks.com |
| **Asia Pacific** | |
| APAC-1 | in.api.central.arubanetworks.com |
| APAC-EAST1 | jp1.api.central.arubanetworks.com |
| APAC-SOUTH1 | au1.api.central.arubanetworks.com |

## Project Structure

```
aruba-noc-mcp-server/
├── src/
│   ├── __init__.py
│   ├── config.py              # ArubaConfig class
│   ├── api_client.py          # call_aruba_api helper
│   ├── server.py              # MCP server + tool definitions
│   └── tools/
│       ├── __init__.py
│       ├── base.py            # StatusLabels + shared utilities
│       ├── devices.py         # Device listing
│       ├── sites.py           # Site health
│       ├── clients.py         # Client monitoring
│       ├── gateways.py        # Gateway listing
│       ├── firmware.py        # Firmware compliance
│       └── ...                # 25+ additional tool handlers
├── tests/                     # 130+ unit tests
├── scripts/                   # Testing utilities
├── Dockerfile
├── docker-compose.yaml
├── deploy.sh                  # Interactive deployment script
├── mcp_config.json            # MCP client config template
├── .env.example               # Environment template
└── README.md
```

## Manual Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/aruba-noc-mcp-server.git
   cd aruba-noc-mcp-server
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env with your Aruba Central credentials
   ```

5. **Run the server:**

   ```bash
   python -m src.server
   ```

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `ARUBA_BASE_URL` | No | Aruba Central API URL (see regions above) |
| `ARUBA_CLIENT_ID` | Yes* | OAuth2 Client ID |
| `ARUBA_CLIENT_SECRET` | Yes* | OAuth2 Client Secret |
| `ARUBA_ACCESS_TOKEN` | No | Pre-generated access token (auto-generated if not provided) |

*Get your credentials from: **Aruba Central > Account Home > API Gateway > My Apps & Tokens**

## Docker Commands

```bash
# Build and start
docker compose up -d --build

# View logs
docker logs aruba-noc-mcp-server -f

# Stop
docker compose down

# Restart
docker compose restart

# Reconfigure credentials
./deploy.sh  # Select 'y' when prompted
```

## MCP Client Configuration

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

### Firmware & Async Tools

| Tool | Description |
|------|-------------|
| `get_firmware_details` | Firmware compliance with upgrade recommendations |
| `get_async_test_result` | Poll async operation status (ping/traceroute) |

## Status Labels Reference

All tools use professional text-based status labels:

| Label | Meaning |
|-------|---------|
| `[OK]` | Healthy, online, success |
| `[WARN]` | Warning condition |
| `[CRIT]` | Critical issue |
| `[ERR]` | Error state |
| `[UP]` | Online, active |
| `[DN]` | Offline, down |
| `[AP]` `[SW]` `[GW]` | Device types |

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=term-missing
```

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

### Adding New Tools

1. Create tool file in `src/tools/` following existing patterns
2. Import `StatusLabels` from `base.py` for consistent output
3. Use `format_bytes`, `format_uptime` helpers as needed
4. Register handler in `src/server.py`
5. Add tests in `tests/tools/`

## License

MIT License - see [LICENSE](LICENSE) file for details.
