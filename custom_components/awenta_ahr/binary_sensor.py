from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)

from .entity import AwentaEntity
from .const import DOMAIN, KEY_FILTER_TIME_LEFT


async def async_setup_entry(hass, entry, async_add_entities):

    data = hass.data[DOMAIN][entry.entry_id]

    api = data["api"]
    coordinator = data["coordinator"]

    async_add_entities(
        AwentaFilterReplaceBinarySensor(
            coordinator, api, device["mac"], device["name"]
        )
        for device in api.devices
    )


class AwentaFilterReplaceBinarySensor(AwentaEntity, BinarySensorEntity):
    """Włączony (= problem), gdy licznik filtra zszedł do zera.

    To ten sam moment, w którym rekuperator zaczyna mrugać na czerwono –
    łatwo zrobić z tego automatyzację z powiadomieniem.
    """

    _attr_translation_key = "filter_replace"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:air-filter"

    def __init__(self, coordinator, api, mac, name):

        super().__init__(coordinator, api, mac, name)

        self._attr_unique_id = f"{mac}_filter_replace"

    @property
    def is_on(self):

        value = self.device_data.get(KEY_FILTER_TIME_LEFT)

        if value is None:
            return None

        try:
            return int(value) <= 0
        except (TypeError, ValueError):
            return None
