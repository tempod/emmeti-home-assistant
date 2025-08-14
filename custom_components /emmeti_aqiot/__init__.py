"""L'integrazione Emmeti AQ-IoT."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EmmetiApiClient
from .const import DOMAIN, PLATFORMS, CONF_INSTALLATION_ID, CONF_GROUPS, CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL

_LOGGER = logging.getLogger(__name__)

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Gestisce gli aggiornamenti delle opzioni."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    client = EmmetiApiClient(
        entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD], async_get_clientsession(hass)
    )
    installation_id = entry.data[CONF_INSTALLATION_ID]
    groups = entry.data[CONF_GROUPS]
    
    polling_interval = entry.options.get(CONF_POLLING_INTERVAL, entry.data.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL))

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
        update_interval=timedelta(seconds=polling_interval),
    )
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
    }
    
    entry.async_on_unload(entry.add_update_listener(update_listener))
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok