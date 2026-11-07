import logging

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN
from .awenta_api import AwentaAPI, AwentaAuthError, AwentaError

_LOGGER = logging.getLogger(__name__)


DATA_SCHEMA = vol.Schema(
    {
        vol.Required("email"): str,
        vol.Required("password"): str,
    }
)


async def _validate(hass, email, password):
    """Sprawdź dane logowania w chmurze Awenta. Zwraca kod błędu albo None."""
    api = AwentaAPI(hass, email, password)
    try:
        await api.login()
    except AwentaAuthError:
        return "invalid_auth"
    except AwentaError:
        return "cannot_connect"
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Unexpected error while validating Awenta credentials")
        return "unknown"
    return None


class AwentaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(self, user_input=None):

        errors = {}

        if user_input is not None:

            await self.async_set_unique_id(user_input["email"])
            self._abort_if_unique_id_configured()

            error = await _validate(
                self.hass, user_input["email"], user_input["password"]
            )

            if error is None:
                return self.async_create_entry(
                    title=f"Awenta HRV ({user_input['email']})",
                    data=user_input,
                )

            errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data):
        """Wywoływane, gdy hasło przestało działać (ConfigEntryAuthFailed)."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):

        errors = {}
        entry = self._get_reauth_entry()

        if user_input is not None:

            error = await _validate(
                self.hass, entry.data["email"], user_input["password"]
            )

            if error is None:
                return self.async_update_reload_and_abort(
                    entry,
                    data={**entry.data, "password": user_input["password"]},
                )

            errors["base"] = error

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required("password"): str}),
            description_placeholders={"email": entry.data["email"]},
            errors=errors,
        )
