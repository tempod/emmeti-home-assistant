"""Costanti per l'integrazione Emmeti AQ-IoT."""
from datetime import time
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature, PERCENTAGE, UnitOfPower

DOMAIN = "emmeti_aqiot"
PLATFORMS = ["sensor", "number", "time", "switch", "binary_sensor"]

# Chiavi per i dati salvati nella config entry
CONF_INSTALLATION_ID = "installation_id"
CONF_GROUPS = "groups"
CONF_POLLING_INTERVAL = "polling_interval"
DEFAULT_POLLING_INTERVAL = 30

# Mappa delle entità con una piattaforma specifica (diversa da 'sensor')
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
    "R8672": "binary_sensor",
    "R8683": "switch",
}

# Mappa per la trasformazione dei dati e la configurazione dei sensori
SENSOR_CONFIG_MAP = {
    # Temperature Riscaldamento
    "R8690": {
        "name": "Attenuazione Riscaldamento",
        "transformation": lambda x: x / 100.0,
        "reverse_transformation": lambda x: int(x * 10),
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 0.5,
        "max_value": 5.0,
        "step": 0.1,
    },
    "R8688": {
        "name": "Confort Riscaldamento",
        "transformation": lambda x: x / 100.0,
        "reverse_transformation": lambda x: int(x * 10),
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 8.0,
        "max_value": 30.0,
        "step": 0.1,
    },
    # Temperature Raffrescamento
    "R8686": {
        "name": "Attenuazione Raffrescamento",
        "transformation": lambda x: x / 100.0,
        "reverse_transformation": lambda x: int(x * 10),
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 0.5,
        "max_value": 5.0,
        "step": 0.1,
    },
    "R8684": {
        "name": "Confort Raffrescamento",
        "transformation": lambda x: x / 100.0,
        "reverse_transformation": lambda x: int(x * 10),
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 15.0,
        "max_value": 30.0,
        "step": 0.1,
    },
    # Temperature ACS
    "R16497": {
        "name": "Temp Mantenimento ACS",
        "transformation": lambda x: x / 10.0,
        "reverse_transformation": lambda x: int(x * 10),
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 0.0,
        "max_value": 70.0,
        "step": 0.1,
    },
    "R16494": {
        "name": "Temp Richiesta 1 ACS",
        "transformation": lambda x: x / 10.0,
        "reverse_transformation": lambda x: int(x * 10),
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 0.0,
        "max_value": 70.0,
        "step": 0.1,
    },
    "R16496": {
        "name": "Temp Richiesta 2 ACS",
        "transformation": lambda x: x / 10.0,
        "reverse_transformation": lambda x: int(x * 10),
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 0.0,
        "max_value": 70.0,
        "step": 0.1,
    },
    # Umidità
    "R8660": {
        "name": "Setpoint Umidità Raffrescamento",
        "transformation": lambda x: x,
        "reverse_transformation": lambda x: int(x),
        "device_class": SensorDeviceClass.HUMIDITY,
        "unit": PERCENTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 30.0,
        "max_value": 99.0,
        "step": 1.0,
    },
    "R8661": {
        "name": "Setpoint Umidità Riscaldamento",
        "transformation": lambda x: x,
        "reverse_transformation": lambda x: int(x),
        "device_class": SensorDeviceClass.HUMIDITY,
        "unit": PERCENTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "min_value": 30.0,
        "max_value": 99.0,
        "step": 1.0,
    },
    # Time Riscaldamento
    "R8691": {
        "name": "Orario Attenuazione Riscaldamento",
        "transformation": lambda total_minutes: time(hour=total_minutes // 60, minute=total_minutes % 60),
        "reverse_transformation": lambda time_obj: time_obj.hour * 60 + time_obj.minute,
    },
    "R8689": {
        "name": "Orario Confort Riscaldamento",
        "transformation": lambda total_minutes: time(hour=total_minutes // 60, minute=total_minutes % 60),
        "reverse_transformation": lambda time_obj: time_obj.hour * 60 + time_obj.minute,
    },
    # Time Raffrescamento
    "R8687": {
        "name": "Orario Attenuazione Raffrescamento",
        "transformation": lambda total_minutes: time(hour=total_minutes // 60, minute=total_minutes % 60),
        "reverse_transformation": lambda time_obj: time_obj.hour * 60 + time_obj.minute,
    },
    "R8685": {
        "name": "Orario Confort Raffrescamento",
        "transformation": lambda total_minutes: time(hour=total_minutes // 60, minute=total_minutes % 60),
        "reverse_transformation": lambda time_obj: time_obj.hour * 60 + time_obj.minute,
    },
    # Time ACS
    "R16493": {
        "name": "Orario Richiesta 1 ACS",
        "transformation": lambda total_minutes: time(hour=total_minutes // 60, minute=total_minutes % 60),
        "reverse_transformation": lambda time_obj: time_obj.hour * 60 + time_obj.minute,
    },
    "R16495": {
        "name": "Orario Richiesta 2 ACS",
        "transformation": lambda total_minutes: time(hour=total_minutes // 60, minute=total_minutes % 60),
        "reverse_transformation": lambda time_obj: time_obj.hour * 60 + time_obj.minute,
    },
    # Switch
    "R8676": {
        "name": "Presenza",
        "transformation": lambda x: x == 1,
        "reverse_transformation": lambda state: 1 if state else 0,
    },
    "R16384": {
        "name": "PDC On/Off",
        "transformation": lambda x: x == 1,
        "reverse_transformation": lambda state: 1 if state else 0,
    },
    "R8692": {
        "name": "Boost",
        "transformation": lambda x: x == 1,
        "reverse_transformation": lambda state: 1 if state else 0,
    },
    "R8683": {
        "name": "Freddo\\Caldo",
        "transformation": lambda x: x == 1,
        "reverse_transformation": lambda state: 1 if state else 0,
    },
    # Binary Sensor
    "R9073": {
        "name": "Eco Hot Water",
        "transformation": lambda x: x == 1,
    },
    "R8672": {
        "name": "Finestra",
        "transformation": lambda x: x == 1,
    },
    # Sensori Sola Lettura
    "R8680": {
        "name": "Punto di Rugiada",
        "transformation": lambda x: x / 10.0,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8707": {
        "name": "Temperatura Attuale",
        "transformation": lambda x: x / 10.0,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8704": {
        "name": "Umidità Attuale",
        "transformation": lambda x: x,
        "device_class": SensorDeviceClass.HUMIDITY,
        "unit": PERCENTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R9123": {
        "name": "Potenza Termica",
        "transformation": lambda x: x / 100.0,
        "device_class": SensorDeviceClass.POWER,
        "unit": UnitOfPower.KILO_WATT,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R9120": {
        "name": "Portata",
        "transformation": lambda x: x,
        "unit": "L/h",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8987": {
        "name": "Temperatura Mandata",
        "transformation": lambda x: x / 10.0,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8988": {
        "name": "Temperatura Ritorno",
        "transformation": lambda x: x / 10.0,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8002": {
        "name": "Assorbimento PDC",
        "transformation": lambda x: x / 100.0,
        "device_class": SensorDeviceClass.POWER,
        "unit": UnitOfPower.KILO_WATT,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8005": {
        "name": "Assorbimento ACS",
        "transformation": lambda x: x / 1000.0,
        "device_class": SensorDeviceClass.POWER,
        "unit": UnitOfPower.KILO_WATT,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R9052": {
        "name": "Temperatura Attuale Acqua PDC",
        "transformation": lambda x: x / 10.0,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R9051": {
        "name": "Temperatura Target Acqua PDC",
        "transformation": lambda x: x / 10.0,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R9042": {
        "name": "Temperatura Minima Radiante Acqua PDC",
        "transformation": lambda x: x / 10.0,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8986": {
        "name": "Temperatura Esterna",
        "transformation": lambda x: x / 10.0,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "R8989": {
        "name": "Temperatura Acqua Calda",
        "transformation": lambda x: x / 10.0,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
}