#!/usr/bin/env python3
import asyncio
import argparse
import json
import os
import sys
import urllib.parse
import hashlib

import aiohttp
import websockets

CRED_PATH = os.path.join(os.path.dirname(__file__), "credentials.json")
API_URL = "https://ahr.awenta.pl/api.php"
WS_URL = "wss://ahr.awenta.pl:31990/"


async def login(session, username, password):
    sha1_password = hashlib.sha1(
        password.encode("iso-8859-1")
    ).hexdigest()

    payload = {
        "action": "version",
        "authorization": {
            "email": username,
            "pass": sha1_password,
            "lang": "pl"
        },
        "params": json.dumps(
            {"model": "Samsung Galaxy (Android 12 S)"},
            separators=(",", ":")
        )
    }
    json_payload = json.dumps(payload, separators=(",", ":"))
    data = f"data={urllib.parse.quote_plus(json_payload)}"
    
    async with session.post(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12)"
        }
    ) as resp:
        text = await resp.text()
        print("Login raw response:", text)
        return json.loads(text)


async def websocket_loop(key, socket_id, mac):
    async with websockets.connect(WS_URL, ssl=True, additional_headers={"source": "android"}) as ws:
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
                                lvl = 2
                            payload = {"act": "send_gear_number", "gear_nr": lvl}
                        elif parts[0] == "mode" and len(parts) > 1:
                            try:
                                lvl = int(parts[1])
                            except Exception:
                                lvl = 1
                            payload = {"act": "send_work_mode", "mode_nr": lvl}
                        else:
                            print("Unknown command. Use: on / off / gear N / mode N / raw {json}")
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
    parser.add_argument("--ws", action="store_true")
    parser.add_argument("--user")
    parser.add_argument("--password")
    parser.add_argument("--mac")
    parser.add_argument("--on", action="store_true", help="Włącz wentylator")
    parser.add_argument("--off", action="store_true", help="Wyłącz wentylator")
    parser.add_argument("--gear", type=int, help="Ustaw bieg (1-3)")
    parser.add_argument("--mode", type=int, help="Ustaw tryb (0-2)")
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
        print("Brak danych logowania.")
        return

    async with aiohttp.ClientSession() as session:
        print("Logging in as", user)
        resp = await login(session, user, password)

        if not resp.get("success"):
            print("Login failed:", resp)
            return

        params = resp.get("params", {})
        key = params.get("key")
        socket_id = params.get("id", 1)
        print(f"key={key}, id={socket_id}")

        if args.ws:
            if not mac:
                print("Brak MAC.")
                return
            print("Enter commands: on / off / gear N / mode N / raw {json}")
            await websocket_loop(key, socket_id, mac)
        else:
            # Tryb sterowania bezpośredniego z CLI
            payload = None
            if args.on: payload = {"act": "send_power_on"}
            elif args.off: payload = {"act": "send_power_off"}
            elif args.gear is not None: payload = {"act": "send_gear_number", "gear_nr": args.gear}
            elif args.mode is not None: payload = {"act": "send_work_mode", "mode_nr": args.mode}

            if payload:
                if not mac:
                    print("Brak MAC.")
                    return
                payload.update({"id": socket_id, "key": key, "mac": mac})
                
                async with websockets.connect(WS_URL, ssl=True, additional_headers={"source": "android"}) as ws:
                    # Dołącz do sesji urządzenia
                    join = {"act": "join", "id": socket_id, "key": key, "mac": mac}
                    await ws.send(json.dumps(join))
                    
                    # Wyślij komendę
                    text = json.dumps(payload)
                    print("SEND:", text)
                    await ws.send(text)
                    # Poczekaj chwilę na przetworzenie przed zamknięciem
                    await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass