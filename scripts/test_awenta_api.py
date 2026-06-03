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
import urllib.parse
import sys

import aiohttp
import websockets

CRED_PATH = os.path.join(os.path.dirname(__file__), "credentials.json")
API_URL = "https://ahr.awenta.pl/api.php"
WS_URL = "wss://ahr.awenta.pl:31990/"

# Use source header only for websocket connection
WS_HEADERS = {"source": "android"}
REST_HEADERS = {"User-Agent": "okhttp/4.9.1"}


async def login(session, username, password):
    payload = {
        "action": "version",
        "authorization": {
            "email": username,
            "pass": password, # Zgodnie z WEBSOCKET_API.md, hasło w postaci jawnego tekstu
            "lang": "pl"
        },
        "params": {
            "model": "Samsung Galaxy (Android 12 S)",
            "version": "2025_10_04"
        }
    }
    # We send raw JSON body because form-urlencoded crashes this specific server
    async with session.post(API_URL, json=payload, headers=REST_HEADERS) as resp:
        text = await resp.text()
        if "Fatal error" in text:
            print("SERVER CRASH: Form-data encoding is not supported by this endpoint.")
        return json.loads(text)


async def list_devices(session, username, password):
    """Używa formatu akcji z dokumentacji REST API."""
    payload = {
        "action": "getListDevices",
        "authorization": {
            "email": username,
            "pass": password, # Zgodnie z WEBSOCKET_API.md, hasło w postaci jawnego tekstu
            "lang": "pl"
        }
    }
    async with session.post(API_URL, json=payload, headers=REST_HEADERS) as resp:
        result = await resp.text()
        print("List devices raw response:", result)
        return json.loads(result)


async def websocket_loop(key, socket_id, mac):
    async with websockets.connect(WS_URL, ssl=True, extra_headers=WS_HEADERS) as ws:
        print("Connected to websocket")

        join = {"act": "join", "id": socket_id, "key": key, "mac": mac}
        await ws.send(json.dumps(join))
        print("Sent join:", join)

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

                if line.startswith("raw "):
                    payload = json.loads(line[4:])
                else:
                    try:
                        payload = json.loads(line)
                    except Exception:
                        parts = line.split()
                        if parts[0] == "on":
                            payload = {"act": "send_power_on"}
                        elif parts[0] == "off":
                            payload = {"act": "send_power_off"}
                        elif parts[0] == "gear" and len(parts) > 1:
                            try:
                                lvl = int(parts[1])
                            except Exception:
                                lvl = 1
                            payload = {"act": "send_gear_number", "level": lvl}
                        else:
                            print("Unknown command. Use: on / off / gear N / raw {json}")
                            continue

                payload.setdefault("id", socket_id)
                payload.setdefault("key", key)
                payload.setdefault("mac", mac)

                text = json.dumps(payload)
                print("SEND:", text)
                await ws.send(text)
        finally:
            rtask.cancel()
            await asyncio.sleep(0.1)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="List devices")
    parser.add_argument("--ws", action="store_true", help="Open interactive websocket")
    parser.add_argument("--user")
    parser.add_argument("--password")
    parser.add_argument("--mac")
    args = parser.parse_args()

    creds = {}
    if os.path.exists(CRED_PATH):
        with open(CRED_PATH, "r", encoding="utf-8") as f:
            try:
                creds = json.load(f)
            except Exception:
                creds = {}

    user = args.user or creds.get("email")
    password = args.password or creds.get("password")
    mac = args.mac or creds.get("mac")

    if not user or not password:
        print("Brak danych logowania. Podaj --user i --password lub ustaw credentials.json")
        return

    async with aiohttp.ClientSession() as session:
        print("Logging in as", user)
        resp = await login(session, user, password)
        print("Login response:", resp)

        key = None
        socket_id = 1

        if resp.get("success"):
            params = resp.get("params", {})
            key = params.get("key_socket") or params.get("key") or resp.get("key")
            socket_id = params.get("id_socket") or params.get("id") or resp.get("id") or 1
            print(f"key={key}, id={socket_id}")
        else:
            print("Login failed:", resp)
            return

        if args.list:
            devices = await list_devices(session, user, password)
            print(json.dumps(devices, indent=2, ensure_ascii=False))

        if args.ws:
            if not mac:
                print("Brak MAC — podaj --mac lub ustaw w credentials.json")
                return
            print("Enter commands: on / off / gear N / raw {json}")
            await websocket_loop(key, socket_id, mac)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass