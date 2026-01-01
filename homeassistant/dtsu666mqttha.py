import json
from aiomqtt import Client as MQTTClient

from dtsu666_constants import REGISTERS

def create_mqtt_client(cfg):
    return MQTTClient(
        hostname=cfg["host"],
        port=cfg.get("port", 1883),
        username=cfg["username"],
        password=cfg["password"],
        keepalive=60,
    )

class DTSU666MqttHa:
    def __init__(self, cfg, client_id="dtsu666"):

        self.client = create_mqtt_client(cfg)

        self.discovery_prefix = "homeassistant"
        self.availability_topic = "DTSU666/availability"

        self.device = {
            "identifiers": ["dtsu666_modbus"],
            "name": "Smart Meter DTSU666",
            "manufacturer": "Huawei",
            "model": "DTSU666",
            "sw_version": "1.0",
        }

    async def connect(self):
        await self.client.__aenter__()

    async  def disconnect(self):
        await self.client.__aexit__(None, None, None)

    # ---------- Discovery ----------
    def publish_discovery(self):
        for s in DTSU_SENSORS:
            component = s.get("component", "sensor")
            object_id = s["object_id"]

            topic = (
                f"{self.discovery_prefix}/"
                f"{component}/dtsu666/{object_id}/config"
            )

            payload = {
                "name": s["name"],
                "unique_id": f"dtsu666_{object_id}",
                "state_topic": s["state_topic"],
                "availability_topic": self.availability_topic,
                "payload_available": "online",
                "payload_not_available": "offline",
                "device": self.device,
            }
            if component == "binary_sensor":
                payload["payload_on"] = s["payload_on"]
                payload["payload_off"] = s["payload_off"]

            if "device_class" in s:
                payload["device_class"] = s["device_class"]
            if "unit" in s:
                payload["unit_of_measurement"] = s["unit"]
            if "state_class" in s:
                payload["state_class"] = s["state_class"]
            if "value_template" in s:
                payload["value_template"] = s["value_template"]
            if "entity_category" in s:
                payload["entity_category"] = s["entity_category"]

            self.client.publish(topic, json.dumps(payload), retain=True)

    # ---------- Availability ----------
    def set_availability(self, online: bool):
        self.client.publish(
            self.availability_topic,
            "online" if online else "offline",
            retain=True,
        )

    # ---------- Data ----------
    async def publish(self, topic, payload):
        await self.client.publish(
            topic,
            json.dumps(payload),
            qos=1,
            retain=True,
        )

    # ---------- Diagnostic ----------
    def publish_diagnostic(self, code,  **extra):
        payload = {
            "code": code,
            "error": MODBUS_EXCEPTIONS[code],
            **extra,
        }
        self.publish("DTSU666/Modbus/Diagnostic", payload)

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
            "object_id": f"{reg['name'].lower()}",
            "name": f"Smart Meter DTSU666 {reg['name'].replace('_', ' ')}",
            "state_topic": f"DTSU666/{reg['name']}",
            "device_class": reg['device_class'],
            "unit": reg.get("unit"),
            "state_class": "measurement",
            "value_template": f"{{{{ value_json.{reg['name']} }}}}",
            "force_update": reg.get("force_update", False),
        })

    return sensors

DTSU_SENSORS = [
    # ---- Diagnostic ----
    {
        "object_id": "modbus_diagnostic",
        "name": "Smart Meter DTSU666 Modbus Diagnose",
        "component": "sensor",
        "state_topic": "DTSU666/Modbus/Diagnostic",
        "value_template": "{{ value_json.error }}",
        "entity_category": "diagnostic",
    },

    # ---- Connectivity ----
    {
        "component": "binary_sensor",
        "object_id": "modbus_connectivity",
        "name": "Smart Meter DTSU666 Modbus Verbindung",
        "state_topic": "DTSU666/Modbus/Health",
        "payload_on": "ok",
        "payload_off": "error",
        "device_class": "connectivity",
    },
    *generate_phase_sensors(),

    # Non-phase Sensors (Frequency, Totals, Energy)
    {
        "object_id": "frequency",
        "name": "Smart Meter DTSU666 Frequency",
        "state_topic": "DTSU666/Frequency",
        "device_class": "frequency",
        "unit": "Hz",
        "state_class": "measurement",
        "value_template": "{{ value_json.Frequency }}",
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