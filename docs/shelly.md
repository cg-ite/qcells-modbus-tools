# Shelly Emulator

Taken and inspired by https://github.com/tomquist/b2500-meter

Ich brauche allerdings das dtsu666 backend, was es nicht gibt.

## Config
```json
{
  "shelly": {
    "device_id": 1,
    "udp_port": 2220
  }
}
```
`device_id` ist der Id des Shelly, falls mehrere eingebaut sind. 
Ist unabhängig vom DTSU666 modbus device_id.

## DeviceId des shelly 
Muss wohl gesetzt sein, damit der Masrstek ihn erkennt:
Ports für die Shellys siehe https://github.com/tomquist/b2500-meter/blob/c2f6a96794edc97684348bfedad725295a048242/main.py#L126
und die DeviceIds siehe https://github.com/tomquist/b2500-meter/blob/c2f6a96794edc97684348bfedad725295a048242/main.py#L207

Bei mir scheint der Marstek den Shelly 3em pro nur auf Port 1010 aufzurufen, was 
ich unter Linux wegen der Rechte nicht wollte. Laut Anleitung https://marstek-power.eu/Files/10/381000/381930/Attachments/Product/65S8397w2278e96T0dQ9zE41L942L0l5.pdf
geht angeblich auch Port 2220. Bei meinem Venus E V3 mit Firmware 144.110.116 aber nicht.

Deswegen habe ich jetzt auf den shellyproem50 auf port 2223 umgestellt. 
Diagnose läuft durch und der Akku läd und entläd. In der App sind so
keine Verbrauchswerte der drei Phasen zu sehen. Darauf kann ich aber
verzichten, da die Verbrauchswerte eh über mqtt an HA gesendet werden.


## Bekannte Probleme
Wenn der Marstek über LAN verbunden ist, 
muss die Antwort des Shelly 250 Zeichen lang sein, bei WLAN-Verbindung wohl nicht:
https://www.photovoltaikforum.com/thread/250638-marstek-venus-e-3-0/?postID=4548181&highlight=B2500#post4548181 und 
https://www.photovoltaikforum.com/thread/250638-marstek-venus-e-3-0/?postID=4548267&highlight=B2500#post4548267

### systemd config
Wer schon die einen User hat, kann den entsprechenden Abschnitt überspringen.

1. Create user and group for service
```
groupadd -r modbus
useradd -r -m -d /var/lib/modbus modbus
usermod -aG dialout modbus

nano /etc/passwd -> note groupid userid modbus

```
Dann in der Proxmox UI dem LXC Container unter resources
die device(s) hinzufügen und mit dem Userid und groupid versehen.

2. Projekt clonen:
```
cd /opt
git clone https://github.com/cg-ite/qcells-modbus-tools.git
chown -R modbus:modbus /opt/qcells-modbus-tools
```

3. DTSU-Service Verzeichnisse erstellen und 
```
mkdir -p /var/log/dtsu-service
chown -R modbus:modbus /var/log/dtsu-service

# Als modbus User anmelden und Dependencys installieren
su -s /bin/bash modbus

# optional uv installieren
curl -Ls https://astral.sh/uv/install.sh | sh
wget -qO- https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

cd /opt/qcells-modbus-tools
uv sync
# testen
uv run dtsu666service.py -d
```


```
# test connection and rights
su -s /bin/bash modbus -c "cd /opt/qcells-modbus-tools && /var/lib/modbus/.local/bin/uv run shelly.py -d"

```

4. Create the file `sudo micro /etc/systemd/system/qmt-dtsu-service.service` with contents:
```
# /etc/systemd/system/qmt-dtsu-service.service
[Unit]
Description=DTSU666 Mqtt/Shelly Service (qmt namespace)
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=modbus
Group=modbus
WorkingDirectory=/opt/qcells-modbus-tools
# ohne mqtt diese Zeile:
ExecStart=/var/lib/modbus/.local/bin/uv run shelly.py

# wenn die dtsu666 Werte per mqtt übertragen werden sollen: 
# ExecStart=/var/lib/modbus/.local/bin/uv run shelly.py -m
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
```
5. Activate service
```
# cmd
systemctl daemon-reload
systemctl enable qmt-dtsu-service
systemctl start qmt-dtsu-service

# debug service
systemctl status qmt-dtsu-service
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

check `micro /var/log/dtsu-service/debug.log` for errors, warnings and infos.

## Log 
24.12.
- Shelly fragt nur EM1.GetStatus ab, obwohl auf 3 Phasig eingestellt
- Marstek Diagnose schläg fehl
- fragt mit ~250ms den shelly ab
25.12.
- Shelly device_id scheint marstek nicht zu überprüfen
- heute funkte es auch auf port 2220 mit 3em pro
- shelly 3em pro wird ~0.9 sec abgefragt
- Hat aber die Diagnose nicht abgeschlossen