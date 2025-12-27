#!/usr/bin/env python3
"""
Comprehensive Endpoint Tester for Aruba NOC MCP Server

Tests all registered tools/endpoints using the credentials from .env

Usage:
    python scripts/test_all_endpoints.py
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()


async def test_all_endpoints():
    """Test all endpoints and report results."""
    from src.config import config
    
    print("=" * 70)
    print("ARUBA NOC MCP SERVER - ENDPOINT TESTER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    # Step 1: Validate configuration
    print("[CONFIG] Checking configuration...")
    print(f"  Base URL: {config.base_url}")
    print(f"  Client ID: {config.client_id[:8]}..." if config.client_id else "  Client ID: NOT SET")
    print(f"  Client Secret: {'*' * 8}..." if config.client_secret else "  Client Secret: NOT SET")
    print(f"  Access Token: {'<placeholder>' if config.access_token == 'your_access_token' else 'SET'}")
    print()
    
    # Step 2: Get fresh access token if needed
    if config.access_token == "your_access_token" or not config.access_token:
        print("[AUTH] Acquiring fresh access token via OAuth2...")
        try:
            token = await config.get_access_token()
            print(f"  [OK] Token acquired: {token[:20]}...")
        except Exception as e:
            print(f"  [ERR] Failed to acquire token: {e}")
            return
    else:
        print(f"[AUTH] Using existing access token: {config.access_token[:20]}...")
    print()
    
    # Import all handlers from server
    from src.server import TOOL_HANDLERS
    
    # Define test cases for each tool
    # Tools are grouped by type:
    # - no_params: Tools that work without any parameters
    # - optional_params: Tools with optional parameters (test with defaults)
    # - required_params: Tools requiring specific parameters (will use sample values)
    
    test_cases = {
        # === NO REQUIRED PARAMS (should work with empty args) ===
        "get_tenant_device_health": {},
        "get_sites_health": {"limit": 5},
        "get_device_list": {"limit": 5},
        "get_device_inventory": {"limit": 5},
        "list_all_clients": {"limit": 5},
        "list_gateways": {"limit": 5},
        "get_firmware_details": {"limit": 5},
        "list_wlans": {"limit": 5},
        "get_client_trends": {"interval": "1hour"},
        "get_top_aps_by_bandwidth": {"limit": 5, "time_range": "24hours"},
        "get_top_clients_by_usage": {"limit": 5, "time_range": "24hours"},
        "list_idps_threats": {"limit": 5},
        "get_firewall_sessions": {"limit": 5},
    }
    
    # Tools that require specific parameters - we'll skip these or use placeholders
    skipped_tools = {
        # These require specific device serial numbers
        "get_switch_details": "Requires: serial",
        "get_ap_details": "Requires: serial_number",
        "get_site_details": "Requires: site_id",
        "get_gateway_details": "Requires: serial_number",
        "get_ap_cpu_utilization": "Requires: serial",
        "get_gateway_cpu_utilization": "Requires: serial",
        "get_ap_radios": "Requires: serial",
        "get_gateway_cluster_info": "Requires: cluster_name",
        "list_gateway_tunnels": "Requires: cluster_name",
        "get_gateway_uplinks": "Requires: serial",
        "get_wlan_details": "Requires: wlan_name",
        "ping_from_ap": "Requires: serial, target",
        "ping_from_gateway": "Requires: serial, target",
        "traceroute_from_ap": "Requires: serial, target",
        "get_async_test_result": "Requires: task_id",
        "get_stack_members": "Requires: stack_id",
        "get_switch_interfaces": "Requires: serial",
    }
    
    # Results tracking
    results = {
        "passed": [],
        "failed": [],
        "skipped": [],
    }
    
    print("[TEST] Testing endpoints...")
    print("-" * 70)
    
    # Test the tools without required params first
    for tool_name, args in test_cases.items():
        print(f"\n>>> Testing: {tool_name}")
        print(f"    Args: {args}")
        
        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            print(f"    [ERR] Handler not found!")
            results["failed"].append((tool_name, "Handler not found"))
            continue
        
        try:
            result = await handler(args)
            # Extract text from TextContent
            if result and hasattr(result[0], 'text'):
                text = result[0].text
                # Check for error indicators
                if "[ERR]" in text or "[ERROR]" in text:
                    print(f"    [FAIL] {text[:200]}...")
                    results["failed"].append((tool_name, text[:100]))
                else:
                    # Show first 150 chars of result
                    preview = text[:150].replace('\n', ' ')
                    print(f"    [OK] {preview}...")
                    results["passed"].append(tool_name)
            else:
                print(f"    [OK] Got response: {type(result)}")
                results["passed"].append(tool_name)
                
        except Exception as e:
            print(f"    [FAIL] Exception: {e}")
            results["failed"].append((tool_name, str(e)))
    
    # Report skipped tools
    print("\n" + "-" * 70)
    print("[SKIPPED] Tools requiring specific parameters:")
    for tool_name, reason in skipped_tools.items():
        print(f"  - {tool_name}: {reason}")
        results["skipped"].append((tool_name, reason))
    
    # Final summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"  PASSED:  {len(results['passed'])}")
    print(f"  FAILED:  {len(results['failed'])}")
    print(f"  SKIPPED: {len(results['skipped'])}")
    print(f"  TOTAL:   {len(TOOL_HANDLERS)}")
    print()
    
    if results["failed"]:
        print("[FAILED ENDPOINTS]")
        for tool_name, error in results["failed"]:
            print(f"  - {tool_name}: {error[:80]}...")
        print()
    
    if results["passed"]:
        print("[PASSED ENDPOINTS]")
        for tool_name in results["passed"]:
            print(f"  [OK] {tool_name}")
    
    print()
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_all_endpoints())
