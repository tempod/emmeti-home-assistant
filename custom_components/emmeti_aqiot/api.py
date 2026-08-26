"""Client API per Emmeti AQ-IoT."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://emmeti.aq-iot.net/aq-iot-server-frontend-ha"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login"
DATA_URL_TEMPLATE = f"{BASE_URL}/api/v2/emmeti/{{installation_id}}/realtime-data"
REALTIME_DATA_URL_TEMPLATE = DATA_URL_TEMPLATE + "?input_group_list={group_list}"

REQUEST_TIMEOUT_SECONDS = 20
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)

WRITE_RETRIES = 3
WRITE_RETRY_DELAY = 2
READ_RETRIES = 2
READ_RETRY_DELAY = 3


def describe_error(err: BaseException) -> str:
    """Descrizione leggibile di un'eccezione di rete.

    str(asyncio.TimeoutError()) restituisce una stringa vuota, per cui i log
    mostravano "Errore nel recuperare i dati:" senza alcuna causa.
    """
    if isinstance(err, (asyncio.TimeoutError, TimeoutError)):
        return f"nessuna risposta entro {REQUEST_TIMEOUT_SECONDS}s"
    text = str(err).strip()
    name = type(err).__name__
    return f"{name}: {text}" if text else name


class EmmetiApiClientError(Exception):
    """Eccezione generica per errori dell'API."""


class EmmetiApiAuthError(EmmetiApiClientError):
    """Credenziali rifiutate dal server."""


def _raise_for_api_error(data: object, context: str) -> None:
    """Intercetta gli errori applicativi restituiti con status HTTP 200.

    Il backend Emmeti segnala i problemi nel corpo della risposta invece che
    nello status: {"errCode": "NOT_FOUND", "code": -1, "msg": "Device"}.
    Senza questo controllo il dizionario verrebbe scambiato per dati validi e
    le piattaforme fallirebbero iterandolo.
    """
    if not isinstance(data, dict):
        return
    err_code = data.get("errCode")
    if err_code or data.get("code") == -1:
        message = data.get("msg") or data.get("message") or "errore non specificato"
        raise EmmetiApiClientError(f"{context}: il server ha risposto {err_code} ({message})")


