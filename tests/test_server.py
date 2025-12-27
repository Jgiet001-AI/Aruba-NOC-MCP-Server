"""
Tests for server.py MCP server
"""

from unittest.mock import AsyncMock, patch

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

    @pytest.mark.asyncio
    async def test_call_tool_get_device_list(self, mock_devices_response):
        """Test dispatching to get_device_list."""
        with patch("src.server.handle_get_device_list", new_callable=AsyncMock) as mock_handler:
            mock_handler.return_value = [{"type": "text", "text": "test"}]

            await call_tool("get_device_list", {"limit": 10})

            mock_handler.assert_called_once_with({"limit": 10})

    @pytest.mark.asyncio
    async def test_call_tool_list_all_clients(self):
        """Test dispatching to list_all_clients."""
        with patch("src.server.handle_list_all_clients", new_callable=AsyncMock) as mock_handler:
            mock_handler.return_value = [{"type": "text", "text": "test"}]

            await call_tool("list_all_clients", {"site_id": "123"})

            mock_handler.assert_called_once_with({"site_id": "123"})

    @pytest.mark.asyncio
    async def test_call_tool_get_firmware_details(self):
        """Test dispatching to get_firmware_details."""
        with patch("src.server.handle_get_firmware_details", new_callable=AsyncMock) as mock_handler:
            mock_handler.return_value = [{"type": "text", "text": "test"}]

            await call_tool("get_firmware_details", {})

            mock_handler.assert_called_once_with({})

    @pytest.mark.asyncio
    async def test_call_tool_list_gateways(self):
        """Test dispatching to list_gateways."""
        with patch("src.server.handle_list_gateways", new_callable=AsyncMock) as mock_handler:
            mock_handler.return_value = [{"type": "text", "text": "test"}]

            await call_tool("list_gateways", {"filter": "status eq ONLINE"})

            mock_handler.assert_called_once_with({"filter": "status eq ONLINE"})

    @pytest.mark.asyncio
    async def test_call_tool_get_sites_health(self):
        """Test dispatching to get_sites_health."""
        with patch("src.server.handle_get_sites_health", new_callable=AsyncMock) as mock_handler:
            mock_handler.return_value = [{"type": "text", "text": "test"}]

            await call_tool("get_sites_health", {"limit": 50})

            mock_handler.assert_called_once_with({"limit": 50})

    @pytest.mark.asyncio
    async def test_call_tool_unknown_raises_error(self):
        """Test that unknown tool raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await call_tool("nonexistent_tool", {})
