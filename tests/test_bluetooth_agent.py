import asyncio

import pytest

import sonos_bt_raop_bridge.bluetooth_agent as bluetooth_agent
from sonos_bt_raop_bridge.bluetooth_agent import AGENT_CAPABILITY, LEGACY_PAIRING_ERROR, Agent


def test_agent_uses_headless_pairing_capability() -> None:
    assert AGENT_CAPABILITY == "NoInputNoOutput"


def test_agent_rejects_legacy_pairing_prompts() -> None:
    agent = Agent()

    with pytest.raises(Exception) as pin_error:
        Agent.RequestPinCode.__wrapped__(agent, "/org/bluez/hci0/dev_00_11_22_33_44_55")
    with pytest.raises(Exception) as passkey_error:
        Agent.RequestPasskey.__wrapped__(agent, "/org/bluez/hci0/dev_00_11_22_33_44_55")

    assert getattr(pin_error.value, "type", None) == LEGACY_PAIRING_ERROR
    assert getattr(passkey_error.value, "type", None) == LEGACY_PAIRING_ERROR


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
