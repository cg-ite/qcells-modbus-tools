"""modbus-bridge
taken and remixed from: https://github.com/pymodbus-dev/pymodbus/blob/v3.11.3/examples/contrib/serial_forwarder.py

Pymodbus SerialRTU2TCP Forwarder

usage :
uv run modbus-bridge.py
"""
import asyncio
import logging
import signal
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pymodbus import ModbusDeviceIdentification
from pymodbus.client import ModbusSerialClient
from pymodbus.framer import FramerType
from pymodbus.datastore import ModbusServerContext
from pymodbus.datastore.remote import RemoteDeviceContext
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

        client = ModbusSerialClient(framer=FramerType.RTU,
                                    port=self.cfg["rtu-port"],
                                    baudrate=self.cfg["rtu-baudrate"],
                                    bytesize=self.cfg["rtu-bytesize"],
                                    parity=self.cfg["rtu-parity"],
                                    stopbits=self.cfg["rtu-stopbits"],
                                    timeout = 1.2,  # > 1s Response timeout laut Doku
                                    retries = 0,  # KEINE Wiederholungen (sonst Timing kaputt)
                                    )

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
        root.setLevel(logging.DEBUG)

        fmt = logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s"
        )

        # === Journal / stdout ===
        console = logging.StreamHandler()
        console.setLevel(log_level)
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
        debug_file.setLevel(logging.DEBUG)
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

async def main():
    config = load_config()
    logging.basicConfig(
        level=config["modbus-bridge"]["log-level"],
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
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
    await stop_event.wait()
    # Server stoppen
    await server.stop()

    logging.info("Shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _logger.info("CTRL+C: modbus bridge exiting.")