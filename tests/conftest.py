"""
Pytest configuration and shared fixtures for Aruba NOC MCP Server tests.
"""

import os
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Automatically mock environment variables for all tests."""
    with patch.dict(os.environ, {
        "ARUBA_BASE_URL": "https://test.api.central.arubanetworks.com",
        "ARUBA_CLIENT_ID": "test_client_id",
        "ARUBA_CLIENT_SECRET": "test_client_secret",
        "ARUBA_ACCESS_TOKEN": "test_access_token",
    }):
        yield


@pytest.fixture
def mock_api_response() -> dict[str, Any]:
    """Standard mock API response structure."""
    return {
        "items": [],
        "total": 0,
        "count": 0,
    }


@pytest.fixture
def mock_devices_response() -> dict[str, Any]:
    """Mock response for devices API."""
    return {
        "items": [
            {
                "deviceType": "ACCESS_POINT",
                "deviceName": "AP-Floor1-01",
                "serialNumber": "CN12345678",
                "status": "ONLINE",
                "model": "AP-515",
                "siteId": "site-001",
                "siteName": "HQ Building",
                "deployment": "Standalone",
            },
            {
                "deviceType": "SWITCH",
                "deviceName": "SW-Core-01",
                "serialNumber": "SN98765432",
                "status": "ONLINE",
                "model": "6300M",
                "siteId": "site-001",
                "siteName": "HQ Building",
                "deployment": "Clustered",
            },
        ],
        "total": 2,
        "count": 2,
    }


@pytest.fixture
def mock_clients_response() -> dict[str, Any]:
    """Mock response for clients API."""
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


@pytest.fixture
def mock_sites_health_response() -> dict[str, Any]:
    """Mock response for sites health API."""
    return {
        "items": [
            {
                "siteId": "site-001",
                "siteName": "HQ Building",
                "overallHealth": "Good",
                "deviceCount": 10,
                "clientCount": 50,
                "alertCount": 0,
            },
            {
                "siteId": "site-002",
                "siteName": "Branch Office",
                "overallHealth": "Fair",
                "deviceCount": 5,
                "clientCount": 20,
                "alertCount": 3,
            },
        ],
        "total": 2,
    }


@pytest.fixture
def mock_gateways_response() -> dict[str, Any]:
    """Mock response for gateways API."""
    return {
        "items": [
            {
                "deviceName": "GW-Main",
                "serialNumber": "GW12345678",
                "status": "ONLINE",
                "model": "9004",
                "deployment": "Clustered",
                "siteName": "HQ Building",
            },
            {
                "deviceName": "GW-Branch",
                "serialNumber": "GW87654321",
                "status": "OFFLINE",
                "model": "7005",
                "deployment": "Standalone",
                "siteName": "Branch Office",
            },
        ],
        "total": 2,
        "count": 2,
    }


@pytest.fixture
def mock_firmware_response() -> dict[str, Any]:
    """Mock response for firmware API."""
    return {
        "items": [
            {
                "deviceName": "AP-Floor1-01",
                "serialNumber": "CN12345678",
                "deviceType": "ACCESS_POINT",
                "softwareVersion": "8.10.0.0",
                "recommendedVersion": "8.11.0.0",
                "upgradeStatus": "Update Available",
                "firmwareClassification": "Feature Release",
            },
            {
                "deviceName": "SW-Core-01",
                "serialNumber": "SN98765432",
                "deviceType": "SWITCH",
                "softwareVersion": "10.10.1010",
                "recommendedVersion": "10.10.1010",
                "upgradeStatus": "Up To Date",
                "firmwareClassification": "Security Patch",
            },
        ],
        "total": 2,
    }


@pytest.fixture
def mock_call_aruba_api():
    """Fixture to mock the call_aruba_api function."""
    with patch("src.api_client.call_aruba_api") as mock:
        mock.return_value = AsyncMock(return_value={"items": [], "total": 0})
        yield mock
