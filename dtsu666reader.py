#!/usr/bin/env python3
import argparse
import asyncio
import logging
import signal
from dataclasses import dataclass
from typing import List, Optional

from pymodbus.pdu.register_message import ReadHoldingRegistersResponse
import pymodbus.client as ModbusClient
from pymodbus import (
    FramerType,
)

from config import load_config
from dtsu666_constants import FOUR_WIRE_KEYS, REGISTERS, TOTAL_ACTIVE_POWER, \
    BLOCK_STATS

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
        address = TOTAL_ACTIVE_POWER
        spec = REGISTERS[address]
        try:
            rr = await self.instrument.read_holding_registers(address,
                                                              count=8,
                                                              device_id=self.device_id)

            if not isinstance(rr, ReadHoldingRegistersResponse):
                _logger.warning(f"Read error: no RegisterResponse @ {address}")
                return None
            if not rr or rr.isError():
                _logger.warning(f"Read error: isError @ {address} Error-code:{rr.exception_code}")
                return None

            raw = self.instrument.convert_from_registers(
                rr.registers, word_order='big',
                data_type = self.instrument.DATATYPE.FLOAT32)
            data = [spec["factor"] * p for p in raw]
        except Exception as e:
            _logger.error(f"Read error@ {address}: Exception {e} ")
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
                    _logger.warning(f"Read error: no RegisterResponse @ {address}")
                    continue
                if not rr or rr.isError():
                    _logger.warning(f"Read error: isError @ {address} Error-code:{rr.exception_code}")
                    return None

                raw = self.instrument.convert_from_registers(
                    rr.registers, word_order='big',
                    data_type=self.instrument.DATATYPE.FLOAT32,
                    string_encoding="ascii")
                data[address] = raw * spec["factor"]
            except Exception as e:
                _logger.error(f"Read error@ {address}: Exception {e} ")
                data[address] = None
        return data

    async def read_stats(self):
        """Reads efficiently all values from the DTSU666 in blocks, but
        without multiplying the right factor"""
        data = {}
        for block in BLOCK_STATS:
            data[block["address"]] = await self.read_value(block["address"], block["count"])
        return data

    def check_exception(self, result):
        """Decode Modbus exception response."""
        if not result.isError():
            return None

        exceptions = {
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

        code = getattr(result, 'exception_code', None)
        if code:
            return code
        return None

    async def read_value(self, address, count=1, factor=1.0):
        """Reads all register starting at address from the DTSU666, mostly for debugging reason """
        res = ModbusReading()
        data = []
        try:
            rr = await self.instrument.read_holding_registers(address,
                                                              count=count,
                                                              device_id=self.device_id)

            if not isinstance(rr, ReadHoldingRegistersResponse):
                _logger.warning(f"Read error: no RegisterResponse @ {address}")
                return None
            if not rr or rr.isError():
                res.error_code = self.check_exception(rr)
                if res.error_code is not None:
                    _logger.warning(f"Read error: isError @ {address} Error-code:{res.error_code}")
                    return res

            raw = self.instrument.convert_from_registers(
                rr.registers, word_order='big',
                data_type=self.instrument.DATATYPE.FLOAT32,
                string_encoding="ascii")
            if isinstance(raw, list):
                data = [factor * p for p in raw]
            else:
                data = raw * factor
        except Exception as e:
            _logger.error(f"Read error@ {address}: Exception {e} ")
            data = None
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
    values = await reader.read_stats()
    print(values)
    reader.close()

def raise_graceful_exit(*_args):
    """Enters shutdown mode"""
    _logger.info("Receiving shutdown signal now.")
    raise SystemExit

@dataclass
class ModbusReading:
    """ Simple class for a modbusreading with values and errorcode """
    readings: Optional[List[float]] = None
    error_code: Optional[int] = None

if __name__ == "__main__":
    try:
        signal.signal(signal.SIGINT, raise_graceful_exit)
        asyncio.run(main())
    except KeyboardInterrupt:
        _logger.info("CTRL+C: dtsu666reader exiting.")
