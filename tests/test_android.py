from sonos_bt_raop_bridge.android import AdbDevice, _parse_adb_devices, _parse_resumed_activity, _select_device


def test_parse_adb_devices_reads_serial_state_and_model() -> None:
    output = """List of devices attached
RFCR31468LJ device usb:2-1 product:t2sxxx model:SM_G996B device:t2s transport_id:1
emulator-5554 offline transport_id:2
"""

    assert _parse_adb_devices(output) == [
        AdbDevice(serial="RFCR31468LJ", state="device", model="SM_G996B"),
        AdbDevice(serial="emulator-5554", state="offline", model=None),
    ]


def test_select_device_prefers_configured_serial() -> None:
    devices = [
        AdbDevice(serial="other", state="device", model=None),
        AdbDevice(serial="wanted", state="offline", model=None),
    ]

    selected = _select_device(devices, configured_serial="wanted")

    assert selected == AdbDevice(serial="wanted", state="offline", model=None)


def test_parse_resumed_activity_prefers_resumed_entry() -> None:
    output = """
      Resumed: ActivityRecord{a9ae187 u0 com.android.settings/.Settings$BluetoothSettingsActivity t21}
      ResumedActivity: ActivityRecord{a9ae187 u0 com.android.settings/.Settings$BluetoothSettingsActivity t21}
    """

    assert _parse_resumed_activity(output) == "com.android.settings/.Settings$BluetoothSettingsActivity"
