"""Diagnostica per Emmeti AQ-IoT."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import CONF_INSTALLATION_ID, DOMAIN, SENSOR_CONFIG_MAP, SPECIAL_ENTITIES
from .coordinator import EmmetiCoordinator

TO_REDACT = {CONF_USERNAME, CONF_PASSWORD, CONF_INSTALLATION_ID}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Esporta lo stato dell'integrazione.

    I groupCode NON sono oscurati: contengono gli identificativi di impianto,
    ma senza di essi il dump non serve a mappare i registri. Chi apre una issue
    puo' sostituirli a mano se preferisce.
    """
    coordinator: EmmetiCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or []

    unmapped: dict[str, Any] = {}
    for group in data:
        for r_code, value_obj in (group.get("data") or {}).items():
            if r_code in SENSOR_CONFIG_MAP or r_code in SPECIAL_ENTITIES:
                continue
            unmapped.setdefault(group.get("groupCode", "?"), {})[r_code] = value_obj

    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
            "groups": coordinator.groups,
        },
        "registri_non_mappati": unmapped,
        "raw_data": data,
    }
