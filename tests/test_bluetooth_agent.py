import asyncio

import sonos_bt_raop_bridge.bluetooth_agent as bluetooth_agent
from sonos_bt_raop_bridge.bluetooth_agent import AGENT_CAPABILITY, Agent


def test_agent_uses_headless_pairing_capability() -> None:
    assert AGENT_CAPABILITY == "NoInputNoOutput"


def test_agent_returns_default_legacy_pairing_values() -> None:
    agent = Agent()

    assert Agent.RequestPinCode.__wrapped__(agent, "/org/bluez/hci0/dev_00_11_22_33_44_55") == "0000"
    assert Agent.RequestPasskey.__wrapped__(agent, "/org/bluez/hci0/dev_00_11_22_33_44_55") == 0


def test_agent_marks_authorized_devices_trusted(monkeypatch) -> None:
    trusted_devices: list[tuple[object, str]] = []

    async def fake_set_device_trusted(bus: object, device: str) -> None:
        trusted_devices.append((bus, device))

    monkeypatch.setattr(bluetooth_agent, "_set_device_trusted", fake_set_device_trusted)

    async def run_authorization() -> None:
        bus = object()
        agent = Agent(bus)
        Agent.AuthorizeService.__wrapped__(
            agent,
            "/org/bluez/hci0/dev_00_11_22_33_44_55",
            "0000110a-0000-1000-8000-00805f9b34fb",
        )
        await asyncio.sleep(0)

        assert trusted_devices == [(bus, "/org/bluez/hci0/dev_00_11_22_33_44_55")]

    asyncio.run(run_authorization())
