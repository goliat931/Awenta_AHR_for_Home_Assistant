import asyncio
import json
import logging
import aiohttp

try:
    import optional_module  # pyright: ignore[reportMissingImports]
except ImportError:
    optional_module = None

_LOGGER = logging.getLogger(__name__)

class AwentaAPI:
    """Klient do komunikacji z serwerem Awenta HRV."""

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.base_url = "https://ahr.awenta.pl/api.php"
        self.ws_url = "wss://ahr.awenta.pl:31990/"
        self.session_key = None
        self.session_id = None
        self._ws = None
        self._session = None

    def _get_session(self):
        """Pobierz lub utwórz współdzieloną sesję HTTP."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Zamknij sesję HTTP i WebSocket."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
        if self._ws:
            await self._ws.close()
            self._ws = None

    async def login(self):
        """Logowanie przez REST API w celu uzyskania kluczy sesji."""
        payload = {
            "action": "version",
            "authorization": {
                "email": self.email,
                "pass": self.password,
                "lang": "pl"
            },
            "params": {
                "model": "HomeAssistant (Python 3.12)",
                "version": "2024_HA"
            }
        }
        
        session = self._get_session()
        async with session.post(self.base_url, data={"data": json.dumps(payload)}) as response:
            if response.status != 200:
                _LOGGER.error("Błąd połączenia z API: %s", response.status)
                return False

            data = await response.json()
            if data.get("error"):
                _LOGGER.error("Błąd logowania: %s", data.get("message"))
                return False

                # Pobieramy klucze sesji z odpowiedzi
                # Uwaga: Serwer może zwracać je bezpośrednio lub w zagnieżdżonym obiekcie
                self.session_key = data.get("key_socket") or data.get("params", {}).get("key_socket")
                self.session_id = data.get("id_socket") or data.get("params", {}).get("id_socket")
                
                if not self.session_key:
                    _LOGGER.error("Zalogowano, ale nie otrzymano kluczy WebSocket. Odpowiedź: %s", data)
                    return False
                return True

    async def get_devices(self):
        """Pobieranie listy urządzeń przypisanych do konta."""
        payload = {
            "action": "getListDevices",
            "authorization": {"email": self.email, "pass": self.password, "lang": "pl"}
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, data={"data": json.dumps(payload)}) as response:
                data = await response.json()
                return data.get("devices", [])

    async def listen_websocket(self, device_mac, callback):
        """Połączenie z WebSocketem i nasłuchiwanie na aktualizacje."""
        if not self.session_key:
            await self.login()

        headers = {"source": "android"}
        session = self._get_session()
        
        while True:
            try:
                # Używamy aiohttp do połączenia WebSocket
                async with session.ws_connect(self.ws_url, headers=headers) as websocket:
                    self._ws = websocket
                    _LOGGER.info("Połączono z WebSocket Awenta")
                    
                    async for message in websocket:
                        # W aiohttp dane z wiadomości znajdują się pod atrybutem .data
                        data = json.loads(message.data)
                        mac = data.get("mac")
                        
                        if mac and mac in self._data_futures and not self._data_futures[mac].done():
                            self._data_futures[mac].set_result(True)

                        if callback:
                            callback(data)
                            
                        for listener in self._listeners:
                            listener(mac, data)
            except Exception as e:
                _LOGGER.warning("WebSocket rozłączony (%s). Reconnect za 5s...", e)
                await asyncio.sleep(5)

    async def send_command(self, mac, action, level=None):
        """Wysyłanie komendy do urządzenia."""
        if not self._ws:
            _LOGGER.error("WebSocket nie jest połączony")
            return

        payload = {
            "act": action,
            "key": self.session_key,
            "id": self.session_id,
            "mac": mac
        }
        if level is not None:
            payload["level"] = level

        # Zmiana z send() na send_str() dla aiohttp
        await self._ws.send_str(json.dumps(payload))

    async def send(self, mac, payload_dict):
        """Wysyłanie niestandardowych komend słownikowych używanych w Home Assistant."""
        if not self._ws:
            _LOGGER.error("WebSocket nie jest połączony")
            return

        payload = {
            "key": self.session_key,
            "id": self.session_id,
            "mac": mac
        }
        payload.update(payload_dict)
        
        # Zmiana z send() na send_str() dla aiohttp
        await self._ws.send_str(json.dumps(payload))