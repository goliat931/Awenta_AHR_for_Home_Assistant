import asyncio
import websockets
import json
import logging
import hashlib
import urllib.parse

import aiohttp

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util.ssl import client_context

from .const import API_URL, WS_URL

_LOGGER = logging.getLogger(__name__)


class AwentaError(Exception):
    """Base error of the Awenta cloud API."""


class AwentaAuthError(AwentaError):
    """Wrong e-mail/password or no socket key returned by the server."""


class AwentaConnectionError(AwentaError):
    """Server unreachable or returned something that is not JSON."""


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
        self._tasks = []
        self._connected = set()  # MAC-i z aktywnym połączeniem WebSocket
        self._stopping = False

    def register_listener(self, callback):
        self.listeners.append(callback)

    async def start(self):

        await self.login()
        await self.list_devices()

        self._stopping = False
        for device in self.devices:
            self._tasks.append(
                self.hass.async_create_background_task(
                    self.websocket_loop(device["mac"]),
                    f"awenta_ahr websocket {device['mac']}",
                )
            )

    async def stop(self):
        """Zamknij wszystkie połączenia WebSocket (przy unload/reload integracji).

        Wcześniej pętle WebSocket działały w nieskończoność także po usunięciu
        lub przeładowaniu integracji, więc każde przeładowanie dokładało kolejne
        połączenia do serwera Awenta.
        """
        self._stopping = True
        for task in self._tasks:
            task.cancel()
        for ws in list(self.ws.values()):
            try:
                await ws.close()
            except Exception:  # noqa: BLE001
                pass
        for task in self._tasks:
            try:
                await task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
        self._tasks.clear()
        self.ws.clear()
        self._connected.clear()

    def is_connected(self, mac):
        """Czy mamy aktywne połączenie WebSocket z danym urządzeniem."""
        return mac in self._connected

    def _notify(self, mac, data):
        for callback in self.listeners:
            callback(mac, data)

    async def _request(self, action: str, params_str: str = "{}"):
        payload = {
            "action": action,
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
        try:
            async with session.post(
                API_URL,
                data=body,
                headers=self.REQUEST_HEADERS,
            ) as resp:
                result = await resp.text()
                _LOGGER.debug("%s response: %s", action, result)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise AwentaConnectionError(f"Cannot connect to Awenta server: {err}") from err

        try:
            return json.loads(result)
        except ValueError as err:
            raise AwentaConnectionError(f"Invalid response from Awenta server: {result!r}") from err

    async def login(self):

        # params musi być stringiem JSON wg quick_test.py
        params_str = json.dumps(
            {"model": "Samsung Galaxy (Android 12 S)"},
            separators=(",", ":")
        )

        j = await self._request("version", params_str)

        if not j.get("success"):
            raise AwentaAuthError(f"Login failed: {j.get('msg')}")

        params = j.get("params", {})
        # Mapowanie kluczy z odpowiedzi 'version'
        self.id_socket = params.get("id") or params.get("id_socket") or 1
        self.key_socket = params.get("key")

        if not self.key_socket:
            raise AwentaAuthError("No socket key received")

    async def list_devices(self):

        j = await self._request("list_devices", "{}")
        self.devices = j.get("devices") or j.get("params") or []

    async def websocket_loop(self, mac):

        while not self._stopping:
            ws = None
            try:
                if self._ssl_context is None:
                    self._ssl_context = client_context()

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
                self._connected.add(mac)

                while True:

                    msg = await ws.recv()
                    data = json.loads(msg)

                    # Resolve the future for initial data if it exists
                    if mac in self._data_futures and not self._data_futures[mac].done():
                        self._data_futures[mac].set_result(data)

                    if not isinstance(data, dict):
                        continue

                    self._notify(mac, data)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                if self._stopping:
                    break
                _LOGGER.warning("Error in websocket loop for %s: %s", mac, e)
            finally:
                was_connected = mac in self._connected
                self._connected.discard(mac)
                self.ws.pop(mac, None)
                if ws is not None:
                    try:
                        await ws.close()
                    except Exception:  # noqa: BLE001
                        pass
                if was_connected and not self._stopping:
                    # Pusta aktualizacja -> encje przeliczą "available".
                    self._notify(mac, {})

            if not self._stopping:
                await asyncio.sleep(5)

    async def send(self, mac, payload):

        ws = self.ws.get(mac)

        if not ws:
            return

        payload["id"] = self.id_socket
        payload["key"] = self.key_socket
        payload["mac"] = mac

        await ws.send(json.dumps(payload))