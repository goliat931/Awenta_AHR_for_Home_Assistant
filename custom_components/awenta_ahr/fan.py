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

    @property
    def is_on(self):
        """Return true if fan is on."""
        data = self.coordinator.data.get(self.mac)
        if data is None:
            return None
        # Zgodnie z WEBSOCKET_API.md status zasilania to pole "power"
        return data.get("power")

    @property
    def percentage(self):
        """Return the current speed percentage."""
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

        # Zawsze wysyłamy komendę włączenia przy ustawianiu prędkości > 0.
        # Zapewnia to, że urządzenie ruszy nawet jeśli stan 'power' w HA 
        # nie zdążył się jeszcze zaktualizować (stale state).
        await self.api.send(self.mac, {"act": "send_power_on"})

        gear = max(1, min(3, round(percentage / 33)))

        await self.api.send(
            self.mac,
            {
                "act": "send_gear_number",
                "gear_nr": gear,
            },
        )

    async def async_turn_off(self, **kwargs):

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