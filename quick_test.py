#!/usr/bin/env python3
"""Quick Production Test - Test all 30 tools"""
import asyncio
import sys
sys.path.insert(0, '/app')

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
from src.tools.list_gateway_tunnels import handle_list_gateway_tunnels
from src.tools.get_stack_members import handle_get_stack_members
from src.tools.list_wlans import handle_list_wlans
from src.tools.get_wlan_details import handle_get_wlan_details
from src.tools.list_idps_threats import handle_list_idps_threats
from src.tools.get_site_details import handle_get_site_details
from src.tools.ping_from_ap import handle_ping_from_ap
from src.tools.ping_from_gateway import handle_ping_from_gateway
from src.tools.traceroute_from_ap import handle_traceroute_from_ap
from src.tools.get_async_test_result import handle_get_async_test_result
from src.api_client import call_aruba_api

async def get_test_data():
    print("Extracting test data...")
    devices = await call_aruba_api("/network-monitoring/v1alpha1/devices", params={"limit": 50})
    items = devices.get("items", [])

    ap = switch = None
    for d in items:
        dt = d.get("deviceType", "")
        sn = d.get("serialNumber", "")
        if dt == "ACCESS_POINT" and not ap:
            ap = sn
        elif dt == "SWITCH" and not switch:
            switch = sn

    # ✅ FIX: Get gateway from gateways endpoint (not devices endpoint)
    gws = await call_aruba_api("/network-monitoring/v1alpha1/gateways", params={"limit": 10})
    gw_items = gws.get("items", [])
    gateway = gw_items[0].get("serialNumber") if gw_items else None
    cluster = gw_items[0].get("clusterName") if gw_items else None

    # ✅ FIX: Use 'wlanName' field instead of 'name'
    wlans = await call_aruba_api("/network-monitoring/v1alpha1/wlans", params={"limit": 10})
    wlan_items = wlans.get("items", [])
    wlan = wlan_items[0].get("wlanName") if wlan_items else None

    # Get site ID for get_site_details
    sites = await call_aruba_api("/network-monitoring/v1alpha1/sites-health", params={"limit": 10})
    site_items = sites.get("items", [])
    site_id = site_items[0].get("siteId") or site_items[0].get("id") if site_items else None

    print(f"AP: {ap}, SW: {switch}, GW: {gateway}, Cluster: {cluster}, WLAN: {wlan}, Site: {site_id}")
    return {"ap": ap, "sw": switch, "gw": gateway, "cluster": cluster, "wlan": wlan, "site": site_id}

async def test():
    print("="*70)
    print("COMPREHENSIVE TEST: ALL 28 ARUBA CENTRAL MCP TOOLS")
    print("="*70)

    td = await get_test_data()

    tests = [
        ("get_device_list", handle_get_device_list, {"limit": 10}),
        ("get_device_inventory", handle_get_device_inventory, {"limit": 10}),
        ("get_sites_health", handle_get_sites_health, {"limit": 10}),
        ("list_all_clients", handle_list_all_clients, {"limit": 10}),
        ("list_gateways", handle_list_gateways, {"limit": 10}),
        ("get_firmware_details", handle_get_firmware_details, {}),
        ("get_tenant_device_health", handle_get_tenant_device_health, {}),
        ("get_switch_details", handle_get_switch_details, {"serial": td["sw"]} if td["sw"] else None),
        ("get_switch_interfaces", handle_get_switch_interfaces, {"serial": td["sw"]} if td["sw"] else None),
        ("get_ap_details", handle_get_ap_details, {"serial_number": td["ap"]} if td["ap"] else None),
        ("get_ap_radios", handle_get_ap_radios, {"serial": td["ap"]} if td["ap"] else None),
        ("get_ap_cpu_utilization", handle_get_ap_cpu_utilization, {"serial": td["ap"]} if td["ap"] else None),
        ("get_gateway_details", handle_get_gateway_details, {"serial_number": td["gw"]} if td["gw"] else None),
        ("get_gateway_uplinks", handle_get_gateway_uplinks, {"serial": td["gw"]} if td["gw"] else None),
        ("get_gateway_cluster_info", handle_get_gateway_cluster_info, {"cluster_name": td["cluster"]} if td["cluster"] else None),
        ("list_gateway_tunnels", handle_list_gateway_tunnels, {"cluster_name": td["cluster"]} if td["cluster"] else None),
        ("get_client_trends", handle_get_client_trends, {}),
        ("get_top_aps_by_bandwidth", handle_get_top_aps_by_bandwidth, {"limit": 10}),
        ("get_top_clients_by_usage", handle_get_top_clients_by_usage, {"limit": 10}),
        ("list_wlans", handle_list_wlans, {"limit": 10}),
        ("get_wlan_details", handle_get_wlan_details, {"wlan_name": td["wlan"]} if td["wlan"] else None),
        ("list_idps_threats", handle_list_idps_threats, {"limit": 10}),
        ("get_site_details", handle_get_site_details, {"site_id": td["site"]} if td["site"] else None),
        ("get_stack_members", handle_get_stack_members, {"serial": td["sw"]} if td["sw"] else None),
        ("ping_from_ap", handle_ping_from_ap, {"serial": td["ap"], "host": "8.8.8.8"} if td["ap"] else None),
        ("ping_from_gateway", handle_ping_from_gateway, {"serial": td["gw"], "host": "8.8.8.8"} if td["gw"] else None),
        ("traceroute_from_ap", handle_traceroute_from_ap, {"serial": td["ap"], "host": "8.8.8.8"} if td["ap"] else None),
        ("get_async_test_result", handle_get_async_test_result, None),  # Requires task_id from previous async operation
    ]

    p = f = s = 0
    fails = []

    for idx, (name, handler, args) in enumerate(tests, 1):
        print(f"[{idx:2d}/28] {name}...", end=" ", flush=True)

        if args is None:
            print("SKIP")
            s += 1
            continue

        try:
            result = await handler(args)
            if result and len(result) > 0:
                print("PASS")
                p += 1
            else:
                print("FAIL (no result)")
                f += 1
                fails.append(name)
        except Exception as e:
            err = str(e)[:50]
            print(f"FAIL ({err})")
            f += 1
            fails.append(f"{name}: {err}")

    print()
    print("="*70)
    print("RESULTS")
    print("="*70)
    tested = p + f
    print(f"Total: {p+f+s}, Tested: {tested}")
    print(f"PASS: {p} ({p/tested*100:.1f}%)")
    print(f"FAIL: {f} ({f/tested*100:.1f}%)")
    print(f"SKIP: {s}")

    if fails:
        print("\nFailed:")
        for fail in fails:
            print(f"  - {fail}")

if __name__ == "__main__":
    asyncio.run(test())
