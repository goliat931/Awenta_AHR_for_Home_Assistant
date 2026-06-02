# WebSocket API - Awenta HR

## Połączenie

**URL WebSocket:** `wss://ahr.awenta.pl:31990/`  
**URL API (HTTP):** `https://ahr.awenta.pl/api.php`

### Inicjalizacja połączenia

```java
// WebSocket client z biblioteki dev.gustavoavila.websocketclient
URI websocketURI = new URI("wss://ahr.awenta.pl:31990/");
WebSocketClient webSocketClient = new WebSocketClient(websocketURI) {
    @Override
    public void onTextReceived(String message) { ... }
    @Override
    public void onBinaryReceived(byte[] data) { ... }
    @Override
    public void onCloseReceived() { ... }
    @Override
    public void onException(Exception e) { ... }
};

// Konfiguracja
webSocketClient.setConnectTimeout(10000); // 10 sekund
webSocketClient.addHeader("source", "android");
webSocketClient.enableAutomaticReconnection(5000); // Reconnect co 5s

// Połączenie
webSocketClient.connect();
```

## Wysyłanie wiadomości

Wszystkie wiadomości wysyłane do serwera są w formacie **JSON**.

### Struktura każdej wiadomości

```json
{
    "act": "ACTION_NAME",
    "key": "SOCKET_KEY",
    "id": SOCKET_ID,
    "mac": "DEVICE_MAC",
    "level": VALUE,
    ...
}
```

**Pola wymagane:**
- `act` - akcja (string)
- `key` - klucz sesji WebSocket (string)
- `id` - ID sesji (integer)
- `mac` - adres MAC urządzenia (string)

### Obsługiwane akcje

| Akcja | Parametry | Opis |
|-------|-----------|------|
| `send_power_on` | `mac`, `key`, `id` | Włączenie urządzenia |
| `send_power_off` | `mac`, `key`, `id` | Wyłączenie urządzenia |
| `send_gear_number` | `mac`, `key`, `id`, `level` | Ustawienie poziomu wentylacji (0-9?) |
| `send_work_mode` | `mac`, `key`, `id`, `level` | Ustawienie trybu pracy |
| `send_higro_level` | `mac`, `key`, `id`, `level` | Ustawienie poziomu wilgotności (0-3?) |
| `send_timer_level` | `mac`, `key`, `id`, `level` | Ustawienie poziomu timera |

### Przykłady wiadomości

#### Włączenie urządzenia
```json
{
    "act": "send_power_on",
    "key": "xxxxx",
    "id": 123,
    "mac": "AA:BB:CC:DD:EE:FF"
}
```

#### Wyłączenie urządzenia
```json
{
    "act": "send_power_off",
    "key": "xxxxx",
    "id": 123,
    "mac": "AA:BB:CC:DD:EE:FF"
}
```

#### Ustawienie poziomu wentylacji
```json
{
    "act": "send_gear_number",
    "key": "xxxxx",
    "id": 123,
    "mac": "AA:BB:CC:DD:EE:FF",
    "level": 3
}
```

#### Ustawienie trybu pracy
```json
{
    "act": "send_work_mode",
    "key": "xxxxx",
    "id": 123,
    "mac": "AA:BB:CC:DD:EE:FF",
    "level": 1
}
```

#### Ustawienie poziomu wilgotności
```json
{
    "act": "send_higro_level",
    "key": "xxxxx",
    "id": 123,
    "mac": "AA:BB:CC:DD:EE:FF",
    "level": 2
}
```

#### Ustawienie timera
```json
{
    "act": "send_timer_level",
    "key": "xxxxx",
    "id": 123,
    "mac": "AA:BB:CC:DD:EE:FF",
    "level": 5
}
```

## Odbieranie wiadomości

Serwer wysyła wiadomości JSON zawierające stan urządzenia.

### Struktura odpowiedzi

```json
{
    "update": false,
    "upd_part": 0,
    "count_parts": 0,
    "data_valid": true,
    "power": true,
    "ht_level": 2,
    "timer_level": 0,
    "time_rtc": 1704067200,
    "master_slave_mode": false,
    "recuperation_gear_adv": 2,
    "temperature_master": 22.5,
    "humidity_sensor": 45.5,
    "temperature_sensor": 21.0,
    "humidity_master": 50.0,
    "mode": 1,
    "option": 0,
    "night_en": false,
    "sync_recuperation_adv": false,
    "sync_recuperation_master": false,
    "time_filter_time_left": 720,
    "timer_left": 0
}
```

