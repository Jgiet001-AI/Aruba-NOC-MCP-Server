"""
Regression tests for base.py format helper functions.

These tests capture the CURRENT WORKING BEHAVIOR before applying lint fixes.
They serve as a safety net to ensure formatting functions continue to work correctly.
"""

# Import directly to avoid broken modules in tools package
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.tools.base import (
    StatusLabels,
    format_bytes,
    format_percentage,
    format_uptime,
)


class TestFormatBytes:
    """Test format_bytes function - converts bytes to human-readable sizes."""

    def test_format_bytes_zero(self):
        """Test zero bytes."""
        assert format_bytes(0) == "0.00 B"

    def test_format_bytes_small(self):
        """Test small byte values stay in bytes."""
        assert format_bytes(500) == "500.00 B"
        assert format_bytes(1) == "1.00 B"

    def test_format_bytes_kilobytes(self):
        """Test conversion to KB."""
        result = format_bytes(1024)
        assert "KB" in result
        assert "1.00" in result

    def test_format_bytes_megabytes(self):
        """Test conversion to MB."""
        result = format_bytes(1024 * 1024)
        assert "MB" in result
        assert "1.00" in result

    def test_format_bytes_gigabytes(self):
        """Test conversion to GB."""
        result = format_bytes(1024 * 1024 * 1024)
        assert "GB" in result
        assert "1.00" in result

    def test_format_bytes_terabytes(self):
        """Test conversion to TB."""
        result = format_bytes(1024 * 1024 * 1024 * 1024)
        assert "TB" in result

    def test_format_bytes_petabytes(self):
        """Test conversion to PB for very large values."""
        result = format_bytes(1024 * 1024 * 1024 * 1024 * 1024)
        assert "PB" in result

    def test_format_bytes_fractional(self):
        """Test fractional values are formatted with 2 decimal places."""
        result = format_bytes(1536)  # 1.5 KB
        assert "1.50 KB" in result

    def test_format_bytes_large_fractional(self):
        """Test large fractional values in MB."""
        result = format_bytes(2621440)  # 2.5 MB
        assert "MB" in result
        assert "2.50" in result


class TestFormatUptime:
    """Test format_uptime function - converts seconds to readable duration."""

    def test_format_uptime_seconds_only(self):
        """Test uptime less than a minute shows seconds."""
        assert format_uptime(30) == "30s"
        assert format_uptime(1) == "1s"
        assert format_uptime(59) == "59s"

    def test_format_uptime_minutes_seconds(self):
        """Test uptime in minutes shows minutes and seconds."""
        result = format_uptime(90)  # 1m 30s
        assert "1m" in result
        assert "30s" in result

    def test_format_uptime_hours_minutes(self):
        """Test uptime in hours shows hours and minutes."""
        result = format_uptime(3720)  # 1h 2m
        assert "1h" in result
        assert "2m" in result

    def test_format_uptime_days_hours_minutes(self):
        """Test uptime in days includes days, hours, and minutes."""
        result = format_uptime(90061)  # 1d 1h 1m
        assert "1d" in result
        assert "1h" in result
        assert "1m" in result

    def test_format_uptime_exact_hour(self):
        """Test exactly one hour shows 0 minutes."""
        result = format_uptime(3600)
        assert "1h" in result
        assert "0m" in result

    def test_format_uptime_multiple_days(self):
        """Test multiple days are displayed correctly."""
        result = format_uptime(5 * 24 * 3600 + 3 * 3600 + 20 * 60)  # 5d 3h 20m
        assert "5d" in result
        assert "3h" in result
        assert "20m" in result


