"""Config flow per Emmeti AQ-IoT."""
import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EmmetiApiClient, EmmetiApiClientError
from .const import DOMAIN, CONF_INSTALLATION_ID, CONF_GROUPS

_LOGGER = logging.getLogger(__name__)


class EmmetiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestisce il config flow per l'integrazione."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = EmmetiApiClient(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD], session
            )
            try:
                auth_data = await client.async_authenticate()
                installation_id = auth_data["installation_id"]
                groups = await client.async_discover_groups(installation_id)
                if not groups:
                    errors["base"] = "no_groups_found"
                else:
                    await self.async_set_unique_id(user_input[CONF_USERNAME])
                    self._abort_if_unique_id_configured()
                    final_data = {
                        **user_input,
                        CONF_INSTALLATION_ID: installation_id,
                        CONF_GROUPS: groups,
                    }
                    return self.async_create_entry(
                        title=user_input[CONF_USERNAME], data=final_data
                    )
            except EmmetiApiClientError:
                errors["base"] = "auth_failed"
            except Exception:
                _LOGGER.exception("Errore imprevisto nel config flow")
                errors["base"] = "unknown_error"
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )