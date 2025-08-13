"""Costanti per l'integrazione Emmeti AQ-IoT."""
from datetime import time
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature

DOMAIN = "emmeti_aqiot"
PLATFORMS = ["sensor", "number", "time", "switch"]

# Chiavi per i dati salvati nella config entry
CONF_INSTALLATION_ID = "installation_id"
CONF_GROUPS = "groups"

# Mappa delle entità che possono essere scritte.
WRITABLE_ENTITIES = {
    "R8684": "number",
    "R8685": "time",
    "R8683": "switch",
}

# Mappa per la trasformazione dei dati e la configurazione dei sensori
SENSOR_CONFIG_MAP = {
    # Temperature
    "R8684": {
        "transformation": lambda x: x / 100.0,
        "reverse_transformation": lambda x: int(x * 10),
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8986": {
        "transformation": lambda x: x / 10.0,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8987": {
        "transformation": lambda x: x / 10.0,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8988": {
        "transformation": lambda x: x / 10.0,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8989": {
        "transformation": lambda x: x / 10.0,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    # Time
    "R8685": {
        "transformation": lambda total_minutes: time(hour=total_minutes // 60, minute=total_minutes % 60),
        "reverse_transformation": lambda time_obj: time_obj.hour * 60 + time_obj.minute,
    },
    # Switch
    "R8683": {
        "transformation": lambda x: x == 1,
        "reverse_transformation": lambda state: 1 if state else 0,
    },
}