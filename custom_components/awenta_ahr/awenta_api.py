import asyncio
import websockets
import json
import logging
import aiohttp

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_URL, WS_URL

_LOGGER = logging.getLogger(__name__)


class AwentaAPI:

    def __init__(self, hass, email, password):

        self.hass = hass
        self.email = email
        self.password = password

        self.id_socket = None
        self.key_socket = None

        self.devices = []
        self.listeners = []
        self.ws = {}
        self._data_futures = {} # To signal when initial data is received for a MAC

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
        """Logowanie do API. Używamy parametrów identycznych jak w działającym skrypcie."""
        headers = {
            "source": "android",
            "User-Agent": "okhttp/4.9.1"
        }

        payload = {
            "action": "version",
            "authorization": {
                "email": self.email,
                "pass": self.password,
                "lang": "pl",
            },
            "params": {
                "model": "Samsung Galaxy (Android 12 S)",
                "version": "2025_10_04"
            },
        }

        session = async_get_clientsession(self.hass)
        async with session.post(API_URL, json=payload, headers=headers) as resp:
            result = await resp.text()
            _LOGGER.debug("Login response: %s", result)

        j = json.loads(result)
        if not j.get("success"):
            _LOGGER.error("Błąd logowania Awenta: %s", j.get("msg", "Nieznany błąd"))
            raise Exception(f"Login failed: {j.get('msg')}")

        params = j.get("params", {})

        self.id_socket = params.get("id_socket") or params.get("id") or j.get("id") or 1
        self.key_socket = params.get("key_socket") or params.get("key") or j.get("key")

        if not self.key_socket:
            _LOGGER.error("Zalogowano, ale nie otrzymano klucza WebSocket")
            raise Exception("No socket key received")

    async def list_devices(self):

        payload = {
            "action": "getListDevices",
            "authorization": {
                "email": self.email,
                "pass": self.password,
                "lang": "pl",
            },
        }

        headers = {"User-Agent": "okhttp/4.9.1"}
        session = async_get_clientsession(self.hass)

        async with session.post(API_URL, json=payload, headers=headers) as resp:
            result = await resp.text()
            _LOGGER.debug("List devices response: %s", result)

        j = json.loads(result)

        if not j.get("success") and "devices" not in j and "params" not in j:
            _LOGGER.error("Błąd pobierania listy urządzeń: %s", j.get("msg"))
            raise Exception("Failed to list devices")

        # Sprawdzamy oba możliwe klucze, gdzie mogą być urządzenia
        self.devices = j.get("devices") or j.get("params") or []
        _LOGGER.info("Znaleziono %d urządzeń Awenta", len(self.devices))

    async def websocket_loop(self, mac):

        while True:
            try:
                ws = await websockets.connect(
                    WS_URL,
                    ssl=True,
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