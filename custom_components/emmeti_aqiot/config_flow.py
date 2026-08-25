"""Config flow per Emmeti AQ-IoT."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EmmetiApiAuthError, EmmetiApiClient, EmmetiApiClientError
from .const import (
    CONF_GROUPS,
    CONF_INSTALLATION_ID,
    CONF_POLLING_INTERVAL,
    DEFAULT_POLLING_INTERVAL,
    DOMAIN,
    MAX_POLLING_INTERVAL,
    MIN_POLLING_INTERVAL,
)
from .options_flow import EmmetiOptionsFlowHandler, parse_groups

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
        ),
        vol.Required(CONF_PASSWORD): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
        vol.Optional(
            CONF_POLLING_INTERVAL, default=DEFAULT_POLLING_INTERVAL
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=MIN_POLLING_INTERVAL,
                max=MAX_POLLING_INTERVAL,
                step=1,
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement="s",
            )
        ),
    }
)

GROUPS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_GROUPS): selector.TextSelector(
            selector.TextSelectorConfig(multiline=True)
        )
    }
)


class EmmetiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestisce il config flow per l'integrazione."""

    VERSION = 1

    def __init__(self) -> None:
        self._user_input: dict[str, Any] = {}
        self._installation_id: str | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> EmmetiOptionsFlowHandler:
        """Espone l'options flow.

        Senza questo metodo il pulsante "Configura" non compare e ne'
        l'intervallo di polling ne' i gruppi sarebbero modificabili.
        """
        return EmmetiOptionsFlowHandler()

    async def async_step_user(self, user_input=None):
        """Credenziali di accesso alla webapp Emmeti."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_POLLING_INTERVAL] = int(
                user_input.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL)
            )
            client = EmmetiApiClient(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                async_get_clientsession(self.hass),
            )
            try:
                auth_data = await client.async_authenticate()
            except EmmetiApiAuthError:
                errors["base"] = "auth_failed"
            except EmmetiApiClientError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Errore imprevisto nel config flow")
                errors["base"] = "unknown_error"
            else:
                await self.async_set_unique_id(user_input[CONF_USERNAME])
                self._abort_if_unique_id_configured()
                self._user_input = user_input
                self._installation_id = auth_data["installation_id"]
                return await self.async_step_groups()

        return self.async_show_form(
            step_id="user", data_schema=USER_SCHEMA, errors=errors
        )

    async def async_step_groups(self, user_input=None):
        """Elenco dei gruppi da monitorare.

        L'API non espone un endpoint per elencarli: quello dei dati realtime
        pretende la lista come parametro e senza risponde NOT_FOUND. I codici
        vanno quindi letti dalle chiamate della webapp.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            groups = parse_groups(user_input[CONF_GROUPS])
            if not groups:
                errors["base"] = "no_groups_found"
            else:
                return self.async_create_entry(
                    title=self._user_input[CONF_USERNAME],
                    data={
                        **self._user_input,
                        CONF_INSTALLATION_ID: self._installation_id,
                        CONF_GROUPS: groups,
                    },
                )

        return self.async_show_form(
            step_id="groups", data_schema=GROUPS_SCHEMA, errors=errors
        )
