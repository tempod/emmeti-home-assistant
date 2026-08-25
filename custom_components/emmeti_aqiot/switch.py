"""Entita' 'switch' per Emmeti AQ-IoT."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
        EmmetiSwitch(coordinator, group_code, device_id, thing_id, r_code)
        for group_code, device_id, thing_id, r_code in iter_platform_registers(
            coordinator.data, "switch"
        )
    ]

    _LOGGER.debug("Aggiunte %d entita' switch Emmeti", len(entities))
    async_add_entities(entities)


class EmmetiSwitch(EmmetiWritableEntity, SwitchEntity):
    """Rappresenta un'entita' switch Emmeti scrivibile."""

    @property
    def is_on(self) -> bool | None:
        return self._current_value

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_write(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_write(False)
