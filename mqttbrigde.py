import asyncio
import json
import logging
import time

_logger = logging.getLogger("dtsu666service")

from asyncio_mqtt import Client as MQTTClient

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
            reader,
            interval_ms=250,
            full_interval_s=15,
            mqtt_client=None,
            mqtt_topic="dtsu666/full",
    ):
        self.reader = reader

        self.interval = interval_ms / 1000.0
        self.full_interval = full_interval_s

        self.mqtt_client = mqtt_client
        self.mqtt_topic = mqtt_topic

        self._task: asyncio.Task | None = None
        self._running = asyncio.Event()
        self._last_full_read = 0.0

        self._cache_lock = asyncio.Lock()
        self._cache = {
            "timestamp": None,
            "powers": None,
            "full": None,
        }

    # --------------------------------------------------

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

        self.reader.close()

    # --------------------------------------------------
    # Single polling loop
    # --------------------------------------------------

    async def _run_loop(self):
        _logger.info("Polling loop started (250ms)")

        try:
            while self._running.is_set():
                loop_start = asyncio.get_running_loop().time()
                now = time.monotonic()

                try:
                    if now - self._last_full_read >= self.full_interval:
                        data = await self.reader.read_values()
                        if data is not None:
                            await self._update_cache("full", data)
                            self._last_full_read = now

                            # 🔹 MQTT async publish (fire & forget)
                            asyncio.create_task(self._publish_full_read_mqtt(data))

                    else:
                        data = await self.reader.read_actpowers_block()
                        if data is not None:
                            await self._update_cache("powers", data)

                except Exception:
                    _logger.exception("Polling error")

                elapsed = asyncio.get_running_loop().time() - loop_start
                await asyncio.sleep(max(0, self.interval - elapsed))

        except asyncio.CancelledError:
            _logger.info("Polling loop cancelled")

    async def _publish_full_read_mqtt(self, data):
        if not self.mqtt_client:
            return

        payload = {
            "timestamp": time.time(),
            "values": data,
        }

        try:
            await self.mqtt_client.publish(
                self.mqtt_topic,
                json.dumps(payload),
                qos=1,
            )
        except Exception:
            _logger.exception("MQTT publish failed")

        # --------------------------------------------------
        # Cache
        # --------------------------------------------------

    async def _update_cache(self, key, data):
        async with self._cache_lock:
            self._cache[key] = data
            self._cache["timestamp"] = time.time()

    async def get_cache(self):
        async with self._cache_lock:
            return dict(self._cache)
