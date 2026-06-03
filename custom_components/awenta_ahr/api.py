import asyncio
import json
import logging
import aiohttp
import websockets

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
        
        async with aiohttp.ClientSession() as session:
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
        
        while True:
            try:
                async with websockets.connect(self.ws_url, additional_headers=headers) as websocket:
                    self._ws = websocket
                    _LOGGER.info("Połączono z WebSocket Awenta")
                    
                    async for message in websocket:
                        data = json.loads(message)
                        # Przekazujemy dane do encji HA przez callback
                        callback(data)
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

        await self._ws.send(json.dumps(payload))