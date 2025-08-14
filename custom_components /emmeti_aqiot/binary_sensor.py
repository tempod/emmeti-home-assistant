"""Definizione delle entità 'binary_sensor' per Emmeti AQ-IoT."""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SPECIAL_ENTITIES, SENSOR_CONFIG_MAP

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    
    if coordinator.data:
        entities = []
        created_entities = set()
        for group_data in coordinator.data:
            device_id = group_data.get("deviceId")
            
            for r_code in group_data.get("data", {}):
                if SPECIAL_ENTITIES.get(r_code) == "binary_sensor":
                    unique_id = f"{device_id}_{r_code}"
                    if unique_id not in created_entities:
                        entities.append(EmmetiBinarySensor(coordinator, device_id, r_code))
                        created_entities.add(unique_id)
        
        _LOGGER.info("Aggiunte %d entità binary_sensor Emmeti", len(entities))
        async_add_entities(entities)

class EmmetiBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Rappresenta un'entità binary_sensor Emmeti."""
    def __init__(self, coordinator, device_id, r_code):
        super().__init__(coordinator)
        self._device_id = device_id
        self._r_code = r_code
        
        self._group_code = None
        for group_data in coordinator.data:
            if group_data.get("deviceId") == device_id and r_code in group_data.get("data", {}):
                self._group_code = group_data.get("groupCode")
                break
        
        sanitized_group_code = self._group_code.lower().replace("@", "_").replace("-", "_")
        self._attr_unique_id = f"emmeti_{self._device_id}_{sanitized_group_code}_{self._r_code.lower()}"
        
        config = SENSOR_CONFIG_MAP.get(r_code, {})
        self._attr_name = config.get("name", f"{self._group_code} {r_code}")
        self._transformation = config.get("transformation", lambda x: False)
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._group_code)}, "name": f"Emmeti Group {self._group_code}",
            "manufacturer": "Emmeti", "model": f"Device ID {self._device_id}",
        }
        self.entity_id = f"binary_sensor.{self._attr_unique_id}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        for group_data in self.coordinator.data:
            if group_data.get("groupCode") == self._group_code:
                value_obj = group_data.get("data", {}).get(self._r_code)
                if value_obj and "i" in value_obj:
                    return self._transformation(value_obj["i"])
        return None

    @property
    def available(self) -> bool:
        return any(g.get("groupCode") == self._group_code for g in self.coordinator.data or [])