class TestFormatPercentage:
    """Test format_percentage function - formats with status indicators."""

    def test_format_percentage_ok_low(self):
        """Test low percentage shows OK status."""
        result = format_percentage(25.0)
        assert StatusLabels.OK in result
        assert "25.0%" in result

    def test_format_percentage_ok_near_threshold(self):
        """Test percentage just below warn threshold shows OK."""
        result = format_percentage(69.9)
        assert StatusLabels.OK in result
        assert "69.9%" in result

    def test_format_percentage_warn(self):
        """Test percentage at warn threshold shows WARN."""
        result = format_percentage(70.0)
        assert StatusLabels.WARN in result
        assert "70.0%" in result

    def test_format_percentage_warn_middle(self):
        """Test percentage in warn range shows WARN."""
        result = format_percentage(85.5)
        assert StatusLabels.WARN in result
        assert "85.5%" in result

    def test_format_percentage_crit(self):
        """Test percentage at crit threshold shows CRIT."""
        result = format_percentage(90.0)
        assert StatusLabels.CRIT in result
        assert "90.0%" in result

    def test_format_percentage_crit_high(self):
        """Test very high percentage shows CRIT."""
        result = format_percentage(99.9)
        assert StatusLabels.CRIT in result
        assert "99.9%" in result

    def test_format_percentage_custom_thresholds(self):
        """Test custom thresholds work correctly."""
        # 50% should be OK with default, but WARN with lower threshold
        result_default = format_percentage(50.0)
        assert StatusLabels.OK in result_default

        result_custom = format_percentage(50.0, threshold_warn=40, threshold_crit=60)
        assert StatusLabels.WARN in result_custom

    def test_format_percentage_custom_crit_threshold(self):
        """Test custom critical threshold."""
        # 75% should be WARN with default, but CRIT with lower crit threshold
        result_default = format_percentage(75.0)
        assert StatusLabels.WARN in result_default

        result_custom = format_percentage(75.0, threshold_warn=50, threshold_crit=70)
        assert StatusLabels.CRIT in result_custom

    def test_format_percentage_zero(self):
        """Test zero percentage."""
        result = format_percentage(0.0)
        assert StatusLabels.OK in result
        assert "0.0%" in result

    def test_format_percentage_hundred(self):
        """Test 100 percent."""
        result = format_percentage(100.0)
        assert StatusLabels.CRIT in result
        assert "100.0%" in result


class TestStatusLabelsCompleteness:
    """Additional tests to verify all StatusLabels are properly defined."""

    def test_all_category_labels_exist(self):
        """Verify all category labels are defined."""
        # Categories
        assert hasattr(StatusLabels, "SEC")
        assert hasattr(StatusLabels, "BUG")
        assert hasattr(StatusLabels, "FEAT")
        assert hasattr(StatusLabels, "HW")
        assert hasattr(StatusLabels, "CLI")
        assert hasattr(StatusLabels, "VPN")
        assert hasattr(StatusLabels, "NET")

    def test_all_data_labels_exist(self):
        """Verify data/stats labels are defined."""
        assert hasattr(StatusLabels, "STATS")
        assert hasattr(StatusLabels, "TREND")
        assert hasattr(StatusLabels, "DATA")
        assert hasattr(StatusLabels, "RANK")

    def test_all_action_labels_exist(self):
        """Verify action/state labels are defined."""
        assert hasattr(StatusLabels, "AVAIL")
        assert hasattr(StatusLabels, "REQ")
        assert hasattr(StatusLabels, "IDLE")
        assert hasattr(StatusLabels, "MORE")
        assert hasattr(StatusLabels, "ALERT")
        assert hasattr(StatusLabels, "ASYNC")

    def test_all_operation_labels_exist(self):
        """Verify operation labels are defined."""
        assert hasattr(StatusLabels, "PING")
        assert hasattr(StatusLabels, "TRACE")

    def test_all_labels_are_bracketed(self):
        """Verify all labels follow the [LABEL] format."""
        for attr in dir(StatusLabels):
            if not attr.startswith("_"):
                value = getattr(StatusLabels, attr)
                assert value.startswith("["), f"{attr} should start with ["
                assert value.endswith("]"), f"{attr} should end with ]"

    def test_labels_are_uppercase(self):
        """Verify all label content (inside brackets) is uppercase."""
        for attr in dir(StatusLabels):
            if not attr.startswith("_"):
                value = getattr(StatusLabels, attr)
                # Extract content between brackets
                content = value[1:-1]
                # Allow "--" for UNKNOWN
                if content != "--":
                    assert content.isupper(), f"{attr} content '{content}' should be uppercase"
