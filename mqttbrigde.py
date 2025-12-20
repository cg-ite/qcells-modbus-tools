import asyncio
import json
import logging
import time

from config import load_config
from dtsu666_constants import BLOCK_STATS, REGISTERS
from dtsu666reader import Dtsu666Reader

_logger = logging.getLogger("dtsu666service")

from aiomqtt import Client as MQTTClient

def create_mqtt_client(cfg):
    return MQTTClient(
        hostname=cfg["host"],
        port=cfg.get("port", 1883),
        username=cfg["username"],
        password=cfg["password"],
        keepalive=60,
    )

class Dtsu666Service:

    def __init__(
            self,
            cfg,
            interval_ms=250,
            full_interval_s=15,
            mqtt_client=None,
            mqtt_topic="dtsu666/full",
    ):
        self.reader = Dtsu666Reader(cfg['dtsu'])

        self.interval = interval_ms / 1000.0
        self.full_interval = full_interval_s

        self.mqtt_client = mqtt_client
        self.mqtt_prefix = mqtt_topic

        self._task: asyncio.Task | None = None
        self._running = asyncio.Event()
        self._last_full_read = 0.0

        self._cache_lock = asyncio.Lock()
        self._cache = {
            "timestamp": None,
            "powers": [0,0,0,0],
            "full": None,
        }

    async def start(self):
        _logger.info("Starting DTSU666 service")
        await self.reader.connect()

        self._running.set()
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self):
        _logger.info("Stopping DTSU666 service")
        self._running.clear()

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        await  self.reader.close()

    async def _run_loop(self):
        """ Reads the powers every 0.250 sec and all stats every 15 sec """
        _logger.info("Polling loop started (250ms)")

        try:
            while self._running.is_set():
                loop_start = asyncio.get_running_loop().time()
                now = time.monotonic()

                try:
                    if now - self._last_full_read >= self.full_interval:
                        data = await self.reader.read_stats()
                        if data is not None:
                            await self._update_cache("full", data)
                            self._last_full_read = now

                            # 🔹 MQTT async publish (fire & forget)
                            #asyncio.create_task(self._publish_full_read_mqtt(data))

                    else:
                        data = await self.reader.read_actpowers_block()
                        if data is not None:
                            await self._update_cache("powers", data)

                except Exception as e:
                    _logger.exception(f"Polling error e:{e}")

                elapsed = asyncio.get_running_loop().time() - loop_start
                await asyncio.sleep(max(0.0, self.interval - elapsed))

        except asyncio.CancelledError:
            _logger.info("Polling loop cancelled")

    async def _publish(self, topic, payload):
        await self.mqtt_client.publish(
            topic,
            json.dumps(payload),
            qos=1,
            retain=True,
        )

    async def _publish_full_read_mqtt(self, data):
        """publishes all data to mqtt"""
        if not self.mqtt_client:
            return

        for block in BLOCK_STATS:
            # Adressen pro block berechnen, count/2 da jede Adresse zwei register lang ist
            addresses = [block['address'] + i * 2 for i in range(block['count']/2)]

            for i, adr in enumerate(addresses):
                value = block['values'][i] * REGISTERS[adr]['factor']
                try:
                    await self._publish(
                        f"{self.mqtt_prefix}/{REGISTERS[adr]['name']}", {
                        f"{REGISTERS[adr]['name']}": value
                    })

                except Exception as e:
                    _logger.exception(f"Topic: {self.mqtt_prefix}/{REGISTERS[adr]['name']}, ex: {e}", e)

    async def _update_cache(self, key, data):
        async with self._cache_lock:
            self._cache[key] = data
            self._cache["timestamp"] = time.time()

    async def get_cache(self):
        async with self._cache_lock:
            return dict(self._cache)

    def get_cache_powers(self):
        # nur primitive Typen → threadsafe genug
        cache = self._cache
        return list(cache.get("powers", [0,0,0,0]))

async def main():
    config = load_config()

    mqtt_cfg = config.get("mqtt")
    mqtt_client = None

    if mqtt_cfg:
        mqtt_client = create_mqtt_client(mqtt_cfg)
        await mqtt_client.__aenter__()  # aiomqtt Client starten

    service = Dtsu666Service(
        config,
        mqtt_client=mqtt_client,
        mqtt_topic="dtsu666"
    )

    await service.start()

    try:
        # läuft "für immer"
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await service.stop()
        if mqtt_client:
            await mqtt_client.__aexit__(None, None, None)


if __name__ == "__main__":
    asyncio.run(main())
