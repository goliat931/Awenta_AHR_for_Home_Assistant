from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfTime

from .entity import AwentaEntity
from .const import DOMAIN, KEY_FILTER_TIME_LEFT


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

        entities.append(
            AwentaFilterTimeLeftSensor(coordinator, api, mac, name)
        )

    async_add_entities(entities)


class AwentaTemperatureSensor(AwentaEntity, SensorEntity):

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, api, mac, name):

        super().__init__(coordinator, api, mac, name)

        # Nazwa encji pochodzi z device_class ("Temperatura"/"Temperature"),
        # HA dokleja ją do nazwy urządzenia.
        self._attr_unique_id = f"{mac}_temperature"

    @property
    def native_value(self):

        data = self.device_data

        if data.get("data_valid") and data.get("valid_sensor", True):
            return data.get("temperature_sensor")

        return None


class AwentaHumiditySensor(AwentaEntity, SensorEntity):

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, api, mac, name):

        super().__init__(coordinator, api, mac, name)

        self._attr_unique_id = f"{mac}_humidity"

    @property
    def native_value(self):

        data = self.device_data

        if data.get("data_valid") and data.get("valid_sensor", True):
            return data.get("humidity_sensor")

        return None


class AwentaFilterTimeLeftSensor(AwentaEntity, SensorEntity):
    """Czas do wymiany filtra – ta sama wartość co w aplikacji Awenta (godziny).

    Device class DURATION pozwala w HA przełączyć jednostkę wyświetlania na
    dni (ustawienia encji), a state_class MEASUREMENT daje wykres w historii.
    """

    _attr_translation_key = "filter_time_left"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_suggested_display_precision = 0
    _attr_icon = "mdi:air-filter"

    def __init__(self, coordinator, api, mac, name):

        super().__init__(coordinator, api, mac, name)

        self._attr_unique_id = f"{mac}_filter_time_left"

    @property
    def native_value(self):

        value = self.device_data.get(KEY_FILTER_TIME_LEFT)

        if value is None:
            return None

        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self):

        hours = self.native_value

        if hours is None:
            return None

        return {"days_left": round(hours / 24, 1)}
