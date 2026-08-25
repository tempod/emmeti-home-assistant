"""Entita' 'time' per Emmeti AQ-IoT."""
from __future__ import annotations

import logging
from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import EmmetiCoordinator
from .entity import EmmetiWritableEntity
from .helpers import iter_platform_registers

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EmmetiCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        EmmetiTime(coordinator, group_code, device_id, thing_id, r_code)
        for group_code, device_id, thing_id, r_code in iter_platform_registers(
            coordinator.data, "time"
        )
    ]

    _LOGGER.debug("Aggiunte %d entita' time Emmeti", len(entities))
    async_add_entities(entities)


class EmmetiTime(EmmetiWritableEntity, TimeEntity):
    """Rappresenta un'entita' time Emmeti scrivibile."""

    @property
    def native_value(self) -> time | None:
        return self._current_value

    async def async_set_value(self, value: time) -> None:
        await self._async_write(value)
