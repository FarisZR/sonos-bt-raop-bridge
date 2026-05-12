#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
ARTIFACT_DIR="$ROOT_DIR/artifacts/discovery-$TIMESTAMP"

mkdir -p "$ARTIFACT_DIR"

capture() {
  local name="$1"
  shift

  {
    printf '$'
    for arg in "$@"; do
      printf ' %q' "$arg"
    done
    printf '\n'
    "$@"
  } >"$ARTIFACT_DIR/$name.txt" 2>&1 || true
}

load_bashrc_export() {
  local key="$1"
  local bashrc="$HOME/.bashrc"
  [[ -f "$bashrc" ]] || return 0

  local line
  line=$(grep -E "^[[:space:]]*export[[:space:]]+$key=" "$bashrc" | tail -n 1 || true)
  [[ -n "$line" ]] || return 0

  # The user keeps Home Assistant credentials in simple export lines.
  # Evaluate only the matching line so discovery works in non-interactive shells.
  eval "$line"
  export "$key"
}

load_bashrc_export HASS_SERVER
load_bashrc_export HASS_TOKEN

capture os-release lsb_release -a
capture uname uname -a
capture id id
capture groups groups
capture systemctl-version systemctl --version
capture package-policy apt-cache policy bluez pipewire wireplumber pipewire-audio pipewire-pulse pipewire-alsa libspa-0.2-bluetooth libpipewire-0.3-modules python3-dbus-next python3-pytest
capture lsusb lsusb
capture lspci lspci -nn
capture hciconfig hciconfig -a
capture bluetoothctl-version bluetoothctl -v
capture bluetoothctl-list bluetoothctl list
capture bluetoothctl-show bluetoothctl show
capture rfkill rfkill list
capture bluetooth-service systemctl status bluetooth --no-pager
capture bluez-tree sudo -n busctl tree org.bluez
capture bluez-adapter sudo -n busctl introspect org.bluez /org/bluez/hci0 org.bluez.Adapter1
capture avahi-service systemctl status avahi-daemon --no-pager
capture avahi-raop avahi-browse -rt _raop._tcp
capture adb-devices adb devices -l
capture adb-version adb version
capture android-version adb shell getprop ro.build.version.release
capture android-model adb shell getprop ro.product.model
capture android-bluetooth-on adb shell settings get global bluetooth_on
capture android-bt-manager adb shell dumpsys bluetooth_manager
capture android-audio adb shell dumpsys audio
capture android-media-session adb shell dumpsys media_session
capture kernel-log sudo -n journalctl -k -b --no-pager
capture homeassistant-probe env PYTHONPATH="$ROOT_DIR/src" python3 "$ROOT_DIR/scripts/probe_home_assistant.py" --artifact-dir "$ARTIFACT_DIR"

printf '%s\n' "$ARTIFACT_DIR"