### Pola odpowiedzi

| Pole | Typ | Opis |
|------|-----|------|
| `update` | boolean | Czy trwa aktualizacja oprogramowania |
| `upd_part` | integer | Numer części aktualizacji |
| `count_parts` | integer | Całkowita liczba części aktualizacji |
| `data_valid` | boolean | Czy dane są prawidłowe |
| `power` | boolean | Stan włączenia (true=on, false=off) |
| `ht_level` | integer | Poziom wilgotności (0-3) |
| `timer_level` | integer | Poziom ustawienia timera |
| `time_rtc` | integer | Czas RTC (UNIX timestamp) |
| `master_slave_mode` | boolean | Tryb master/slave |
| `recuperation_gear_adv` | integer | Poziom regeneracji (zaawansowany) |
| `temperature_master` | double | Temperatura urządzenia głównego (°C) |
| `humidity_sensor` | double | Wilgotność z czujnika (%) |
| `temperature_sensor` | double | Temperatura z czujnika (°C) |
| `humidity_master` | double | Wilgotność urządzenia głównego (%) |
| `mode` | integer | Tryb pracy (0=manual, 1=auto, etc.) |
| `option` | integer | Opcja pracy |
| `night_en` | boolean | Czy tryb nocny włączony |
| `sync_recuperation_adv` | boolean | Synchronizacja regeneracji (zaawansowana) |
| `sync_recuperation_master` | boolean | Synchronizacja regeneracji (główna) |
| `time_filter_time_left` | integer | Czas pozostały do wymiany filtru (godziny) |
| `timer_left` | integer | Czas pozostały timera (sekundy) |

## Obsługa zdarzeń WebSocket

### onTextReceived(String message)
Wywoływane gdy serwer wyśle wiadomość tekstową (JSON).

### onBinaryReceived(byte[] data)
Wywoływane gdy serwer wyśle dane binarne.

### onCloseReceived()
Wywoływane gdy połączenie zostanie zamknięte.

### onException(Exception e)
Wywoływane gdy wystąpi błąd połączenia.

## Autoryzacja

Klucz sesji (`key`) i ID sesji (`id`) są pobierane z:
- `ConfigApp.key_socket` - klucz sesji (string)
- `ConfigApp.id_socket` - ID sesji (integer)

Te wartości są ustanawiane podczas logowania poprzez REST API (`https://ahr.awenta.pl/api.php`).

## Nagłówki HTTP

WebSocket klient wysyła nagłówek:
```
source: android
```

## Timeout i reconnection

- **Connect Timeout:** 10000 ms (10 sekund)
- **Automatic Reconnection:** 5000 ms (5 sekund między próbami)

## Biblioteka WebSocket

Aplikacja używa biblioteki `dev.gustavoavila.websocketclient` do obsługi komunikacji WebSocket.

Lokalizacja w kodzie: `smali/dev/gustavoavila/websocketclient/WebSocketClient.smali`

---

# REST API - HTTP

## Punkt końcowy

**Endpoint:** `https://ahr.awenta.pl/api.php`  
**Metoda:** POST  
**Content-Type:** `application/x-www-form-urlencoded`

## Uwierzytelnianie

Każde żądanie wymaga poświadczeń:
- `email` - adres email użytkownika
- `pass` - hasło użytkownika
- `lang` - język ("pl", "en", itp.)

## Format żądania

```
POST /api.php HTTP/1.1
Host: ahr.awenta.pl
Content-Type: application/x-www-form-urlencoded

data={
    "action": "ACTION_NAME",
    "authorization": {
        "email": "user@example.com",
        "pass": "password",
        "lang": "pl"
    },
    "params": {
        ...opcjonalne parametry...
    }
}
```

## Obsługiwane akcje

### version (Login)
Logowanie i pobieranie danych sesji WebSocket.

