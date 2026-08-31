"""Coordinator per Emmeti AQ-IoT."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EmmetiApiAuthError, EmmetiApiClient, EmmetiApiClientError
from .const import DOMAIN, SENSOR_CONFIG_MAP

_LOGGER = logging.getLogger(__name__)

# Radice dei logger per registro: <base>.R8682 segue il solo R8682.
# Si aggancia al pacchetto, non a questo modulo: il nome resta
# custom_components.emmeti_aqiot.delta anche se il codice si sposta di file.
DELTA_LOGGER_BASE = f"{__name__.rsplit('.', 1)[0]}.delta"


class EmmetiCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Scarica periodicamente i dati realtime dell'impianto."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: EmmetiApiClient,
        installation_id: str,
        groups: list[str],
        polling_interval: int,
        show_unmapped: bool = False,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=polling_interval),
        )
        self.client = client
        self.installation_id = installation_id
        self.groups = groups
        self.show_unmapped = show_unmapped
        self._previous: dict[tuple[str, str], int] = {}
        self._delta_loggers: dict[str, logging.Logger] = {}
        # Indice groupCode -> gruppo, ricostruito a ogni ciclo. Con oltre
        # centocinquanta entita' che leggono a ogni aggiornamento, la
        # scansione lineare della lista veniva ripetuta migliaia di volte.
        self.by_group: dict[str, dict[str, Any]] = {}

    async def _async_update_data(self) -> list[dict[str, Any]]:
        try:
            data = await self.client.async_get_realtime_data(
                self.installation_id, self.groups
            )
        except EmmetiApiAuthError as err:
            raise UpdateFailed(f"Autenticazione fallita: {err}") from err
        except EmmetiApiClientError as err:
            raise UpdateFailed(f"Errore di comunicazione con l'API: {err}") from err

        if not data:
            raise UpdateFailed("Il server ha restituito una risposta vuota")

        self.by_group = {
            g["groupCode"]: g for g in data if isinstance(g, dict) and g.get("groupCode")
        }
        self._log_deltas(data)
        return data

    def _delta_logger(self, r_code: str) -> logging.Logger:
        """Logger dedicato a un singolo registro.

        Ogni DELTA esce su un logger figlio che porta il codice nel nome, cosi'
        si puo' seguire un registro alla volta invece di accendere tutto:

        logger:
          logs:
            custom_components.emmeti_aqiot.delta.R8682: debug

        logging.getLogger() tiene in cache le istanze, quindi i centocinquanta
        logger non pesano.
        """
        logger = self._delta_loggers.get(r_code)
        if logger is None:
            logger = logging.getLogger(f"{DELTA_LOGGER_BASE}.{r_code}")
            self._delta_loggers[r_code] = logger
        return logger

    def _delta_logging_attivo(self) -> bool:
        """Vero se serve calcolare i delta.

        Non basta guardare il logger del coordinator: con i logger per registro
        il debug puo' essere acceso solo su un figlio, e un controllo sul solo
        padre scarterebbe tutto prima ancora di arrivarci.
        """
        if _LOGGER.isEnabledFor(logging.DEBUG):
            return True
        radice = logging.getLogger(DELTA_LOGGER_BASE)
        if radice.isEnabledFor(logging.DEBUG):
            return True
        prefisso = f"{DELTA_LOGGER_BASE}."
        return any(
            nome.startswith(prefisso)
            and logging.getLogger(nome).isEnabledFor(logging.DEBUG)
            for nome in logging.root.manager.loggerDict
        )

    def _log_deltas(self, data: list[dict[str, Any]]) -> None:
        """Logga i soli registri il cui valore e' cambiato.

        Serve a identificare i registri non ancora mappati: si modifica un
        parametro sulla webapp Emmeti e si guarda quale coppia gruppo/registro
        si muove. Il salto indica anche la scala (+10 = decimi, +100 =
        centesimi). Per vederli tutti:

        logger:
          logs:
            custom_components.emmeti_aqiot: debug

        Per seguirne uno solo, senza il resto del rumore:

        logger:
          default: warning
          logs:
            custom_components.emmeti_aqiot.delta.R8682: debug
        """
        if not self._delta_logging_attivo():
            # Senza questa guardia si costruirebbe comunque la mappa a ogni
            # polling, per poi buttarla via.
            self._previous.clear()
            return

        for group in data:
            group_code = group.get("groupCode")
            if not group_code:
                continue
            for r_code, value_obj in (group.get("data") or {}).items():
                if not isinstance(value_obj, dict) or "i" not in value_obj:
                    continue
                new = value_obj["i"]
                key = (group_code, r_code)
                old = self._previous.get(key)
                self._previous[key] = new
                if old is None or old == new:
                    continue
                logger = self._delta_logger(r_code)
                if not logger.isEnabledFor(logging.DEBUG):
                    continue
                delta = new - old if isinstance(new, (int, float)) else "n/d"
                known = SENSOR_CONFIG_MAP.get(r_code, {}).get("name", "NON MAPPATO")
                logger.debug(
                    "DELTA %s %s (%s): %s -> %s (%s)",
                    group_code,
                    r_code,
                    known,
                    old,
                    new,
                    f"{delta:+}" if isinstance(delta, (int, float)) else delta,
                )
