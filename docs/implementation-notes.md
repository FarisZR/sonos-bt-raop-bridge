# Implementation Notes

## 2026-05-12

- Confirmed Debian 13 host.
- Confirmed TP-Link UB500 Bluetooth adapter exposes `hci0` through BlueZ.
- Confirmed Home Assistant token is exported from `.bashrc` using `HASS_SERVER` and `HASS_TOKEN`.
- Installed PipeWire, WirePlumber, Bluetooth SPA support, and pytest on the host.
- Confirmed Home Assistant reachability is currently blocked by a network timeout to the configured `HASS_SERVER`.
- Captured a sanitized discovery summary in `artifacts/discovery-20260512T172219Z/`.
- Diagnosed the `auto_null`-only PipeWire state to per-user inotify exhaustion from another `clawd` process consuming almost the entire watch budget.
- Replaced the PipeWire and BlueZ probe placeholders with live scripts and wired the CLI subcommands to them.
- Added Debian setup automation to install missing packages, add `pulseaudio-utils`, and raise `fs.inotify.max_user_watches` persistently.
- Added repo-managed host drop-ins for PipeWire RAOP discovery and WirePlumber Bluetooth A2DP sink mode.
- Added a systemd oneshot unit to set the Bluetooth adapter alias, pairable mode, and discoverable mode for headless operation.
- Confirmed Home Assistant is reachable through the Nabu Casa URL and that `media_player.kitchen` resolves to `Kitchen speakers`.
- Updated Debian setup to write `/etc/sonos-bt-raop-bridge/env` from `.bashrc` exports so non-interactive probes and services can use `HASS_SERVER` and `HASS_TOKEN`.
- Confirmed ADB-driven Chrome playback can start a live Bluetooth media session on the Galaxy S21.
- Switched the WirePlumber Bluetooth policy back to default media-source playback behavior and added a CLI helper to pin the configured Kitchen RAOP sink as PipeWire's default sink.
- Changed the BlueZ agent to `NoInputNoOutput` and updated adapter prep to advertise an Audio/Video loudspeaker class so phones treat `SonosBridge` as a speaker instead of a laptop.
