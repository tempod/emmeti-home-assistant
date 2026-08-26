"""Classe base condivisa dalle entita' Emmeti AQ-IoT."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    PENDING_MAX_UPDATES,
    SENSOR_CONFIG_MAP,
    friendly_group_name,
)
from .coordinator import EmmetiCoordinator

_LOGGER = logging.getLogger(__name__)


class EmmetiEntity(CoordinatorEntity[EmmetiCoordinator]):
    """Base per tutte le entita' Emmeti.

    Raccoglie la logica che era duplicata nelle cinque piattaforme: ricerca del
    gruppo, unique_id, device_info, disponibilita' e valore ottimistico.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EmmetiCoordinator,
        group_code: str,
        device_id: Any,
        r_code: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._group_code = group_code
        self._device_id = device_id
        self._r_code = r_code
        self._config: dict[str, Any] = (
            config if config is not None else SENSOR_CONFIG_MAP.get(r_code, {})
        )
        self._pending: Any = None
        self._pending_ticks = 0

        sanitized = group_code.lower().replace("@", "_").replace("-", "_")
        # Formato invariato rispetto alle versioni precedenti: cambiarlo
        # farebbe perdere storico e personalizzazioni delle entita' esistenti.
        self._attr_unique_id = f"emmeti_{device_id}_{sanitized}_{r_code.lower()}"

        self._attr_name = self._config.get("name", r_code)
        if not self._config:
            # I registri non ancora identificati restano attivi e con storico,
            # ma finiscono nella sezione Diagnostica della pagina dispositivo
            # invece di affollare i sensori principali.
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, group_code)},
            name=friendly_group_name(group_code),
            manufacturer="Emmeti",
            model="Febos AQ-IoT",
            serial_number=str(device_id),
        )

    # ------------------------------------------------------------------
    # Accesso ai dati del coordinator
    # ------------------------------------------------------------------
    @property
    def _group_data(self) -> dict[str, Any] | None:
        return self.coordinator.by_group.get(self._group_code)

    def _raw(self, r_code: str) -> Any:
        """Valore grezzo di un registro qualsiasi dello stesso gruppo."""
        group = self._group_data
        if not group:
            return None
        value_obj = (group.get("data") or {}).get(r_code)
        if isinstance(value_obj, dict) and "i" in value_obj:
            return value_obj["i"]
        return None

    @property
    def _raw_value(self) -> Any:
        return self._raw(self._r_code)

    def _transform(self, raw: Any) -> Any:
        """Applica la trasformazione del registro, se definita."""
        if raw is None:
            return None
        transformation = self._config.get("transformation")
        if transformation is None:
            return raw
        try:
            return transformation(raw)
        except (TypeError, ValueError) as err:
            _LOGGER.warning(
                "Valore inatteso %r per il registro %s (%s): %s",
                raw,
                self._r_code,
                self._group_code,
                err,
            )
            return None

    def _reverse(self, value: Any) -> Any:
        reverse = self._config.get("reverse_transformation")
        return reverse(value) if reverse else value

    @property
    def _coordinator_value(self) -> Any:
        return self._transform(self._raw_value)

    @property
    def available(self) -> bool:
        return super().available and self._group_data is not None

    # ------------------------------------------------------------------
    # Valore ottimistico
    # ------------------------------------------------------------------
    @property
    def _current_value(self) -> Any:
        """Valore da esporre, dando la precedenza a una scrittura in corso."""
        if self._pending is not None:
            return self._pending
        return self._coordinator_value

    def _set_pending(self, value: Any) -> None:
        """Mostra subito il valore appena scritto.

        La webapp puo' impiegare piu' cicli di polling a riflettere la
        modifica: senza questo la UI tornerebbe al vecchio valore per poi
        cambiare di nuovo.
        """
        self._pending = value
        self._pending_ticks = PENDING_MAX_UPDATES
        self.async_write_ha_state()

    def _handle_coordinator_update(self) -> None:
        if self._pending is not None:
            self._pending_ticks -= 1
            if self._coordinator_value == self._pending or self._pending_ticks <= 0:
                if self._pending_ticks <= 0 and self._coordinator_value != self._pending:
                    _LOGGER.debug(
                        "Il server non ha confermato %s = %r, torno al valore letto",
                        self._r_code,
                        self._pending,
                    )
                self._pending = None
        super()._handle_coordinator_update()


class EmmetiWritableEntity(EmmetiEntity):
    """Base per le entita' che scrivono sull'API."""

    def __init__(
        self,
        coordinator: EmmetiCoordinator,
        group_code: str,
        device_id: Any,
        thing_id: Any,
        r_code: str,
    ) -> None:
        super().__init__(coordinator, group_code, device_id, r_code)
        self._thing_id = thing_id

    async def _async_write(self, value: Any) -> bool:
        """Invia un valore e aggiorna lo stato in modo ottimistico."""
        api_value = self._reverse(value)
        _LOGGER.debug(
            "Imposto %s a %r (valore API: %r)", self.entity_id, value, api_value
        )
        success = await self.coordinator.client.async_set_value(
            self._device_id, self._thing_id, self._r_code, api_value
        )
        if success:
            self._set_pending(value)
            await self.coordinator.async_request_refresh()
        return success


class EmmetiCompositeEntity(EmmetiEntity):
    """Entita' il cui valore nasce da due registri a 16 bit.

    I contatori di energia superano i 65535 centesimi di kWh dopo appena
    655 kWh, quindi il firmware li spezza in parola alta e parola bassa.
    Prese singolarmente sarebbero inutilizzabili: la bassa torna a zero a
    ogni superamento e la alta resta ferma per mesi.
    """

    def __init__(
        self,
        coordinator: EmmetiCoordinator,
        group_code: str,
        device_id: Any,
        low_code: str,
        high_code: str,
        config: dict[str, Any],
    ) -> None:
        super().__init__(coordinator, group_code, device_id, low_code, config)
        self._high_code = high_code
        # unique_id distinto da quello che avrebbe il singolo registro basso:
        # altrimenti riuserebbe l'entita' grezza preesistente, mescolando nello
        # storico i valori crudi con i kWh.
        sanitized = group_code.lower().replace("@", "_").replace("-", "_")
        self._attr_unique_id = (
            f"emmeti_{device_id}_{sanitized}_{high_code.lower()}_{low_code.lower()}"
        )

    def _word(self, r_code: str) -> int | None:
        group = self._group_data
        if not group:
            return None
        value_obj = (group.get("data") or {}).get(r_code)
        if isinstance(value_obj, dict) and isinstance(value_obj.get("i"), int):
            return value_obj["i"]
        return None

    @property
    def _raw_value(self) -> Any:
        low, high = self._word(self._r_code), self._word(self._high_code)
        if low is None or high is None:
            return None
        return high * 65536 + low

    @property
    def available(self) -> bool:
        return super().available and self._raw_value is not None
