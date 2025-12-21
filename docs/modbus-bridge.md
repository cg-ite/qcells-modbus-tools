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
Create user and group for service
```
groupadd -r modbus
useradd -r -g modbus -d /var/lib/modbus -s /usr/sbin/nologin modbus
usermod -aG dialout modbus
groupadd dialout

mkdir -p /etc/modbus-bridge
mkdir -p /var/log/modbus-bridge
chown -R modbus:modbus /etc/modbus-bridge /var/log/modbus-bridge
```

Create the file `sudo nano /etc/systemd/system/modbus-bridge.service` with contents:
```
[Unit]
Description=Modbus RTU → TCP Bridge
After=network.target

[Service]
User=modbus
Group=modbus
ExecStart=/usr/bin/uv run /opt/modbus-bridge/modbus-bridge.py
WorkingDirectory=/opt/modbus-bridge
Restart=on-failure
RestartSec=5

# Security Hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/modbus-bridge

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

# Zugriffsrechte von modbus user auf dongle
sudo -u modbus cat /dev/ttyUSB0


```
