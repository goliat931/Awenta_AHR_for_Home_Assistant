#!/usr/bin/env python3
"""Simple test harness for Awenta AHR API and websocket.

Features:
- Load credentials from `scripts/credentials.json` (example provided)
- REST `login` and `list_devices`
- Connect to websocket and allow sending raw JSON payloads
- Log sent and received frames

Usage: python scripts/test_awenta_api.py --list --ws
"""
import asyncio
import argparse
import json
import os
import sys
from urllib.parse import urlencode

import aiohttp
import websockets

CRED_PATH = os.path.join(os.path.dirname(__file__), "credentials.json")
API_URL = "https://ahr.awenta.pl/api.php"
WS_URL = "wss://ahr.awenta.pl:31990/"


async def login(session, username, password):
    data = {"login": username, "password": password}
    payload = {"data": json.dumps(data)}
    async with session.post(API_URL, data=payload) as resp:
        text = await resp.text()
        return json.loads(text)


async def list_devices(session, key):
    data = {"act": "list_devices", "key": key}
    payload = {"data": json.dumps(data)}
    async with session.post(API_URL, data=payload) as resp:
        text = await resp.text()
        return json.loads(text)


async def websocket_loop(key, device, mac):
    async with websockets.connect(WS_URL, ssl=True) as ws:
        print("Connected to websocket")

        async def reader():
            try:
                async for msg in ws:
                    print("RECV:", msg)
            except Exception as e:
                print("Reader closed:", e)

        rtask = asyncio.create_task(reader())

        try:
            while True:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                # allow sending raw JSON or shorthand actions
                if line.startswith("raw "):
                    payload = json.loads(line[4:])
                else:
                    # try to parse as JSON otherwise
                    try:
                        payload = json.loads(line)
                    except Exception:
                        # interpret as simple commands: on/off/gear N
                        parts = line.split()
                        if parts[0] == "on":
                            payload = {"act": "send_power_on", "key": key, "mac": mac}
                        elif parts[0] == "off":
                            payload = {"act": "send_power_off", "key": key, "mac": mac}
                        elif parts[0] == "gear" and len(parts) > 1:
                            try:
                                lvl = int(parts[1])
                            except Exception:
                                lvl = 0
                            payload = {"act": "send_gear_number", "key": key, "mac": mac, "level": lvl}
                        else:
                            print("Unknown command. Use raw JSON or: on/off/gear N")
                            continue
                # attach id if missing
                if "id" not in payload:
                    payload.setdefault("id", 1)
                if "key" not in payload and key:
                    payload["key"] = key
                if "mac" not in payload and mac:
                    payload["mac"] = mac
                text = json.dumps(payload)
                print("SEND:", text)
                await ws.send(text)
        finally:
            rtask.cancel()
            await asyncio.sleep(0.1)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--ws", action="store_true")
    parser.add_argument("--user")
    parser.add_argument("--password")
    parser.add_argument("--mac")
    parser.add_argument("--raw", help="send a single raw json payload and exit")
    args = parser.parse_args()

    creds = {}
    if os.path.exists(CRED_PATH):
        with open(CRED_PATH, "r", encoding="utf-8") as f:
            try:
                creds = json.load(f)
            except Exception:
                creds = {}

    user = args.user or creds.get("username")
    password = args.password or creds.get("password")
    mac = args.mac or creds.get("mac")

    async with aiohttp.ClientSession() as session:
        key = None
        if user and password:
            print("Logging in as", user)
            resp = await login(session, user, password)
            print("Login response:", resp)
            key = resp.get("key") or resp.get("data", {}).get("key") if isinstance(resp, dict) else None

        if args.list:
            if not key:
                print("Need login key to list devices")
            else:
                devices = await list_devices(session, key)
                print(json.dumps(devices, indent=2, ensure_ascii=False))

        if args.raw:
            if not key:
                print("Warning: sending raw without key attached")
            payload = json.loads(args.raw)
            if "key" not in payload and key:
                payload["key"] = key
            if "mac" not in payload and mac:
                payload["mac"] = mac
            print("Would send:", json.dumps(payload))

        if args.ws:
            if not key:
                print("Connecting without key. You can type raw JSON or commands (on/off/gear N).")
            print("Enter commands (on/off/gear N) or 'raw {json}'")
            await websocket_loop(key, None, mac)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
