import asyncio
import json
import os
from api import AwentaAPI

async def test_integration():
    # 1. Wczytaj poświadczenia
    creds_path = os.path.join(os.path.dirname(__file__), "scripts", "credentials.json")
    with open(creds_path, "r") as f:
        creds = json.load(f)

    api = AwentaAPI(creds["email"], creds["password"])

    print(f"--- Logowanie dla: {creds['email']} ---")
    if await api.login():
        print(f"SUKCES: Zalogowano. Key: {api.session_key}, ID: {api.session_id}")
    else:
        print("BŁĄD: Logowanie nieudane. Sprawdź e-mail/hasło.")
        return

    print("\n--- Pobieranie listy urządzeń ---")
    devices = await api.get_devices()
    if devices:
        for dev in devices:
            print(f"Znaleziono: {dev.get('name')} (MAC: {dev.get('mac')}) - Status: {dev.get('status')}")
            if dev.get('mac') == creds['mac']:
                print(">> To urządzenie zgadza się z Twoim credentials.json!")
    else:
        print("BŁĄD: Nie znaleziono żadnych urządzeń na tym koncie.")

    print("\n--- Próba połączenia WebSocket (nasłuch przez 10s) ---")
    def update_callback(data):
        print(f"Odebrano dane z WS: {json.dumps(data, indent=2)}")

    try:
        # Uruchamiamy nasłuchiwanie w tle
        task = asyncio.create_task(api.listen_websocket(creds['mac'], update_callback))
        print("Połączono. Czekam na dane...")
        await asyncio.sleep(10)
        task.cancel()
        print("\nTest zakończony pomyślnie.")
    except Exception as e:
        print(f"BŁĄD WebSocket: {e}")

if __name__ == "__main__":
    asyncio.run(test_integration())