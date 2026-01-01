"""
Tests for base.py shared utilities
"""

from src.tools.base import (
    StatusLabels,
    build_error_response,
    build_text_response,
    extract_params,
    format_json,
    format_pagination_message,
    get_status_label,
    safe_get,
)


class TestStatusLabels:
    """Test StatusLabels constants."""

    def test_status_labels_exist(self):
        """Test that all expected status labels are defined."""
        assert StatusLabels.OK == "[OK]"
        assert StatusLabels.WARN == "[WARN]"
        assert StatusLabels.CRIT == "[CRIT]"
        assert StatusLabels.UP == "[UP]"
        assert StatusLabels.DN == "[DN]"
        assert StatusLabels.UNKNOWN == "[--]"

    def test_device_type_labels(self):
        """Test device type labels."""
        assert StatusLabels.AP == "[AP]"
        assert StatusLabels.SW == "[SW]"
        assert StatusLabels.GW == "[GW]"
        assert StatusLabels.DEV == "[DEV]"

    def test_connection_labels(self):
        """Test connection type labels."""
        assert StatusLabels.WIFI == "[WIFI]"
        assert StatusLabels.WIRED == "[WIRED]"


class TestFormatJson:
    """Test format_json function."""

    def test_format_json_simple(self):
        """Test formatting simple dictionary."""
        data = {"key": "value"}
        result = format_json(data)
        assert '"key": "value"' in result

    def test_format_json_nested(self):
        """Test formatting nested dictionary."""
        data = {"outer": {"inner": "value"}}
        result = format_json(data)
        assert "outer" in result
        assert "inner" in result

    def test_format_json_custom_indent(self):
        """Test custom indentation."""
        data = {"a": 1}
        result = format_json(data, indent=4)
        assert result.count(" ") >= 4


class TestExtractParams:
    """Test extract_params function."""

    def test_extract_params_basic(self):
        """Test basic parameter extraction."""
        args = {"limit": 50, "offset": 10}
        result = extract_params(args)
        assert result["limit"] == 50
        assert result["offset"] == 10

    def test_extract_params_with_mapping(self):
        """Test parameter extraction with name mapping."""
        args = {"site_id": "123", "serial_number": "SN456"}
        param_map = {"site_id": "site-id", "serial_number": "serial-number"}
        result = extract_params(args, param_map=param_map)
        assert result["site-id"] == "123"
        assert result["serial-number"] == "SN456"

    def test_extract_params_with_defaults(self):
        """Test parameter extraction with defaults."""
        args = {"limit": 50}
        defaults = {"limit": 100, "offset": 0}
        result = extract_params(args, defaults=defaults)
        assert result["limit"] == 50  # Override from args
        assert result["offset"] == 0  # Default

    def test_extract_params_ignores_none(self):
        """Test that None values are ignored."""
        args = {"limit": 100, "filter": None}
        result = extract_params(args)
        assert result["limit"] == 100
        assert "filter" not in result


class TestSafeGet:
    """Test safe_get function."""

    def test_safe_get_existing_key(self):
        """Test getting existing key."""
        data = {"name": "test"}
        assert safe_get(data, "name") == "test"

    def test_safe_get_missing_key(self):
        """Test default for missing key."""
        data = {"name": "test"}
        assert safe_get(data, "missing") == "Unknown"

    def test_safe_get_custom_default(self):
        """Test custom default value."""
        data = {"name": "test"}
        assert safe_get(data, "missing", default="N/A") == "N/A"

    def test_safe_get_none_value(self):
        """Test that None values use default."""
        data = {"name": None}
        assert safe_get(data, "name") == "Unknown"


class TestGetStatusLabel:
    """Test get_status_label function."""

    def test_get_status_label_found(self):
        """Test getting label for known status."""
        label_map = {"Good": "[OK]", "Poor": "[CRIT]"}
        assert get_status_label("Good", label_map) == "[OK]"

    def test_get_status_label_unknown(self):
        """Test default for unknown status."""
        label_map = {"Good": "[OK]"}
        assert get_status_label("Unknown", label_map) == StatusLabels.UNKNOWN


class TestFormatPaginationMessage:
    """Test format_pagination_message function."""

    def test_pagination_with_more(self):
        """Test message when more results exist."""
        result = format_pagination_message(has_more=True)
        assert result is not None
        assert "[MORE]" in result

    def test_pagination_no_more(self):
        """Test no message when no more results."""
        result = format_pagination_message(has_more=False)
        assert result is None


class TestBuildTextResponse:
    """Test build_text_response function."""

    def test_build_text_response(self):
        """Test building standard response."""
        summary = "Test Summary"
        data = {"result": "test"}
        result = build_text_response(summary, data)

        assert len(result) == 1
        assert result[0].type == "text"
        assert "Test Summary" in result[0].text
        assert '"result"' in result[0].text


class TestBuildErrorResponse:
    """Test build_error_response function."""

    def test_build_error_response(self):
        """Test building error response."""
        result = build_error_response("Something failed", "test_tool")

        assert len(result) == 1
        assert result[0].type == "text"
        assert "[ERROR]" in result[0].text
        assert "test_tool" in result[0].text
        assert "Something failed" in result[0].text
