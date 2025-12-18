## 2. DTSU666 Modbusreader
Einfache Klasse für das Auslesen eines DTSU666 per Modbus RTU. Wird von der Mqtt-Bridge 
benutzt, um die Daten des DTSU auszulesen und an einen Mqtt-Server zu schicken.

Zum Testen der Verbindung zum DTSU `uv run dtsu666reader.py` aufrufen.
Im Erfolgsfall werden alle verfügbaren Daten des DTSU angezeigt.

Die Konfiguration erfolgt über eine json Datei:
```json
{"dtsu": {
        "device_id": 1,
        "port": "/dev/ttyS0",
        "baudrate": 9600,
        "parity": "N",
        "stopbits": 1,
        "timeout": 1
    },
    "logging": {
        "level": 10
    }
}
```