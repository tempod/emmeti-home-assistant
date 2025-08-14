"""Definizione delle entità 'switch' per Emmeti AQ-IoT."""
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    client = data["client"]
    
    if coordinator.data:
        entities = []
        created_entities = set()
        for group_data in coordinator.data:
            device_id = group_data.get("deviceId")
            thing_id = group_data.get("thingId")
            
            for r_code in group_data.get("data", {}):
                if SPECIAL_ENTITIES.get(r_code) == "switch":
                    unique_id = f"{device_id}_{r_code}"
                    if unique_id not in created_entities:
                        entities.append(EmmetiSwitch(coordinator, client, device_id, thing_id, r_code))
                        created_entities.add(unique_id)
        
        _LOGGER.info("Aggiunte %d entità switch Emmeti", len(entities))
        async_add_entities(entities)

class EmmetiSwitch(CoordinatorEntity, SwitchEntity):
    """Rappresenta un'entità switch Emmeti scrivibile."""
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
        
        sanitized_group_code = self._group_code.lower().replace("@", "_").replace("-", "_")
        self._attr_unique_id = f"emmeti_{self._device_id}_{sanitized_group_code}_{self._r_code.lower()}"
        
        config = SENSOR_CONFIG_MAP.get(r_code, {})
        self._attr_name = config.get("name", f"{self._group_code} {r_code}")
        self._transformation = config.get("transformation", lambda x: False)
        self._reverse_transformation = config.get("reverse_transformation", lambda x: 0)
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._group_code)}, "name": f"Emmeti Group {self._group_code}",
            "manufacturer": "Emmeti", "model": f"Device ID {self._device_id}",
        }
        self.entity_id = f"switch.{self._attr_unique_id}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        for group_data in self.coordinator.data:
            if group_data.get("groupCode") == self._group_code:
                value_obj = group_data.get("data", {}).get(self._r_code)
                if value_obj and "i" in value_obj:
                    return self._transformation(value_obj["i"])
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        api_value = self._reverse_transformation(True)
        _LOGGER.info("Tentativo di accendere %s (valore API: %d)", self.entity_id, api_value)
        success = await self._client.async_set_value(
            self._device_id, self._thing_id, self._r_code, api_value
        )
        if success:
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        api_value = self._reverse_transformation(False)
        _LOGGER.info("Tentativo di spegnere %s (valore API: %d)", self.entity_id, api_value)
        success = await self._client.async_set_value(
            self._device_id, self._thing_id, self._r_code, api_value
        )
        if success:
            await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        return any(g.get("groupCode") == self._group_code for g in self.coordinator.data or [])