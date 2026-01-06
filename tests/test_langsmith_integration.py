"""
Tests for LangSmith integration

Verifies that LangSmith tracing is properly integrated into the MCP server.
"""

import os
from unittest.mock import patch

import pytest


class TestLangSmithIntegration:
    """Test LangSmith tracing integration."""

    def test_langsmith_available_when_api_key_set(self):
        """Verify LangSmith is enabled when API key is configured."""
        # Set API key in environment
        with patch.dict(os.environ, {"LANGSMITH_API_KEY": "test_key"}):
            # Reimport to pick up environment change
            import importlib

            from src import langsmith_tracing

            importlib.reload(langsmith_tracing)

            # Should be available when API key is set
            assert langsmith_tracing.langsmith_available or langsmith_tracing.is_langsmith_enabled()

    def test_langsmith_disabled_without_api_key(self):
        """Verify LangSmith is disabled when no API key configured."""
        # Remove API key from environment
        with patch.dict(os.environ, {}, clear=True):
            # Reimport to pick up environment change
            import importlib

            from src import langsmith_tracing

            importlib.reload(langsmith_tracing)

            # Should NOT be available without API key
            assert not langsmith_tracing.is_langsmith_enabled()

    @pytest.mark.asyncio
    async def test_trace_mcp_tool_call_context_manager(self):
        """Verify trace_mcp_tool_call context manager works."""
        from src.langsmith_tracing import trace_mcp_tool_call

        # Should work even if LangSmith is disabled (graceful degradation)
        async with trace_mcp_tool_call("test_tool", {"arg1": "value1"}):
            # Context manager should yield without error
            result = "success"

        assert result == "success"

    @pytest.mark.asyncio
    async def test_trace_handles_exceptions(self):
        """Verify trace_mcp_tool_call handles exceptions correctly."""
        from src.langsmith_tracing import trace_mcp_tool_call

        with pytest.raises(ValueError, match="test error"):
            async with trace_mcp_tool_call("test_tool", {"arg1": "value1"}):
                # Exception should propagate
                raise ValueError("test error")

    def test_get_langsmith_project_url(self):
        """Verify LangSmith project URL generation."""
        from src.langsmith_tracing import get_langsmith_project_url

        # Should return None if not enabled
        # (Implementation depends on whether API key is set)
        url = get_langsmith_project_url()

        if url:
            assert "smith.langchain.com" in url
            assert "aruba-noc-server" in url

    def test_log_tracing_status(self):
        """Verify tracing status logging works."""
        from src.langsmith_tracing import log_tracing_status

        # Should not raise exception
        log_tracing_status()
