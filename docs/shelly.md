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
geht angeblich auch Port 2220. Bei meinem Venus E V3 mit Firmware 144.110... aber nicht.

Deswegen habe ich jetzt auf den shellyproem50 auf port 2223 umgestellt. 
Diagnose läuft aber noch nicht...

## Log 
24.12.
- Shelly fragt nur EM1.GetStatus ab, obwohl auf 3 Phasig eingestellt
- Marstek Diagnose schläg fehl
- fragt mit ~250ms den shelly ab