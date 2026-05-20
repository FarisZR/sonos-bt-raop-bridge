# AGENTS.md

Trust `src/sonos_bt_raop_bridge/config.py`, `src/sonos_bt_raop_bridge/cli.py`, `scripts/*.sh`, and `systemd/*.service` over `README.md` when they disagree. The README command list and config-precedence note are stale.

## Runtime Shape

- This repo is not just a Python package. Live behavior depends on `src/`, `scripts/`, `config/`, and `systemd/` together.
- The real module entrypoint is `python3 -m sonos_bt_raop_bridge`. Use `scripts/sonos-bt-bridge` or the installed `/usr/local/bin/sonos-bt-bridge` when possible. Do not use `python3 -m sonos_bt_raop_bridge.cli`; it does not invoke `main()`.
- `src/sonos_bt_raop_bridge/android.py` only probes ADB state. It does not start media playback.
- `src/sonos_bt_raop_bridge/pipewire.py` is the RAOP sink selector/default-sink mutator. `src/sonos_bt_raop_bridge/bluetooth_agent.py` is the headless BlueZ pairing agent.

## Config And Env

- Actual config overlay order in `load_config()` is: repo `.env` -> `/etc/sonos-bt-raop-bridge/env` -> `/etc/sonos-bt-bridge-lab/env` -> process environment.
- `HASS_SERVER` and `HASS_TOKEN` are accepted aliases for `HA_URL` and `HA_TOKEN`.
- Default target matching is `Kitchen|Küche|Kueche`; this is how `set-default-sink` finds the Sonos RAOP sink.
- `scripts/setup_debian.sh` and `scripts/discover_environment.sh` scrape `~/.bashrc` for simple `export HASS_SERVER=...` and `export HASS_TOKEN=...` lines. If those exports become more complex, non-interactive discovery/install will stop picking them up.

## Install And Service Gotchas

- `bash scripts/setup_debian.sh` is the authoritative install flow. It copies repo files into `/etc/pipewire/pipewire.conf.d`, `/etc/wireplumber/wireplumber.conf.d`, `/usr/local/lib/sonos-bt-raop-bridge`, `/usr/local/bin`, and `/etc/systemd/system`, writes `/etc/sonos-bt-raop-bridge/env`, disables `bluealsa.service` and `bluealsa-aplay.service`, and restarts the target user's PipeWire services if a user session bus exists.
- Editing repo drop-ins or `scripts/configure_bluetooth_adapter.sh` does not change the live system until you reinstall or copy the files into their installed locations.
- Service wiring is asymmetric:
- `sonos-bt-adapter.service` runs the installed copy `/usr/local/lib/sonos-bt-raop-bridge/configure_bluetooth_adapter.sh`.
- `sonos-bt-agent.service` and `sonos-bt-delay-forwarder.service` import from `/home/clawd/sonos-bt-raop-bridge/src` via hard-coded `PYTHONPATH`. Moving the repo breaks those services unless the unit files are updated and reinstalled.
- `scripts/configure_bluetooth_adapter.sh` sets `BRIDGE_BT_CLASS` with `hciconfig hci0 class ...`; the default is `0x240414` (Audio/Video loudspeaker). `bluetooth_agent.py` registers `NoInputNoOutput`. If a phone asks for a PIN or classifies the host as a laptop, verify the installed adapter script/service, not only the repo copy.
- If PipeWire collapses to `auto_null`, use `bash scripts/probe_pipewire_raop.sh` first. It checks user-session-bus access and reports per-user inotify exhaustion, which is a known failure mode on this host.

## Commands That Actually Matter

- Automated verification in repo is just focused pytest files; there is no lint, formatter, or typecheck config.
- `pytest tests/test_config.py`
- `pytest tests/test_pipewire.py`
- `pytest tests/test_android.py`
- `pytest tests/test_bluetooth_agent.py`
- Live host probes:
- `bash scripts/probe_pipewire_raop.sh [target-user]`
- `bash scripts/probe_bluez_a2dp.sh`
- `bash scripts/discover_environment.sh`
- `sonos-bt-bridge set-default-sink` is the only CLI command that currently mutates live PipeWire state.
- `calibrate`, `install-systemd`, and `set-delay` are stubs. `doctor` only prints JSON status. `sonos-bt-delay-forwarder.service` is therefore placeholder wiring, not real delay forwarding.

## Session-Bus And Routing Quirks

- Raw `wpctl`, `pw-dump`, and `pactl` checks must run in the target user's PipeWire session context. Reuse `scripts/sonos-bt-bridge` or `scripts/probe_pipewire_raop.sh` instead of running them as root with no session env.
- Incoming Bluetooth playback follows the current PipeWire default sink. If audio goes to the wrong room, run `sonos-bt-bridge set-default-sink` before debugging anything deeper.
- The live success condition is a `bluez_input.*` stream linked into the Kitchen RAOP sink in `wpctl status -n`.
- Keep `bluealsa.service` and `bluealsa-aplay.service` disabled. This repo assumes PipeWire and WirePlumber are the only Bluetooth audio manager.
