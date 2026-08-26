"""Costanti per l'integrazione Emmeti AQ-IoT."""
from __future__ import annotations

from datetime import time
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    Platform,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)

DOMAIN = "emmeti_aqiot"

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TIME,
]

# Chiavi per i dati salvati nella config entry
CONF_INSTALLATION_ID = "installation_id"
CONF_GROUPS = "groups"
CONF_POLLING_INTERVAL = "polling_interval"
CONF_SHOW_UNMAPPED = "show_unmapped"
# Spento di default: i registri non identificati sono un centinaio e
# scriverebbero uno stato a ogni ciclo senza dare nulla in cambio. Chi vuole
# contribuire alla mappatura lo accende dalle opzioni.
DEFAULT_SHOW_UNMAPPED = False
DEFAULT_POLLING_INTERVAL = 30
MIN_POLLING_INTERVAL = 10
MAX_POLLING_INTERVAL = 300

# Cicli del coordinator da attendere prima di scartare un valore impostato in
# modo ottimistico e mai confermato dal server.
PENDING_MAX_UPDATES = 6


# --------------------------------------------------------------------------
# Helper per le trasformazioni
# --------------------------------------------------------------------------
def scaled(factor: float) -> dict[str, Any]:
    """Lettura e scrittura per un registro con un dato fattore di scala.

    Definire le due direzioni in un unico punto impedisce che divisore e
    moltiplicatore divergano, com'era per i setpoint di temperatura.
    Il round() prima di int() e' necessario: int(21.3 * 10) darebbe 212.
    """
    if factor == 1:
        # Nessuna divisione: raw / 1 restituirebbe un float e lo stato delle
        # entita' esistenti passerebbe da "45" a "45.0".
        return {
            "transformation": lambda raw: raw,
            "reverse_transformation": lambda value: int(round(value)),
        }
    return {
        "transformation": lambda raw, f=factor: raw / f,
        "reverse_transformation": lambda value, f=factor: int(round(value * f)),
    }


