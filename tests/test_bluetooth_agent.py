from sonos_bt_raop_bridge.bluetooth_agent import AGENT_CAPABILITY, Agent


def test_agent_uses_headless_pairing_capability() -> None:
    assert AGENT_CAPABILITY == "NoInputNoOutput"


def test_agent_returns_default_legacy_pairing_values() -> None:
    agent = Agent()

    assert Agent.RequestPinCode.__wrapped__(agent, "/org/bluez/hci0/dev_00_11_22_33_44_55") == "0000"
    assert Agent.RequestPasskey.__wrapped__(agent, "/org/bluez/hci0/dev_00_11_22_33_44_55") == 0
