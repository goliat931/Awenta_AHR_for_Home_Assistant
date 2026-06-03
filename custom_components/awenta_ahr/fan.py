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
        self._attr_speed_count = 3

    @property
    def is_on(self):

        data = self.coordinator.data.get(self.mac, {})
        return data.get("recuperation_gear_adv", 0) > 0

    @property
    def percentage(self):

        gear = self.coordinator.data.get(self.mac, {}).get(
            "recuperation_gear_adv", 0
        )

        if gear == 0:
            return 0

        return int(gear / 3 * 100)

    async def async_set_percentage(self, percentage):
        self._last_percentage = percentage

        if percentage == 0:
            await self.async_turn_off()
            return

        gear = max(1, min(3, round(percentage / 33)))

        await self.api.send(
            self.mac,
            {
                "act": "send_gear_number",
                "level": gear,
            },
        )

    async def async_turn_off(self, **kwargs):

        await self.api.send(
            self.mac,
            {
                "act": "send_power_off",
            },
        )

    async def async_turn_on(self, percentage=None, **kwargs):
        if percentage is None:
            # If no percentage is given, try to restore last known percentage
            # or just send a generic power on command.
            if getattr(self, "_last_percentage", None):
                await self.async_set_percentage(self._last_percentage)
                return
            await self.api.send(
                self.mac,
                {
                    "act": "send_power_on",
                },
            )
            return

        # If percentage is given, delegate to async_set_percentage
        await self.async_set_percentage(percentage)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {"last_percentage": getattr(self, "_last_percentage", None)}