"""Sensori di sola lettura per Emmeti AQ-IoT."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SPECIAL_ENTITIES
from .coordinator import EmmetiCoordinator
from .entity import EmmetiEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configura i sensori dalla config entry."""
    coordinator: EmmetiCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        EmmetiSensor(coordinator, group_code, group.get("deviceId"), r_code)
        for group in coordinator.data or []
        if (group_code := group.get("groupCode"))
        for r_code in (group.get("data") or {})
        if r_code not in SPECIAL_ENTITIES
    ]

    _LOGGER.debug("Aggiunti %d sensori Emmeti", len(entities))
    async_add_entities(entities)


class EmmetiSensor(EmmetiEntity, SensorEntity):
    """Rappresenta un sensore Emmeti di sola lettura."""

    def __init__(self, coordinator, group_code, device_id, r_code) -> None:
        super().__init__(coordinator, group_code, device_id, r_code)
        self._attr_device_class = self._config.get("device_class")
        self._attr_native_unit_of_measurement = self._config.get("unit")
        self._attr_state_class = self._config.get("state_class")

    @property
    def native_value(self):
        """Valore corrente del registro."""
        return self._current_value
