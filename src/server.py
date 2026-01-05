import logging
from typing import Any

from dotenv import load_dotenv
from mcp.server import Server

# Load environment variables from .env file
load_dotenv()
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Import handler functions from tool modules
from src.tools.clients import handle_list_all_clients
from src.tools.devices import handle_get_device_list
from src.tools.firmware import handle_get_firmware_details
from src.tools.gateways import handle_list_gateways
from src.tools.get_ap_cpu_utilization import handle_get_ap_cpu_utilization
from src.tools.get_ap_details import handle_get_ap_details
from src.tools.get_ap_radios import handle_get_ap_radios
from src.tools.get_async_test_result import handle_get_async_test_result
from src.tools.get_client_trends import handle_get_client_trends
from src.tools.get_device_inventory import handle_get_device_inventory
from src.tools.get_firewall_sessions import handle_get_firewall_sessions
from src.tools.get_gateway_cluster_info import handle_get_gateway_cluster_info
from src.tools.get_gateway_cpu_utilization import handle_get_gateway_cpu_utilization
from src.tools.get_gateway_details import handle_get_gateway_details
from src.tools.get_gateway_uplinks import handle_get_gateway_uplinks
from src.tools.get_site_details import handle_get_site_details
from src.tools.get_stack_members import handle_get_stack_members
from src.tools.get_switch_details import handle_get_switch_details
from src.tools.get_switch_interfaces import handle_get_switch_interfaces
from src.tools.get_tenant_device_health import handle_get_tenant_device_health
from src.tools.get_top_aps_by_bandwidth import handle_get_top_aps_by_bandwidth
from src.tools.get_top_clients_by_usage import handle_get_top_clients_by_usage
from src.tools.get_wlan_details import handle_get_wlan_details
from src.tools.list_gateway_tunnels import handle_list_gateway_tunnels
from src.tools.list_idps_threats import handle_list_idps_threats
from src.tools.list_wlans import handle_list_wlans
from src.tools.ping_from_ap import handle_ping_from_ap
from src.tools.ping_from_gateway import handle_ping_from_gateway
from src.tools.sites import handle_get_sites_health
from src.tools.traceroute_from_ap import handle_traceroute_from_ap

logger = logging.getLogger("aruba-noc-server")

app = Server("Aruba NOC Server", "1.0.0")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_device_list",
            description=(
                "Retrieves a comprehensive list of all network devices including access points, "
                "switches, and gateways. Returns device name, model, serial number, IP address, "
                "software version, status, uptime, site assignment, and deployment type. "
                "Essential for network inventory management, device health monitoring, "
                "multi-device troubleshooting, and compliance reporting.\n\n"
                "**Filtering Capabilities:**\n"
                "• Device Type: Filter by ACCESS_POINT, SWITCH, or GATEWAY\n"
                "• Status: Filter by ONLINE, OFFLINE, or other operational states\n"
                "• Site: Filter devices by specific site ID\n"
                "• Deployment: Filter by deployment type (e.g., Standalone, Clustered)\n"
                "• Model/Serial: Search for specific hardware models or serial numbers\n\n"
                "**Typical Queries:**\n"
                "• 'Show me all offline access points'\n"
                "• 'List all switches in site 12345'\n"
                "• 'What devices are online right now?'\n"
                "• 'Give me a complete network inventory'\n\n"
                "**Use OData v4.0 filters** with 'and' conjunction. The API supports sorting "
                "by deviceName, model, serialNumber, siteId, or siteName. Pagination is handled "
                "via the 'next' cursor token for datasets larger than the limit."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": (
                            "OData v4.0 filter criteria. Available fields: clusterName, deployment, "
                            "deviceName, deviceType, model, serialNumber, siteId, status. "
                            "Examples: 'deviceType eq ACCESS_POINT', 'status eq ONLINE', "
                            "'siteId eq 12345 and status eq OFFLINE'"
                        ),
                    },
                    "sort": {
                        "type": "string",
                        "description": (
                            "Sort order. Format: 'field direction'. "
                            "Available fields: deviceName, model, serialNumber, siteId, siteName. "
                            "Examples: 'deviceName asc', 'lastSeenAt desc', 'siteId asc'"
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of devices to return (default: 100)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 100,
                    },
                    "next": {
                        "type": "string",
                        "description": "Pagination cursor token for retrieving next page of results",
                    },
                },
            },
        ),
        Tool(
            name="list_all_clients",
            description=(
                "Retrieves list of all connected clients across the network. Returns MAC address, "
                "hostname, connection type (wired/wireless), associated device, signal strength, "
                "bandwidth usage, authentication status, and connection duration. Essential for "
                "client connectivity troubleshooting, network usage analysis, user experience "
                "monitoring, and capacity planning.\n\n"
                "**Client Information:**\n"
                "• Connection Details: Type (Wired/Wireless), status, experience score\n"
                "• Network Details: SSID, VLAN, IP addressing\n"
                "• Device Association: Connected AP or switch details\n"
                "• Performance: Signal strength, bandwidth usage\n"
                "• Authentication: User role, auth status\n\n"
                "**Filtering Capabilities:**\n"
                "• By Site: Filter clients at specific location\n"
                "• By Device: Clients connected to specific AP/switch\n"
                "• By Time Range: Clients active during specific period\n"
                "• By Experience: Filter by Good, Fair, or Poor experience\n"
                "• By Status: Connected, Disconnected, Idle\n\n"
                "**Typical Queries:**\n"
                "• 'How many users are connected?'\n"
                "• 'Show me wireless clients with poor experience'\n"
                "• 'List clients on AP-Floor2-03'\n"
                "• 'Who was connected between 2pm and 4pm?'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "site_id": {
                        "type": "string",
                        "description": "Filter clients by specific site ID",
                    },
                    "serial_number": {
                        "type": "string",
                        "description": "Filter clients connected to specific device serial number",
                    },
                    "start_query_time": {
                        "type": "string",
                        "description": (
                            "Start time for query window in epoch milliseconds. "
                            "Example: 1702900800000 (Unix timestamp in ms)"
                        ),
                        "format": "int64",
                    },
                    "end_query_time": {
                        "type": "string",
                        "description": (
                            "End time for query window in epoch milliseconds. "
                            "Example: 1702987200000 (Unix timestamp in ms)"
                        ),
                        "format": "int64",
                    },
                    "filter": {
                        "type": "string",
                        "description": (
                            "OData v4.0 filter criteria. Available fields: experience (Good/Fair/Poor), "
                            "status (Connected/Disconnected/Idle), type (Wired/Wireless), network, "
                            "vlanId, tunnel, role. Examples: 'experience eq Poor', "
                            "'type eq Wireless and status eq Connected'"
                        ),
                    },
                    "sort": {
                        "type": "string",
                        "description": (
                            "Sort order. Available fields: name, experience, status, type, mac, ipv4, "
                            "ipv6, connectedDeviceSerial, lastSeenAt, port, role, network, vlanId, "
                            "connectedSince. Example: 'lastSeenAt desc'"
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of clients to return (default: 100)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 100,
                    },
                    "next": {
                        "type": "string",
                        "description": "Pagination cursor token for next page",
                    },
                },
            },
        ),
        Tool(
            name="get_firmware_details",
            description=(
                "Provides detailed firmware information for all devices in the network. "
                "Returns current firmware version, available updates, recommended upgrades, "
                "device compliance status, and upgrade schedules. Critical for firmware "
                "compliance audits, update planning and scheduling, security patch management, "
                "and version standardization across the infrastructure.\n\n"
                "**Firmware Information:**\n"
                "• Current Version: Installed firmware on each device\n"
                "• Recommended Version: Suggested upgrade target\n"
                "• Upgrade Status: Up To Date, Update Available, Update Required\n"
                "• Classification: Bug Fix, Feature Release, Security Patch\n"
                "• Device Details: Model, serial number, site assignment\n\n"
                "**Filtering Capabilities:**\n"
                "• By Site: Firmware status for specific location\n"
                "• By Device Type: Filter APs, switches, or gateways\n"
                "• By Upgrade Status: Find devices needing updates\n"
                "• By Classification: Filter security patches, bug fixes, etc.\n\n"
                "**Typical Queries:**\n"
                "• 'Which devices need firmware updates?'\n"
                "• 'Show me security patches available'\n"
                "• 'List devices with outdated firmware'\n"
                "• 'Firmware compliance status report'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": (
                            "OData v4.0 filter criteria. Available fields: siteId, upgradeStatus, "
                            "firmwareClassification, serialNumber, deviceName, softwareVersion, "
                            "deviceType. Examples: 'upgradeStatus eq Update Required', "
                            "'firmwareClassification eq Security Patch', "
                            "'deviceType eq ACCESS_POINT and upgradeStatus eq Update Available'"
                        ),
                    },
                    "sort": {
                        "type": "string",
                        "description": "Sort order for results. Format: 'field direction'",
                    },
                    "search": {
                        "type": "string",
                        "description": (
                            "Free-text search query for finding specific devices or firmware versions. "
                            "Searches across device names, serial numbers, and firmware versions."
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 100)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 100,
                    },
                    "next": {"type": "string", "description": "Pagination cursor token"},
                },
            },
        ),
        Tool(
            name="list_gateways",
            description=(
                "Returns comprehensive list of all gateways in the network. Provides gateway "
                "status, uptime, cluster membership, tunnel information, throughput stats, "
                "and configuration details. Essential for gateway health monitoring, VPN tunnel "
                "status verification, traffic analysis, and cluster management operations.\n\n"
                "**Gateway Information:**\n"
                "• Status & Health: Online/offline status, uptime, health scores\n"
                "• Deployment: Standalone or Clustered configuration\n"
                "• Network Details: Model, serial number, MAC address, site\n"
                "• Cluster Info: Cluster membership and role\n"
                "• Performance: Throughput, active connections\n\n"
                "**Filtering Capabilities:**\n"
                "• By Site: Gateways at specific location\n"
                "• By Status: Filter online or offline gateways\n"
                "• By Deployment: Standalone vs clustered\n"
                "• By Model: Specific gateway hardware models\n\n"
                "**Typical Queries:**\n"
                "• 'Show me all offline gateways'\n"
                "• 'List gateways in cluster MainCluster'\n"
                "• 'Which gateways are standalone?'\n"
                "• 'Gateway inventory and status'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": (
                            "OData v4.0 filter criteria. Available fields: siteId, model, status, "
                            "deployment, macAddress. Examples: 'status eq ONLINE', "
                            "'deployment eq Clustered', 'siteId eq 12345 and status eq OFFLINE'"
                        ),
                    },
                    "sort": {
                        "type": "string",
                        "description": (
                            "Sort order. Available fields: siteId, model, status, deployment, "
                            "serialNumber, deviceName, macAddress. Example: 'deviceName asc'"
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of gateways to return (default: 100)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 100,
                    },
                    "next": {"type": "string", "description": "Pagination cursor token"},
                },
            },
        ),
        Tool(
            name="get_sites_health",
            description=(
                "Returns health overview for all sites in the network. Provides overall health "
                "scores, device counts, client counts, bandwidth usage, and status summaries for "
                "each site. Critical for executive dashboards, multi-site monitoring, SLA compliance "
                "tracking, and capacity planning across the entire network infrastructure.\n\n"
                "**Health Metrics:**\n"
                "• Overall Health Score: Good, Fair, or Poor\n"
                "• Device Status: Total devices and breakdown by status\n"
                "• Client Connectivity: Connected client counts\n"
                "• Active Alerts: Count and severity of current alerts\n"
                "• Bandwidth Usage: Network throughput statistics\n\n"
                "**Typical Queries:**\n"
                "• 'What sites are having issues?'\n"
                "• 'Show me overall network health'\n"
                "• 'Which sites have the most alerts?'\n"
                "• 'Give me a health summary of all locations'\n\n"
                "**Use for:** Multi-site dashboards, executive reports, SLA tracking, "
                "capacity planning, and identifying problem sites requiring attention."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of sites to return per page (default: 100)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 100,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Pagination offset for retrieving additional sites (default: 0)",
                        "minimum": 0,
                        "default": 0,
                    },
                },
            },
        ),
        Tool(
            name="get_device_inventory",
            description=(
                "Provides comprehensive hardware inventory across all network devices. "
                "Returns detailed hardware specifications, model information, MAC addresses, "
                "serial numbers, subscription tiers, device SKUs, and deployment status. "
                "Essential for asset management, hardware lifecycle planning, compliance audits, "
                "and subscription tracking.\n\n"
                "USE THIS WHEN the user asks about hardware inventory, device models, "
                "subscription status, or asset tracking. For example: 'What hardware do we have?', "
                "'List all device models', 'Show subscription status', 'Hardware audit report'.\n\n"
                "DO NOT USE when the user wants operational status (online/offline) - use "
                "get_device_list instead. DO NOT USE for troubleshooting specific devices - "
                "use get_switch_details or get_ap_details instead."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": (
                            "OData v4.0 filter criteria. Available fields: deviceType, model, "
                            "subscriptionTier, siteId. Examples: 'deviceType eq ACCESS_POINT', "
                            "'subscriptionTier eq Foundation', 'model eq AP-515'"
                        ),
                    },
                    "sort": {
                        "type": "string",
                        "description": (
                            "Sort order. Available fields: deviceName, model, deviceType, siteId. Example: 'model asc'"
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of devices to return (default: 100)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 100,
                    },
                    "next": {"type": "string", "description": "Pagination cursor token for next page"},
                },
            },
        ),
        Tool(
            name="get_switch_details",
            description=(
                "Retrieves comprehensive operational details for a SPECIFIC switch using its "
                "serial number. Returns current status, port count, stack membership, uptime, "
                "CPU and memory utilization, firmware version, IP address, and detailed "
                "configuration information. Essential for troubleshooting individual switch "
                "issues, performance analysis, and configuration verification.\n\n"
                "USE THIS WHEN the user asks about ONE specific switch by name or serial number. "
                "For example: 'Show me details for switch SW-Core-01', 'What's the status of "
                "serial CN12345678', 'Check switch performance for SW-Distro-02'.\n\n"
                "DO NOT USE when listing multiple switches - use get_device_list instead. "
                "DO NOT USE for general inventory - use get_device_inventory instead. "
                "This tool requires a specific serial number."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "serial": {
                        "type": "string",
                        "description": "Serial number of the switch (required). Example: CN12345678",
                    }
                },
                "required": ["serial"],
            },
        ),
        Tool(
            name="get_ap_details",
            description=(
                "Retrieves comprehensive operational details for a SPECIFIC access point using "
                "its serial number. Returns current status, radio information (2.4GHz and 5GHz), "
                "connected client count, channel assignments, transmit power, CPU and memory "
                "utilization, firmware version, and wireless performance metrics. Critical for "
                "wireless troubleshooting, RF optimization, and client connectivity issues.\n\n"
                "USE THIS WHEN the user asks about ONE specific access point by name or serial "
                "number. For example: 'Show me details for AP-Floor2-03', 'Check AP status for "
                "serial SN12345678', 'Why is the WiFi slow near AP-Lobby-01', 'What channel is "
                "AP-Conference-Room using'.\n\n"
                "DO NOT USE when listing multiple APs - use get_device_list instead. "
                "DO NOT USE for general inventory - use get_device_inventory instead. "
                "This tool requires a specific serial number."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "serial_number": {
                        "type": "string",
                        "description": "Serial number of the access point (required). Example: SN12345678",
                    }
                },
                "required": ["serial_number"],
            },
        ),
        Tool(
            name="get_site_details",
            description=(
                "Retrieves comprehensive health and operational details for a SPECIFIC site "
                "using its site ID. Returns overall site health score, device counts by type "
                "and status, connected client statistics, active alert counts by severity, "
                "bandwidth utilization, and site-wide performance indicators. Essential for "
                "single-site troubleshooting, detailed site analysis, and targeted issue "
                "resolution.\n\n"
                "USE THIS WHEN the user asks about ONE specific site, location, or building. "
                "For example: 'How is Building A doing?', 'Show me site 12345 status', "
                "'What's wrong with the downtown office?', 'Site health for headquarters'.\n\n"
                "DO NOT USE when the user wants an overview of ALL sites - use get_sites_health "
                "instead. This tool requires a specific site ID."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "site_id": {"type": "string", "description": "Site identifier (required). Example: 12345"}
                },
                "required": ["site_id"],
            },
        ),
        Tool(
            name="get_tenant_device_health",
            description=(
                "Provides organization-wide device health overview aggregated across all sites. "
                "Returns total device counts across the entire network, health score distribution, "
                "device type breakdown, overall network health percentage, and infrastructure-wide "
                "status summary. Essential for executive dashboards, SLA compliance reporting, "
                "high-level network status monitoring, and organization-wide health tracking.\n\n"
                "USE THIS WHEN the user asks about overall network health, total device status, "
                "or organization-wide metrics. For example: 'What's our overall network health?', "
                "'How many devices total?', 'Network health score', 'Infrastructure status summary', "
                "'Are we meeting SLA targets?'.\n\n"
                "DO NOT USE when the user wants site-by-site breakdown - use get_sites_health instead. "
                "DO NOT USE when the user wants specific site details - use get_site_details instead."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_client_trends",
            description=(
                "Provides historical client connection trends over time. Returns time-series data "
                "showing client counts at different time intervals, wireless vs wired client breakdown, "
                "peak usage times, average client counts, and connection growth patterns. Essential "
                "for capacity planning, usage pattern analysis, historical trend reporting, and "
                "identifying peak usage periods.\n\n"
                "USE THIS WHEN the user asks about client trends over time, historical usage patterns, "
                "capacity planning, or peak usage. For example: 'Show me client trends this week', "
                "'What are peak usage times?', 'How has client count changed?', 'Usage patterns "
                "last month', 'When are we busiest?'.\n\n"
                "DO NOT USE when the user wants current connected clients - use list_all_clients instead. "
                "DO NOT USE for specific client details - this provides aggregated counts only."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "site_id": {"type": "string", "description": "Filter trends by specific site ID (optional)"},
                    "start_time": {
                        "type": "string",
                        "description": (
                            "Start time for trend analysis in RFC 3339 format (ISO 8601). "
                            "Example: 2024-12-18T00:00:00Z. Defaults to 24 hours ago if not specified."
                        ),
                        "format": "date-time",
                    },
                    "end_time": {
                        "type": "string",
                        "description": (
                            "End time for trend analysis in RFC 3339 format (ISO 8601). "
                            "Example: 2024-12-25T23:59:59Z. Defaults to now if not specified."
                        ),
                        "format": "date-time",
                    },
                    "interval": {
                        "type": "string",
                        "description": (
                            "Data point interval. Options: '5min', '15min', '1hour', '1day'. Default: '1hour'"
                        ),
                        "enum": ["5min", "15min", "1hour", "1day"],
                        "default": "1hour",
                    },
                },
            },
        ),
        Tool(
            name="get_gateway_details",
            description=(
                "Retrieves comprehensive operational details for a SPECIFIC gateway using its "
                "serial number. Returns current status, cluster membership and role, uplink interface "
                "information, active VPN tunnel counts, throughput statistics, CPU and memory utilization, "
                "firmware version, and configuration details. Essential for gateway troubleshooting, "
                "WAN connectivity issues, VPN tunnel status verification, and branch office connectivity "
                "diagnosis.\n\n"
                "USE THIS WHEN the user asks about ONE specific gateway by name or serial number. "
                "For example: 'Show me details for gateway GW-Main-01', 'Check gateway status for "
                "serial SN12345678', 'Why is the VPN down at site X?', 'What's the WAN link status "
                "for GW-Branch-05?', 'Gateway performance check'.\n\n"
                "DO NOT USE when listing multiple gateways - use list_gateways instead. "
                "DO NOT USE for general inventory - use get_device_inventory instead. "
                "This tool requires a specific serial number."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "serial_number": {
                        "type": "string",
                        "description": "Serial number of the gateway (required). Example: SN12345678",
                    }
                },
                "required": ["serial_number"],
            },
        ),
        Tool(
            name="get_top_aps_by_bandwidth",
            description=(
                "Identifies access points with highest wireless bandwidth consumption. Returns ranked "
                "list of APs sorted by total data usage, including download/upload throughput, number of "
                "connected clients, and usage percentage. Essential for capacity planning, identifying "
                "bandwidth-heavy access points, network optimization, and determining which APs may need "
                "capacity upgrades or load balancing.\n\n"
                "USE THIS WHEN the user asks about bandwidth usage by APs, which APs are busiest, "
                "capacity planning, or network hotspots. For example: 'Which APs use the most bandwidth?', "
                "'Show me top 10 busiest access points', 'Where are the network hotspots?', 'Which APs "
                "need capacity upgrades?', 'Bandwidth leaders'.\n\n"
                "DO NOT USE for client bandwidth usage - use get_top_clients_by_usage instead. "
                "DO NOT USE for general AP inventory - use get_device_list instead."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "site_id": {"type": "string", "description": "Filter by specific site ID (optional)"},
                    "limit": {
                        "type": "integer",
                        "description": "Number of top APs to return (default: 10)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 100,
                    },
                    "time_range": {
                        "type": "string",
                        "description": (
                            "Time period for analysis: '1hour', '24hours', '7days', '30days' (default: '24hours')"
                        ),
                        "enum": ["1hour", "24hours", "7days", "30days"],
                        "default": "24hours",
                    },
                },
            },
        ),
        Tool(
            name="get_top_clients_by_usage",
            description=(
                "Identifies clients consuming the most network bandwidth. Returns ranked list of top "
                "bandwidth consumers including total data transferred, download/upload breakdown, "
                "connection type, hostname, MAC address, and connected device. Essential for troubleshooting "
                "slow network performance, identifying bandwidth-heavy users, enforcing usage policies, "
                "and network optimization.\n\n"
                "USE THIS WHEN the user asks about bandwidth hogs, heavy users, network slowness caused "
                "by clients, or usage analysis. For example: 'Who's using the most bandwidth?', 'Show me "
                "top 10 bandwidth consumers', 'Which users are slowing down the network?', 'Find bandwidth "
                "hogs', 'Top data users'.\n\n"
                "DO NOT USE for AP bandwidth usage - use get_top_aps_by_bandwidth instead. "
                "DO NOT USE for general client list - use list_all_clients instead."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "site_id": {"type": "string", "description": "Filter by specific site ID (optional)"},
                    "limit": {
                        "type": "integer",
                        "description": "Number of top clients to return (default: 10)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 100,
                    },
                    "time_range": {
                        "type": "string",
                        "description": "Time period: '1hour', '24hours', '7days' (default: '24hours')",
                        "enum": ["1hour", "24hours", "7days"],
                        "default": "24hours",
                    },
                    "connection_type": {
                        "type": "string",
                        "description": "Filter by connection: 'WIRELESS', 'WIRED', or 'ALL' (default: 'ALL')",
                        "enum": ["WIRELESS", "WIRED", "ALL"],
                        "default": "ALL",
                    },
                },
            },
        ),
        Tool(
            name="get_ap_cpu_utilization",
            description=(
                "Retrieves CPU utilization trends for a specific access point over time. Returns "
                "time-series data showing CPU usage percentages at different intervals, average CPU load, "
                "peak utilization, and performance trend indicators. Essential for identifying overloaded "
                "access points, performance monitoring, capacity planning, and predicting hardware upgrade "
                "needs.\n\n"
                "USE THIS WHEN the user asks about AP performance, CPU usage for specific AP, or "
                "performance trends. For example: 'How is AP-Floor2-03 performing?', 'CPU usage for "
                "AP SN12345678', 'Is the AP overloaded?', 'Performance trends for access point', "
                "'AP resource usage'.\n\n"
                "DO NOT USE for gateway CPU - use get_gateway_cpu_utilization instead. "
                "DO NOT USE for multiple APs at once - this requires a specific serial number. "
                "This tool is for deep-dive performance analysis of ONE AP."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "serial": {"type": "string", "description": "Serial number of the access point (required)"},
                    "start_time": {
                        "type": "string",
                        "description": "Start time in RFC 3339 format (default: 24 hours ago)",
                        "format": "date-time",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in RFC 3339 format (default: now)",
                        "format": "date-time",
                    },
                    "interval": {
                        "type": "string",
                        "description": "Data interval: '5min', '1hour' (default: '1hour')",
                        "enum": ["5min", "1hour"],
                        "default": "1hour",
                    },
                },
                "required": ["serial"],
            },
        ),
        Tool(
            name="get_gateway_cpu_utilization",
            description=(
                "Retrieves CPU utilization trends for a specific gateway over time. Returns time-series "
                "data showing CPU usage percentages at different intervals, average CPU load, peak "
                "utilization, and performance trend indicators. Essential for identifying gateway performance "
                "bottlenecks, VPN capacity planning, branch office connectivity monitoring, and predicting "
                "hardware upgrade needs.\n\n"
                "USE THIS WHEN the user asks about gateway performance, CPU usage for specific gateway, "
                "or VPN performance. For example: 'How is gateway GW-Main-01 performing?', 'CPU usage for "
                "gateway SN12345678', 'Is the gateway overloaded?', 'VPN capacity check', 'Gateway "
                "performance trends'.\n\n"
                "DO NOT USE for AP CPU - use get_ap_cpu_utilization instead. "
                "DO NOT USE for multiple gateways - this requires a specific serial number. "
                "This tool is for deep-dive performance analysis of ONE gateway."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "serial": {"type": "string", "description": "Serial number of the gateway (required)"},
                    "start_time": {
                        "type": "string",
                        "description": "Start time in RFC 3339 format (default: 24 hours ago)",
                        "format": "date-time",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in RFC 3339 format (default: now)",
                        "format": "date-time",
                    },
                    "interval": {
                        "type": "string",
                        "description": "Data interval: '5min', '1hour' (default: '1hour')",
                        "enum": ["5min", "1hour"],
                        "default": "1hour",
                    },
                },
                "required": ["serial"],
            },
        ),
        Tool(
            name="list_wlans",
            description=(
                "Retrieves list of all wireless networks (WLANs/SSIDs) configured across the environment. "
                "Returns WLAN name, security type, authentication method, VLAN assignment, enabled status, "
                "SSID broadcast settings, and band steering configuration. Essential for wireless network "
                "inventory, SSID management, security auditing, and guest network oversight.\n\n"
                "USE THIS WHEN the user asks about SSIDs, wireless networks, WiFi names, or network "
                "inventory. For example: 'What SSIDs are configured?', 'Show me all wireless networks', "
                "'List WiFi names', 'What guest networks exist?', 'WLAN inventory'.\n\n"
                "DO NOT USE for specific WLAN details - use get_wlan_details instead. "
                "DO NOT USE for client connectivity - use list_all_clients instead."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "site_id": {"type": "string", "description": "Filter WLANs by specific site ID (optional)"},
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of WLANs to return (default: 100)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 100,
                    },
                },
            },
        ),
        Tool(
            name="get_wlan_details",
            description=(
                "Retrieves detailed configuration and operational statistics for a specific wireless "
                "network (WLAN/SSID). Returns comprehensive settings including security configuration, "
                "authentication methods, VLAN assignment, QoS settings, band steering, client limits, "
                "connected client count, throughput statistics, and operational status. Essential for "
                "WLAN troubleshooting, security auditing, and configuration verification.\n\n"
                "USE THIS WHEN the user asks about a SPECIFIC SSID's configuration or performance. For "
                "example: 'Details for Guest-WiFi', 'Configuration of Corporate-WiFi', 'How is the guest "
                "network configured?', 'Show me settings for SSID X', 'Guest WiFi details'.\n\n"
                "DO NOT USE for listing all WLANs - use list_wlans instead. "
                "This tool requires a specific WLAN name."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "wlan_name": {"type": "string", "description": "Name of the WLAN/SSID to retrieve (required)"}
                },
                "required": ["wlan_name"],
            },
        ),
        Tool(
            name="get_ap_radios",
            description=(
                "Retrieves radio status and channel information for a specific access point. Returns "
                "detailed information for each radio including band (2.4GHz/5GHz/6GHz), current channel, "
                "channel width, transmit power, number of connected clients, radio utilization percentage, "
                "operational status, and interference levels. Essential for wireless troubleshooting, RF "
                "optimization, channel conflict diagnosis, and performance tuning.\n\n"
                "USE THIS WHEN the user asks about AP radio status, channel assignments, wireless "
                "performance issues, or RF settings. For example: 'What channel is AP-Floor2-03 using?', "
                "'Radio status for AP SN12345678', 'Why is WiFi slow on this AP?', 'Show me radio "
                "details', 'Channel information for access point'.\n\n"
                "DO NOT USE for general AP status - use get_ap_details instead. "
                "This tool provides deep RF/radio-level diagnostics for ONE specific AP."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "serial": {"type": "string", "description": "Serial number of the access point (required)"}
                },
                "required": ["serial"],
            },
        ),
        Tool(
            name="get_gateway_cluster_info",
            description=(
                "Retrieves detailed information about a gateway cluster including all member gateways, "
                "their roles (primary/backup), cluster health status, high-availability configuration, "
                "failover status, and synchronization state. Returns cluster name, member count, primary "
                "gateway, backup gateways, cluster operational status, and configuration sync status. "
                "Essential for high-availability monitoring, cluster health verification, failover testing, "
                "and gateway redundancy management.\n\n"
                "USE THIS WHEN the user asks about gateway clusters, HA status, cluster membership, or "
                "failover configuration. For example: 'Show me MainCluster details', 'Gateway cluster "
                "status', 'Which gateways are in the cluster?', 'HA configuration check', 'Cluster "
                "health for MainCluster'.\n\n"
                "DO NOT USE for individual gateway details - use get_gateway_details instead. "
                "This tool requires a specific cluster name."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "cluster_name": {"type": "string", "description": "Name of the gateway cluster (required)"}
                },
                "required": ["cluster_name"],
            },
        ),
        Tool(
            name="list_gateway_tunnels",
            description=(
                "Retrieves list of all VPN tunnels configured for a gateway cluster. Returns tunnel "
                "name, type (IPsec/GRE), status (up/down), source and destination endpoints, encryption "
                "settings, throughput statistics, packet counts, and connection health. Essential for "
                "VPN monitoring, site-to-site connectivity verification, branch office troubleshooting, "
                "and tunnel health analysis.\n\n"
                "USE THIS WHEN the user asks about VPN tunnels, site-to-site connections, or branch "
                "connectivity. For example: 'Show me VPN tunnels', 'What tunnels are down?', 'Branch "
                "office connectivity status', 'VPN tunnel health for MainCluster', 'List all tunnels'.\n\n"
                "DO NOT USE for general gateway status - use list_gateways or get_gateway_details instead. "
                "This tool requires a specific cluster name and focuses on VPN tunnel details."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "cluster_name": {"type": "string", "description": "Name of the gateway cluster (required)"},
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of tunnels to return (default: 100)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 100,
                    },
                },
                "required": ["cluster_name"],
            },
        ),
        Tool(
            name="get_gateway_uplinks",
            description=(
                "Retrieves WAN uplink status and performance metrics for a specific gateway. Returns "
                "detailed information for each uplink/WAN interface including interface name, operational "
                "status (up/down), connection type (ethernet/cellular/DSL), IP address configuration, "
                "gateway/DNS settings, throughput statistics, packet counts, error counts, and health "
                "indicators. Essential for WAN connectivity monitoring, failover verification, bandwidth "
                "analysis, and multi-WAN troubleshooting.\n\n"
                "USE THIS WHEN the user asks about WAN links, internet connectivity, uplink status, or "
                "gateway interfaces. For example: 'Show me WAN status for gateway', 'Uplink health check', "
                "'Internet connection status', 'WAN interface details for GW-Main-01', 'Which uplink is "
                "active?'.\n\n"
                "DO NOT USE for general gateway status - use get_gateway_details instead. "
                "This tool provides WAN-specific interface diagnostics for ONE specific gateway."
            ),
            inputSchema={
                "type": "object",
                "properties": {"serial": {"type": "string", "description": "Serial number of the gateway (required)"}},
                "required": ["serial"],
            },
        ),
        Tool(
            name="ping_from_ap",
            description=(
                "Initiates a ping test FROM a specific access point TO a target host or IP address. "
                "This is an active diagnostic tool that sends ICMP echo requests from the AP to verify "
                "network connectivity, measure latency, and test reachability. Returns an async task ID "
                "that must be polled using get_async_test_result to retrieve ping statistics (packets "
                "sent/received, packet loss %, min/avg/max latency).\n\n"
                "USE THIS WHEN the user wants to test connectivity FROM an AP to a specific destination. "
                "For example: 'Ping 8.8.8.8 from AP-Floor2-03', 'Test connectivity from AP to server', "
                "'Can AP reach 10.1.1.1?', 'Run ping test from access point'.\n\n"
                "DO NOT USE for general AP status - use get_ap_details instead. "
                "DO NOT USE for pinging FROM gateway - use ping_from_gateway instead. "
                "This tool initiates an active test and returns a task ID - you MUST poll for results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "serial": {"type": "string", "description": "Serial number of the access point (required)"},
                    "target": {"type": "string", "description": "Target hostname or IP address to ping (required)"},
                    "count": {
                        "type": "integer",
                        "description": "Number of ping packets to send (default: 5)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 5,
                    },
                    "packet_size": {
                        "type": "integer",
                        "description": "Size of ping packets in bytes (default: 64)",
                        "minimum": 32,
                        "maximum": 1500,
                        "default": 64,
                    },
                },
                "required": ["serial", "target"],
            },
        ),
        Tool(
            name="ping_from_gateway",
            description=(
                "Initiates a ping test FROM a specific gateway TO a target host or IP address. This is "
                "an active diagnostic tool that sends ICMP echo requests from the gateway to verify WAN "
                "connectivity, measure internet latency, and test external reachability. Returns an async "
                "task ID that must be polled using get_async_test_result to retrieve ping statistics "
                "(packets sent/received, packet loss %, min/avg/max latency).\n\n"
                "USE THIS WHEN the user wants to test connectivity FROM a gateway to external destinations. "
                "For example: 'Ping 8.8.8.8 from gateway', 'Test internet from GW-Main-01', 'Can gateway "
                "reach external server?', 'Run ping from gateway to verify WAN'.\n\n"
                "DO NOT USE for general gateway status - use get_gateway_details instead. "
                "DO NOT USE for pinging FROM AP - use ping_from_ap instead. "
                "This tool initiates an active test and returns a task ID - you MUST poll for results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "serial": {"type": "string", "description": "Serial number of the gateway (required)"},
                    "target": {"type": "string", "description": "Target hostname or IP address to ping (required)"},
                    "count": {
                        "type": "integer",
                        "description": "Number of ping packets to send (default: 5)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 5,
                    },
                    "source_interface": {
                        "type": "string",
                        "description": "Source WAN interface to use (optional, uses primary by default)",
                    },
                },
                "required": ["serial", "target"],
            },
        ),
        Tool(
            name="traceroute_from_ap",
            description=(
                "Initiates a traceroute test FROM a specific access point TO a target host or IP address. "
                "This is an active diagnostic tool that traces the network path by sending packets with "
                "incrementing TTL values to discover each hop in the route. Returns an async task ID that "
                "must be polled using get_async_test_result to retrieve the complete path (hop-by-hop "
                "IP addresses, hostnames, and latency for each hop).\n\n"
                "USE THIS WHEN the user wants to trace the network path FROM an AP to a destination or "
                "diagnose routing issues. For example: 'Traceroute to 8.8.8.8 from AP-Floor2-03', 'Trace "
                "path from AP to server', 'Show route from access point to 10.1.1.1', 'Find where packets "
                "are getting stuck'.\n\n"
                "DO NOT USE for simple connectivity tests - use ping_from_ap instead. "
                "DO NOT USE for traceroute FROM gateway - use a gateway-specific tool if available. "
                "This tool initiates an active test and returns a task ID - you MUST poll for results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "serial": {"type": "string", "description": "Serial number of the access point (required)"},
                    "target": {
                        "type": "string",
                        "description": "Target hostname or IP address for traceroute (required)",
                    },
                    "max_hops": {
                        "type": "integer",
                        "description": "Maximum number of hops to trace (default: 30)",
                        "minimum": 1,
                        "maximum": 64,
                        "default": 30,
                    },
                },
                "required": ["serial", "target"],
            },
        ),
        Tool(
            name="get_async_test_result",
            description=(
                "Retrieves the results of a previously initiated async diagnostic operation such as ping, "
                "traceroute, speedtest, or other network tests. This is the unified polling tool used with "
                "ALL async operations - you provide the task ID returned from the initial test, and this "
                "tool checks if results are ready. Returns test status (IN_PROGRESS, COMPLETED, FAILED) and "
                "complete results when finished including statistics, measurements, and diagnostic data.\n\n"
                "USE THIS WHEN you have a task ID from a previous diagnostic test and need to check results. "
                "For example: After calling ping_from_ap, ping_from_gateway, or traceroute_from_ap, you "
                "receive a task ID - use THIS tool to poll for results. You may need to call this multiple "
                "times if status is still IN_PROGRESS.\n\n"
                "DO NOT USE to initiate tests - use ping_from_ap, ping_from_gateway, traceroute_from_ap, etc. "
                "This tool ONLY retrieves results from already-started operations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID returned from the initial async operation (required)",
                    }
                },
                "required": ["task_id"],
            },
        ),
        Tool(
            name="list_idps_threats",
            description=(
                "Retrieves active security threats detected by the Intrusion Detection and Prevention "
                "System (IDPS). Returns comprehensive threat information including threat name, severity "
                "level (CRITICAL/HIGH/MEDIUM/LOW), threat type/category (malware, exploit, DoS, etc.), "
                "source IP/device, destination IP/device, detection timestamp, threat signature ID, "
                "mitigation action taken (blocked/allowed/logged), and affected gateway/firewall. "
                "Essential for security monitoring, incident response, threat analysis, and compliance "
                "reporting.\n\n"
                "USE THIS WHEN the user asks about security threats, attacks, intrusions, malware, or "
                "suspicious activity. For example: 'Show security threats', 'Any attacks detected?', "
                "'List active threats', 'IDPS alerts', 'What malware has been blocked?', 'Security "
                "incidents'.\n\n"
                "DO NOT USE for firewall session logs - use get_firewall_sessions instead. "
                "This tool focuses on security threats detected by the IDPS engine."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "severity": {
                        "type": "string",
                        "description": "Filter by severity level",
                        "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                    },
                    "gateway_serial": {"type": "string", "description": "Filter threats detected by specific gateway"},
                    "start_time": {
                        "type": "string",
                        "description": "Start time for threat query (RFC 3339 format)",
                        "format": "date-time",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time for threat query (RFC 3339 format)",
                        "format": "date-time",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of threats to return",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 100,
                    },
                },
            },
        ),
        Tool(
            name="get_firewall_sessions",
            description=(
                "Retrieves active and recent firewall sessions including blocked connections and allowed "
                "traffic. Returns detailed session information including source IP/port, destination "
                "IP/port, protocol (TCP/UDP/ICMP), application/service, firewall rule that matched, "
                "session status (ACTIVE/CLOSED/BLOCKED), byte/packet counts, session duration, and "
                "gateway that processed the traffic. Essential for firewall troubleshooting, analyzing "
                "blocked traffic, verifying firewall rules, and investigating connectivity issues.\n\n"
                "USE THIS WHEN the user asks about firewall activity, blocked traffic, connection logs, "
                "or wants to see what's being allowed/denied. For example: 'Show blocked traffic', "
                "'Firewall sessions', 'What connections are blocked?', 'Show firewall logs', 'Traffic "
                "analysis', 'Why can't I reach this server?'.\n\n"
                "DO NOT USE for security threats - use list_idps_threats instead. "
                "This tool focuses on firewall session logs and rule matching, not threat detection."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "site_id": {"type": "string", "description": "Filter sessions by site ID"},
                    "status": {
                        "type": "string",
                        "description": "Filter by session status",
                        "enum": ["ACTIVE", "CLOSED", "BLOCKED"],
                    },
                    "protocol": {"type": "string", "description": "Filter by protocol", "enum": ["TCP", "UDP", "ICMP"]},
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of sessions to return",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 100,
                    },
                },
            },
        ),
        Tool(
            name="get_stack_members",
            description=(
                "Retrieves detailed information about all members in a switch stack. Returns comprehensive "
                "stack topology including each member's serial number, device name, stack role (COMMANDER/ "
                "MEMBER/STANDBY), stack position/ID, operational status (UP/DOWN), model number, software "
                "version, MAC address, uptime, and connectivity to other stack members. Essential for "
                "managing switch stacks, verifying stack membership, monitoring stack health, troubleshooting "
                "failover scenarios, and planning stack upgrades.\n\n"
                "USE THIS WHEN the user asks about switch stack members, stack topology, or stack status. "
                "For example: 'Show stack members', 'What switches are in the stack?', 'Stack topology', "
                "'Which switch is the commander?', 'Stack member status', 'Show stack configuration'.\n\n"
                "DO NOT USE for individual switch details - use get_switch_details instead. "
                "DO NOT USE for port/interface information - use get_switch_interfaces instead. "
                "This tool is specifically for switch stacking topology and membership."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "stack_id": {
                        "type": "string",
                        "description": "Stack identifier (required) - can be stack name or ID",
                    }
                },
                "required": ["stack_id"],
            },
        ),
        Tool(
            name="get_switch_interfaces",
            description=(
                "Retrieves comprehensive information about all physical interfaces (ports) on a specific "
                "switch. Returns detailed port-level data including interface name/number, operational "
                "status (UP/DOWN), administrative status (enabled/disabled), link speed (1G/10G/25G/etc.), "
                "duplex mode (full/half), VLAN assignment (access/trunk), allowed VLANs, native VLAN, "
                "PoE status and power consumption, connected device (LLDP/CDP neighbor), MAC address, "
                "error counters (CRC/collisions/drops), and traffic statistics. Essential for port-level "
                "troubleshooting, connectivity diagnosis, VLAN verification, and PoE power management.\n\n"
                "USE THIS WHEN the user asks about switch ports, port status, interface configuration, or "
                "connectivity issues. For example: 'Show switch ports', 'Port status for switch', 'Which "
                "ports are down?', 'PoE power on ports', 'VLAN assignments', 'Interface errors', 'What's "
                "connected to port 24?'.\n\n"
                "DO NOT USE for overall switch details - use get_switch_details instead. "
                "DO NOT USE for stack topology - use get_stack_members instead. "
                "This tool is specifically for port/interface-level information."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "serial": {"type": "string", "description": "Switch serial number (required)"},
                    "status_filter": {
                        "type": "string",
                        "description": "Filter ports by status",
                        "enum": ["UP", "DOWN", "ALL"],
                    },
                },
                "required": ["serial"],
            },
        ),
    ]


# =============================================================================
# TOOL HANDLER REGISTRY
# =============================================================================
# Registry pattern: Maps tool names to handler functions for clean dispatch

TOOL_HANDLERS = {
    # Core inventory and device tools
    "get_device_list": handle_get_device_list,
    "get_device_inventory": handle_get_device_inventory,
    "get_sites_health": handle_get_sites_health,
    "list_all_clients": handle_list_all_clients,
    "list_gateways": handle_list_gateways,
    "get_firmware_details": handle_get_firmware_details,
    # Site and tenant tools
    "get_site_details": handle_get_site_details,
    "get_tenant_device_health": handle_get_tenant_device_health,
    # AP tools
    "get_ap_details": handle_get_ap_details,
    "get_ap_cpu_utilization": handle_get_ap_cpu_utilization,
    "get_ap_radios": handle_get_ap_radios,
    # Switch tools
    "get_switch_details": handle_get_switch_details,
    "get_switch_interfaces": handle_get_switch_interfaces,
    "get_stack_members": handle_get_stack_members,
    # Gateway tools
    "get_gateway_details": handle_get_gateway_details,
    "get_gateway_cpu_utilization": handle_get_gateway_cpu_utilization,
    "get_gateway_cluster_info": handle_get_gateway_cluster_info,
    "get_gateway_uplinks": handle_get_gateway_uplinks,
    "list_gateway_tunnels": handle_list_gateway_tunnels,
    # WLAN tools
    "list_wlans": handle_list_wlans,
    "get_wlan_details": handle_get_wlan_details,
    # Client and bandwidth tools
    "get_client_trends": handle_get_client_trends,
    "get_top_aps_by_bandwidth": handle_get_top_aps_by_bandwidth,
    "get_top_clients_by_usage": handle_get_top_clients_by_usage,
    # Network diagnostics (async operations)
    "ping_from_ap": handle_ping_from_ap,
    "ping_from_gateway": handle_ping_from_gateway,
    "traceroute_from_ap": handle_traceroute_from_ap,
    "get_async_test_result": handle_get_async_test_result,
    # Security tools
    "list_idps_threats": handle_list_idps_threats,
    "get_firewall_sessions": handle_get_firewall_sessions,
}


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    Dispatch a tool call to the appropriate handler.

    Provides consistent error handling and logging for all tool invocations.

    Args:
        name: Tool name to invoke
        arguments: Tool arguments from MCP client

    Returns:
        List of TextContent responses

    Raises:
        ValueError: If tool name is unknown
    """
    handler = TOOL_HANDLERS.get(name)

    if handler is None:
        logger.error(f"Unknown tool requested: {name}")
        from src.tools.base import StatusLabels

        return [
            TextContent(
                type="text",
                text=(
                    f"{StatusLabels.ERR} Unknown tool: {name}\n\n"
                    f"Available tools: {', '.join(sorted(TOOL_HANDLERS.keys()))}"
                ),
            )
        ]

    try:
        logger.info(f"Executing tool: {name}")
        result = await handler(arguments)
    except Exception as e:
        logger.exception(f"Tool {name} failed with error")
        from src.tools.base import StatusLabels

        return [
            TextContent(
                type="text",
                text=(
                    f"{StatusLabels.ERR} Tool {name} failed: {e!s}\n\n"
                    "Please check the logs for detailed error information."
                ),
            )
        ]
    else:
        logger.info(f"Tool {name} completed successfully")
        return result


async def main():
    """Run the MCP server."""
    import sys
    from src.version_check import VERSION_ID, HAS_AUTO_TOKEN_FIX

    print(f"Starting Aruba NOC Server [{VERSION_ID}]...", file=sys.stderr)
    print(f"Auto-token fix: {'ENABLED' if HAS_AUTO_TOKEN_FIX else 'DISABLED'}", file=sys.stderr)

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
