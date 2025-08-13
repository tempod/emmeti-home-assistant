"""Definizione dei sensori per Emmeti AQ-IoT."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity

from .const import DOMAIN, WRITABLE_ENTITIES, SENSOR_CONFIG_MAP

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configura i sensori dalla config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    
    if coordinator.data:
        entities = []
        for group_data in coordinator.data:
            group_code = group_data.get("groupCode")
            device_id = group_data.get("deviceId")
            
            for r_code in group_data.get("data", {}):
                if r_code not in WRITABLE_ENTITIES:
                    entities.append(EmmetiSensor(coordinator, group_code, device_id, r_code))
        
        _LOGGER.info("Aggiunti %d sensori Emmeti", len(entities))
        async_add_entities(entities)

class EmmetiSensor(CoordinatorEntity, SensorEntity):
    """Rappresenta un sensore Emmeti di sola lettura."""
    def __init__(self, coordinator, group_code, device_id, r_code):
        super().__init__(coordinator)
        self._group_code = group_code
        self._r_code = r_code
        # CORREZIONE: Sanitizza il group_code per l'ID univoco
        sanitized_group_code = group_code.replace("@", "_")
        self._attr_unique_id = f"emmeti_{device_id}_{sanitized_group_code}_{r_code}"
        
        config = SENSOR_CONFIG_MAP.get(r_code)
        if config:
            self._attr_device_class = config.get("device_class")
            self._attr_native_unit_of_measurement = config.get("unit")
            self._attr_state_class = config.get("state_class")
        
        # Rimosso self._attr_name per forzare l'uso della traduzione
        self._attr_device_info = {
            "identifiers": {(DOMAIN, group_code)}, "name": f"Emmeti Group {group_code}",
            "manufacturer": "Emmeti", "model": f"Device ID {device_id}",
        }
        self.entity_id = f"sensor.{self._attr_unique_id}"

    @property
    def native_value(self):
        for group_data in self.coordinator.data:
            if group_data.get("groupCode") == self._group_code:
                value_obj = group_data.get("data", {}).get(self._r_code)
                if value_obj and "i" in value_obj:
                    raw_value = value_obj["i"]
                    config = SENSOR_CONFIG_MAP.get(self._r_code)
                    if config and "transformation" in config:
                        return config["transformation"](raw_value)
                    return raw_value
        return None

    @property
    def available(self) -> bool:
        return any(g.get("groupCode") == self._group_code for g in self.coordinator.data or [])