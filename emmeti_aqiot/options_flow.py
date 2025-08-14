"""Options flow per Emmeti AQ-IoT."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL

class EmmetiOptionsFlowHandler(config_entries.OptionsFlow):
    """Gestisce il flusso delle opzioni per l'integrazione."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Inizializza il gestore del flusso delle opzioni."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Gestisce il passo iniziale del flusso delle opzioni."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_POLLING_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=10,
                        max=300,
                        step=1,
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=options_schema
        )