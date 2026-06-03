#!/usr/bin/env python3

import json
import urllib.parse
import requests
import hashlib

API_URL = "https://ahr.awenta.pl/api.php"

EMAIL = "goliat931@gmail.com"
PASSWORD = "k7VdGX2NVB8NBFm"

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