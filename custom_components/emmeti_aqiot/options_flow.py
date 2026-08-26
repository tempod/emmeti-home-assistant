"""Options flow per Emmeti AQ-IoT."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_GROUPS,
    CONF_POLLING_INTERVAL,
    CONF_SHOW_UNMAPPED,
    DEFAULT_POLLING_INTERVAL,
    DEFAULT_SHOW_UNMAPPED,
    MAX_POLLING_INTERVAL,
    MIN_POLLING_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


def parse_groups(raw: str) -> list[str]:
    """Converte il testo inserito dall'utente in una lista di gruppi."""
    return [g.strip() for g in raw.replace("\n", ",").split(",") if g.strip()]


class EmmetiOptionsFlowHandler(config_entries.OptionsFlow):
    """Gestisce il flusso delle opzioni.

    Nessun __init__: dal 2024.11 assegnare self.config_entry e' deprecato,
    la entry e' gia' fornita dalla classe base.
    """

    def _current_groups(self) -> list[str]:
        return self.config_entry.options.get(
            CONF_GROUPS, self.config_entry.data.get(CONF_GROUPS, [])
        )

    def _current_interval(self) -> int:
        return self.config_entry.options.get(
            CONF_POLLING_INTERVAL,
            self.config_entry.data.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL),
        )

    async def async_step_init(self, user_input=None):
        """Intervallo di polling e gestione dei gruppi."""
        errors: dict[str, str] = {}
        groups = self._current_groups()
        interval = self._current_interval()
        show_unmapped = self.config_entry.options.get(
            CONF_SHOW_UNMAPPED, DEFAULT_SHOW_UNMAPPED
        )

        if user_input is not None:
            interval = int(user_input[CONF_POLLING_INTERVAL])
            groups = parse_groups(user_input.get(CONF_GROUPS, ""))
            show_unmapped = bool(user_input.get(CONF_SHOW_UNMAPPED, False))

            if not groups:
                errors["base"] = "no_groups_found"

            if not errors:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_POLLING_INTERVAL: interval,
                        CONF_GROUPS: groups,
                        CONF_SHOW_UNMAPPED: show_unmapped,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_POLLING_INTERVAL, default=interval
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_POLLING_INTERVAL,
                        max=MAX_POLLING_INTERVAL,
                        step=1,
                        mode=selector.NumberSelectorMode.SLIDER,
                        unit_of_measurement="s",
                    )
                ),
                vol.Optional(
                    CONF_GROUPS, default="\n".join(groups)
                ): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                ),
                vol.Optional(
                    CONF_SHOW_UNMAPPED, default=show_unmapped
                ): selector.BooleanSelector(),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
