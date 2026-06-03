import logging
import asyncio

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class AwentaCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, api):

        super().__init__(
            hass,
            _LOGGER,
            name="awenta",
            update_interval=None,
        )

        self.api = api
        self.data = {}

        self.api.register_listener(self._handle_update)

    async def async_wait_for_initial_data(self):
        """Wait for the first data update for all devices."""
        _LOGGER.debug("Waiting for initial data for %d devices", len(self.api.devices))
        futures = []
        for device in self.api.devices:
            mac = device["mac"]
            future = asyncio.Future()
            self.api._data_futures[mac] = future
            futures.append(future)
        await asyncio.gather(*futures)
        _LOGGER.debug("Initial data received for all devices")

    def _handle_update(self, mac, data):

        self.data[mac] = data

        self.async_set_updated_data(self.data)