import argparse
import asyncio
import logging
import socket
import threading
import json
from concurrent.futures import ThreadPoolExecutor

from config import load_config
from dtsu666service import Dtsu666Service

logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)
logger = logging.getLogger("shelly")


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
        logger.debug(f"Received UDP message: {request_str}")
        logger.debug(f"From: {addr[0]}:{addr[1]}")

        try:
            request = json.loads(request_str)
            logger.debug(f"Parsed request: {json.dumps(request, indent=2)}")
            if isinstance(request.get("params", {}).get("id"), int):
                powers = self._powermeter.get_cache_powers()

                if request.get("method") == "EM.GetStatus":
                    response = self._create_em_response(request["id"], powers)
                elif request.get("method") == "EM1.GetStatus":
                    response = self._create_em1_response(request["id"], powers)
                else:
                    return

                response_json = json.dumps(response, separators=(",", ":"))
                logger.debug(f"Sending response: {response_json}")
                response_data = response_json.encode()
                with self._send_lock:
                    sock.sendto(response_data, addr)
        except json.JSONDecodeError:
            logger.error("Error: Invalid JSON")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def udp_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", self._udp_port))
        logger.info(f"Shelly emulator listening on UDP port {self._udp_port}...")

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
    config = load_config()
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s",
                        level=config["logging"]["level"], )
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--debug", default=False,
        action=argparse.BooleanOptionalAction,
        help="sets logging level to debug, for debugging from cmd", )
    args = parser.parse_args()
    if args.debug:
        logging.getLogger("dtsu666service").setLevel(logging.DEBUG)
        logging.getLogger("shelly").setLevel(logging.DEBUG)

    dtsu = Dtsu666Service(config)
    shelly = Shelly(cfg=config, powermeter=dtsu)

    try:
        await dtsu.start()
        shelly.start()
        # läuft "für immer"
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await dtsu.stop()
        shelly.join()
        shelly.stop()
        logger.info("Emulator stopped.")

if __name__ == "__main__":
    asyncio.run(main())
