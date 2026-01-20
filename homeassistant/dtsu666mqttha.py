import json
from aiomqtt import Client as MQTTClient

from dtsu666_constants import REGISTERS


def create_mqtt_client(cfg):
    """
    Erstellt einen aiomqtt-Client.

    :param cfg: Ein Wörterbuch mit Konfigurationseinstellungen für den MQTT-Client.
                Erwartete Keys: 'host', 'username', 'password', 'port' (optional).
    :return: Ein instanziierter MQTTClient, konfiguriert mit den angegebenen Einstellungen.
    """
    return MQTTClient(
        hostname=cfg["host"],
        port=cfg.get("port", 1883),
        username=cfg["username"],
        password=cfg["password"],
        keepalive=60,
        timeout=cfg.get("timeout", 10),
    )


class DTSU666MqttHa:
    def __init__(self, cfg):
        self.client = create_mqtt_client(cfg)
        self.device = dtsu666_device()

        self.discovery_prefix = "homeassistant"
        self.availability_topic = f"{self.get_mqtt_prefix()}/availability"


    async def connect(self):
        await self.client.__aenter__()

    async def disconnect(self):
        await self.client.__aexit__(None, None, None)

    # ---------- Discovery ----------
    async def publish_discovery(self):
        for s in DTSU_SENSORS:
            component = s.get("component", "sensor")
            topic = (
                f"{self.discovery_prefix}/"
                f"{component}/dtsu666/{s["topic"]}/config"
            )
            s["available"] = False
            await self.client.publish(topic, json.dumps(s), retain=True)

    # ---------- Availability ----------
    def set_availability(self, online: bool):
        self.client.publish(
            self.availability_topic,
            "online" if online else "offline",
            retain=True,
        )

    def get_mqtt_prefix(self):
        return self.device['model']
    def get_mqtt_topic(self, address):
        return REGISTERS[address]['name']

    # ---------- Data ----------
    async def publish(self, address, value):
        await self.client.publish(
            f"{self.get_mqtt_prefix()}/{self.get_mqtt_topic(address)}",
            json.dumps({
                f"{self.get_mqtt_topic(address)}": value
            }),
            qos=1,
            retain=True,
        )

    # ---------- Diagnostic ----------
    def publish_diagnostic(self, code, **extra):
        payload = {
            "code": code,
            "error": MODBUS_EXCEPTIONS[code],
            **extra,
        }
        self.client.publish(
            f"{self.get_mqtt_prefix()}/Modbus/Diagnostic",
            json.dumps(payload),
            qos=1,
            retain=True, )


class ModbusHealth:
    def __init__(self, ha):
        self.ha = ha
        self.state = "ok"

    def ok(self):
        if self.state != "ok":
            self.state = "ok"
            self.ha.client.publish(
                "DTSU666/Modbus/Health",
                "ok",
                retain=True,
            )

    def error(self):
        if self.state != "error":
            self.state = "error"
            self.ha.client.publish(
                "DTSU666/Modbus/Health",
                "error",
                retain=True,
            )


def generate_phase_sensors():
    """ generates the sensor json for auto discovery """
    sensors = []

    for key, reg in REGISTERS.items():
        sensors.append({
            "topic": f"{reg['name'].lower()}",
            "unique_id": f"{dtsu666_device()['identifiers'][0]}_{reg['name'].lower()}",
            "entity_id": f"sensor.{dtsu666_device()['identifiers'][0]}_{reg['name'].lower()}",
            "component": "sensor",
            "name": f"{reg['name'].replace('_', ' ').title()}",
            "state_topic": f"{dtsu666_device()['model']}/{reg['name']}",
            "device_class": reg['device_class'],
            "unit_of_measurement": reg.get("unit"),
            "state_class": "measurement",
            "value_template": f"{{{{ value_json.{reg['name']} }}}}",
            "force_update": reg.get("force_update", False),
            "device": dtsu666_device(),
            "has_entity_name": True,
        })

    return sensors


def dtsu666_device():
    """
    Erzeugt ein Gerätedaten-Dictionary für den Smart Meter DTSU666.

    :return: Ein Wörterbuch mit Informationen über das Gerät,
             einschließlich Identifikatoren, Hersteller, Modell,
             Softwareversion und Name.
    :rtype: dict
    """
    return {
        "identifiers": ["dtsu666"],
        "manufacturer": "Huawei",
        "model": "DTSU666",
        "sw_version": "1.0",
        "name": "Smart Meter DTSU666",
    }



DTSU_SENSORS = [
    # ---- Diagnostic ----
    {
        "topic": "modbus_diagnostic",
        "unique_id": f"{dtsu666_device()['identifiers'][0]}_modbus_diagnostic",
        "name": "Modbus Diagnose",
        "component": "sensor",
        "state_topic": f"{dtsu666_device()['model']}/Modbus/Diagnostic",
        "value_template": "{{ value_json.error }}",
        "entity_category": "diagnostic",
        "device": dtsu666_device(),
        "has_entity_name": True,
    },

    # ---- Connectivity ----
    {
        "component": "binary_sensor",
        "topic": "modbus_connectivity",
        "unique_id": f"{dtsu666_device()['identifiers'][0]}_modbus_connectivity",
        "name": "Modbus Verbindung",
        "state_topic": f"{dtsu666_device()['model']}/Modbus/Health",
        "payload_on": "ok",
        "payload_off": "error",
        "device_class": "connectivity",
        "device": dtsu666_device(),
        "has_entity_name": True,
    },
    *generate_phase_sensors(),

    # Non-phase Sensors (Frequency, Totals, Energy)
    {
        "topic": "frequency",
        "unique_id": f"{dtsu666_device()['identifiers'][0]}_frequency",
        "name": "Frequency",
        "state_topic": f"{dtsu666_device()['model']}/Frequency",
        "device_class": "frequency",
        "unit_of_measurement": "Hz",
        "state_class": "measurement",
        "value_template": "{{ value_json.Frequency }}",
        "device": dtsu666_device(),
        "has_entity_name": True,
    },
]

MODBUS_EXCEPTIONS = {
    0x01: "Illegal Function - Function code not supported",
    0x02: "Illegal Data Address - Address not allowed",
    0x03: "Illegal Data Value - Value out of range",
    0x04: "Slave Device Failure - Device error",
    0x05: "Acknowledge - Request accepted, processing",
    0x06: "Slave Device Busy - Try again later",
    0x08: "Memory Parity Error - Device memory error",
    0x0A: "Gateway Path Unavailable - Gateway error",
    0x0B: "Gateway Target Failed - Target not responding"
}
