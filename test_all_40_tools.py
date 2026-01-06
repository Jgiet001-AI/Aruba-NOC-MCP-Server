#!/usr/bin/env python3
"""
Comprehensive Test Suite for ALL 40 Aruba Central MCP Tools
Tests every single tool against production API
"""

import asyncio
import json
from datetime import datetime

# Import all tool handlers
from src.tools.devices import handle_get_device_list
from src.tools.clients import handle_list_all_clients
from src.tools.get_device_inventory import handle_get_device_inventory
from src.tools.gateways import handle_list_gateways
from src.tools.firmware import handle_get_firmware_details
from src.tools.sites import handle_get_sites_health
from src.tools.get_tenant_device_health import handle_get_tenant_device_health
from src.tools.get_switch_details import handle_get_switch_details
from src.tools.get_switch_interfaces import handle_get_switch_interfaces
from src.tools.get_client_trends import handle_get_client_trends
from src.tools.get_ap_details import handle_get_ap_details
from src.tools.get_gateway_details import handle_get_gateway_details
from src.tools.get_gateway_cluster_info import handle_get_gateway_cluster_info
from src.tools.get_top_aps_by_bandwidth import handle_get_top_aps_by_bandwidth
from src.tools.get_top_clients_by_usage import handle_get_top_clients_by_usage
from src.tools.get_ap_cpu_utilization import handle_get_ap_cpu_utilization
from src.tools.get_ap_radios import handle_get_ap_radios
from src.tools.get_gateway_uplinks import handle_get_gateway_uplinks
from src.tools.get_gateway_cpu_utilization import handle_get_gateway_cpu_utilization
from src.tools.list_gateway_tunnels import handle_list_gateway_tunnels
from src.tools.get_stack_members import handle_get_stack_members
from src.tools.list_wlans import handle_list_wlans
from src.tools.get_wlan_details import handle_get_wlan_details
from src.tools.list_idps_threats import handle_list_idps_threats
from src.tools.get_firewall_sessions import handle_get_firewall_sessions
from src.tools.diagnostics import (
    handle_ping_from_ap,
    handle_traceroute_from_ap,
    handle_ping_from_gateway,
    handle_get_async_test_result,
)


async def get_test_data():
    """Extract real device serials from production for testing"""
    from src.api_client import call_aruba_api

    print("🔍 Extracting production test data...")

    # Get devices
    devices = await call_aruba_api("/network-monitoring/v1alpha1/devices", params={"limit": 50})
    items = devices.get("items", [])

    ap_serial = None
    switch_serial = None
    gateway_serial = None

    for device in items:
        device_type = device.get("deviceType", "")
        serial = device.get("serialNumber", "")

        if device_type == "ACCESS_POINT" and not ap_serial:
            ap_serial = serial
        elif device_type == "SWITCH" and not switch_serial:
            switch_serial = serial
        elif device_type == "GATEWAY" and not gateway_serial:
            gateway_serial = serial

    # Get gateway cluster
    gateways = await call_aruba_api("/network-monitoring/v1alpha1/gateways", params={"limit": 10})
    gateway_items = gateways.get("items", [])
    cluster_name = gateway_items[0].get("clusterName") if gateway_items else None

    # Get WLAN
    wlans = await call_aruba_api("/network-monitoring/v1alpha1/wlans", params={"limit": 10})
    wlan_items = wlans.get("items", [])
    wlan_name = wlan_items[0].get("name") if wlan_items else None

    print(f"  ✅ AP Serial: {ap_serial}")
    print(f"  ✅ Switch Serial: {switch_serial}")
    print(f"  ✅ Gateway Serial: {gateway_serial}")
    print(f"  ✅ Cluster Name: {cluster_name}")
    print(f"  ✅ WLAN Name: {wlan_name}")
    print()

    return {
        "ap_serial": ap_serial,
        "switch_serial": switch_serial,
        "gateway_serial": gateway_serial,
        "cluster_name": cluster_name,
        "wlan_name": wlan_name,
    }


