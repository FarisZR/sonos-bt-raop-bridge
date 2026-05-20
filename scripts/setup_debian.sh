#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  exec sudo --preserve-env=DEBIAN_FRONTEND "$0" "$@"
fi

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
TARGET_USER=${SUDO_USER:-${PKEXEC_UID:+#${PKEXEC_UID}}}
PACKAGES=(
  avahi-utils
  bluez
  libpipewire-0.3-modules
  libspa-0.2-bluetooth
  pipewire
  pipewire-alsa
  pipewire-audio
  pipewire-bin
  pipewire-pulse
  pulseaudio-utils
  python3-dbus-next
  python3-pytest
  wireplumber
)
SYSCTL_FILE=/etc/sysctl.d/90-sonos-bt-raop-bridge-inotify.conf
PIPEWIRE_DROPIN_DIR=/etc/pipewire/pipewire.conf.d
WIREPLUMBER_DROPIN_DIR=/etc/wireplumber/wireplumber.conf.d
INSTALL_LIB_DIR=/usr/local/lib/sonos-bt-raop-bridge
INSTALL_BIN_DIR=/usr/local/bin
SYSTEMD_UNIT_DIR=/etc/systemd/system
BLUETOOTH_SERVICE_DROPIN_DIR=$SYSTEMD_UNIT_DIR/bluetooth.service.d
ENV_DIR=/etc/sonos-bt-raop-bridge
ENV_FILE=$ENV_DIR/env
BLUETOOTH_MAIN_CONF=/etc/bluetooth/main.conf
BRIDGE_BT_CLASS_DEFAULT=0x240414

resolve_target_user() {
  if [[ -z "$TARGET_USER" ]]; then
    return 1
  fi

  if [[ "$TARGET_USER" == \#* ]]; then
    id -nu "${TARGET_USER#\#}"
    return
  fi

  printf '%s\n' "$TARGET_USER"
}

load_bashrc_export() {
  local user_name="$1"
  local key="$2"
  local bashrc
  bashrc=$(getent passwd "$user_name" | cut -d: -f6)/.bashrc
  [[ -f "$bashrc" ]] || return 0

  awk -F= -v key="$key" '
    $0 ~ "^[[:space:]]*export[[:space:]]+" key "=" {
      value = $0
    }
    END {
      sub(/^[^=]+= */, "", value)
      gsub(/^\"|\"$/, "", value)
      gsub(/^\047|\047$/, "", value)
      print value
    }
  ' "$bashrc"
}

pick_config_value() {
  local explicit_value="$1"
  local fallback_value="$2"

  if [[ -n "$explicit_value" ]]; then
    printf '%s\n' "$explicit_value"
    return
  fi

  printf '%s\n' "$fallback_value"
}

disable_conflicting_bluetooth_audio_services() {
  local unit
  local disabled_units=()

  for unit in bluealsa.service bluealsa-aplay.service; do
    if [[ $(systemctl show -p LoadState --value "$unit" 2>/dev/null || true) == "not-found" ]]; then
      continue
    fi

    systemctl disable --now "$unit" >/dev/null 2>&1 || true
    disabled_units+=("$unit")
  done

  if [[ ${#disabled_units[@]} -gt 0 ]]; then
    printf 'Disabled conflicting Bluetooth audio services: %s\n' "${disabled_units[*]}"
  fi
}

configure_bluez_device_class() {
  local bridge_class="${BRIDGE_BT_CLASS:-$BRIDGE_BT_CLASS_DEFAULT}"
  local device_class
  printf -v device_class '0x%06x' "$((bridge_class & 0x001ffc))"

  set_bluez_general_option Class "$device_class"
}

set_bluez_general_option() {
  local key="$1"
  local value="$2"

  if [[ ! -f "$BLUETOOTH_MAIN_CONF" ]]; then
    printf '[General]\n%s = %s\n' "$key" "$value" >"$BLUETOOTH_MAIN_CONF"
    return
  fi

  if grep -q "^[[:space:]]*#\\?[[:space:]]*$key[[:space:]]*=" "$BLUETOOTH_MAIN_CONF"; then
    sed -i -E "0,/^[[:space:]]*#?[[:space:]]*$key[[:space:]]*=.*/s//$key = $value/" "$BLUETOOTH_MAIN_CONF"
    return
  fi

  if grep -q '^[[:space:]]*\[General\]' "$BLUETOOTH_MAIN_CONF"; then
    sed -i -E "/^[[:space:]]*\[General\]/a $key = $value" "$BLUETOOTH_MAIN_CONF"
    return
  fi

  {
    printf '[General]\n%s = %s\n\n' "$key" "$value"
    cat "$BLUETOOTH_MAIN_CONF"
  } >"$BLUETOOTH_MAIN_CONF.tmp"
  mv "$BLUETOOTH_MAIN_CONF.tmp" "$BLUETOOTH_MAIN_CONF"
}

configure_bluez_pairing_policy() {
  set_bluez_general_option AlwaysPairable true
  set_bluez_general_option PairableTimeout 0
  set_bluez_general_option JustWorksRepairing always
  set_bluez_general_option ControllerMode bredr
}

configure_bluetoothd_plugins() {
  install -d "$BLUETOOTH_SERVICE_DROPIN_DIR"
  cat >"$BLUETOOTH_SERVICE_DROPIN_DIR/10-sonos-bt-raop-bridge.conf" <<'EOF'
[Service]
ExecStart=
ExecStart=/usr/libexec/bluetooth/bluetoothd --noplugin=sap
EOF
}

apt-get update
apt-get install -y "${PACKAGES[@]}"

install -d /etc/sysctl.d
printf '%s\n' 'fs.inotify.max_user_watches = 524288' >"$SYSCTL_FILE"
sysctl --load="$SYSCTL_FILE"

install -d "$PIPEWIRE_DROPIN_DIR" "$WIREPLUMBER_DROPIN_DIR" "$INSTALL_LIB_DIR" "$INSTALL_BIN_DIR" "$SYSTEMD_UNIT_DIR" "$ENV_DIR"
install -m 0644 "$ROOT_DIR/config/pipewire/50-sonos-bt-raop-discover.conf" "$PIPEWIRE_DROPIN_DIR/50-sonos-bt-raop-discover.conf"
install -m 0644 "$ROOT_DIR/config/wireplumber/50-sonos-bt-a2dp-sink.conf" "$WIREPLUMBER_DROPIN_DIR/50-sonos-bt-a2dp-sink.conf"
install -m 0755 "$ROOT_DIR/scripts/configure_bluetooth_adapter.sh" "$INSTALL_LIB_DIR/configure_bluetooth_adapter.sh"
install -m 0755 "$ROOT_DIR/scripts/sonos-bt-bridge" "$INSTALL_BIN_DIR/sonos-bt-bridge"
install -m 0644 "$ROOT_DIR/systemd/sonos-bt-adapter.service" "$SYSTEMD_UNIT_DIR/sonos-bt-adapter.service"
install -m 0644 "$ROOT_DIR/systemd/sonos-bt-agent.service" "$SYSTEMD_UNIT_DIR/sonos-bt-agent.service"
install -m 0644 "$ROOT_DIR/systemd/sonos-bt-delay-forwarder.service" "$SYSTEMD_UNIT_DIR/sonos-bt-delay-forwarder.service"
configure_bluez_device_class
configure_bluez_pairing_policy
configure_bluetoothd_plugins

if target_user_name=$(resolve_target_user 2>/dev/null); then
  hass_server=$(pick_config_value "${HA_URL:-${HASS_SERVER:-}}" "$(load_bashrc_export "$target_user_name" HASS_SERVER)")
  hass_token=$(pick_config_value "${HA_TOKEN:-${HASS_TOKEN:-}}" "$(load_bashrc_export "$target_user_name" HASS_TOKEN)")
  {
    if [[ -n "$hass_server" ]]; then
      printf 'HASS_SERVER=%s\n' "$hass_server"
    fi
    if [[ -n "$hass_token" ]]; then
      printf 'HASS_TOKEN=%s\n' "$hass_token"
    fi
  } >"$ENV_FILE"
  chown root:"$(id -gn "$target_user_name")" "$ENV_FILE"
  chmod 0640 "$ENV_FILE"
fi

systemctl daemon-reload
disable_conflicting_bluetooth_audio_services
systemctl restart bluetooth.service
systemctl enable --now sonos-bt-agent.service
systemctl enable --now sonos-bt-adapter.service

if [[ -n "${target_user_name:-}" ]]; then
  TARGET_UID=$(id -u "$target_user_name")
  RUNTIME_DIR=/run/user/$TARGET_UID
  SESSION_BUS=unix:path=$RUNTIME_DIR/bus
  if [[ -S "$RUNTIME_DIR/bus" ]]; then
    sudo -u "$target_user_name" env XDG_RUNTIME_DIR="$RUNTIME_DIR" DBUS_SESSION_BUS_ADDRESS="$SESSION_BUS" systemctl --user restart pipewire.service wireplumber.service pipewire-pulse.service
  fi
fi

printf 'Installed packages and applied %s\n' "$SYSCTL_FILE"
printf 'Wrote runtime environment to %s\n' "$ENV_FILE"
