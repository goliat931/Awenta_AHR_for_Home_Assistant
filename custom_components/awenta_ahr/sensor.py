from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature, PERCENTAGE

from .entity import AwentaEntity
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):

    data = hass.data[DOMAIN][entry.entry_id]

    api = data["api"]
    coordinator = data["coordinator"]

    entities = []

    for device in api.devices:

        mac = device["mac"]
        name = device["name"]

        entities.append(
            AwentaTemperatureSensor(coordinator, api, mac, name)
        )

        entities.append(
            AwentaHumiditySensor(coordinator, api, mac, name)
        )

    async_add_entities(entities)


class AwentaTemperatureSensor(AwentaEntity, SensorEntity):

    def __init__(self, coordinator, api, mac, name):

        super().__init__(coordinator, api, mac, name)

        self._attr_name = f"{name} Temperature"
        self._attr_unique_id = f"{mac}_temperature"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self):

        data = self.coordinator.data.get(self.mac, {})

        if data.get("data_valid") and data.get("valid_sensor", True):
            return data.get("temperature_sensor")

        return None


class AwentaHumiditySensor(AwentaEntity, SensorEntity):

    def __init__(self, coordinator, api, mac, name):

        super().__init__(coordinator, api, mac, name)

        self._attr_name = f"{name} Humidity"
        self._attr_unique_id = f"{mac}_humidity"
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self):

        data = self.coordinator.data.get(self.mac, {})

        if data.get("data_valid") and data.get("valid_sensor", True):
            return data.get("humidity_sensor")

        return None