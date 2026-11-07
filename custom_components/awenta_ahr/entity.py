from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, MANUFACTURER, MODEL


class AwentaEntity(CoordinatorEntity):

    _attr_has_entity_name = True

    def __init__(self, coordinator, api, mac, name):

        super().__init__(coordinator)

        self.api = api
        self.mac = mac
        self.device_name = name

    @property
    def device_data(self):
        """Ostatni znany stan urządzenia (ramka z WebSocket)."""
        return (self.coordinator.data or {}).get(self.mac, {})

    @property
    def available(self):
        """Encja dostępna tylko gdy mamy połączenie i jakiekolwiek dane."""
        return (
            super().available
            and self.mac in (self.coordinator.data or {})
            and bool(self.api.is_connected(self.mac))
        )

    @property
    def device_info(self):

        return DeviceInfo(
            identifiers={(DOMAIN, self.mac)},
            name=self.device_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            connections={("mac", self.mac)},
        )
