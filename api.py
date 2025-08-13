"""Client API per Emmeti AQ-IoT."""
import asyncio
import logging
from typing import Any
from datetime import datetime, timezone

import aiohttp

_LOGGER = logging.getLogger(__name__)

LOGIN_URL = "https://emmeti.aq-iot.net/aq-iot-server-frontend-ha/api/v1/auth/login"
DATA_URL_TEMPLATE = "https://emmeti.aq-iot.net/aq-iot-server-frontend-ha/api/v2/emmeti/{installation_id}/realtime-data"
REALTIME_DATA_URL_TEMPLATE = DATA_URL_TEMPLATE + "?input_group_list={group_list}"


class EmmetiApiClientError(Exception):
    """Eccezione generica per errori dell'API."""


class EmmetiApiClient:
    """Client per l'API di Emmeti AQ-IoT."""

    def __init__(self, username: str, password: str, session: aiohttp.ClientSession):
        self._username = username
        self._password = password
        self._session = session
        self._token = None
        self._installation_id = None

    async def async_authenticate(self) -> dict[str, Any]:
        payload = {"username": self._username, "password": self._password}
        try:
            async with self._session.post(LOGIN_URL, json=payload, timeout=20) as response:
                response.raise_for_status()
                data = await response.json()
                self._token = response.headers.get("Authorization")
                installation_ids = data.get("installationIdList")
                if installation_ids:
                    self._installation_id = installation_ids[0]
                if not self._token or not self._installation_id:
                    raise EmmetiApiClientError("Token o Installation ID non trovati")
                _LOGGER.info("Autenticazione riuscita. Installation ID: %s", self._installation_id)
                return {"token": self._token, "installation_id": self._installation_id}
        except Exception as e:
            _LOGGER.error("Errore durante l'autenticazione: %s", e)
            raise EmmetiApiClientError("Autenticazione fallita") from e

    async def async_discover_groups(self, installation_id: str) -> list[str]:
        if not self._token:
            await self.async_authenticate()
        headers = {"Authorization": f"Bearer {self._token}"}
        url = DATA_URL_TEMPLATE.format(installation_id=installation_id)
        try:
            async with self._session.get(url, headers=headers, timeout=20) as response:
                data = await response.json()
                if response.status != 200 and isinstance(data, dict) and data.get("errCode") == "NOT_FOUND":
                    raise EmmetiApiClientError("Discovery URL returned NOT_FOUND")
                response.raise_for_status()
                groups = [item.get("groupCode") for item in data if isinstance(item, dict) and item.get("groupCode")]
                if groups:
                    _LOGGER.info("Gruppi scoperti dinamicamente con successo: %s", groups)
                    return groups
                raise EmmetiApiClientError("Discovery returned empty/invalid list")
        except Exception as e:
            _LOGGER.warning("La scoperta dinamica dei gruppi è fallita (%s). Verrà utilizzata la lista di fallback.", e)
            return [
                "FB-AMB-DT@D13577@T44164", "FB-EP-SUMM@D13577@T44166", "FB-EP-SUPP@D13577@T44166",
                "FB-HP-DT1@D13577@T44167", "FB-HP-SUPP@D13577@T44167", "FB-HW-DT@D13577@T44165",
                "FB-HW-SUMM@D13577@T44165",
            ]

    async def async_get_realtime_data(self, installation_id: str, groups: list[str]) -> list[dict[str, Any]]:
        if not self._token:
            await self.async_authenticate()
        headers = {"Authorization": f"Bearer {self._token}"}
        url = REALTIME_DATA_URL_TEMPLATE.format(installation_id=installation_id, group_list=",".join(groups))
        try:
            async with self._session.get(url, headers=headers, timeout=20) as response:
                if response.status == 401:
                    _LOGGER.warning("Token scaduto, rieseguo autenticazione")
                    auth_data = await self.async_authenticate()
                    headers["Authorization"] = f"Bearer {auth_data['token']}"
                    async with self._session.get(url, headers=headers, timeout=20) as retry_response:
                        retry_response.raise_for_status()
                        return await retry_response.json()
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            raise EmmetiApiClientError(f"Errore di rete nel recuperare i dati: {e}") from e

    async def async_set_value(self, device_id: int, thing_id: int, r_code: str, value: int) -> bool:
        """Invia un nuovo valore al server."""
        if not self._token or not self._installation_id:
            _LOGGER.error("Impossibile scrivere il valore: autenticazione non valida.")
            return False
        headers = {"Authorization": f"Bearer {self._token}"}
        url = DATA_URL_TEMPLATE.format(installation_id=self._installation_id)
        
        now = datetime.now(timezone.utc)
        ts_formatted = f"{now.strftime('%Y-%m-%dT%H:%M:%S')}.{now.microsecond // 1000:03d}Z"

        payload = {
            "deviceId": device_id,
            "thingId": thing_id,
            "ts": ts_formatted,
            "data": {
                r_code: {"i": value}
            }
        }
        
        _LOGGER.debug("Invio scrittura a URL: %s con payload: %s", url, payload)
        try:
            async with self._session.post(url, headers=headers, json=payload, timeout=20) as response:
                if response.status not in [200, 204]:
                    _LOGGER.error("La scrittura ha restituito uno status inatteso: %d, %s", response.status, await response.text())
                    response.raise_for_status()
                _LOGGER.info("Scrittura valore per %s (Device: %d) riuscita. Status: %d", r_code, device_id, response.status)
                return True
        except Exception as e:
            _LOGGER.error("Errore durante la scrittura del valore per %s: %s", r_code, e)
            return False