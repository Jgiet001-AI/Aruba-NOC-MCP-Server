#!/usr/bin/env python3
"""
Test Connection - Verify Aruba Central API connectivity

This script tests the connection to Aruba Central API by:
1. Loading credentials from .env
2. Generating an access token (if using client credentials)
3. Making a simple API call to verify connectivity
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from src.config import ArubaConfig
from src.api_client import call_aruba_api


async def test_connection():
    """Test connection to Aruba Central API"""
    print("=" * 60)
    print("Aruba Central API Connection Test")
    print("=" * 60)

    # Load environment variables
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    # Check configuration
    print("\n📋 Configuration Check:")
    print(f"  Base URL: {os.getenv('ARUBA_BASE_URL', 'Not set (will use default)')}")
    print(f"  Client ID: {'✓ Set' if os.getenv('ARUBA_CLIENT_ID') else '✗ Not set'}")
    print(f"  Client Secret: {'✓ Set' if os.getenv('ARUBA_CLIENT_SECRET') else '✗ Not set'}")
    print(f"  Access Token: {'✓ Set' if os.getenv('ARUBA_ACCESS_TOKEN') else '✗ Not set'}")

    # Initialize config
    print("\n🔧 Initializing configuration...")
    try:
        config = ArubaConfig()
        print("  ✓ Configuration loaded")
    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        return False

    # Test token generation/validation
    print("\n🔐 Testing authentication...")
    try:
        if not config.access_token:
            print("  → Generating access token from client credentials...")
            await config.get_access_token()
        print(f"  ✓ Access token available (length: {len(config.access_token)})")
    except Exception as e:
        print(f"  ✗ Authentication error: {e}")
        return False

    # Test API connectivity
    print("\n🌐 Testing API connectivity...")
    try:
        # Try to list devices (minimal request)
        result = await call_aruba_api(
            config,
            "/monitoring/v2/devices",
            params={"limit": 1, "offset": 0},
        )
        print("  ✓ API connection successful!")

        if "total" in result:
            print(f"  📊 Total devices in Central: {result['total']}")
        elif "devices" in result:
            print(f"  📊 Devices returned: {len(result['devices'])}")

    except Exception as e:
        print(f"  ✗ API error: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ Connection test PASSED")
    print("=" * 60)
    return True


async def main():
    """Main entry point"""
    try:
        success = await test_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