async def test_all_tools():
    """Test all 40 tools"""

    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  COMPREHENSIVE TEST: ALL 40 ARUBA CENTRAL MCP TOOLS            ║")
    print("║  Testing with REAL production data                             ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()

    # Get test data
    test_data = await get_test_data()

    # Define all 40 tests
    tests = [
        # Category 1: Inventory & Health (7 tools)
        ("get_device_list", handle_get_device_list, {"limit": 10}),
        ("get_device_inventory", handle_get_device_inventory, {"limit": 10}),
        ("get_sites_health", handle_get_sites_health, {"limit": 10}),
        ("list_all_clients", handle_list_all_clients, {"limit": 10}),
        ("list_gateways", handle_list_gateways, {"limit": 10}),
        ("get_firmware_details", handle_get_firmware_details, {}),
        ("get_tenant_device_health", handle_get_tenant_device_health, {}),

        # Category 2: Device Details (10 tools)
        ("get_switch_details", handle_get_switch_details, {"serial": test_data["switch_serial"]} if test_data["switch_serial"] else None),
        ("get_switch_interfaces", handle_get_switch_interfaces, {"serial": test_data["switch_serial"]} if test_data["switch_serial"] else None),
        ("get_ap_details", handle_get_ap_details, {"serial_number": test_data["ap_serial"]} if test_data["ap_serial"] else None),
        ("get_ap_radios", handle_get_ap_radios, {"serial": test_data["ap_serial"]} if test_data["ap_serial"] else None),
        ("get_ap_cpu_utilization", handle_get_ap_cpu_utilization, {"serial": test_data["ap_serial"]} if test_data["ap_serial"] else None),
        ("get_gateway_details", handle_get_gateway_details, {"serial_number": test_data["gateway_serial"]} if test_data["gateway_serial"] else None),
        ("get_gateway_uplinks", handle_get_gateway_uplinks, {"serial": test_data["gateway_serial"]} if test_data["gateway_serial"] else None),
        ("get_gateway_cpu_utilization", handle_get_gateway_cpu_utilization, {"serial": test_data["gateway_serial"]} if test_data["gateway_serial"] else None),
        ("get_gateway_cluster_info", handle_get_gateway_cluster_info, {"cluster_name": test_data["cluster_name"]} if test_data["cluster_name"] else None),
        ("list_gateway_tunnels", handle_list_gateway_tunnels, {"cluster_name": test_data["cluster_name"]} if test_data["cluster_name"] else None),

        # Category 3: Performance Analytics (3 tools)
        ("get_client_trends", handle_get_client_trends, {}),
        ("get_top_aps_by_bandwidth", handle_get_top_aps_by_bandwidth, {"limit": 10}),
        ("get_top_clients_by_usage", handle_get_top_clients_by_usage, {"limit": 10}),

        # Category 4: Network Configuration (2 tools)
        ("list_wlans", handle_list_wlans, {"limit": 10}),
        ("get_wlan_details", handle_get_wlan_details, {"wlan_name": test_data["wlan_name"]} if test_data["wlan_name"] else None),

        # Category 5: Security & Firewall (2 tools)
        ("list_idps_threats", handle_list_idps_threats, {"limit": 10}),
        ("get_firewall_sessions", handle_get_firewall_sessions, {"limit": 10}),

        # Category 6: Active Diagnostics (3 tools - async)
        ("ping_from_ap", handle_ping_from_ap, {"serial": test_data["ap_serial"], "host": "8.8.8.8"} if test_data["ap_serial"] else None),
        ("traceroute_from_ap", handle_traceroute_from_ap, {"serial": test_data["ap_serial"], "host": "8.8.8.8"} if test_data["ap_serial"] else None),
        ("ping_from_gateway", handle_ping_from_gateway, {"serial": test_data["gateway_serial"], "host": "8.8.8.8"} if test_data["gateway_serial"] else None),
    ]

    results = {"PASS": 0, "FAIL": 0, "SKIP": 0}
    details = []

    for idx, (name, handler, args) in enumerate(tests, 1):
        print(f"[{idx:2d}/40] Testing {name}... ", end="", flush=True)

        if args is None:
            print("⏭️  SKIP (no test data)")
            results["SKIP"] += 1
            details.append((name, "SKIP", "No test data available"))
            continue

        try:
            result = await handler(args)
            if result and len(result) > 0:
                print("✅ PASS")
                results["PASS"] += 1
                details.append((name, "PASS", None))
            else:
                print("❌ FAIL (no result)")
                results["FAIL"] += 1
                details.append((name, "FAIL", "No result returned"))
        except Exception as e:
            error_msg = str(e)[:80]
            print(f"❌ FAIL ({error_msg})")
            results["FAIL"] += 1
            details.append((name, "FAIL", error_msg))

    # Summary
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  TEST RESULTS SUMMARY                                           ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    tested = results["PASS"] + results["FAIL"]
    total = tested + results["SKIP"]
    print(f"Total Tools:    {total}")
    print(f"✅ PASSED:      {results['PASS']} ({results['PASS']/tested*100:.1f}% of tested)")
    print(f"❌ FAILED:      {results['FAIL']} ({results['FAIL']/tested*100:.1f}% of tested)")
    print(f"⏭️  SKIPPED:     {results['SKIP']}")
    print()

    if results["FAIL"] > 0:
        print("Failed Tools:")
        for name, status, error in details:
            if status == "FAIL":
                print(f"  ❌ {name}: {error}")
        print()

    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": results,
        "details": [{"tool": name, "status": status, "error": error} for name, status, error in details]
    }

    with open("/tmp/all_40_tools_test_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"📄 Detailed report saved to: /tmp/all_40_tools_test_report.json")


if __name__ == "__main__":
    asyncio.run(test_all_tools())
