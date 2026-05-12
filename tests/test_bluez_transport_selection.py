from sonos_bt_raop_bridge.bluez import MediaTransport, select_active_transport


def test_select_active_transport_prefers_active_over_pending() -> None:
    transports = [
        MediaTransport(path="/pending", device="/dev1", state="pending"),
        MediaTransport(path="/active", device="/dev1", state="active"),
    ]
    selected = select_active_transport(transports, device_path="/dev1")
    assert selected is not None
    assert selected.path == "/active"


def test_select_active_transport_filters_by_device() -> None:
    transports = [
        MediaTransport(path="/one", device="/dev1", state="active"),
        MediaTransport(path="/two", device="/dev2", state="active"),
    ]
    selected = select_active_transport(transports, device_path="/dev2")
    assert selected is not None
    assert selected.path == "/two"
