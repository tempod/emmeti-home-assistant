"""Sensori di sola lettura per Emmeti AQ-IoT."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    COMPOSITE_REGISTERS,
    COMPOSITE_SENSORS,
    DOMAIN,
    SENSOR_CONFIG_MAP,
    SPECIAL_ENTITIES,
)
from .coordinator import EmmetiCoordinator
from .entity import EmmetiCompositeEntity, EmmetiEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configura i sensori dalla config entry."""
    coordinator: EmmetiCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []
    scartati: list[str] = []

    for group in coordinator.data or []:
        group_code = group.get("groupCode")
        if not group_code:
            continue
        device_id = group.get("deviceId")
        registers = group.get("data") or {}

        for r_code in registers:
            # I registri che compongono un contatore a 32 bit non generano
            # entita' proprie: da soli non significano nulla.
            if r_code in SPECIAL_ENTITIES or r_code in COMPOSITE_REGISTERS:
                continue
            if r_code not in SENSOR_CONFIG_MAP and not coordinator.show_unmapped:
                # Registri non ancora identificati: senza l'opzione attiva non
                # diventano entita' e non finiscono nel database. Restano
                # comunque visibili nel log dei DELTA e nella diagnostica.
                scartati.append(
                    EmmetiSensor.build_unique_id(device_id, group_code, r_code)
                )
                continue
            entities.append(EmmetiSensor(coordinator, group_code, device_id, r_code))

        for low_code, config in COMPOSITE_SENSORS.items():
            if low_code in registers and config["high"] in registers:
                entities.append(
                    EmmetiEnergySensor(
                        coordinator,
                        group_code,
                        device_id,
                        low_code,
                        config["high"],
                        config,
                    )
                )

    if scartati:
        _pulisci_registro(hass, entry, scartati)
        _LOGGER.debug(
            "%d registri non identificati esclusi (opzione disattivata)", len(scartati)
        )

    _LOGGER.debug("Aggiunti %d sensori Emmeti", len(entities))
    async_add_entities(entities)


def _pulisci_registro(
    hass: HomeAssistant, entry: ConfigEntry, unique_ids: list[str]
) -> None:
    """Rimuove dal registro le entita' dei registri non piu' esposti.

    Senza questa pulizia resterebbero un centinaio di entita' orfane, segnate
    come non disponibili, da cancellare a mano una per una.
    """
    registry = er.async_get(hass)
    for unique_id in unique_ids:
        entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
        if entity_id:
            registry.async_remove(entity_id)


class EmmetiSensor(EmmetiEntity, SensorEntity):
    """Rappresenta un sensore Emmeti di sola lettura."""

    @staticmethod
    def build_unique_id(device_id, group_code: str, r_code: str) -> str:
        """Identificativo che avrebbe l'entita', senza doverla costruire."""
        sanitized = group_code.lower().replace("@", "_").replace("-", "_")
        return f"emmeti_{device_id}_{sanitized}_{r_code.lower()}"

    def __init__(self, coordinator, group_code, device_id, r_code) -> None:
        super().__init__(coordinator, group_code, device_id, r_code)
        self._attr_device_class = self._config.get("device_class")
        self._attr_native_unit_of_measurement = self._config.get("unit")
        self._attr_state_class = self._config.get("state_class")

    @property
    def native_value(self):
        """Valore corrente del registro."""
        return self._current_value


class EmmetiEnergySensor(EmmetiCompositeEntity, SensorEntity):
    """Contatore di energia ricomposto da due registri a 16 bit."""

    def __init__(
        self, coordinator, group_code, device_id, low_code, high_code, config
    ) -> None:
        super().__init__(
            coordinator, group_code, device_id, low_code, high_code, config
        )
        self._attr_device_class = config.get("device_class")
        self._attr_native_unit_of_measurement = config.get("unit")
        self._attr_state_class = config.get("state_class")
        self._attr_suggested_display_precision = 2

    @property
    def native_value(self):
        return self._current_value
