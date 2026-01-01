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
    "tcp-port": 1502,
    "rtu-port": "/dev/ttyUSB0",
    "rtu-baudrate": 9600,
    "rtu-bytesize": 8,
    "rtu-parity": "N",
    "rtu-stopbits": 1
    }
}
```
- `log_level` - Der Service loggt mit level Warning ins journal und mit
`log_level`  in die Datei `/var/log/modbus-bridge/debug.log`, um bei Bedarf
mehr Fehler, Warnungen und Infos zu bekommen.
- `device_ids` - Modbus Id des WR. Theoretisch können mehrere Ids angegeben werden,
da ich den originalen Code an dieser Stelle nicht angepasst habe.
- `tcp-ip` - Die Ip-Adresse des Servers auf der der ModbusTCP-Server horchen soll.
- `tcp-port` - Der Port auf der der ModbusTCP-Server horchen soll. Da Port unter 1024
unter Linux `root` Rechte benötigen, habe ich ihn auf 1502 gesetzt. Es gibt wie immer
auch andere Möglichkeiten: https://serverfault.com/questions/268099/bind-to-ports-less-than-1024-without-root-access
Unter HA kann man den Port auch einstellen und es funktioniert ohne Probleme.
- `rtu-port` - Der Port auf dem euer ModbusRTU-Dongle für den WR hängt

Der Rest ist eigentlich selbsterklärend.

### systemd config
Create user and group for service
```
groupadd -r modbus
useradd -r -m -d /var/lib/modbus modbus
usermod -aG dialout modbus
# groupadd dialout

mkdir -p /etc/modbus-bridge
mkdir -p /var/log/modbus-bridge
chown -R modbus:modbus /etc/modbus-bridge /var/log/modbus-bridge

nano /etc/passwd -> note groupid userid modbus

```
Dann in Proxmox gui unter resources device hinzufügen mit dem Userid und groupid

```
mkdir -p /opt/qcells-modbus-tools
cd /opt
git clone https://github.com/cg-ite/qcells-modbus-tools.git
chown -R modbus:modbus /opt/qcells-modbus-tools


# Dependencys installieren
su -s /bin/bash modbus

# optional uv installieren
curl -Ls https://astral.sh/uv/install.sh | sh
wget -qO- https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

cd /opt/qcells-modbus-tools
uv add pyserial
uv sync
uv run modbus-bridge.py -d
exit

# test connection and rights
su -s /bin/bash modbus -c "cd /opt/qcells-modbus-tools && /var/lib/modbus/.local/bin/uv run modbus_bridge.py -d"

```

Create the file `sudo micro /etc/systemd/system/qmt-modbus-bridge.service` with contents:
```
# /etc/systemd/system/qmt-modbus-bridge.service
[Unit]
Description=QCells Modbus Bridge (qmt namespace)
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=modbus
Group=modbus
WorkingDirectory=/opt/qcells-modbus-tools
ExecStart=/var/lib/modbus/.local/bin/uv run modbus-bridge.py
Restart=always
RestartSec=5
# Logging über Journalctl
StandardOutput=journal
StandardError=journal
# Optional: Limits für Ressourcennutzung
# LimitNOFILE=4096
# LimitNPROC=512

[Install]
WantedBy=multi-user.target

# cmd
systemctl daemon-reload
systemctl enable qmt-modbus-bridge
systemctl start qmt-modbus-bridge

# debug service
systemctl status qmt-modbus-bridge
```

Edit config.json and set the desired loglevel:
```
# Log-level cheatsheet
CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0
```

check `micro /var/log/modbus-bridge/debug.log` for errors, warnings and infos.

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
su -u modbus cat /dev/ttyUSB0


```
