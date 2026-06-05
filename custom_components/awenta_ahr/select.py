from homeassistant.components.select import SelectEntity

from .entity import AwentaEntity
from .const import DOMAIN


MODE_MAP = {
    "Recuperation": 2,
    "Supply": 1,
    "Extract": 0,
}

MODE_MAP_REV = {v: k for k, v in MODE_MAP.items()}


async def async_setup_entry(hass, entry, async_add_entities):

    data = hass.data[DOMAIN][entry.entry_id]

    api = data["api"]
    coordinator = data["coordinator"]

    entities = []

    for device in api.devices:

        entities.append(
            AwentaModeSelect(coordinator, api, device["mac"], device["name"])
        )

    async_add_entities(entities)


class AwentaModeSelect(AwentaEntity, SelectEntity):

    def __init__(self, coordinator, api, mac, name):

        super().__init__(coordinator, api, mac, name)

        self._attr_name = f"{name} Mode"
        self._attr_unique_id = f"{mac}_mode"
        self._attr_options = list(MODE_MAP.keys())

    @property
    def current_option(self):
        data = self.coordinator.data.get(self.mac, {})

        # Jeśli urządzenie jest wyłączone, priorytetyzujemy tryb zapamiętany lokalnie
        if not data.get("power") and self.mac in self.api.last_modes:
            return MODE_MAP_REV.get(self.api.last_modes[self.mac])

        mode = data.get("mode")
        return MODE_MAP_REV.get(mode)

    async def async_select_option(self, option):
        mode_nr = MODE_MAP[option]
        self.api.last_modes[self.mac] = mode_nr

        await self.api.send(
            self.mac,
            {
                "act": "send_work_mode",
                "mode_nr": mode_nr,
            },
        )

        self.async_write_ha_state()