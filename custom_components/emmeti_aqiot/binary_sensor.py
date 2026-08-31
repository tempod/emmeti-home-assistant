"""Entita' 'binary_sensor' per Emmeti AQ-IoT."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import EmmetiCoordinator
from .entity import EmmetiEntity
from .helpers import iter_platform_registers

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EmmetiCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        EmmetiBinarySensor(coordinator, group_code, device_id, r_code)
        for group_code, device_id, _thing_id, r_code in iter_platform_registers(
            coordinator.data, "binary_sensor"
        )
    ]

    _LOGGER.debug("Aggiunte %d entita' binary_sensor Emmeti", len(entities))
    async_add_entities(entities)


class EmmetiBinarySensor(EmmetiEntity, BinarySensorEntity):
    """Rappresenta un'entita' binary_sensor Emmeti."""

    def __init__(self, coordinator, group_code, device_id, r_code) -> None:
        super().__init__(coordinator, group_code, device_id, r_code)
        # Prima la device_class dichiarata nella mappa veniva ignorata dai
        # binary_sensor: la leggeva solo la piattaforma sensor.
        self._attr_device_class = self._config.get("device_class")

    @property
    def is_on(self) -> bool | None:
        return self._current_value
