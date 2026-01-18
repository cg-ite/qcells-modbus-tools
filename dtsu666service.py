import argparse
import asyncio
import logging
import sys
import threading
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import load_config
from dtsu666_constants import BLOCK_STATS, REGISTERS
from dtsu666reader import Dtsu666Reader
from homeassistant.dtsu666mqttha import DTSU666MqttHa

_logger = logging.getLogger("dtsu666service")

class Dtsu666Service:

    def __init__(
            self,
            cfg,
            mqtt_client=None,
    ):
        self.reader = None # Dtsu666Reader(cfg['dtsu']) -> falscher thread/event loop bei Aufruf von shelly
        self.dtsu_conf = cfg['dtsu']
        self.interval = cfg['dtsu-service']['dtsu-interval-ms'] / 1000.0
        self.full_interval = cfg['dtsu-service']['full-interval-s']

        self.mqtt_client = mqtt_client

        self._task: asyncio.Task | None = None
        self._running = asyncio.Event()
        self._last_full_read = 0.0

        self._powers_atomic = [0.0, 0.0, 0.0, 0.0]
        self._powers_lock = threading.Lock()

        self._cache_lock = asyncio.Lock()
        self._cache = {
            "timestamp": None,
            "powers": [0,0,0,0],
            "full": None,
        }
        self.setup_logging(cfg["dtsu-service"]["log-level"])

    def setup_logging(self, log_level):
        root = logging.getLogger()

        if root.handlers:
            return  # verhindert doppelte Handler

        fmt = logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s"
        )

        # === Journal / stdout ===
        console = logging.StreamHandler()
        console.setLevel(logging.WARNING)
        console.setFormatter(fmt)
        root.addHandler(console)

        # === Debug-Log-Datei ===
        log_dir = Path("/var/log/dtsu-service")
        log_dir.mkdir(parents=True, exist_ok=True)

        debug_file = RotatingFileHandler(
            log_dir / "debug.log",
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=5,
        )
        debug_file.setLevel(log_level)
        debug_file.setFormatter(fmt)
        root.addHandler(debug_file)

        logging.getLogger("pymodbus").setLevel(logging.WARNING)
        if log_level == logging.DEBUG:
            logging.getLogger("pymodbus.transport").setLevel(logging.DEBUG)
            logging.getLogger("pymodbus.framer").setLevel(logging.DEBUG)

    async def start(self):
        _logger.info("Starting DTSU666 service")
        self.reader = Dtsu666Reader(self.dtsu_conf)
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

    async def _run_loop(self):
        """ Reads the powers every 0.250 sec and all stats every 15 sec """
        _logger.info(f"Polling loop started ({self.interval}s)")

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
                            asyncio.create_task(self._publish_full_read_mqtt(data))

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

    async def _publish_full_read_mqtt(self, data):
        """publishes all data to mqtt"""
        if not self.mqtt_client:
            return

        for block in BLOCK_STATS:
            # Adressen pro block berechnen, count/2 da jede Adresse zwei register lang ist
            addresses = [block['address'] + i * 2 for i in range(block['count']/2)]

            for i, adr in enumerate(addresses):
                value = data['values'][i] * REGISTERS[adr]['factor']
                try:
                    await self.mqtt_client.publish(adr, value)

                except Exception as e:
                    _logger.exception(f"Register: {REGISTERS[adr]['name']}, ex: {e}", e)

    async def _update_cache(self, key, data):
        async with self._cache_lock:
            self._cache[key] = data
            self._cache["timestamp"] = time.time()

        if key == "powers":
            _logger.debug(f"Updating cache: {key}, {data}")
            with self._powers_lock:
                self._powers_atomic = list(data)

    async def get_cache(self):
        async with self._cache_lock:
            return dict(self._cache)

    def get_cache_powers(self):
        # nur primitive Typen → threadsafe genug
        _logger.debug(f"read powers from cache")
        cache = self._cache
        return list(cache.get("powers", [0,0,0,0]))

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", default="config.json",
        help="path to config.json", )

    parser.add_argument(
        "-d", "--debug", default=False,
        action=argparse.BooleanOptionalAction,
        help="sets logging level to debug, for debugging from cmd", )

    parser.add_argument("-m", "--mqtt", default=False,
                        action=argparse.BooleanOptionalAction,
                        help="enables mqtt client for publishing the data to a mqtt server",)
    args = parser.parse_args()

    config = load_config(args.config)
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s",
                       level=config["dtsu-service"]["log-level"], )

    if args.debug:
        logging.getLogger("dtsu666service").setLevel(logging.DEBUG)

    mqtt_cfg = config.get("mqtt")
    mqtt_client = None

    service = Dtsu666Service(
        config,
        mqtt_client=mqtt_client,
    )

    # only start mqtt
    if args.mqtt:
        if mqtt_cfg:
            mqtt_client = DTSU666MqttHa(mqtt_cfg)
            try:
                await mqtt_client.connect()
                await mqtt_client.publish_discovery()
            except Exception as e:
                logging.error(f"Failed to connect to MQTT broker: {e}")
                if not args.debug:
                    return
                logging.info("Continuing in debug mode without MQTT...")
                mqtt_client = None

    else:
        await service.start()

    try:
        # läuft "für immer"
        await asyncio.Event().wait()
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        if args.mqtt:
            if mqtt_client:
                await mqtt_client.disconnect()
        else:
            await service.stop()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
