"""modbus-bridge
taken and remixed from: https://github.com/pymodbus-dev/pymodbus/blob/v3.11.3/examples/contrib/serial_forwarder.py

Pymodbus SerialRTU2TCP Forwarder

usage :
uv run modbus-bridge.py
"""
import asyncio
import logging
import signal
import sys
import threading
import time
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pymodbus import ModbusDeviceIdentification, ExceptionResponse
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusIOException
from pymodbus.framer import FramerType
from pymodbus.datastore import ModbusServerContext
from pymodbus.datastore.remote import RemoteDeviceContext
from pymodbus.pdu import ModbusPDU
from pymodbus.pdu.register_message import ReadInputRegistersResponse
from pymodbus.server import ModbusTcpServer, StartAsyncTcpServer

from config import load_config

_logger = logging.getLogger("modbus-bridge")

# def raise_graceful_exit(*_args):
#     """Enters shutdown mode"""
#     _logger.info("receiving shutdown signal now")
#     raise SystemExit
#
# def handle_sigint():
#     _logger.info("Shutdown requested")
    #server.stop_event.set()

class SerialForwarderTCPServer:
    """SerialRTU2TCP Forwarder Server"""

    def __init__(self, cfg):
        """Initialize the server"""
        self.server = None
        self.cfg = cfg
        self.stop_event = asyncio.Event()

        self.server_task = None
        self.stop_event = asyncio.Event()
        self.setup_logging(cfg["log-level"])
        self.runmode = None

        raw_client = ModbusSerialClient(framer=FramerType.RTU,
                                    port=self.cfg["rtu-port"],
                                    baudrate=self.cfg["rtu-baudrate"],
                                    bytesize=self.cfg["rtu-bytesize"],
                                    parity=self.cfg["rtu-parity"],
                                    stopbits=self.cfg["rtu-stopbits"],
                                    timeout = 1.2,  # > 1s Response timeout laut Doku
                                    retries = 1,  # KEINE Wiederholungen (sonst Timing kaputt)
                                    )
        client = ThrottledSerialClient(raw_client, delay=0.02)

        message = f"RTU bus on {self.cfg["rtu-port"]} - baudrate {self.cfg["rtu-baudrate"]}"
        _logger.info(message)
        store = {}
        for i in self.cfg["device_ids"]:
            unit_id = int(i)
            _logger.info(f"added device id: {unit_id}")
            store[unit_id] = RemoteDeviceContext(client, device_id=unit_id)
        context = ModbusServerContext(devices=store, single=False)

        # identity
        self.identity = ModbusDeviceIdentification()
        self.identity.VendorName = "modbus bridge"
        self.identity.ProductCode = "mbus-bridge"
        self.identity.VendorUrl = "https://github.com/cg-ite/qcells-modbus-tools"
        self.identity.ProductName = "Modbus RTU to TCP bridge"

        self.server = ModbusTcpServer(
            context=context,
            address=(self.cfg["tcp-ip"], self.cfg["tcp-port"]),
        )

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
        log_dir = Path("/var/log/modbus-bridge")
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
        """Run the server"""
        message = f"starting bridge on {self.cfg["tcp-ip"]} port {self.cfg["tcp-port"]}"
        _logger.info(message)
        message = f"listening to device_ids {self.server.context.device_ids()}"
        _logger.info(message)
        #await self.server.serve_forever()
        self.server_task = asyncio.create_task(self.server.serve_forever())
        _logger.info(f"bridge started")

    async def stop(self):
        """Stop the server"""
        _logger.info(f"modbus bridge stopping")
        self.stop_event.set()

        # cancel running tasks
        if self.server_task:
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass
            _logger.info("TCP server is down")

class ThrottledSerialClient:
    def __init__(self, client, delay=0.02):
        self.client = client
        self.delay = delay
        self.lock = threading.Lock()
        self.runmode = Runmode.WAIT_MODE

    def read_input_registers(self, *args, **kwargs):
        with self.lock:
            try:
                # address & count extrahieren
                address = args[0] if len(args) > 0 else kwargs.get("address")
                count = args[1] if len(args) > 1 else kwargs.get("count", 1)

                result = self.client.read_input_registers(*args, **kwargs)
                time.sleep(self.delay)
                if not isinstance(result, ReadInputRegistersResponse):
                    _logger.warning(f"Read error: no RegisterResponse @ {address}")
                    return None
                if not result or result.isError():
                    error_code = self.check_exception(result)
                    if error_code is not None:
                        _logger.warning(f"Read error: isError @ {address} Error-code:{error_code}")
                        return result

                if address <= 0x040F < address + count:
                    idx = 0x040F - address
                    self.runmode = result.registers[idx]
                    _logger.debug(f"Runmode:{self.runmode}")

                return result
            except Exception as e:
                if self.runmode == Runmode.NORMAL_MODE:
                    _logger.error(f"Read error: Exception {e} ")
                return ExceptionResponse(0x00, 0x04)

    def read_holding_registers(self, *args, **kwargs):
        with self.lock:
            try:
                result = self.client.read_holding_registers(*args, **kwargs)
                time.sleep(self.delay)
                return result

            except ModbusIOException as e:
                if self.runmode == Runmode.NORMAL_MODE:
                    _logger.error(f"Read error: Exception {e} ")
                # saubere Modbus-Exception zurückgeben
                return ExceptionResponse(0x00, 0x04)
        """exceptions = {
            0x01: "Illegal Function - Function code not supported",
            0x02: "Illegal Data Address - Address not allowed",
            0x03: "Illegal Data Value - Value out of range",
            0x04: "Slave Device Failure - Device error",
            0x05: "Acknowledge - Request accepted, processing",
            0x06: "Slave Device Busy - Try again later",
            0x08: "Memory Parity Error - Device memory error",
            0x0A: "Gateway Path Unavailable - Gateway error",
            0x0B: "Gateway Target Failed - Target not responding"
        }"""

    def __getattr__(self, name):
        # alles andere direkt durchreichen (connect, close, etc.)
        return getattr(self.client, name)

class Runmode(Enum):
    """ Status mode of the Inverter"""
    WAIT_MODE = 0
    CHECK_MODE = 1
    NORMAL_MODE = 2
    FAULT_MODE = 3
    PERMANENT_FAULT_MODE = 4

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", default="config.json",
        help="path to config.json", )
    args = parser.parse_args()

    config = load_config(args.config)
    # logging.basicConfig(
    #     level=config["modbus-bridge"]["log-level"],
    #     format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    # )
    server = SerialForwarderTCPServer(cfg=config["modbus-bridge"])

    # -----------------------------
    # Start des Emulators
    # -----------------------------
    await server.start()

    # -----------------------------
    # Shutdown-Handler (SIGINT/SIGTERM)
    # -----------------------------
    stop_event = asyncio.Event()

    def shutdown_handler(*args):
        logging.info("Shutdown signal received...")
        stop_event.set()

    # Signalhandler registrieren
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, shutdown_handler)
    loop.add_signal_handler(signal.SIGTERM, shutdown_handler)

    # Warten, bis Stopp-Signal kommt
    try:
        await stop_event.wait()
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    # Server stoppen
    await server.stop()

    logging.info("Shutdown complete.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _logger.info("CTRL+C: modbus bridge exiting.")