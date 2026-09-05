from homeassistant.components.fan import FanEntity, FanEntityFeature

from .entity import AwentaEntity
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):

    data = hass.data[DOMAIN][entry.entry_id]

    api = data["api"]
    coordinator = data["coordinator"]

    entities = []

    for device in api.devices:

        entities.append(
            AwentaFan(coordinator, api, device["mac"], device["name"])
        )

    async_add_entities(entities)


class AwentaFan(AwentaEntity, FanEntity):

    def __init__(self, coordinator, api, mac, name):

        super().__init__(coordinator, api, mac, name)

        self._attr_name = name
        self._attr_unique_id = f"{mac}_fan"
        self._attr_supported_features = FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        self._last_percentage = 33 # Domyślna prędkość startowa (Bieg 1)
        self._attr_speed_count = 3

        # Stan optymistyczny: ustawiany od razu po wysłaniu komendy, żeby HA
        # nie pokazywało wentylatora jako wyłączonego, dopóki nie dotrze
        # (czasem opóźnione o sekundę-dwie) potwierdzenie z urządzenia przez
        # WebSocket. Bez tego trzeba było klikać zmianę prędkości dwa razy.
        self._optimistic_is_on = None
        self._optimistic_percentage = None

    def _handle_coordinator_update(self):
        """Każda świeża wiadomość z urządzenia wygrywa z naszą optymistyczną zgadywanką."""
        self._optimistic_is_on = None
        self._optimistic_percentage = None
        super()._handle_coordinator_update()

    @property
    def is_on(self):
        """Return true if fan is on."""
        if self._optimistic_is_on is not None:
            return self._optimistic_is_on

        data = self.coordinator.data.get(self.mac)
        if data is None:
            return None
        # Zgodnie z WEBSOCKET_API.md status zasilania to pole "power"
        return data.get("power")

    @property
    def percentage(self):
        """Return the current speed percentage."""
        if self._optimistic_percentage is not None:
            return self._optimistic_percentage

        data = self.coordinator.data.get(self.mac)
        if data is None:
            return None

        gear = data.get("recuperation_gear_adv", 0)

        if gear == 0:
            return 0

        return int(gear / 3 * 100)

    async def async_set_percentage(self, percentage):
        if percentage == 0:
            await self.async_turn_off()
            return

        # Zapisujemy prędkość tylko jeśli jest większa od 0
        self._last_percentage = percentage

        # WAŻNE: sprawdzamy to PRZED ustawieniem stanu optymistycznego poniżej,
        # inaczej zawsze wyszłoby "True" (bo sami je za chwilę tak ustawimy).
        was_already_on = bool(self.is_on)

        # Pokaż od razu żądany stan w HA (patrz komentarz w __init__), zanim
        # jeszcze przyjdzie potwierdzenie z urządzenia.
        self._optimistic_is_on = True
        self._optimistic_percentage = percentage
        self.async_write_ha_state()

        # Komendę włączenia wysyłamy TYLKO gdy wentylator faktycznie był
        # wyłączony. Urządzenie potrafi zareagować na "power on" wysłane do
        # już pracującego wentylatora restartem/zgaśnięciem zamiast zmiany
        # biegu - to właśnie powodowało, że np. zmiana z 66% na 33% gasiła
        # wentylator zamiast zmienić prędkość.
        if not was_already_on:
            await self.api.send(self.mac, {"act": "send_power_on"})

            # Jeśli użytkownik ustawiał tryb pracy (select), gdy wentylator był
            # wyłączony, wysyłamy ten tryb teraz przy uruchamianiu.
            if self.mac in self.api.last_modes:
                await self.api.send(
                    self.mac,
                    {
                        "act": "send_work_mode",
                        "mode_nr": self.api.last_modes[self.mac],
                    },
                )

        gear = max(1, min(3, round(percentage / 33)))

        await self.api.send(
            self.mac,
            {
                "act": "send_gear_number",
                "gear_nr": gear,
            },
        )

    async def async_turn_off(self, **kwargs):

        self._optimistic_is_on = False
        self._optimistic_percentage = 0
        self.async_write_ha_state()

        await self.api.send(
            self.mac,
            {
                "act": "send_power_off",
            },
        )

    async def async_turn_on(self, percentage=None, preset_mode=None, **kwargs):
        if percentage is None:
            # Jeśli kliknięto tylko "Włącz", używamy ostatniej prędkości lub domyślnej
            percentage = self._last_percentage or 33

        # Przekazujemy wykonanie do async_set_percentage, 
        # która obsłuży wysłanie power_on oraz gear_number.
        await self.async_set_percentage(percentage)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {"last_percentage": getattr(self, "_last_percentage", None)}