def _minutes_to_time(raw: int) -> time | None:
    """Converte i minuti dalla mezzanotte in un oggetto time.

    Ritorna None fuori range: senza questo controllo time() solleverebbe
    ValueError dentro una property e l'entita' andrebbe in errore.
    """
    if raw is None or not 0 <= raw < 1440:
        return None
    return time(hour=raw // 60, minute=raw % 60)


def _time_to_minutes(value: time) -> int:
    return value.hour * 60 + value.minute


TIME_TRANSFORM: dict[str, Any] = {
    "transformation": _minutes_to_time,
    "reverse_transformation": _time_to_minutes,
}

BOOL_TRANSFORM: dict[str, Any] = {
    "transformation": lambda raw: raw == 1,
    "reverse_transformation": lambda state: 1 if state else 0,
}


# --------------------------------------------------------------------------
# Nomi leggibili dei dispositivi
# --------------------------------------------------------------------------
GROUP_NAME_MAP = {
    "FB-AMB": "Ambiente",
    "FB-HP": "Pompa di Calore",
    "FB-HW": "Acqua Calda Sanitaria",
    "FB-EP": "Energia",
}


def friendly_group_name(group_code: str) -> str:
    """Ricava un nome leggibile dal groupCode (es. FB-AMB-DT@D13577@T44164)."""
    base = group_code.split("@")[0]
    for prefix, label in GROUP_NAME_MAP.items():
        if base.startswith(prefix):
            suffix = base[len(prefix) :].strip("-")
            return f"Emmeti {label} {suffix}".strip() if suffix else f"Emmeti {label}"
    return f"Emmeti {base}"


# --------------------------------------------------------------------------
# Contatori di energia su due registri a 16 bit
#
# L'energia e' memorizzata a 32 bit su due registri:
#   valore = parola_alta * 65536 + parola_bassa,  unita 0,01 kWh
# La parola bassa cambia di continuo, quella alta avanza solo ogni 655,36 kWh
# (per questo nei log sembrava ferma). Presi singolarmente sarebbero
# inutilizzabili.
#
# Verificato su due scale indipendenti. Totali storici:
#   R8101|R8102 = 68533  -> 685,33 kWh  contro 681,49 dichiarati (+0,6%)
#   R8106|R8107 = 554871 -> 5548,71 kWh contro 5475,78 dichiarati (+1,3%)
# Valori di giornata, dove lo scarto sistematico sparisce:
#   R8107 +99 unita in 5h06m = 0,99 kWh, con 2,05 kWh sull'intera giornata
#   R8102 +2 unita           = 0,02 kWh, con 0,03 kWh sull'intera giornata
#
# La chiave del dizionario e' la parola bassa.
# --------------------------------------------------------------------------
COMPOSITE_SENSORS: dict[str, dict[str, Any]] = {
    "R8102": {
        "high": "R8101",
        **scaled(100),
        "name": "Energia Prodotta/Immessa",
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "R8107": {
        "high": "R8106",
        **scaled(100),
        "name": "Energia Prelevata dalla Rete",
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
}

# Registri assorbiti dai contatori compositi: da soli non significano nulla,
# quindi non devono generare entita' proprie.
COMPOSITE_REGISTERS: set[str] = {
    code for low, cfg in COMPOSITE_SENSORS.items() for code in (low, cfg["high"])
}


# --------------------------------------------------------------------------
# Mappa delle entita' con una piattaforma specifica (diversa da 'sensor')
# --------------------------------------------------------------------------
SPECIAL_ENTITIES = {
    "R8684": "number",
    "R8685": "time",
    "R8690": "number",
    "R8688": "number",
    "R8691": "time",
    "R8689": "time",
    "R8686": "number",
    "R8687": "time",
    "R8660": "number",
    "R8661": "number",
    "R8676": "switch",
    "R16384": "switch",
    "R8692": "switch",
    "R16497": "number",
    "R16494": "number",
    "R16496": "number",
    "R16493": "time",
    "R16495": "time",
    "R9073": "binary_sensor",
    "R8683": "switch",
}

# --------------------------------------------------------------------------
# Mappa per la trasformazione dei dati e la configurazione dei sensori
# --------------------------------------------------------------------------
SENSOR_CONFIG_MAP: dict[str, dict[str, Any]] = {
    # Temperature Riscaldamento
    #
    # NOTA SCALA: questi quattro setpoint usano fattore 100 (centesimi di
    # grado). Prima lettura e scrittura erano disallineate (/100 in lettura,
    # *10 in scrittura). Se sulla UI i valori risultano dieci volte piu'
    # piccoli del reale, il fattore giusto e' 10: basta sostituire
    # scaled(100) con scaled(10) e le due direzioni restano coerenti.
    "R8690": {
        **scaled(100),
        "name": "Attenuazione Riscaldamento",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 0.5,
        "max_value": 5.0,
        "step": 0.1,
    },
    "R8688": {
        **scaled(100),
        "name": "Confort Riscaldamento",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 8.0,
        "max_value": 30.0,
        "step": 0.1,
    },
    # Temperature Raffrescamento
    "R8686": {
        **scaled(100),
        "name": "Attenuazione Raffrescamento",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 0.5,
        "max_value": 5.0,
        "step": 0.1,
    },
    "R8684": {
        **scaled(100),
        "name": "Confort Raffrescamento",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 15.0,
        "max_value": 30.0,
        "step": 0.1,
    },
    # Temperature ACS
    "R16497": {
        **scaled(10),
        "name": "Temp Mantenimento ACS",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 0.0,
        "max_value": 70.0,
        "step": 0.1,
    },
    "R16494": {
        **scaled(10),
        "name": "Temp Richiesta 1 ACS",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 0.0,
        "max_value": 70.0,
        "step": 0.1,
    },
    "R16496": {
        **scaled(10),
        "name": "Temp Richiesta 2 ACS",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 0.0,
        "max_value": 70.0,
        "step": 0.1,
    },
    # Umidita'
    "R8660": {
        **scaled(1),
        "name": "Setpoint Umidita Raffrescamento",
        "device_class": SensorDeviceClass.HUMIDITY,
        "unit": PERCENTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 30.0,
        "max_value": 99.0,
        "step": 1.0,
    },
    "R8661": {
        **scaled(1),
        "name": "Setpoint Umidita Riscaldamento",
        "device_class": SensorDeviceClass.HUMIDITY,
        "unit": PERCENTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 30.0,
        "max_value": 99.0,
        "step": 1.0,
    },
    # Time Riscaldamento
    "R8691": {**TIME_TRANSFORM, "name": "Orario Attenuazione Riscaldamento"},
    "R8689": {**TIME_TRANSFORM, "name": "Orario Confort Riscaldamento"},
    # Time Raffrescamento
    "R8687": {**TIME_TRANSFORM, "name": "Orario Attenuazione Raffrescamento"},
    "R8685": {**TIME_TRANSFORM, "name": "Orario Confort Raffrescamento"},
    # Time ACS
    "R16493": {**TIME_TRANSFORM, "name": "Orario Richiesta 1 ACS"},
    "R16495": {**TIME_TRANSFORM, "name": "Orario Richiesta 2 ACS"},
    # Switch
    "R8676": {**BOOL_TRANSFORM, "name": "Presenza"},
    "R16384": {**BOOL_TRANSFORM, "name": "PDC On/Off"},
    "R8692": {**BOOL_TRANSFORM, "name": "Boost"},
    "R8683": {**BOOL_TRANSFORM, "name": "Freddo/Caldo"},
    # Binary Sensor
    "R9073": {**BOOL_TRANSFORM, "name": "Eco Hot Water"},
    # Sensori Sola Lettura
    "R8680": {
        **scaled(10),
        "name": "Punto di Rugiada",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    # R8703, non R8707: quest'ultimo non e' mai stato restituito dal server.
    # Verificato per via psicrometrica: il punto di rugiada calcolato da
    # R8703 (27,6 C) e R8704 (68%) vale 21,16 C, contro i 21,1 C letti in
    # R8680. Coerenza a 0,06 C.
    "R8703": {
        **scaled(10),
        "name": "Temperatura Attuale",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8704": {
        **scaled(1),
        "name": "Umidita Attuale",
        "device_class": SensorDeviceClass.HUMIDITY,
        "unit": PERCENTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R9123": {
        **scaled(100),
        "name": "Potenza Termica",
        "device_class": SensorDeviceClass.POWER,
        "unit": UnitOfPower.KILO_WATT,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R9120": {
        **scaled(1),
        "name": "Portata",
        "unit": "L/h",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8987": {
        **scaled(10),
        "name": "Temperatura Mandata",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8988": {
        **scaled(10),
        "name": "Temperatura Ritorno",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    # Confermati per integrazione sulla giornata: R8005 da' 0,766 kWh contro
    # i 0,76 della webapp (scarto 0,8%). Sono POTENZE, non energie: per
    # ottenere i kWh giornalieri serve un integrale di Riemann in HA.
    # Sono i primi due dei quattro ingressi a impulsi del modulo FEBOS-Energy
    # (R8002, R8005, R8008, R8011); gli altri due sono a zero.
    "R8002": {
        **scaled(1000),
        "name": "Assorbimento PDC",
        "device_class": SensorDeviceClass.POWER,
        "unit": UnitOfPower.KILO_WATT,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8005": {
        **scaled(1000),
        "name": "Assorbimento ACS",
        "device_class": SensorDeviceClass.POWER,
        "unit": UnitOfPower.KILO_WATT,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R9052": {
        **scaled(10),
        "name": "Temperatura Attuale Acqua PDC",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R9051": {
        **scaled(10),
        "name": "Temperatura Target Acqua PDC",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R9042": {
        **scaled(10),
        "name": "Temperatura Minima Radiante Acqua PDC",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8986": {
        **scaled(10),
        "name": "Temperatura Esterna",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8989": {
        **scaled(10),
        "name": "Temperatura Acqua Calda",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    # Tensione di rete, in decivolt. Era mappato come "Consumo Casa" in kW.
    # Su 1743 letture in una giornata resta fra 210,8 e 236,4 V con media
    # 225,6 e deviazione standard 3,7 V: e' l'andamento di una tensione di
    # rete, non di un consumo domestico, che varierebbe di ordini di grandezza.
    "R8100": {
        **scaled(10),
        "name": "Tensione di Rete",
        "device_class": SensorDeviceClass.VOLTAGE,
        "unit": UnitOfElectricPotential.VOLT,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    # Potenza del canale configurabile (fotovoltaico oppure, come nella mia
    # installazione, la ricarica dell'auto). Integrata sulla giornata da
    # 0,04 kWh contro i 0,05 dichiarati dalla webapp.
    "R8105": {
        **scaled(1000),
        "name": "Produzione Solare",
        "device_class": SensorDeviceClass.POWER,
        "unit": UnitOfPower.KILO_WATT,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    # Potenza prelevata dalla rete, in watt. Verificata per integrazione:
    # 4,93 kWh sulla giornata contro i 4,80 della webapp (+2,7%).
    "R8110": {
        **scaled(1000),
        "name": "Prelievo da Rete",
        "device_class": SensorDeviceClass.POWER,
        "unit": UnitOfPower.KILO_WATT,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R9008": {
        **scaled(1),
        "name": "Potenza Compressore",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    # Corrente assorbita, in milliampere. Nello stesso test del forno passa
    # da 1603 (1,60 A) a 16112 (16,11 A). Il rapporto con la potenza di
    # R9127 da' un fattore di potenza di 0,54 a riposo e 0,96 con il forno
    # acceso: coerente con un carico reattivo che lascia il posto a una
    # resistenza pura.
    # Angolo di sfasamento fra tensione e corrente, in gradi.
    # Tre riscontri indipendenti: il valore non supera mai 359 su oltre 11.000
    # campioni; il suo coseno correla a +0,938 con P/(V*I) calcolato da R8110,
    # R8100 e R8112; e rispetta la disuguaglianza fisica cos(fi) >= fattore di
    # potenza reale nel 97,8% dei casi, con lo scarto sempre nella direzione
    # giusta (la differenza sono le armoniche).
    # Con un forno acceso, cioe' un carico resistivo puro, passa da 337 a 351
    # gradi: cos 0,987 contro un fattore di potenza misurato di 0,991.
    "R8114": {
        **scaled(1),
        "name": "Angolo di Sfasamento",
        "unit": DEGREE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8112": {
        **scaled(1000),
        "name": "Corrente Assorbita",
        "device_class": SensorDeviceClass.CURRENT,
        "unit": UnitOfElectricCurrent.AMPERE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
}
