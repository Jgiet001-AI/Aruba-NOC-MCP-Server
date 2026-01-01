"""
Tests for server.py MCP server
"""

from unittest.mock import MagicMock, patch

import pytest

from src.server import call_tool, list_tools


class TestListTools:
    """Test cases for list_tools function."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_tools(self):
        """Test that list_tools returns all expected tools."""
        tools = await list_tools()

        assert len(tools) >= 5

        tool_names = [t.name for t in tools]
        assert "get_device_list" in tool_names
        assert "list_all_clients" in tool_names
        assert "get_firmware_details" in tool_names
        assert "list_gateways" in tool_names
        assert "get_sites_health" in tool_names

    @pytest.mark.asyncio
    async def test_tools_have_descriptions(self):
        """Test that all tools have descriptions."""
        tools = await list_tools()

        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 50  # Should be descriptive

    @pytest.mark.asyncio
    async def test_tools_have_input_schemas(self):
        """Test that all tools have input schemas."""
        tools = await list_tools()

        for tool in tools:
            assert tool.inputSchema is not None
            assert tool.inputSchema.get("type") == "object"


class TestCallTool:
    """Test cases for call_tool dispatcher."""

    @pytest.fixture(autouse=True)
    def mock_api_call(self):
        """Mock the API client to prevent actual network calls"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": [], "total": 0, "count": 0}

        with (
            patch("src.api_client.config") as mock_config,
            patch("src.api_client.httpx.AsyncClient") as mock_client_class,
        ):
            mock_config.access_token = "test_token"
            mock_config.base_url = "https://api.test.com"
            mock_config.get_headers.return_value = {"Authorization": "Bearer test_token"}

            mock_client_instance = MagicMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client_instance
            mock_client_class.return_value.__aexit__.return_value = None

            async def mock_request(*args, **kwargs):
                return mock_response

            mock_client_instance.request = mock_request

            yield

    @pytest.mark.asyncio
    async def test_call_tool_get_device_list(self):
        """Test dispatching to get_device_list."""
        result = await call_tool("get_device_list", {"limit": 10})
        # Should return a list with TextContent
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_call_tool_list_all_clients(self):
        """Test dispatching to list_all_clients."""
        result = await call_tool("list_all_clients", {"site_id": "123"})
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_call_tool_get_firmware_details(self):
        """Test dispatching to get_firmware_details."""
        result = await call_tool("get_firmware_details", {})
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_call_tool_list_gateways(self):
        """Test dispatching to list_gateways."""
        result = await call_tool("list_gateways", {"filter": "status eq ONLINE"})
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_call_tool_get_sites_health(self):
        """Test dispatching to get_sites_health."""
        result = await call_tool("get_sites_health", {"limit": 50})
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_call_tool_unknown_raises_error(self):
        """Test that unknown tool raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await call_tool("nonexistent_tool", {})
