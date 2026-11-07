import logging

from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import DOMAIN, PLATFORMS
from .awenta_api import AwentaAPI, AwentaAuthError, AwentaError
from .coordinator import AwentaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry):

    hass.data.setdefault(DOMAIN, {})

    email = entry.data["email"]
    password = entry.data["password"]

    api = AwentaAPI(hass, email, password)

    try:
        await api.start()
    except AwentaAuthError as err:
        # HA pokaże "wymagane ponowne uwierzytelnienie" zamiast cichego błędu.
        raise ConfigEntryAuthFailed(str(err)) from err
    except AwentaError as err:
        # Serwer chwilowo niedostępny -> HA sam ponowi próbę później.
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = AwentaCoordinator(hass, api)

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    await coordinator.async_wait_for_initial_data()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass, entry):

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )

    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data["api"].stop()

    return unload_ok
