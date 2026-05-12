# sonos-bt-raop-bridge

Dedicated Bluetooth-to-Sonos/AirPlay bridge for Debian.

## Goal

Route Android Bluetooth A2DP audio into PipeWire on Debian and forward it to the Sonos stereo pair named `Kitchen`, `Küche`, or `Kueche` through the PipeWire RAOP/AirPlay sink.

Target path:

```text
Android phone
  -> Bluetooth A2DP
  -> BlueZ + PipeWire + WirePlumber on Debian
  -> PipeWire RAOP/AirPlay sink
  -> Sonos Kitchen stereo pair
```

## Current status

- Repo skeleton and config loader are in place.
- Bluetooth controller discovery is working with the TP-Link UB500 adapter.
- Home Assistant credentials are available through shell environment variables.
- PipeWire, WirePlumber, RAOP, Home Assistant probing, Android automation, and delay forwarding are being implemented iteratively.
- Debian setup now installs a persistent inotify fix, a Bluetooth-speaker WirePlumber drop-in, PipeWire RAOP discovery drop-in, disables conflicting BlueALSA services, a no-PIN pairing agent, and a systemd adapter-prep unit.

## Configuration

Configuration is loaded in this order:

1. Process environment variables.
2. `.env` in the repo root.
3. `/etc/sonos-bt-raop-bridge/env`
4. `/etc/sonos-bt-bridge-lab/env`

Supported variables include:

- `ANDROID_SERIAL`
- `HA_URL`
- `HA_TOKEN`
- `HA_TARGET_ENTITY`
- `HA_TARGET_FRIENDLY_NAMES`
- `HASS_SERVER` as an alias for `HA_URL`
- `HASS_TOKEN` as an alias for `HA_TOKEN`
- `BRIDGE_BT_ALIAS`
- `SONOS_RAOP_NAME_REGEX`
- `SAFE_TEST_VOLUME`
- `MAX_TEST_VOLUME`
- `TEST_HTTP_PORT`
- `DEFAULT_REPORTED_DELAY_MS`
- `CALIBRATION_MIN_DELAY_MS`
- `CALIBRATION_MAX_DELAY_MS`

## Layout

```text
sonos-bt-raop-bridge/
  README.md
  config/
  docs/
  src/sonos_bt_raop_bridge/
  scripts/
  systemd/
  tests/
  artifacts/
```

## Commands

The CLI entry point is `sonos-bt-bridge` and will grow into these commands:

- `discover`
- `ha-probe`
- `pipewire-probe`
- `bluez-probe`
- `set-default-sink`
- `set-delay`
- `calibrate`
- `status`
- `install-systemd`
- `doctor`

See `docs/` for the detailed design and troubleshooting notes.

## Host Setup

Run:

```bash
bash ./scripts/setup_debian.sh
```

That installs host packages, raises the inotify watch budget, disables conflicting BlueALSA services so PipeWire owns Bluetooth audio, enables PipeWire RAOP discovery, configures WirePlumber for incoming Bluetooth A2DP sink playback, makes the adapter advertise as a loudspeaker, enables no-PIN headless pairing, enables `sonos-bt-adapter.service`, and writes `/etc/sonos-bt-raop-bridge/env` from the target user's `.bashrc` exports when `HASS_SERVER` or `HASS_TOKEN` are present.
