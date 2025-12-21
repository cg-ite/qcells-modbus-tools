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