**Request:**
```json
{
    "action": "version",
    "authorization": {
        "email": "user@example.com",
        "pass": "password",
        "lang": "pl"
    },
    "params": {
        "model": "Samsung Galaxy (Android 12 S)",
        "version": "2025_10_04"
    }
}
```

### getListDevices
Pobieranie listy urządzeń użytkownika.

**Request:**
```json
{
    "action": "getListDevices",
    "authorization": {
        "email": "user@example.com",
        "pass": "password",
        "lang": "pl"
    }
}
```

**Response:**
```json
{
    "devices": [
        {
            "id": "device_id_1",
            "name": "Salon",
            "mac": "AA:BB:CC:DD:EE:FF",
            "model": "AHR-PRO",
            "status": "online",
            "last_seen": 1704067200
        }
    ]
}
```

### setNewNameDevice
Zmiana nazwy urządzenia.

**Request:**
```json
{
    "action": "setNewNameDevice",
    "authorization": {
        "email": "user@example.com",
        "pass": "password",
        "lang": "pl"
    },
    "params": {
        "device_id": "device_id_1",
        "new_name": "Nowa nazwa"
    }
}
```

### deleteDevice
Usunięcie urządzenia z konta.

**Request:**
```json
{
    "action": "deleteDevice",
    "authorization": {
        "email": "user@example.com",
        "pass": "password",
        "lang": "pl"
    },
    "params": {
        "device_id": "device_id_1"
    }
}
```

### addNewDevice
Dodanie nowego urządzenia.

**Request:**
```json
{
    "action": "addNewDevice",
    "authorization": {
        "email": "user@example.com",
        "pass": "password",
        "lang": "pl"
    },
    "params": {
        "mac": "AA:BB:CC:DD:EE:FF",
        "name": "Nowe urządzenie",
        "model": "AHR-PRO"
    }
}
```

### register
Rejestracja nowego konta.

**Request:**
```json
{
    "action": "register",
    "authorization": {
        "email": "newuser@example.com",
        "pass": "password",
        "lang": "pl"
    },
    "params": {
        "model": "Samsung Galaxy (Android 12 S)",
        "version": "2025_10_04"
    }
}
```

### remindpassword
Przypomnienie hasła.

**Request:**
```json
{
    "action": "remindpassword",
    "authorization": {
        "email": "user@example.com",
        "pass": "",
        "lang": "pl"
    },
    "params": {
        "email": "user@example.com"
    }
}
```

### getListUsers (Share)
Pobieranie listy użytkowników z dostępem do urządzenia.

**Request:**
```json
{
    "action": "getListUsers",
    "authorization": {
        "email": "user@example.com",
        "pass": "password",
        "lang": "pl"
    },
    "params": {
        "device_id": "device_id_1"
    }
}
```

### addUser (Share)
Dodanie użytkownika do współdzielenia urządzenia.

**Request:**
```json
{
    "action": "addUser",
    "authorization": {
        "email": "user@example.com",
        "pass": "password",
        "lang": "pl"
    },
    "params": {
        "device_id": "device_id_1",
        "email": "friend@example.com"
    }
}
```

### deleteUser (Share)
Usunięcie użytkownika ze współdzielenia.

**Request:**
```json
{
    "action": "deleteUser",
    "authorization": {
        "email": "user@example.com",
        "pass": "password",
        "lang": "pl"
    },
    "params": {
        "device_id": "device_id_1",
        "user_id": "user_id_to_delete"
    }
}
```

### deleteAccount
Usunięcie konta.

**Request:**
```json
{
    "action": "deleteAccount",
    "authorization": {
        "email": "user@example.com",
        "pass": "password",
        "lang": "pl"
    }
}
```

## Parametry HTTP

| Parametr | Typ | Opis |
|----------|-----|------|
| `data` | string | Zakodowany JSON z żądaniem (URL-encoded) |

## Timeout

- **Connect Timeout:** 20 000 ms (20 sekund)
- **Read Timeout:** 40 000 ms (40 sekund)

## Obsługa błędów

Odpowiedzi mogą zawierać pola błędu:
- `error` - opis błędu
- `code` - kod błędu
- `message` - komunikat dla użytkownika

Przykład odpowiedzi z błędem:
```json
{
    "error": true,
    "code": 401,
    "message": "Unauthorized"
}
```
