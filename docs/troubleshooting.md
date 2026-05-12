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

## PipeWire only shows `auto_null`

Check:

```bash
./scripts/probe_pipewire_raop.sh
```

If WirePlumber logs `inotify_add_watch() failed: No space left on device`, another process has exhausted the per-user inotify watch budget. Apply the repo setup script or raise `fs.inotify.max_user_watches` and restart the user PipeWire services.

## Adapter is not pairable or discoverable

Check:

```bash
systemctl status sonos-bt-adapter.service --no-pager
bluetoothctl show
```

The bridge setup service should leave the adapter powered, pairable, discoverable, and aliased as `SonosBridge`.

If phones do not classify the host as a speaker, verify that `hciconfig -a` shows an Audio/Video loudspeaker class instead of `Computer, Laptop`.

## Phone asks for a pairing PIN

Check:

```bash
systemctl status sonos-bt-agent.service --no-pager
journalctl -u sonos-bt-agent.service -n 50 --no-pager
```

The bridge should register a BlueZ agent with `NoInputNoOutput` capability so Android uses a headless just-works flow instead of prompting for a PIN or passkey.

## Phone does not show the host as an audio output

Check:

```bash
./scripts/probe_bluez_a2dp.sh
```

The adapter should advertise the `Audio Sink` UUID and an Audio/Video loudspeaker device class. If it still shows `Computer, Laptop`, rerun `sonos-bt-adapter.service` or `bash ./scripts/configure_bluetooth_adapter.sh` to refresh the class of device.

## PipeWire never claims Bluetooth audio

Check:

```bash
systemctl status bluealsa.service bluealsa-aplay.service --no-pager
sudo -u "$USER" journalctl --user -u wireplumber --no-pager -n 100
```

If WirePlumber logs `Properties changed in unknown transport` or warns that multiple sound servers are trying to use Bluetooth audio at the same time, stop and disable `bluealsa.service` and `bluealsa-aplay.service`. The bridge expects PipeWire and WirePlumber to be the only Bluetooth audio manager on the host.

## Phone playback goes to the wrong room

Check:

```bash
sonos-bt-bridge set-default-sink
sudo -u "$USER" env XDG_RUNTIME_DIR="/run/user/$(id -u)" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus" wpctl status -n
```

Incoming Bluetooth media-source playback follows the current PipeWire default sink. Use `sonos-bt-bridge set-default-sink` to pin the configured `Kitchen` / `Küche` / `Kueche` RAOP target as the default sink.
