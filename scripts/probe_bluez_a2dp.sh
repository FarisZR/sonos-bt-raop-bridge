#!/usr/bin/env bash
set -euo pipefail

printf '== bluetoothctl list ==\n'
bluetoothctl list || true

printf '\n== bluetoothctl show ==\n'
bluetoothctl show || true

printf '\n== hciconfig -a ==\n'
hciconfig -a || true

printf '\n== bluetoothctl devices ==\n'
bluetoothctl devices || true

printf '\n== bluetoothctl paired devices ==\n'
bluetoothctl devices Paired || true

printf '\n== hci0 adapter ==\n'
sudo -n busctl introspect org.bluez /org/bluez/hci0 org.bluez.Adapter1 || true

printf '\n== BlueZ object tree ==\n'
sudo -n busctl tree org.bluez || true

printf '\n== bluetooth.service ==\n'
systemctl status bluetooth --no-pager || true

printf '\n== sonos bluetooth services ==\n'
systemctl status sonos-bt-agent.service sonos-bt-adapter.service --no-pager || true

printf '\n== conflicting bluetooth audio services ==\n'
systemctl status bluealsa.service bluealsa-aplay.service --no-pager || true
