## 1. Modbus RTU to TCP bridge
Der WR kann über modbus rtu mit dem passenden HA addon ausgelesen werden. Da mein HA nicht im Keller steht und ich kein Kabel nach oben legen wollte, wird eine modbus bridge aus der python lib pymodbus verwendet. Diese läuft als systemd Dienst.

Sie kann als einfache bridge für alle möglichen Geräte benutzt werden und ist nicht QCells speziefisch.

Die Konfiguration erfolgt über eine json Datei:
```json
{"modbus-bridge": 
  {
    "log-level": 10,
    "device_ids": [1],
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
### systemd config
Create the file `sudo nano /etc/systemd/system/modbus-bridge.service` with contents:
```
[Unit]
Description=Modbus RTU to TCP Bridge
After=network.target
Wants=network.target

[Service]
Type=simple

# User / Gruppe (empfohlen: NICHT root)
User=root
Group=root

WorkingDirectory=/root/dtsu666-mqtt-gateway

# uv verwenden
ExecStart=/usr/bin/uv run modbus-bridge.py
ExecStop=/bin/kill -SIGTERM $MAINPID

# sauberes Stoppen
KillSignal=SIGTERM
TimeoutStopSec=10

# Neustart-Strategie
Restart=on-failure
RestartSec=3

# Logging → journal
StandardOutput=journal
StandardError=journal

# Environment
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target

```
### Debug hints
Die bridge kann mit `uv run modbus-bridge.py` zum Testen gestartet werden.
```
# Live-Logs
journalctl -u modbus-bridge -f

# Nur Fehler
journalctl -u modbus-bridge -p err

# Debug-Log ansehen
less /var/log/modbus-bridge/debug.log

# Neustart
systemctl restart modbus-bridge

# Sauber stoppen
systemctl stop modbus-bridge

```
