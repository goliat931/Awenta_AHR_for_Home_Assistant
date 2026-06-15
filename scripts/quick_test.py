#!/usr/bin/env python3

import json
import urllib.parse
import requests
import hashlib
import os
import sys

API_URL = "https://ahr.awenta.pl/api.php"

EMAIL = os.environ.get("AWENTA_EMAIL")
PASSWORD = os.environ.get("AWENTA_PASSWORD")

if not EMAIL or not PASSWORD:
    print("Error: AWENTA_EMAIL and AWENTA_PASSWORD environment variables must be set.")
    sys.exit(1)

SHA1_PASSWORD = hashlib.sha1(
    PASSWORD.encode("iso-8859-1")
).hexdigest()

payload = {
    "action": "list_devices",
    "authorization": {
        "email": EMAIL,
        "pass": SHA1_PASSWORD,
        "lang": "pl"
    },
    "params": "{}"
}

json_payload = json.dumps(payload, separators=(",", ":"))

body = "data=" + urllib.parse.quote_plus(json_payload)

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12)"
}

r = requests.post(
    API_URL,
    data=body,
    headers=headers,
    timeout=30
)

print("STATUS:", r.status_code)
print()
print(r.text)

try:
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
except:
    pass