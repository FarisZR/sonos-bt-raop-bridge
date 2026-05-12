# Discovery 20260512T172219Z

This is the committed, sanitized summary of the first corrected discovery pass.

Raw command captures were collected locally during discovery and remain untracked.

## Commands captured

- `lsb_release -a`
- `uname -a`
- `id`
- `groups`
- `systemctl --version`
- `apt-cache policy ...`
- `lsusb`
- `lspci -nn`
- `hciconfig -a`
- `bluetoothctl -v`
- `bluetoothctl list`
- `bluetoothctl show`
- `rfkill list`
- `systemctl status bluetooth --no-pager`
- `sudo busctl tree org.bluez`
- `sudo busctl introspect org.bluez /org/bluez/hci0 org.bluez.Adapter1`
- `systemctl status avahi-daemon --no-pager`
- `avahi-browse -rt _raop._tcp`
- `adb devices -l`
- `adb shell getprop ro.build.version.release`
- `adb shell getprop ro.product.model`
- `adb shell settings get global bluetooth_on`
- `adb shell dumpsys bluetooth_manager`
- `adb shell dumpsys audio`
- `adb shell dumpsys media_session`
- `sudo journalctl -k -b --no-pager`
- `PYTHONPATH=src python3 scripts/probe_home_assistant.py`

## Conclusions

- Host OS is Debian 13.
- BlueZ 5.82 is installed.
- A working Bluetooth controller is present through the TP-Link UB500 USB adapter and exposed as `hci0`.
- The adapter advertises A2DP sink-related UUIDs and is suitable for bridge bring-up.
- PipeWire and WirePlumber are not installed yet.
- Avahi is active, but no RAOP services were visible during discovery.
- One Android device is reachable over ADB and reports Android 15 on an `SM-G996B` handset.
- Home Assistant credentials are configured through shell exports, but the configured Home Assistant server at `HASS_SERVER` timed out from this host during discovery, so entity discovery is currently blocked by network reachability rather than missing credentials.

## Next actions chosen from discovery

1. Install PipeWire, WirePlumber, Bluetooth SPA modules, and pytest.
2. Configure the host as an A2DP sink with a dedicated bridge alias.
3. Re-test RAOP discovery after PipeWire is installed.
4. Keep Home Assistant probing in the workflow, but treat HA reachability as an external blocker until the configured server responds.
