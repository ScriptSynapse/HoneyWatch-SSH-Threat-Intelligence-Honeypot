#!/usr/bin/env python3
"""
Quick standalone check that a Kaspersky OpenTIP key works, independent of the
rest of the honeypot/database. Doesn't touch honeypot.db.

Usage:
    export KASPERSKY_OPENTIP_KEY="your_key"
    python3 check_kaspersky_key.py 8.8.8.8
"""
import os
import sys
import json
import requests

KEY = os.environ.get("KASPERSKY_OPENTIP_KEY", "")
ip = sys.argv[1] if len(sys.argv) > 1 else "8.8.8.8"

if not KEY:
    sys.exit("Set KASPERSKY_OPENTIP_KEY first, e.g.:\n"
              "  export KASPERSKY_OPENTIP_KEY='your_key'\n"
              "  python3 check_kaspersky_key.py 8.8.8.8")

r = requests.get(
    "https://opentip.kaspersky.com/api/v1/search/ip",
    headers={"x-api-key": KEY, "Accept": "application/json"},
    params={"request": ip},
    timeout=10,
)

print(f"IP checked:    {ip}")
print(f"HTTP status:   {r.status_code}")

if r.status_code == 200:
    data = r.json()
    print(f"Zone:          {data.get('Zone')}")
    print(f"Categories:    {data.get('Categories')}")
    print("\nFull response:")
    print(json.dumps(data, indent=2)[:2000])
elif r.status_code == 401:
    print("Key rejected (401 Unauthorized) — double-check the key value and that")
    print("it hasn't expired (tokens are requested at https://opentip.kaspersky.com/token).")
elif r.status_code == 403:
    print("403 Forbidden — quota or rate limit exceeded for this key.")
else:
    print("Unexpected response body:")
    print(r.text[:1000])
