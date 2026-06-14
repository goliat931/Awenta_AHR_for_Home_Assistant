import asyncio
import websockets
import json
import logging
import hashlib
import urllib.parse
import ssl

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_URL, WS_URL

_LOGGER = logging.getLogger(__name__)


class AwentaAPI:
    REQUEST_HEADERS = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12)"
    }

    def __init__(self, hass, email, password):

        self.hass = hass
        self.email = email
        self.password = password
        self._sha1_pass = hashlib.sha1(
            self.password.encode("iso-8859-1")
        ).hexdigest()

        self.id_socket = None
        self.key_socket = None

        self.devices = []
        self.listeners = []
        self.ws = {}
        self.last_modes = {}
        self._data_futures = {} # To signal when initial data is received for a MAC
        self._ssl_context = None

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

        # params musi być stringiem JSON wg quick_test.py
        params_str = json.dumps(
            {"model": "Samsung Galaxy (Android 12 S)"},
            separators=(",", ":")
        )

        payload = {
            "action": "version",
            "authorization": {
                "email": self.email,
                "pass": self._sha1_pass,
                "lang": "pl",
            },
            "params": params_str,
        }

        json_payload = json.dumps(payload, separators=(",", ":"))
        body = f"data={urllib.parse.quote_plus(json_payload)}"

        session = async_get_clientsession(self.hass)
        async with session.post(
            API_URL,
            data=body,
            headers=self.REQUEST_HEADERS,
        ) as resp:
            result = await resp.text()
            _LOGGER.debug("Login response: %s", result)

        j = json.loads(result)
        if not j.get("success"):
            raise Exception(f"Login failed: {j.get('msg')}")

        params = j.get("params", {})
        # Mapowanie kluczy z odpowiedzi 'version'
        self.id_socket = params.get("id") or params.get("id_socket") or 1
        self.key_socket = params.get("key")

        if not self.key_socket:
            raise Exception("No socket key received")

    async def list_devices(self):

        payload = {
            "action": "list_devices", # Zmieniono na "list_devices" zgodnie z quick_test.py
            "authorization": {
                "email": self.email,
                "pass": self._sha1_pass,
                "lang": "pl",
            },
            "params": "{}" # Dodano pusty string JSON dla params, zgodnie z quick_test.py
        }

        json_payload = json.dumps(payload, separators=(",", ":"))
        body = f"data={urllib.parse.quote_plus(json_payload)}"

        session = async_get_clientsession(self.hass)
        async with session.post(
            API_URL,
            data=body,
            headers=self.REQUEST_HEADERS,
        ) as resp:
            result = await resp.text()
            _LOGGER.debug("list_devices response: %s", result)

        j = json.loads(result)
        self.devices = j.get("devices") or j.get("params") or []

    async def websocket_loop(self, mac):

        while True:
            try:
                if self._ssl_context is None:
                    # Tworzymy kontekst SSL w executorze, aby nie blokować pętli zdarzeń
                    self._ssl_context = await self.hass.async_add_executor_job(
                        ssl.create_default_context
                    )

                ws = await websockets.connect(
                    WS_URL,
                    ssl=self._ssl_context,
                    additional_headers={"source": "android"},
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

                    # Resolve the future for initial data if it exists
                    if mac in self._data_futures and not self._data_futures[mac].done():
                        self._data_futures[mac].set_result(data)

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