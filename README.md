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
- `set-delay`
- `calibrate`
- `status`
- `install-systemd`
- `doctor`

See `docs/` for the detailed design and troubleshooting notes.
