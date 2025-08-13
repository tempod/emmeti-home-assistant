"""Definizione delle entità 'time' per Emmeti AQ-IoT."""
import logging
from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, WRITABLE_ENTITIES, SENSOR_CONFIG_MAP

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]
    
    if coordinator.data:
        entities = []
        for group_data in coordinator.data:
            device_id = group_data.get("deviceId")
            thing_id = group_data.get("thingId")
            
            for r_code in group_data.get("data", {}):
                if WRITABLE_ENTITIES.get(r_code) == "time":
                    entities.append(EmmetiTime(coordinator, client, device_id, thing_id, r_code))
        
        _LOGGER.info("Aggiunte %d entità time Emmeti", len(entities))
        async_add_entities(entities)

class EmmetiTime(CoordinatorEntity, TimeEntity):
    """Rappresenta un'entità time Emmeti scrivibile."""
    def __init__(self, coordinator, client, device_id, thing_id, r_code):
        super().__init__(coordinator)
        self._client = client
        self._device_id = device_id
        self._thing_id = thing_id
        self._r_code = r_code
        
        self._group_code = None
        for group_data in coordinator.data:
            if group_data.get("deviceId") == device_id and r_code in group_data.get("data", {}):
                self._group_code = group_data.get("groupCode")
                break
        
        sanitized_group_code = self._group_code.replace("@", "_")
        self._attr_unique_id = f"emmeti_{self._device_id}_{sanitized_group_code}_{self._r_code}"
        
        config = SENSOR_CONFIG_MAP.get(r_code, {})
        self._transformation = config.get("transformation", lambda x: time(0, 0))
        self._reverse_transformation = config.get("reverse_transformation", lambda x: 0)
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._group_code)}, "name": f"Emmeti Group {self._group_code}",
            "manufacturer": "Emmeti", "model": f"Device ID {self._device_id}",
        }
        self.entity_id = f"time.{self._attr_unique_id}"

    @property
    def native_value(self) -> time | None:
        """Ritorna lo stato corrente dell'entità."""
        for group_data in self.coordinator.data:
            if group_data.get("groupCode") == self._group_code:
                value_obj = group_data.get("data", {}).get(self._r_code)
                if value_obj and "i" in value_obj:
                    return self._transformation(value_obj["i"])
        return None

    async def async_set_value(self, value: time) -> None:
        """Imposta un nuovo valore."""
        api_value = self._reverse_transformation(value)
        
        _LOGGER.info("Tentativo di impostare %s a %s (valore API: %d)", self.entity_id, value, api_value)
        
        success = await self._client.async_set_value(
            self._device_id, self._thing_id, self._r_code, api_value
        )
        
        if success:
            await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        return any(g.get("groupCode") == self._group_code for g in self.coordinator.data or [])