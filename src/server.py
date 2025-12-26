import logging
from mcp.server import Server
from mcp.server.stdio import StdIO_server
from mcp.types import Tool, TextContent
from typing import Any

# Import handler functions from tool modules
from src.tools.devices import handle_get_device_list, handle_get_device_inventory
from src.tools.sites import handle_get_sites_health, handle_get_site_details
from src.tools.clients import handle_list_all_clients
from src.tools.gateways import handle_list_gateways
from src.tools.firmware import handle_get_firmware_details

logger = logging.getLogger("aruba-noc-server")

app = Server("Aruba NOC Server", "1.0.0")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return[
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
                )
            },
            "sort": {
                "type": "string",
                "description": (
                    "Sort order. Format: 'field direction'. "
                    "Available fields: deviceName, model, serialNumber, siteId, siteName. "
                    "Examples: 'deviceName asc', 'lastSeenAt desc', 'siteId asc'"
                )
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of devices to return (default: 100)",
                "minimum": 1,
                "maximum": 1000,
                "default": 100
            },
            "next": {
                "type": "string",
                "description": "Pagination cursor token for retrieving next page of results"
            }
        }
    }
)
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> TextContent:
    """Dispatches a tool call to the appropriate handler."""
    
    if name == "get_device_list":
        return await handle_get_device_list(arguments)
    elif name == "get_device_inventory":
        return await handle_get_device_inventory(arguments)
    elif name == "get_sites_health":
        return await handle_get_sites_health(arguments)
    elif name == "get_site_details":
        return await handle_get_site_details(arguments)
    elif name == "list_all_clients":
        return await handle_list_all_clients(arguments)
    elif name == "list_gateways":
        return await handle_list_gateways(arguments)
    elif name == "get_firmware_details":
        return await handle_get_firmware_details(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server."""
    logger.info("Starting Aruba NOC Server...")

    async with StdIO_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )
        