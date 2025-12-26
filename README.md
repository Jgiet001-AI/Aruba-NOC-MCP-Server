# Aruba NOC MCP Server

An MCP (Model Context Protocol) server for integrating with Aruba Central API, enabling AI assistants to manage and monitor Aruba network infrastructure.

## 🚀 Features

- **Device Management**: List, query, and monitor network devices
- **Site Management**: Manage sites and retrieve site-specific information
- **Client Monitoring**: Track wireless clients and bandwidth usage
- **Gateway Monitoring**: Monitor gateways, uplinks, and VPN tunnels
- **Firmware Management**: Check compliance and upgrade status
- **OAuth2 Authentication**: Automatic token management with HPE SSO

## 📁 Project Structure

```
aruba-noc-mcp-server/
├── src/
│   ├── __init__.py
│   ├── config.py          # ArubaConfig class
│   ├── api_client.py      # call_aruba_api helper
│   ├── server.py          # MCP server initialization
│   └── tools/
│       ├── __init__.py
│       ├── base.py        # Shared tool patterns
│       ├── devices.py     # Device-related tools
│       ├── sites.py       # Site-related tools
│       ├── clients.py     # Client-related tools
│       ├── gateways.py    # Gateway-related tools
│       └── firmware.py    # Firmware-related tools
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_api_client.py
│   └── tools/
│       ├── test_devices.py
│       └── test_sites.py
├── scripts/
│   └── test_connection.py
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .env
├── .gitignore
└── README.md
```

## ⚙️ Installation

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

## 🔐 Configuration

Set the following environment variables in your `.env` file:

| Variable | Required | Description |
|----------|----------|-------------|
| `ARUBA_BASE_URL` | No | Aruba Central API URL (defaults to US1) |
| `ARUBA_CLIENT_ID` | Yes* | OAuth2 Client ID |
| `ARUBA_CLIENT_SECRET` | Yes* | OAuth2 Client Secret |
| `ARUBA_ACCESS_TOKEN` | Yes* | Pre-generated access token |

*Either `ARUBA_ACCESS_TOKEN` or both `ARUBA_CLIENT_ID` and `ARUBA_CLIENT_SECRET` are required.

## 🔌 Test Connection

Before running the server, verify your API credentials:

```bash
python scripts/test_connection.py
```

## 🏃 Running the Server

```bash
python -m src.server
```

Or using the MCP CLI:

```bash
mcp run src/server.py
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src

# Run specific test file
pytest tests/test_config.py -v
```

## 🛠️ Available Tools

### Device Tools

- `list_devices` - List devices with filtering
- `get_device` - Get device details
- `get_device_health` - Get health metrics
- `get_device_config` - Get device configuration
- `get_device_stats` - Get device statistics

### Site Tools

- `list_sites` - List all sites
- `get_site` - Get site details
- `get_site_devices` - Get devices at a site
- `get_site_health` - Get site health summary

### Client Tools

- `list_clients` - List wireless clients
- `get_client` - Get client details
- `get_client_count` - Get client counts
- `get_client_bandwidth` - Get client bandwidth
- `get_wireless_clients_summary` - Get wireless summary

### Gateway Tools

- `list_gateways` - List all gateways
- `get_gateway` - Get gateway details
- `get_gateway_uplinks` - Get uplink info
- `get_gateway_tunnels` - Get VPN tunnels
- `get_gateway_health` - Get health metrics
- `get_gateway_stats` - Get statistics

### Firmware Tools

- `list_firmware_versions` - List available firmware
- `get_device_firmware` - Get device firmware info
- `get_firmware_compliance` - Get compliance status
- `get_upgrade_status` - Get upgrade task status
- `get_firmware_recommendations` - Get recommendations

## 📄 License

MIT License - see LICENSE file for details.
