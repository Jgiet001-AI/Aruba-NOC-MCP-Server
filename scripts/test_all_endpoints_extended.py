#!/usr/bin/env python3
"""
Extended Endpoint Tester for Aruba NOC MCP Server

Tests ALL endpoints including those requiring specific device IDs by
discovering real device data first.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


async def run_extended_tests():
    """Run extended tests on all endpoints."""
    from src.config import config
    from src.server import TOOL_HANDLERS
    
    print("=" * 70)
    print("ARUBA NOC MCP SERVER - EXTENDED ENDPOINT TESTER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Get fresh token
    if config.access_token == "your_access_token":
        await config.get_access_token()
        print(f"[AUTH] Token acquired\n")
    
    results = {"passed": [], "failed": []}
    
    # ==================================================================
    # PHASE 1: Discovery - Get real device data
    # ==================================================================
    print("[PHASE 1] Discovering real device data...")
    print("-" * 70)
    
    # Get device list to find real serials
    ap_serial = None
    switch_serial = None
    gateway_serial = None
    site_id = None
    wlan_name = None
    
    try:
        device_result = await TOOL_HANDLERS["get_device_list"]({"limit": 20})
        text = device_result[0].text if device_result else ""
        print(f"[INFO] Got device list response")
        
        # Parse the JSON portion to get real data
        import json
        if "{\n" in text:
            json_str = text[text.index("{\n"):]
            data = json.loads(json_str)
            for device in data.get("items", []):
                dtype = device.get("deviceType")
                serial = device.get("serialNumber")
                site = device.get("siteId")
                
                if dtype == "ACCESS_POINT" and not ap_serial:
                    ap_serial = serial
                    print(f"    Found AP: {serial}")
                elif dtype == "SWITCH" and not switch_serial:
                    switch_serial = serial
                    print(f"    Found Switch: {serial}")
                elif dtype == "GATEWAY" and not gateway_serial:
                    gateway_serial = serial
                    print(f"    Found Gateway: {serial}")
                
                if site and not site_id:
                    site_id = site
                    print(f"    Found Site ID: {site}")
    except Exception as e:
        print(f"[ERR] Failed to get device list: {e}")
    
    # Get WLAN names
    try:
        wlan_result = await TOOL_HANDLERS["list_wlans"]({"limit": 5})
        text = wlan_result[0].text if wlan_result else ""
        if "{\n" in text:
            import json
            json_str = text[text.index("{\n"):]
            data = json.loads(json_str)
            for wlan in data.get("items", []):
                name = wlan.get("essid") or wlan.get("name") or wlan.get("wlanName")
                if name:
                    wlan_name = name
                    print(f"    Found WLAN: {name}")
                    break
    except Exception as e:
        print(f"[WARN] Failed to get WLANs: {e}")
    
    print()
    
    # ==================================================================
    # PHASE 2: Test endpoints with discovered data
    # ==================================================================
    print("[PHASE 2] Testing endpoints with real device data...")
    print("-" * 70)
    
    # Calculate time range for time-based endpoints
    now = datetime.utcnow()
    start_time = (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Define test cases with discovered data
    test_cases = []
    
    # AP-specific tools
    if ap_serial:
        test_cases.extend([
            ("get_ap_details", {"serial_number": ap_serial}),
            ("get_ap_radios", {"serial": ap_serial}),
            ("get_ap_cpu_utilization", {"serial": ap_serial}),
        ])
    
    # Switch-specific tools
    if switch_serial:
        test_cases.extend([
            ("get_switch_details", {"serial": switch_serial}),
            ("get_switch_interfaces", {"serial": switch_serial}),
        ])
    
    # Gateway-specific tools
    if gateway_serial:
        test_cases.extend([
            ("get_gateway_details", {"serial_number": gateway_serial}),
            ("get_gateway_cpu_utilization", {"serial": gateway_serial}),
            ("get_gateway_uplinks", {"serial": gateway_serial}),
        ])
    
    # Site-specific tools
    if site_id:
        test_cases.extend([
            ("get_site_details", {"site_id": site_id}),
            # Re-test failing endpoints with site_id
            ("list_all_clients", {"site_id": site_id, "limit": 5}),
            ("get_client_trends", {"site_id": site_id, "start_time": start_time, "end_time": end_time}),
            ("get_firewall_sessions", {"site_id": site_id, "limit": 5}),
        ])
    
    # WLAN-specific tools
    if wlan_name:
        test_cases.append(("get_wlan_details", {"wlan_name": wlan_name}))
    
    # Re-test time-based endpoints with proper time ranges
    test_cases.extend([
        ("get_top_aps_by_bandwidth", {"limit": 5}),  # Try without time-range
        ("get_top_clients_by_usage", {"limit": 5}),
        ("list_idps_threats", {"limit": 5, "start_time": start_time, "end_time": end_time}),
    ])
    
    # Run tests
    for tool_name, args in test_cases:
        print(f"\n>>> Testing: {tool_name}")
        print(f"    Args: {args}")
        
        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            print(f"    [ERR] Handler not found")
            results["failed"].append((tool_name, "Handler not found"))
            continue
        
        try:
            result = await handler(args)
            text = result[0].text if result else ""
            
            if "[ERR]" in text or "[ERROR]" in text:
                print(f"    [FAIL] {text[:150]}...")
                results["failed"].append((tool_name, text[:100]))
            else:
                print(f"    [OK] {text[:120].replace(chr(10), ' ')}...")
                results["passed"].append(tool_name)
                
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"    [FAIL] Exception: {error_msg}")
            results["failed"].append((tool_name, error_msg))
    
    # ==================================================================
    # PHASE 3: Summary
    # ==================================================================
    print("\n" + "=" * 70)
    print("EXTENDED TEST SUMMARY")
    print("=" * 70)
    print(f"  PASSED: {len(results['passed'])}")
    print(f"  FAILED: {len(results['failed'])}")
    
    if results["failed"]:
        print("\n[FAILED ENDPOINTS]")
        for name, error in results["failed"]:
            print(f"  - {name}: {error}")
    
    if results["passed"]:
        print(f"\n[PASSED ENDPOINTS] ({len(results['passed'])})")
        for name in results["passed"]:
            print(f"  [OK] {name}")
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_extended_tests())
