#!/usr/bin/env bash
set -euo pipefail

BRIDGE_ALIAS=${BRIDGE_BT_ALIAS:-${1:-SonosBridge}}
BRIDGE_CLASS=${BRIDGE_BT_CLASS:-0x240414}

wait_for_controller() {
  local attempt
  for attempt in $(seq 1 20); do
    if bluetoothctl list | grep -q 'Controller '; then
      return 0
    fi
    sleep 1
  done
  printf 'Bluetooth controller hci0 did not appear in time\n' >&2
  return 1
}

run_bluetoothctl_script() {
  bluetoothctl <<EOF
$1
quit
EOF
}

bluetoothctl_retry() {
  local attempt
  for attempt in $(seq 1 10); do
    if bluetoothctl "$@"; then
      return 0
    fi
    sleep 1
  done
  bluetoothctl "$@"
}

wait_for_controller
bluetoothctl_retry power on
bluetoothctl_retry system-alias "$BRIDGE_ALIAS"
busctl set-property org.bluez /org/bluez/hci0 org.bluez.Adapter1 PairableTimeout u 0
busctl set-property org.bluez /org/bluez/hci0 org.bluez.Adapter1 DiscoverableTimeout u 0
bluetoothctl_retry pairable on
bluetoothctl_retry discoverable on

hciconfig hci0 name "$BRIDGE_ALIAS"
hciconfig hci0 class "$BRIDGE_CLASS"

# Report headless I/O capability so phones use just-works pairing.
run_bluetoothctl_script "menu mgmt
le off
bredr on
ssp on
io-cap NoInputNoOutput
back"

bluetoothctl show
hciconfig -a
