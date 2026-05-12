# Troubleshooting

## No Bluetooth controller

Check:

```bash
bluetoothctl list
hciconfig -a
sudo busctl tree org.bluez
```

## Home Assistant not reachable

Check:

```bash
source ~/.bashrc
curl -H "Authorization: Bearer $HASS_TOKEN" "$HASS_SERVER/api/"
```

## Sonos RAOP not visible

Check:

```bash
avahi-browse -rt _raop._tcp
```
