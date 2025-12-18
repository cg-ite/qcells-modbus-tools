# qcells-modbus-tools
Some tools for QCells Inverter, modbus, mqtt, Shelly 3empro, Marstek Venus 3 and Home Assistant

Diese Sammlung an tools benötige ich für meine PV Anlage, die aus einem QCells Q.Volt P5T besteht, der mit einem DTSU666 über modbus rtu kommuniziert und die Energie-Daten in die Cloud läd.

Dazu habe ich mir nach gut einem Jahr einen Akku Marstek Venus V3 gekauft, da meine Verbrauchdaten gezeigt haben, dass ich ihn gut 300 Zyklen laden kann. In Verbindung mit unserem Strompreis von 0.35 € sollte er sich im schlechtesten Fall in gut 3.5 Jahren amortisieren.

Um alle Geräte in den Home Assistant zu integrieren, war allerdings etwas Recherche und Programmierung angesagt, da mein HA nicht im Keller neben dem WR steht. Dafür steht dort unser Home-Server, mit dem ich auf alle Geräte zugreifen und die Daten an den HA weiterreichen kann.

Folgende Tools benötige ich dazu:
1. Modbus Bridge from rtu to tcp
2. DTSU666 modbus reader
3. Mqtt bridge for the dtsu666
4. Shelly 3em pro adapter for the Marstek Akku to get the energy data from the dtsu666

Alle Tools können auch mehr oder weniger einzeln benutzt werden.

Die config umfasst alle Tools, da ich alle benötige. Das logging level ist zentral
und gilt für alle Tools gemeinsam.

Alle Skripte können zum debuggen einzeln aufgerufen werden.

## 1. Modbus RTU to TCP bridge
Der WR kann über modbus rtu mit dem passenden HA addon ausgelesen werden. Da mein HA nicht im Keller steht und ich kein Kabel nach oben legen wollte, wird eine modbus bridge aus der python lib pymodbus verwendet. Diese läuft als systemd Dienst.

Sie kann als einfache bridge für alle möglichen Geräte benutzt werden und ist nicht QCells speziefisch.

Die Konfiguration erfolgt über eine json Datei:
```json
{"modbus-bridge": {
                "log-level": 10,
                "device_id": 1,
                "tcp-ip": "127.0.0.1",
                "tcp-port": 502,
                "rtu-port": "/dev/ttyUSB0",
                "rtu-baudrate": 9600,
                "rtu-bytesize": 8,
                "rtu-parity": "N",
                "rtu-stopbits": 1
            }
}
```

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
## 3. Mqtt-Bridge