class EmmetiApiClient:
    """Client per l'API di Emmeti AQ-IoT."""

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
        installation_id: str | None = None,
    ) -> None:
        self._username = username
        self._password = password
        self._session = session
        self._token: str | None = None
        self._installation_id = installation_id

    @property
    def installation_id(self) -> str | None:
        """Installation ID noto al client."""
        return self._installation_id

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    async def async_authenticate(self) -> dict[str, Any]:
        """Esegue il login e memorizza token e installation id."""
        payload = {"username": self._username, "password": self._password}
        try:
            async with self._session.post(
                LOGIN_URL, json=payload, timeout=REQUEST_TIMEOUT
            ) as response:
                response.raise_for_status()
                data = await response.json()
                token = response.headers.get("Authorization")
                if token:
                    # Alcuni backend restituiscono gia' il prefisso "Bearer":
                    # senza questo strip finirebbe duplicato nelle richieste.
                    token = token.removeprefix("Bearer").strip()
                self._token = token or None

                installation_ids = data.get("installationIdList")
                if installation_ids:
                    if (
                        self._installation_id
                        and self._installation_id not in installation_ids
                    ):
                        _LOGGER.warning(
                            "L'installation ID configurato (%s) non e' piu' "
                            "presente nella lista restituita dal server: %s",
                            self._installation_id,
                            installation_ids,
                        )
                    if not self._installation_id:
                        self._installation_id = installation_ids[0]

                if not self._token or not self._installation_id:
                    raise EmmetiApiAuthError("Token o Installation ID non trovati")

                _LOGGER.debug(
                    "Autenticazione riuscita. Installation ID: %s",
                    self._installation_id,
                )
                return {"token": self._token, "installation_id": self._installation_id}
        except EmmetiApiClientError:
            raise
        except aiohttp.ClientResponseError as err:
            self._token = None
            if err.status in (401, 403):
                raise EmmetiApiAuthError("Credenziali non valide") from err
            raise EmmetiApiClientError(f"Autenticazione fallita: {describe_error(err)}") from err
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            self._token = None
            raise EmmetiApiClientError(f"Autenticazione fallita: {describe_error(err)}") from err

    async def async_get_realtime_data(
        self, installation_id: str, groups: list[str]
    ) -> list[dict[str, Any]]:
        """Legge i dati realtime per i gruppi indicati.

        La webapp e' lenta e ogni tanto non risponde entro il timeout: un
        singolo errore rendeva non disponibili tutte le entita' fino al
        polling successivo, facendo fallire le automazioni che le usavano.
        Si riprova qualche volta prima di dichiarare fallito il ciclo.
        """
        if not self._token:
            await self.async_authenticate()

        url = REALTIME_DATA_URL_TEMPLATE.format(
            installation_id=installation_id, group_list=",".join(groups)
        )
        last_error = "causa sconosciuta"

        for attempt in range(1, READ_RETRIES + 1):
            try:
                async with self._session.get(
                    url, headers=self._headers(), timeout=REQUEST_TIMEOUT
                ) as response:
                    if response.status == 401:
                        _LOGGER.debug("Token scaduto in lettura, rieseguo il login")
                        self._token = None
                        await self.async_authenticate()
                        last_error = "token scaduto"
                        continue
                    response.raise_for_status()
                    data = await response.json(content_type=None)
            except EmmetiApiAuthError:
                raise
            except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
                last_error = describe_error(err)
                _LOGGER.debug(
                    "Lettura dati fallita (tentativo %d/%d): %s",
                    attempt,
                    READ_RETRIES,
                    last_error,
                )
                if attempt < READ_RETRIES:
                    await asyncio.sleep(READ_RETRY_DELAY)
                continue

            _raise_for_api_error(data, "Lettura dati")
            if not isinstance(data, list):
                raise EmmetiApiClientError(
                    f"Risposta in formato inatteso ({type(data).__name__}): "
                    "controlla i codici gruppo nelle opzioni"
                )
            return data

        raise EmmetiApiClientError(
            f"Nessun dato dopo {READ_RETRIES} tentativi ({last_error})"
        )

    async def async_set_value(
        self, device_id: int, thing_id: int, r_code: str, value: int
    ) -> bool:
        """Invia un nuovo valore al server.

        La webapp Emmeti risponde spesso 400 "Bad Response from device" anche
        quando la richiesta e' valida, quindi si riprova qualche volta. Il 401
        viene gestito rinnovando il token: prima i tentativi successivi
        riusavano quello scaduto ed erano destinati a fallire tutti.
        """
        if not self._installation_id:
            _LOGGER.error("Impossibile scrivere il valore: installation ID mancante")
            return False
        if not self._token:
            try:
                await self.async_authenticate()
            except EmmetiApiClientError as err:
                _LOGGER.error("Impossibile autenticarsi per la scrittura: %s", err)
                return False

        url = DATA_URL_TEMPLATE.format(installation_id=self._installation_id)
        now = datetime.now(timezone.utc)
        payload = {
            "deviceId": device_id,
            "thingId": thing_id,
            "ts": f"{now.strftime('%Y-%m-%dT%H:%M:%S')}."
            f"{now.microsecond // 1000:03d}Z",
            "data": {r_code: {"i": value}},
        }

        last_error: str | None = None
        for attempt in range(1, WRITE_RETRIES + 1):
            try:
                _LOGGER.debug(
                    "Scrittura %s = %s (tentativo %d/%d)",
                    r_code,
                    value,
                    attempt,
                    WRITE_RETRIES,
                )
                async with self._session.post(
                    url, headers=self._headers(), json=payload, timeout=REQUEST_TIMEOUT
                ) as response:
                    if response.status in (200, 204):
                        _LOGGER.debug(
                            "Scrittura %s (device %s) riuscita", r_code, device_id
                        )
                        return True

                    if response.status == 401:
                        _LOGGER.debug("Token scaduto in scrittura, rieseguo il login")
                        self._token = None
                        await self.async_authenticate()
                        last_error = "token scaduto"
                        continue

                    body = await response.text()
                    if response.status == 400 and "Bad Response from device" in body:
                        last_error = "Bad Response from device"
                        _LOGGER.debug(
                            "Il dispositivo non ha risposto per %s, riprovo tra %ds",
                            r_code,
                            WRITE_RETRY_DELAY,
                        )
                        await asyncio.sleep(WRITE_RETRY_DELAY)
                        continue

                    last_error = f"status {response.status}"
                    _LOGGER.error(
                        "Scrittura di %s rifiutata dal server: status %d",
                        r_code,
                        response.status,
                    )
                    return False

            except EmmetiApiAuthError as err:
                _LOGGER.error("Autenticazione fallita durante la scrittura: %s", err)
                return False
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                last_error = str(err)
                _LOGGER.debug(
                    "Errore di rete al tentativo %d di scrittura di %s: %s",
                    attempt,
                    r_code,
                    err,
                )
                if attempt < WRITE_RETRIES:
                    await asyncio.sleep(WRITE_RETRY_DELAY)

        _LOGGER.error(
            "Scrittura di %s fallita dopo %d tentativi (ultimo errore: %s)",
            r_code,
            WRITE_RETRIES,
            last_error,
        )
        return False
