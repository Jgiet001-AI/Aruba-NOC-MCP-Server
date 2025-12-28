"""
Unit tests for Pydantic v2 input models.

These tests verify input validation, normalization, and error handling.
"""

import pytest
from pydantic import ValidationError

from src.tools.models import (
    GetAPDetailsInput,
    GetAPRadiosInput,
    GetDeviceListInput,
    GetGatewayDetailsInput,
    GetSiteDetailsInput,
    GetSwitchDetailsInput,
    ListAllClientsInput,
    PingFromAPInput,
)


class TestGetAPDetailsInput:
    """Tests for GetAPDetailsInput model."""

    def test_valid_serial(self):
        """Valid serial number should pass."""
        model = GetAPDetailsInput(serial_number="CN12345678")
        assert model.serial_number == "CN12345678"

    def test_serial_normalization_uppercase(self):
        """Serial number should be uppercased."""
        model = GetAPDetailsInput(serial_number="cn12345678")
        assert model.serial_number == "CN12345678"

    def test_serial_normalization_strips_whitespace(self):
        """Serial number should be stripped of whitespace."""
        model = GetAPDetailsInput(serial_number="  CN12345678  ")
        assert model.serial_number == "CN12345678"

    def test_missing_serial_raises(self):
        """Missing serial_number should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GetAPDetailsInput()
        assert "serial_number" in str(exc_info.value)

    def test_short_serial_raises(self):
        """Serial number too short should raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            GetAPDetailsInput(serial_number="ABC")
        assert "at least 5 characters" in str(exc_info.value)


class TestGetSwitchDetailsInput:
    """Tests for GetSwitchDetailsInput model."""

    def test_valid_serial(self):
        """Valid serial should pass."""
        model = GetSwitchDetailsInput(serial="SN98765432")
        assert model.serial == "SN98765432"

    def test_serial_normalization(self):
        """Serial should be normalized."""
        model = GetSwitchDetailsInput(serial=" sn98765432 ")
        assert model.serial == "SN98765432"

    def test_missing_serial_raises(self):
        """Missing serial should raise ValidationError."""
        with pytest.raises(ValidationError):
            GetSwitchDetailsInput()


class TestGetGatewayDetailsInput:
    """Tests for GetGatewayDetailsInput model."""

    def test_valid_serial(self):
        """Valid serial_number should pass."""
        model = GetGatewayDetailsInput(serial_number="GW12345678")
        assert model.serial_number == "GW12345678"


class TestGetSiteDetailsInput:
    """Tests for GetSiteDetailsInput model."""

    def test_valid_site_id(self):
        """Valid site_id should pass."""
        model = GetSiteDetailsInput(site_id="site-001")
        assert model.site_id == "site-001"

    def test_site_id_strips_whitespace(self):
        """Site ID should be stripped of whitespace."""
        model = GetSiteDetailsInput(site_id="  site-001  ")
        assert model.site_id == "site-001"

    def test_missing_site_id_raises(self):
        """Missing site_id should raise ValidationError."""
        with pytest.raises(ValidationError):
            GetSiteDetailsInput()


class TestGetDeviceListInput:
    """Tests for GetDeviceListInput (paginated) model."""

    def test_defaults(self):
        """Default values should be set correctly."""
        model = GetDeviceListInput()
        assert model.limit == 100
        assert model.filter is None
        assert model.sort is None
        assert model.next is None

    def test_custom_values(self):
        """Custom values should be accepted."""
        model = GetDeviceListInput(filter="status eq 'ONLINE'", limit=50)
        assert model.filter == "status eq 'ONLINE'"
        assert model.limit == 50

    def test_limit_minimum(self):
        """Limit must be at least 1."""
        with pytest.raises(ValidationError) as exc_info:
            GetDeviceListInput(limit=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_limit_maximum(self):
        """Limit must be at most 100."""
        with pytest.raises(ValidationError) as exc_info:
            GetDeviceListInput(limit=200)
        assert "less than or equal to 100" in str(exc_info.value)


class TestListAllClientsInput:
    """Tests for ListAllClientsInput model."""

    def test_defaults(self):
        """Default values should be set correctly."""
        model = ListAllClientsInput()
        assert model.limit == 100
        assert model.site_id is None
        assert model.serial_number is None

    def test_with_site_id(self):
        """Site ID filter should be accepted."""
        model = ListAllClientsInput(site_id="site-001", limit=50)
        assert model.site_id == "site-001"
        assert model.limit == 50


class TestPingFromAPInput:
    """Tests for PingFromAPInput model."""

    def test_valid_input(self):
        """Valid input should pass."""
        model = PingFromAPInput(serial_number="CN12345678", target="8.8.8.8")
        assert model.serial_number == "CN12345678"
        assert model.target == "8.8.8.8"
        assert model.count == 4  # Default

    def test_custom_count(self):
        """Custom count should be accepted."""
        model = PingFromAPInput(serial_number="CN12345678", target="8.8.8.8", count=10)
        assert model.count == 10

    def test_count_bounds(self):
        """Count must be between 1 and 10."""
        with pytest.raises(ValidationError):
            PingFromAPInput(serial_number="CN12345678", target="8.8.8.8", count=0)
        with pytest.raises(ValidationError):
            PingFromAPInput(serial_number="CN12345678", target="8.8.8.8", count=11)

    def test_missing_required_fields(self):
        """Missing required fields should raise ValidationError."""
        with pytest.raises(ValidationError):
            PingFromAPInput()
        with pytest.raises(ValidationError):
            PingFromAPInput(serial_number="CN12345678")


class TestGetAPRadiosInput:
    """Tests for GetAPRadiosInput model."""

    def test_valid_serial(self):
        """Valid serial should pass."""
        model = GetAPRadiosInput(serial="CN12345678")
        assert model.serial == "CN12345678"
