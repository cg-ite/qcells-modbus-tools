import asyncio
import contextlib
import json
import logging
import time

from aiomqtt import Client as MQTTClient
from aiomqtt import MqttError

from dtsu666_constants import REGISTERS

_logger = logging.getLogger("dtsu666mqttha")


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
        max_queued_outgoing_messages=cfg.get("max_queued_outgoing_messages", 1),
        max_inflight_messages=cfg.get("max_inflight_messages", 1),
        max_concurrent_outgoing_calls=cfg.get("max_concurrent_outgoing_calls", 1),
    )


def get_cfg_float(cfg, key, default):
    return cfg.get(key, cfg.get(key.replace("_", "-"), default))


class DTSU666MqttHa:
    def __init__(self, cfg):
        self.cfg = cfg
        self.client = create_mqtt_client(cfg)
        self.device = dtsu666_device()

        self.discovery_prefix = "homeassistant"
        self.availability_topic = f"{self.get_mqtt_prefix()}/availability"

        self.connected = False
        self.publish_timeout = get_cfg_float(cfg, "publish_timeout", 1.0)
        self.reconnect_interval = get_cfg_float(cfg, "reconnect_interval", 30.0)
        self.offline_until = 0.0
        self._client_entered = False
        self._publish_lock = asyncio.Lock()
        self._connect_lock = asyncio.Lock()


    async def connect(self):
        await self.client.__aenter__()
        self.connected = True
        self._client_entered = True
        self.offline_until = 0.0

    async def disconnect(self):
        self.connected = False
        if self._client_entered:
            with contextlib.suppress(Exception):
                await self.client.__aexit__(None, None, None)
        self._client_entered = False

    async def _ensure_connected(self):
        if self.connected:
            return True

        now = time.monotonic()
        if now < self.offline_until:
            return False

        if self._connect_lock.locked():
            return False

        async with self._connect_lock:
            if self.connected:
                return True

            if self._client_entered:
                with contextlib.suppress(Exception):
                    await self.client.__aexit__(None, None, None)
                self._client_entered = False
            self.client = create_mqtt_client(self.cfg)
            try:
                await self.client.__aenter__()
            except Exception as exc:
                self._mark_offline(exc)
                return False

            self.connected = True
            self._client_entered = True
            self.offline_until = 0.0
            _logger.info("Reconnected to MQTT broker.")
            return True

    def _mark_offline(self, exc):
        self.connected = False
        self.offline_until = time.monotonic() + self.reconnect_interval
        _logger.warning(
            "MQTT broker unavailable, dropping publishes for %.1fs: %s",
            self.reconnect_interval,
            exc,
        )

    async def _publish(self, topic, payload, qos=0, retain=False):
        if self._publish_lock.locked():
            return False

        if not await self._ensure_connected():
            return False

        async with self._publish_lock:
            try:
                await self.client.publish(
                    topic,
                    payload,
                    qos=qos,
                    retain=retain,
                    timeout=self.publish_timeout,
                )
                return True
            except (MqttError, asyncio.TimeoutError, OSError) as exc:
                self._mark_offline(exc)
                return False
            except Exception as exc:
                self._mark_offline(exc)
                return False

    def _publish_background(self, topic, payload, qos=0, retain=False):
        try:
            asyncio.get_running_loop().create_task(
                self._publish(topic, payload, qos=qos, retain=retain)
            )
        except RuntimeError:
            _logger.debug("No running event loop, dropping MQTT publish for %s", topic)

    # ---------- Discovery ----------
    async def publish_discovery(self):
        for s in DTSU_SENSORS:
            component = s.get("component", "sensor")
            topic = (
                f"{self.discovery_prefix}/"
                f"{component}/dtsu666/{s["topic"]}/config"
            )
            s["available"] = False
            await self._publish(topic, json.dumps(s), retain=True)

    # ---------- Availability ----------
    def set_availability(self, online: bool):
        self._publish_background(
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
        await self._publish(
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
        self._publish_background(
            f"{self.get_mqtt_prefix()}/Modbus/Diagnostic",
            json.dumps(payload),
            qos=1,
            retain=True,
        )


class ModbusHealth:
    def __init__(self, ha):
        self.ha = ha
        self.state = "ok"

    def ok(self):
        if self.state != "ok":
            self.state = "ok"
            self.ha._publish_background(
                "DTSU666/Modbus/Health",
                "ok",
                retain=True,
            )

    def error(self):
        if self.state != "error":
            self.state = "error"
            self.ha._publish_background(
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
            "state_class": reg.get("state_class", "measurement"),
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
