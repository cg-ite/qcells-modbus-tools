import json
import os


def load_config(path="config.json"):
    """Load default config from JSON file"""
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    else:
        # fallback default
        return {
            "dtsu": {
                "device_id": 1,
                "port": "/dev/ttyUSB0",
                "baudrate": 9600,
                "parity": "N",
                "stopbits": 1,
                "timeout": 1
            },
            "mqtt": {
                "host": "localhost",
                "port": 1883,
                "username": "user",
                "password": "pass",
                "topic_prefix": "DTSU666"
            },
            "poll_interval": 30,
            "shelly": {
                "device_id": 1,
                "udp_port": 2220
            },
            "device": {
                "id": 1
            },
            "emulator": {
                "enabled": True,
                "port": "/dev/ttyUSB0",
                "baudrate": 9600,
                "parity": "N",
                "stopbits": 1
            },
            "modbus-bridge": {
                "log-level": 10,
                "device_ids": [1],
                "tcp-ip": "192.168.1.24",
                "tcp-port": 502,
                "rtu-port": "/dev/ttyS0",
                "rtu-baudrate": 9600,
                "rtu-bytesize": 8,
                "rtu-parity": "N",
                "rtu-stopbits": 1
            },
            "logging": {
                "level": 10
            }
        }

# Log-level cheatsheet
# CRITICAL = 50
# FATAL = CRITICAL
# ERROR = 40
# WARNING = 30
# WARN = WARNING
# INFO = 20
# DEBUG = 10
# NOTSET = 0
