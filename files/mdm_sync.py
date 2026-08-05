#!/usr/bin/env python3
"""
Standalone MDM sync script.

Usage:
  python3 mdm_sync.py                     # sync all devices
  python3 mdm_sync.py --email user@...    # lookup devices for user
  python3 mdm_sync.py --device <id>       # get device details
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

OAUTH_URL = "https://accounts.zoho.in/oauth/v2/token"
MDM_BASE = "https://mdm.manageengine.in/api/v1/mdm"


def get_access_token():
    client_id = os.environ.get("CLIENT_ID", "").strip()
    client_secret = os.environ.get("CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("REFRESH_TOKEN", "").strip()

    if not all([client_id, client_secret, refresh_token]):
        print("Missing CLIENT_ID, CLIENT_SECRET, or REFRESH_TOKEN in environment")
        sys.exit(1)

    resp = requests.post(OAUTH_URL, data={
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_device_list(access_token):
    resp = requests.get(
        f"{MDM_BASE}/devices",
        headers={"Authorization": f"Zoho-oauthtoken {access_token}"},
    )
    resp.raise_for_status()
    return resp.json()


def get_device_details(access_token, device_id):
    resp = requests.get(
        f"{MDM_BASE}/devices/{device_id}",
        headers={"Authorization": f"Zoho-oauthtoken {access_token}"},
    )
    resp.raise_for_status()
    return resp.json()


def get_user_devices(access_token, email):
    resp = requests.get(
        f"{MDM_BASE}/users/devices",
        headers={"Authorization": f"Zoho-oauthtoken {access_token}"},
        params={"email_id": email},
    )
    resp.raise_for_status()
    return resp.json()


def parse_device_fields(device):
    user_info = device.get("user", {})
    product_name = device.get("product_name", "")
    device_id = device.get("device_id", "")
    raw_serial = (device.get("serial_number") or "").strip()
    udid = device.get("udid", "")
    serial_number = raw_serial or udid or device_id
    manufacturer = "Samsung" if product_name and "SM-" in product_name else ""
    device_type_map = {
        "1": "Mobile Device", "2": "Tablet", "3": "Desktop Computer",
        "4": "iPhone", "5": "Android Phone", "9": "Windows Laptop",
        "10": "macOS Laptop", "11": "Linux Workstation",
    }

    return {
        "device_id": device_id,
        "device_name": device.get("device_name", ""),
        "platform_type": device.get("platform_type", ""),
        "os_version": device.get("os_version", ""),
        "model": device.get("model", ""),
        "product_name": product_name,
        "serial_number": serial_number,
        "udid": udid,
        "owned_by": user_info.get("user_name", "") if user_info else "",
        "user_id": user_info.get("user_id", "") if user_info else "",
        "user_email": user_info.get("user_email", "") if user_info else "",
        "customer_id": device.get("customer_id", ""),
        "managed_status": device.get("managed_status", ""),
        "is_supervised": device.get("is_supervised", False),
        "is_removed": device.get("is_removed", "false"),
        "last_contact_time": device.get("last_contact_time", ""),
        "asset_type": device_type_map.get(str(device.get("device_type", "")), "Mobile Device"),
        "manufacturer": manufacturer,
    }


def sync_devices():
    print("=== MDM Sync ===")
    token = get_access_token()
    print("Access token obtained\n")

    print("Fetching device list...")
    data = get_device_list(token)
    devices = data.get("devices", [])
    if isinstance(devices, dict):
        devices = [devices]
    print(f"Found {len(devices)} device(s)\n")

    for device in devices:
        fields = parse_device_fields(device)
        print(f"--- Device: {fields['device_name']} ---")
        for k, v in fields.items():
            print(f"  {k}: {v}")
        print()

        device_id = fields["device_id"]
        print(f"Fetching details for {device_id}...")
        details = get_device_details(token, device_id)
        registered_time = details.get("registered_time", "")
        added_time = details.get("added_time", "")
        if registered_time:
            reg_date = datetime.fromtimestamp(int(registered_time) / 1000, tz=timezone.utc)
            print(f"  registered_time: {reg_date} ({registered_time})")
        if added_time:
            add_date = datetime.fromtimestamp(int(added_time) / 1000, tz=timezone.utc)
            print(f"  added_time:      {add_date} ({added_time})")
        print()


def main():
    token = get_access_token()

    if "--email" in sys.argv:
        idx = sys.argv.index("--email")
        email = sys.argv[idx + 1]
        print(f"=== Devices for user: {email} ===")
        result = get_user_devices(token, email)
        print(json.dumps(result, indent=2))

    elif "--device" in sys.argv:
        idx = sys.argv.index("--device")
        device_id = sys.argv[idx + 1]
        print(f"=== Device details: {device_id} ===")
        details = get_device_details(token, device_id)
        print(json.dumps(details, indent=2))

    else:
        sync_devices()


if __name__ == "__main__":
    main()
