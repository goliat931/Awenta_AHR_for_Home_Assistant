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
            # Jeśli dane już przyszły w międzyczasie, nie czekamy
            if mac not in self.data:
                future = self.api._data_futures.setdefault(mac, asyncio.Future())
                if not future.done():
                    futures.append(future)
        
        if futures:
            try:
                # Nie blokuj startu HA dłużej niż 10 sekund
                await asyncio.wait_for(asyncio.gather(*futures), timeout=10.0)
            except asyncio.TimeoutError:
                _LOGGER.warning("Timed out waiting for initial data from Awenta devices. Setup continuing...")
        _LOGGER.debug("Initial data received for all devices")

    def _handle_update(self, mac, data):

        # Serwer Awenta czasem wysyła stan częściowo (widać to po polach
        # update/upd_part/count_parts w API). Podmiana całego słownika
        # (self.data[mac] = data) potrafi więc chwilowo "zgubić" pola takie
        # jak power/recuperation_gear_adv, przez co encje w HA pokazują
        # wentylator jako wyłączony tuż po zmianie prędkości. Scalamy więc
        # nowe dane z tym, co już wiemy, zamiast nadpisywać w całości.
        self.data[mac] = {**self.data.get(mac, {}), **data}

        self.async_set_updated_data(self.data)