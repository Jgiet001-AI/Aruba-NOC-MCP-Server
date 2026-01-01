"""
Regression tests for tool handler response patterns.

These tests verify the CURRENT WORKING BEHAVIOR of tool handlers:
- Response structure (list of TextContent)
- Summary formatting patterns
- JSON data inclusion
- Status label usage

Run these tests before applying lint fixes to ensure handlers continue
producing correctly structured output.
"""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from mcp.types import TextContent


class TestDevicesHandlerPatterns:
    """Test handle_get_device_list response patterns."""

    @pytest.fixture
    def mock_devices_data(self) -> dict[str, Any]:
        """Standard mock API response for devices."""
        return {
            "items": [
                {
                    "deviceType": "ACCESS_POINT",
                    "deviceName": "AP-Test-01",
                    "serialNumber": "CN12345",
                    "status": "ONLINE",
                    "model": "AP-515",
                    "deployment": "Standalone",
                },
                {
                    "deviceType": "SWITCH",
                    "deviceName": "SW-Test-01",
                    "serialNumber": "SN98765",
                    "status": "OFFLINE",
                    "model": "6300M",
                    "deployment": "Clustered",
                },
            ],
            "total": 2,
            "count": 2,
        }

    @pytest.mark.asyncio
    async def test_devices_handler_returns_list(self, mock_devices_data):
        """Verify handler returns list of TextContent."""
        from src.tools.devices import handle_get_device_list

        with patch("src.tools.devices.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_devices_data

            result = await handle_get_device_list({})

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert result[0].type == "text"

    @pytest.mark.asyncio
    async def test_devices_handler_summary_content(self, mock_devices_data):
        """Verify summary contains expected sections."""
        from src.tools.devices import handle_get_device_list

        with patch("src.tools.devices.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_devices_data

            result = await handle_get_device_list({})
            text = result[0].text

            # Check for required sections
            assert "Device Inventory Summary" in text
            assert "By Device Type" in text
            assert "By Status" in text

    @pytest.mark.asyncio
    async def test_devices_handler_status_labels(self, mock_devices_data):
        """Verify correct status labels are used."""
        from src.tools.devices import handle_get_device_list

        with patch("src.tools.devices.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_devices_data

            result = await handle_get_device_list({})
            text = result[0].text

            # Device type labels
            assert "[AP]" in text
            assert "[SW]" in text

            # Status labels
            assert "[UP]" in text  # ONLINE
            assert "[DN]" in text  # OFFLINE

    @pytest.mark.asyncio
    async def test_devices_handler_includes_verification_guardrails(self, mock_devices_data):
        """Verify verification guardrails are included in response (no raw JSON)."""
        from src.tools.devices import handle_get_device_list

        with patch("src.tools.devices.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_devices_data

            result = await handle_get_device_list({})
            text = result[0].text

            # Verify verification checkpoint is present
            assert "VERIFICATION CHECKPOINT" in text or "[CHECKPOINT]" in text
            # Verify anti-hallucination footer is present
            assert "BEFORE REPORTING, VERIFY" in text

    @pytest.mark.asyncio
    async def test_devices_handler_default_limit(self, mock_devices_data):
        """Verify default limit is applied when not provided."""
        from src.tools.devices import handle_get_device_list

        with patch("src.tools.devices.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_devices_data

            await handle_get_device_list({})

            # Check that limit was set to 100 by default
            call_args = mock_api.call_args
            params = call_args[1]["params"]
            assert params.get("limit") == 100


class TestClientsHandlerPatterns:
    """Test handle_list_all_clients response patterns."""

    @pytest.fixture
    def mock_clients_data(self) -> dict[str, Any]:
        """Standard mock API response for clients."""
        return {
            "items": [
                {
                    "macAddress": "AA:BB:CC:DD:EE:01",
                    "name": "laptop-001",
                    "type": "Wireless",
                    "status": "Connected",
                    "experience": "Good",
                },
                {
                    "macAddress": "AA:BB:CC:DD:EE:02",
                    "name": "desktop-001",
                    "type": "Wired",
                    "status": "Connected",
                    "experience": "Fair",
                },
            ],
            "total": 2,
            "count": 2,
        }

    @pytest.mark.asyncio
    async def test_clients_handler_returns_list(self, mock_clients_data):
        """Verify handler returns list of TextContent."""
        from src.tools.clients import handle_list_all_clients

        with patch("src.tools.clients.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_clients_data

            result = await handle_list_all_clients({})

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], TextContent)

    @pytest.mark.asyncio
    async def test_clients_handler_connection_labels(self, mock_clients_data):
        """Verify connection type labels are used."""
        from src.tools.clients import handle_list_all_clients

        with patch("src.tools.clients.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_clients_data

            result = await handle_list_all_clients({})
            text = result[0].text

            assert "[WIFI]" in text
            assert "[WIRED]" in text

    @pytest.mark.asyncio
    async def test_clients_handler_experience_labels(self, mock_clients_data):
        """Verify experience status labels are used."""
        from src.tools.clients import handle_list_all_clients

        with patch("src.tools.clients.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_clients_data

            result = await handle_list_all_clients({})
            text = result[0].text

            assert "[OK]" in text  # Good experience
            assert "[WARN]" in text  # Fair experience

    @pytest.mark.asyncio
    async def test_clients_handler_hyphenated_params(self, mock_clients_data):
        """Verify snake_case args are converted to hyphenated API params."""
        from src.tools.clients import handle_list_all_clients

        with patch("src.tools.clients.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_clients_data

            await handle_list_all_clients(
                {
                    "site_id": "test-site",
                    "serial_number": "SN123",
                }
            )

            call_args = mock_api.call_args
            params = call_args[1]["params"]

            # Verify hyphenated parameter names
            assert "site-id" in params
            assert "serial-number" in params
            assert params["site-id"] == "test-site"


class TestGatewaysHandlerPatterns:
    """Test handle_list_gateways response patterns."""

    @pytest.fixture
    def mock_gateways_data(self) -> dict[str, Any]:
        """Standard mock API response for gateways."""
        return {
            "items": [
                {
                    "deviceName": "GW-Main",
                    "serialNumber": "GW123",
                    "status": "ONLINE",
                    "model": "9004",
                    "deployment": "Clustered",
                    "siteName": "HQ",
                },
                {
                    "deviceName": "GW-Branch",
                    "serialNumber": "GW456",
                    "status": "OFFLINE",
                    "model": "7005",
                    "deployment": "Standalone",
                    "siteName": "Branch",
                },
            ],
            "total": 2,
            "count": 2,
        }

    @pytest.mark.asyncio
    async def test_gateways_handler_structure(self, mock_gateways_data):
        """Verify handler returns correct structure."""
        from src.tools.gateways import handle_list_gateways

        with patch("src.tools.gateways.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_gateways_data

            result = await handle_list_gateways({})

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], TextContent)

    @pytest.mark.asyncio
    async def test_gateways_handler_deployment_labels(self, mock_gateways_data):
        """Verify deployment type labels are used."""
        from src.tools.gateways import handle_list_gateways

        with patch("src.tools.gateways.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_gateways_data

            result = await handle_list_gateways({})
            text = result[0].text

            assert "[CLUST]" in text  # Clustered
            assert "[SOLO]" in text  # Standalone

    @pytest.mark.asyncio
    async def test_gateways_handler_offline_alert(self, mock_gateways_data):
        """Verify offline gateways trigger alert section."""
        from src.tools.gateways import handle_list_gateways

        with patch("src.tools.gateways.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_gateways_data

            result = await handle_list_gateways({})
            text = result[0].text

            # Should show alert for offline gateway
            assert "[ALERT]" in text
            assert "Offline Gateways" in text

    @pytest.mark.asyncio
    async def test_gateways_handler_availability_calc(self, mock_gateways_data):
        """Verify availability percentage is calculated."""
        from src.tools.gateways import handle_list_gateways

        with patch("src.tools.gateways.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_gateways_data

            result = await handle_list_gateways({})
            text = result[0].text

            # With 1 online out of 2, should show 50%
            assert "Availability" in text
            assert "50.0%" in text


class TestFirmwareHandlerPatterns:
    """Test handle_get_firmware_details response patterns."""

    @pytest.fixture
    def mock_firmware_data(self) -> dict[str, Any]:
        """Standard mock API response for firmware."""
        return {
            "items": [
                {
                    "deviceName": "AP-01",
                    "serialNumber": "CN123",
                    "deviceType": "ACCESS_POINT",
                    "softwareVersion": "8.10.0.0",
                    "recommendedVersion": "8.11.0.0",
                    "upgradeStatus": "Update Available",
                    "firmwareClassification": "Feature Release",
                },
                {
                    "deviceName": "SW-01",
                    "serialNumber": "SN456",
                    "deviceType": "SWITCH",
                    "softwareVersion": "10.10.1010",
                    "recommendedVersion": "10.10.1010",
                    "upgradeStatus": "Up To Date",
                    "firmwareClassification": "Security Patch",
                },
            ],
            "total": 2,
        }

    @pytest.mark.asyncio
    async def test_firmware_handler_structure(self, mock_firmware_data):
        """Verify handler returns correct structure."""
        from src.tools.firmware import handle_get_firmware_details

        with patch("src.tools.firmware.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_firmware_data

            result = await handle_get_firmware_details({})

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], TextContent)

    @pytest.mark.asyncio
    async def test_firmware_handler_upgrade_labels(self, mock_firmware_data):
        """Verify upgrade status labels are used."""
        from src.tools.firmware import handle_get_firmware_details

        with patch("src.tools.firmware.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_firmware_data

            result = await handle_get_firmware_details({})
            text = result[0].text

            assert "[OK]" in text  # Up To Date
            assert "[AVAIL]" in text  # Update Available

    @pytest.mark.asyncio
    async def test_firmware_handler_classification_labels(self, mock_firmware_data):
        """Verify classification labels are used."""
        from src.tools.firmware import handle_get_firmware_details

        with patch("src.tools.firmware.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_firmware_data

            result = await handle_get_firmware_details({})
            text = result[0].text

            assert "[SEC]" in text  # Security Patch
            assert "[FEAT]" in text  # Feature Release


class TestPaginationPatterns:
    """Test pagination handling across handlers."""

    @pytest.mark.asyncio
    async def test_devices_pagination_indicator(self):
        """Verify devices handler shows pagination indicator when more results exist."""
        from src.tools.devices import handle_get_device_list

        paginated_data = {
            "items": [{"deviceType": "ACCESS_POINT", "deviceName": "AP-01", "status": "ONLINE"}],
            "total": 100,
            "count": 1,
            "next": "cursor_token_123",
        }

        with patch("src.tools.devices.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = paginated_data

            result = await handle_get_device_list({})
            text = result[0].text

            assert "PAGINATED" in text or "More results" in text

    @pytest.mark.asyncio
    async def test_clients_pagination_indicator(self):
        """Verify clients handler shows MORE indicator when paginated."""
        from src.tools.clients import handle_list_all_clients

        paginated_data = {
            "items": [{"macAddress": "AA:BB:CC:DD:EE:01", "type": "Wireless", "status": "Connected"}],
            "total": 100,
            "count": 1,
            "next": "cursor_token_456",
        }

        with patch("src.tools.clients.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = paginated_data

            result = await handle_list_all_clients({})
            text = result[0].text

            assert "[MORE]" in text


class TestEmptyResponsePatterns:
    """Test handler behavior with empty responses."""

    @pytest.mark.asyncio
    async def test_devices_empty_response(self):
        """Verify devices handler handles empty results gracefully."""
        from src.tools.devices import handle_get_device_list

        empty_data = {"items": [], "total": 0, "count": 0}

        with patch("src.tools.devices.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = empty_data

            result = await handle_get_device_list({})

            assert isinstance(result, list)
            assert len(result) == 1
            text = result[0].text
            assert "Total devices: 0" in text

    @pytest.mark.asyncio
    async def test_gateways_empty_no_alert(self):
        """Verify gateways handler doesn't show alert with no offline gateways."""
        from src.tools.gateways import handle_list_gateways

        all_online_data = {
            "items": [{"deviceName": "GW-01", "status": "ONLINE", "deployment": "Clustered", "model": "9004"}],
            "total": 1,
        }

        with patch("src.tools.gateways.call_aruba_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = all_online_data

            result = await handle_list_gateways({})
            text = result[0].text

            # Should not show offline alert
            assert "[ALERT]" not in text or "Offline Gateways" not in text
