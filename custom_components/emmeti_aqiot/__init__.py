"""L'integrazione Emmeti AQ-IoT."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EmmetiApiClient
from .const import (
    CONF_GROUPS,
    CONF_INSTALLATION_ID,
    CONF_POLLING_INTERVAL,
    CONF_SHOW_UNMAPPED,
    DEFAULT_POLLING_INTERVAL,
    DEFAULT_SHOW_UNMAPPED,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import EmmetiCoordinator

_LOGGER = logging.getLogger(__name__)


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Ricarica l'integrazione quando cambiano le opzioni."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configura l'integrazione da una config entry."""
    installation_id = entry.data[CONF_INSTALLATION_ID]
    # I gruppi possono essere modificati dalle opzioni: quelli in data sono
    # solo il valore iniziale deciso al momento della configurazione.
    groups = entry.options.get(CONF_GROUPS) or entry.data[CONF_GROUPS]
    polling_interval = entry.options.get(
        CONF_POLLING_INTERVAL,
        entry.data.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL),
    )

    client = EmmetiApiClient(
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        async_get_clientsession(hass),
        installation_id=installation_id,
    )

    show_unmapped = entry.options.get(CONF_SHOW_UNMAPPED, DEFAULT_SHOW_UNMAPPED)

    coordinator = EmmetiCoordinator(
        hass, entry, client, installation_id, groups, polling_interval, show_unmapped
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Scarica una config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    return unload_ok
