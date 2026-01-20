import argparse
import asyncio
import logging
import socket
import sys
import threading
import json
from concurrent.futures import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import load_config
from dtsu666service import Dtsu666Service
from homeassistant.dtsu666mqttha import DTSU666MqttHa

_logger = logging.getLogger("shelly")

def _calculate_derived_values(power):
    decimal_point_enforcer = 0.001
    if abs(power) < 0.1:
        return decimal_point_enforcer

    return round(
        power
        + (decimal_point_enforcer if power == round(power) or power == 0 else 0),
        1,
    )


class Shelly:
    """
        Shelly 3em Pro Emulator taken from b2500-meter
        it uses the unofficial udp rpc json api of the shelly
        I swaped out the powermeters for my dtsu666reader
    """

    def __init__(
        self,
        cfg,
        powermeter: Dtsu666Service
    ):
        self._udp_port = cfg["shelly"]["udp_port"]
        self._device_id = cfg["shelly"]["device_id"]
        self._powermeter = powermeter
        self._udp_thread = None
        self._stop = False
        self._value_mutex = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=5)
        self._send_lock = threading.Lock()
        self.setup_logging(cfg["shelly"]["log-level"])

    def setup_logging(self, log_level):
        root = logging.getLogger()
        root.setLevel(log_level)

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
            log_dir / "shelly-debug.log",
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=5,
        )
        debug_file.setLevel(logging.DEBUG)
        debug_file.setFormatter(fmt)
        root.addHandler(debug_file)

        logging.getLogger("pymodbus").setLevel(logging.WARNING)
        if log_level == logging.DEBUG:
            logging.getLogger("pymodbus.transport").setLevel(logging.DEBUG)
            logging.getLogger("pymodbus.framer").setLevel(logging.DEBUG)


    def _create_em_response(self, request_id, powers):
        if powers is None:
            powers = [0, 0, 0, 0]

        total_act_power = _calculate_derived_values(powers[0])
        a = _calculate_derived_values(powers[1])
        b = _calculate_derived_values(powers[2])
        c = _calculate_derived_values(powers[3])

        return {
            "id": request_id,
            "src": self._device_id,
            "dst": "unknown",
            "result": {
                "a_act_power": a,
                "b_act_power": b,
                "c_act_power": c,
                "total_act_power": total_act_power,
                "a_freq": 50.00,
                "b_freq": 50.00,
                "c_freq": 50.00,
                "a_pf": 1.00,
                "b_pf": 1.00,
                "c_pf": 1.00,
                "a_current": _calculate_derived_values(a/230),
                "b_current": _calculate_derived_values(b/230),
                "c_current": _calculate_derived_values(c/230),
            },
        }

    def _create_em1_response(self, request_id, powers):
        if powers is None:
            powers = [0, 0, 0, 0]

        total_act_power = _calculate_derived_values(powers[0])

        return {
            "id": request_id,
            "src": self._device_id,
            "dst": "unknown",
            "result": {
                "act_power": total_act_power,
            },
        }

    def _handle_request(self, sock, data, addr):
        request_str = data.decode()
        _logger.debug(f"Received UDP message: {request_str}")
        _logger.debug(f"From: {addr[0]}:{addr[1]}")

        try:
            request = json.loads(request_str)
            _logger.debug(f"Parsed request: {json.dumps(request, indent=2)}")
            if isinstance(request.get("params", {}).get("id"), int):
                powers = self._powermeter.get_cache_powers()

                if request.get("method") == "EM.GetStatus":
                    response = self._create_em_response(request["id"], powers)
                elif request.get("method") == "EM1.GetStatus":
                    response = self._create_em1_response(request["id"], powers)
                else:
                    return

                response_json = json.dumps(response, separators=(",", ":"))
                _logger.debug(f"Sending response: {response_json}")
                response_data = response_json.encode()
                with self._send_lock:
                    sock.sendto(response_data, addr)
        except json.JSONDecodeError:
            _logger.error("Error: Invalid JSON")
        except Exception as e:
            _logger.error(f"Error processing message: {e}")

    def udp_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", self._udp_port))
        _logger.info(f"Shelly emulator listening on UDP port {self._udp_port}...")

        try:
            while not self._stop:
                data, addr = sock.recvfrom(1024)
                self._executor.submit(self._handle_request, sock, data, addr)

        finally:
            sock.close()

    def start(self):
        if self._udp_thread:
            return
        self._stop = False
        self._udp_thread = threading.Thread(target=self.udp_server)
        self._udp_thread.start()

    def join(self):
        if self._udp_thread:
            self._udp_thread.join()

    def stop(self):
        self._stop = True
        if self._udp_thread:
            self._udp_thread.join()
            self._udp_thread = None
        self._executor.shutdown(wait=True)

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
                        help="enables mqtt client for publishing the data to a mqtt server", )

    parser.add_argument("-t", "--test-mqtt", default=False,
                        action=argparse.BooleanOptionalAction,
                        help="runs the loop 3 times with example data to test mqtt publish", )

    args = parser.parse_args()

    config = load_config(args.config)
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s",
                        level=config["logging"]["level"], )

    if args.debug:
        logging.getLogger("dtsu666service").setLevel(logging.DEBUG)
        logging.getLogger("shelly").setLevel(logging.DEBUG)

    mqtt_cfg = config.get("mqtt")
    mqtt_client = None

    if (args.mqtt or args.test_mqtt) and mqtt_cfg:
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

    dtsu = Dtsu666Service(config,
                          mqtt_client=mqtt_client,
                          test_mode=args.test_mqtt)
    shelly = Shelly(cfg=config, powermeter=dtsu)

    try:
        await dtsu.start()
        shelly.start()
        # läuft "für immer"
        await asyncio.Event().wait()
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        await dtsu.stop()
        shelly.join()
        shelly.stop()
        _logger.info("Emulator stopped.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
