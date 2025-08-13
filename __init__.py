"""L'integrazione Emmeti AQ-IoT."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EmmetiApiClient
from .const import DOMAIN, PLATFORMS, CONF_INSTALLATION_ID, CONF_GROUPS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    client = EmmetiApiClient(
        entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], async_get_clientsession(hass)
    )
    installation_id = entry.data[CONF_INSTALLATION_ID]
    groups = entry.data[CONF_GROUPS]
    async def async_update_data():
        try:
            return await client.async_get_realtime_data(installation_id, groups)
        except Exception as err:
            raise UpdateFailed(f"Errore di comunicazione con l'API: {err}")
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Emmeti AQ-IoT Data",
        update_method=async_update_data,
        update_interval=timedelta(minutes=2),
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok