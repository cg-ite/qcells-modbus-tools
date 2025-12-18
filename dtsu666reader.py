#!/usr/bin/env python3
import argparse
import asyncio
import logging
import signal
from pymodbus.pdu.register_message import ReadHoldingRegistersResponse
import pymodbus.client as ModbusClient
from pymodbus import (
    FramerType,
)

from config import load_config
from dtsu666_constants import FOUR_WIRE_KEYS, REGISTERS, ACTIVE_POWER_PHASE_A, ACTIVE_POWER_ALL

CONFIG_FILE = "config.json"
_logger = logging.getLogger("dtsu666reader")

# --------------------------------------------------------------------------- #
# Logging configuration
# --------------------------------------------------------------------------- #

class Dtsu666Reader:
    """Reader class for Chint DTSU666 energy meter"""

    def __init__(self, cfg):
        self.device_id = cfg["device_id"]
        self.instrument = ModbusClient.AsyncModbusSerialClient(
            framer=FramerType.RTU,
            port=cfg["port"],
            timeout=cfg["timeout"],
            baudrate=cfg["baudrate"],
            parity=cfg["parity"],
            stopbits=cfg["stopbits"],
            bytesize=8,
            # retries=3,
            # handle_local_echo=False,
        )

    async def connect(self):
        await self.instrument.connect()
        if not self.instrument.connected:
            _logger.error("Could not connect to DTSU666 serial port.")
            return
        _logger.info("Connected to DTSU666 serial port.")

    def close(self):
        self.instrument.close()
        _logger.info("Close connection to DTSU666 serial port.")

    async def read_actpowers_block(self):
        """ reads the act-power values with one modbus query for the shelly """
        address = ACTIVE_POWER_ALL
        data = []
        spec = REGISTERS[address]
        try:
            rr = await self.instrument.read_holding_registers(address,
                                                              count=8,
                                                              device_id=self.device_id)

            if not isinstance(rr, ReadHoldingRegistersResponse):
                return None
            if not rr or rr.isError():
                _logger.warning(f"Read error from DTSU666 @ {address}")
                return None

            raw = self.instrument.convert_from_registers(
                rr.registers, word_order='big',
                data_type = self.instrument.DATATYPE.FLOAT32)
            data = [spec["factor"] * p for p in raw]
        except Exception as e:
            print(f"Read error {address}: {e}")
            data = None
        return data

    async def read_values(self, count=1):
        """Reads the most important values from the DTSU666"""
        data = {}
        for address in FOUR_WIRE_KEYS:
            try:
                spec = REGISTERS[address]
                rr = await self.instrument.read_holding_registers(address,
                                                                  count=spec["words"],
                                                                  device_id=self.device_id)

                if not isinstance(rr, ReadHoldingRegistersResponse):
                    continue
                if not rr or rr.isError():
                    _logger.warning(f"Read error from DTSU666 @ {address}")
                    return [0] * count

                raw = self.instrument.convert_from_registers(
                    rr.registers, word_order='big',
                    data_type=self.instrument.DATATYPE.FLOAT32,
                    string_encoding="ascii")
                data[address] = raw * spec["factor"]
            except Exception as e:
                print(f"Read error {address}: {e}")
                data[address] = None
        return data

    async def read_values2(self, count=1):
            """Reads the most important values from the DTSU666"""
            data = {}
            address = 0x2013
            try:
                rr = await self.instrument.read_holding_registers(address,
                                                                  count=8,
                                                                  device_id=self.device_id)

                if not isinstance(rr, ReadHoldingRegistersResponse):
                    return
                if not rr or rr.isError():
                    _logger.warning(f"Read error from DTSU666 @ {address}")
                    return [0] * count

                raw = self.instrument.convert_from_registers(
                    rr.registers, word_order='big',
                    data_type=self.instrument.DATATYPE.FLOAT32,
                    string_encoding="ascii")

                #data[address] = raw * 0.1
                data = {f"{address + i:#06x}": v for i, v in enumerate(raw)}
            except Exception as e:
                print(f"Read error {address}: {e}")
                data[address] = None
            return data

async def main():
    """Reads the consumption data of a dtsu666 once"""

    # load defaults from config.json
    config = load_config()
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s",
        level=config["logging"]["level"],)

    reader = Dtsu666Reader(
        cfg=config["dtsu"]
    )

    await reader.connect()
    values = await reader.read_values2()
    if values:
        for k, v in values.items():
            print(f"{k:30}: {v:.3f}")
    reader.close()

def raise_graceful_exit(*_args):
    """Enters shutdown mode"""
    _logger.info("Receiving shutdown signal now.")
    raise SystemExit

if __name__ == "__main__":
    try:
        signal.signal(signal.SIGINT, raise_graceful_exit)
        asyncio.run(main())
    except KeyboardInterrupt:
        _logger.info("CTRL+C: dtsu666reader exiting.")
