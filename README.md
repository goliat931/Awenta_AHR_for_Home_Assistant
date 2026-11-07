# Integracja Awenta HRV dla Home Assistant

Profesjonalna integracja umożliwiająca pełne sterowanie i monitorowanie rekuperatorów marki **Awenta** serii HRV z poziomu systemu Home Assistant. 

*Autorem oryginalnego projektu jest **MateiiK**.*

---

## Główne Funkcjonalności

Integracja zapewnia dwukierunkową komunikację z urządzeniem, co pozwala na:

### 1. Sterowanie wentylacją (Entity: Fan)
*   **Włączanie/Wyłączanie:** Pełna kontrola nad stanem zasilania jednostki.
*   **Regulacja prędkości:** Obsługa 3 stopni prędkości (Niska, Średnia, Wysoka), mapowanych na procentowe wartości w Home Assistant (33%, 66%, 100%).
*   **Pamięć stanu:** Przywracanie ostatnio używanej prędkości po ponownym włączeniu.

### 2. Monitorowanie parametrów (Entities: Sensor)
*   **Temperatura:** Odczyt temperatury z czujnika jednostki w czasie rzeczywistym.
*   **Wilgotność:** Odczyt poziomu wilgotności powietrza.
*   **Status danych:** Inteligentne sprawdzanie poprawności danych (`data_valid`) oraz statusu czujników, co zapobiega wyświetlaniu błędnych odczytów (np. 0°C), gdy czujnik jest offline.

### 3. Stan filtra (Entities: Sensor + Binary sensor)
*   **Czas do wymiany filtra** (`sensor.<urządzenie>_czas_do_wymiany_filtra`): ta sama wartość, którą aplikacja Awenta pokazuje jako stan filtra, w godzinach (np. `2160 h`). Atrybut `days_left` podaje wartość w dniach, a w ustawieniach encji można zmienić jednostkę wyświetlania np. na dni.
*   **Wymiana filtra** (`binary_sensor.<urządzenie>_wymiana_filtra`, klasa *problem*): włącza się, gdy licznik zejdzie do 0 – to ten sam moment, w którym rekuperator zaczyna mrugać na czerwono.

Przykładowa automatyzacja z powiadomieniem:

```yaml
automation:
  - alias: "Rekuperator – wymień filtr"
    triggers:
      - trigger: state
        entity_id: binary_sensor.rekuperator_wymiana_filtra
        to: "on"
    actions:
      - action: notify.notify
        data:
          message: "Czas wymienić filtr w rekuperatorze Awenta."
```

> Kasowanie licznika po wymianie filtra robi się na urządzeniu / w aplikacji Awenta – komenda resetu nie jest (jeszcze) znana z API, więc integracja jej nie wysyła.

### 4. Zarządzanie trybami pracy (Entity: Select)
Możliwość szybkiego przełączania między zdefiniowanymi trybami pracy urządzenia:
*   **Recuperation (Odzysk ciepła):** Standardowy tryb pracy zrównoważonej.
*   **Supply (Nawiew):** Praca wyłącznie wentylatora nawiewnego.
*   **Extract (Wywiew):** Praca wyłącznie wentylatora wywiewnego.

### 5. Technologia Cloud-Push
W przeciwieństwie do standardowych integracji opartych na odpytywaniu (polling), to rozwiązanie wykorzystuje:
*   **REST API:** Do bezpiecznego logowania i autoryzacji sesji.
*   **WebSocket:** Do natychmiastowego odbierania powiadomień o zmianie stanu urządzenia. Każda zmiana parametrów na panelu fizycznym lub w aplikacji mobilnej jest widoczna w Home Assistant bez opóźnień.
*   **Dostępność:** gdy połączenie WebSocket z urządzeniem zostanie zerwane, encje przechodzą w stan *niedostępny* zamiast pokazywać nieaktualne dane.
*   **Obsługa błędów logowania:** złe hasło jest wykrywane już przy dodawaniu integracji, a gdy hasło przestanie działać, Home Assistant poprosi o ponowne zalogowanie (reauth). Chwilowa niedostępność serwera Awenta nie psuje konfiguracji – HA sam ponawia próbę.

---

## Instalacja

### Metoda 1: HACS (Zalecana)
1.  Przejdź do **HACS** → **Integracje**.
2.  Kliknij trzy kropki w prawym górnym rogu i wybierz **Niestandardowe repozytoria**.
3.  Wklej URL: `<https://github.com/MateiiK/awenta_ha>` i wybierz kategorię **Integracja**.
4.  Zainstaluj komponent i zrestartuj Home Assistant.

### Metoda 2: Instalacja ręczna
1.  Pobierz archiwum ZIP z repozytorium.
2.  Wypakuj zawartość do folderu `/config/custom_components/awenta_ahr`.
3.  Zrestartuj Home Assistant.

---

## Konfiguracja

Po zainstalowaniu integracji:
1.  Przejdź do **Ustawienia** → **Urządzenia oraz usługi** → **Dodaj integrację**.
2.  Wyszukaj **Awenta HRV**.
3.  Zaloguj się przy użyciu swojego adresu e-mail oraz hasła do aplikacji Awenta Pro.
4.  Integracja automatycznie wykryje wszystkie urządzenia przypisane do Twojego konta.

---

## Architektura projektu

*   **`awenta_api.py`**: Rdzeń komunikacyjny obsługujący sesje i gniazda WebSocket.
*   **`coordinator.py`**: Zarządza przepływem danych i zapewnia natychmiastowe odświeżanie encji po otrzymaniu ramki JSON.
*   **`fan.py` / `sensor.py` / `select.py`**: Implementacje specyficznych encji Home Assistant.

---

## Wsparcie i Rozwój

Jeśli integracja jest dla Ciebie użyteczna, możesz wesprzeć autora oryginału:

[!Buy Me A Coffee](https://www.buymeacoffee.com/MateiK)

---

## Licencja
Projekt udostępniany na licencji MIT. Więcej szczegółów w pliku LICENSE.