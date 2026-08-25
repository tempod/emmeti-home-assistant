"""Entita' 'number' per Emmeti AQ-IoT."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
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
        EmmetiNumber(coordinator, group_code, device_id, thing_id, r_code)
        for group_code, device_id, thing_id, r_code in iter_platform_registers(
            coordinator.data, "number"
        )
    ]

    _LOGGER.debug("Aggiunte %d entita' number Emmeti", len(entities))
    async_add_entities(entities)


class EmmetiNumber(EmmetiWritableEntity, NumberEntity):
    """Rappresenta un'entita' number Emmeti scrivibile."""

    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, group_code, device_id, thing_id, r_code) -> None:
        super().__init__(coordinator, group_code, device_id, thing_id, r_code)

        device_class = self._config.get("device_class")
        if device_class is not None:
            # SensorDeviceClass e NumberDeviceClass condividono i valori, ma
            # per una NumberEntity va usata la seconda.
            try:
                self._attr_device_class = NumberDeviceClass(str(device_class))
            except ValueError:
                _LOGGER.debug(
                    "device_class %s non valida per una number (%s)",
                    device_class,
                    r_code,
                )

        self._attr_native_unit_of_measurement = self._config.get("unit")
        if "min_value" in self._config:
            self._attr_native_min_value = self._config["min_value"]
        if "max_value" in self._config:
            self._attr_native_max_value = self._config["max_value"]
        if "step" in self._config:
            self._attr_native_step = self._config["step"]

    @property
    def native_value(self) -> float | None:
        return self._current_value

    async def async_set_native_value(self, value: float) -> None:
        await self._async_write(value)
