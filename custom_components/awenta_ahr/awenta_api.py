import asyncio
import websockets
import hashlib
import json
import urllib.parse
import aiohttp

from .const import API_URL, WS_URL


class AwentaAPI:

    def __init__(self, hass, email, password):

        self.hass = hass
        self.email = email
        self.password = password

        self.sha1 = None
        self.id_socket = None
        self.key_socket = None

        self.devices = []
        self.listeners = []
        self.ws = {}

    def register_listener(self, callback):
        self.listeners.append(callback)

    async def start(self):

        await self.login()
        await self.list_devices()

        for device in self.devices:
            self.hass.async_create_task(
                self.websocket_loop(device["mac"])
            )

    async def login(self):

        self.sha1 = hashlib.sha1(self.password.encode()).hexdigest()

        payload = {
            "action": "version",
            "authorization": {
                "email": self.email,
                "pass": self.sha1,
                "lang": "pl",
            },
            "params": json.dumps({"model": "HA"}),
        }

        data = {"data": json.dumps(payload)}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                API_URL,
                data=urllib.parse.urlencode(data),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as resp:
                result = await resp.text()

        j = json.loads(result)

        self.id_socket = j["params"]["id"]
        self.key_socket = j["params"]["key"]

    async def list_devices(self):

        payload = {
            "action": "list_devices",
            "authorization": {
                "email": self.email,
                "pass": self.sha1,
                "lang": "pl",
            },
            "params": "{}",
        }

        data = {"data": json.dumps(payload)}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                API_URL,
                data=urllib.parse.urlencode(data),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as resp:
                result = await resp.text()

        j = json.loads(result)

        self.devices = j["params"]

    async def websocket_loop(self, mac):

        while True:

            try:

                ws = await websockets.connect(
                    WS_URL,
                    extra_headers={"source": "android"},
                )

                self.ws[mac] = ws

                join = {
                    "act": "join",
                    "id": self.id_socket,
                    "key": self.key_socket,
                    "mac": mac,
                }

                await ws.send(json.dumps(join))

                while True:

                    msg = await ws.recv()
                    data = json.loads(msg)

                    for callback in self.listeners:
                        callback(mac, data)

            except Exception:

                await asyncio.sleep(5)

    async def send(self, mac, payload):

        ws = self.ws.get(mac)

        if not ws:
            return

        payload["id"] = self.id_socket
        payload["key"] = self.key_socket
        payload["mac"] = mac

        await ws.send(json.dumps(payload))