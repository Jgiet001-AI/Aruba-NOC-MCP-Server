"""
Site Helper - Automatic site_id extraction for Aruba Central API calls

Many Aruba Central APIs require a site-id parameter. This module provides
helpers to automatically fetch a valid site ID when not provided by the user.
"""

import logging
from functools import lru_cache
from typing import Any

from src.api_client import call_aruba_api

logger = logging.getLogger("aruba-noc-server")

# Cache site ID for 5 minutes to avoid repeated API calls
_cached_site_id: str | None = None
_cache_time: float = 0


async def get_default_site_id() -> str:
    """
    Get a default site ID from the Aruba Central production environment.

    This function attempts multiple strategies to find a valid site ID:
    1. Query sites-health endpoint for first available site
    2. Fallback to devices endpoint and extract siteId from first device
    3. Raise error if no site ID can be found

    Returns:
        str: A valid site ID

    Raises:
        ValueError: If no site ID can be determined
    """
    import time

    global _cached_site_id, _cache_time

    # Return cached value if still valid (5 minute cache)
    if _cached_site_id and (time.time() - _cache_time < 300):
        logger.debug(f"Using cached site ID: {_cached_site_id}")
        return _cached_site_id

    # Strategy 1: Query sites-health endpoint
    try:
        logger.info("Fetching default site ID from sites-health endpoint")
        data = await call_aruba_api("/network-monitoring/v1alpha1/sites-health", params={"limit": 1})

        if data.get("items"):
            site_id = data["items"][0].get("siteId", data["items"][0].get("id"))
            if site_id:
                _cached_site_id = site_id
                _cache_time = time.time()
                logger.info(f"✅ Found site ID from sites-health: {site_id}")
                return site_id

    except Exception as e:
        logger.warning(f"Failed to get site ID from sites-health: {e}")

    # Strategy 2: Fallback to devices endpoint
    try:
        logger.info("Fallback: Fetching site ID from devices endpoint")
        data = await call_aruba_api("/network-monitoring/v1alpha1/devices", params={"limit": 1})

        if data.get("items"):
            site_id = data["items"][0].get("siteId")
            if site_id:
                _cached_site_id = site_id
                _cache_time = time.time()
                logger.info(f"✅ Found site ID from device: {site_id}")
                return site_id

    except Exception as e:
        logger.warning(f"Failed to get site ID from devices: {e}")

    # No site ID found
    raise ValueError(
        "Unable to determine site ID. "
        "Please provide site_id parameter explicitly or ensure devices exist in your environment."
    )


async def get_site_id_for_device(serial: str) -> str:
    """
    Get the site ID for a specific device by its serial number.

    Args:
        serial: Device serial number

    Returns:
        str: Site ID where the device is located

    Raises:
        ValueError: If device not found or has no site ID
    """
    try:
        logger.info(f"Fetching site ID for device: {serial}")

        # Query devices endpoint with filter for this serial
        data = await call_aruba_api("/network-monitoring/v1alpha1/devices", params={"limit": 100})

        # Find device in response
        for device in data.get("items", []):
            if device.get("serialNumber") == serial:
                site_id = device.get("siteId")
                if site_id:
                    logger.info(f"✅ Found site ID for {serial}: {site_id}")
                    return site_id
                else:
                    raise ValueError(f"Device {serial} has no site ID assigned")

        raise ValueError(f"Device with serial {serial} not found")

    except Exception as e:
        logger.error(f"Failed to get site ID for device {serial}: {e}")
        raise


async def ensure_site_id(params: dict[str, Any], device_serial: str | None = None) -> dict[str, Any]:
    """
    Ensure a site-id parameter is present in params, auto-fetching if needed.

    This is a convenience function that modifies params in-place to add site-id
    if it's not already present.

    Args:
        params: API parameters dictionary
        device_serial: Optional device serial to get specific site ID

    Returns:
        dict: Updated params with site-id guaranteed to be present

    Raises:
        ValueError: If site ID cannot be determined
    """
    if "site-id" not in params:
        if device_serial:
            site_id = await get_site_id_for_device(device_serial)
        else:
            site_id = await get_default_site_id()

        params["site-id"] = site_id
        logger.info(f"✅ Auto-added site-id parameter: {site_id}")

    return params


def clear_site_cache():
    """Clear the cached site ID (useful for testing or after config changes)"""
    global _cached_site_id, _cache_time
    _cached_site_id = None
    _cache_time = 0
    logger.info("Site ID cache cleared")
