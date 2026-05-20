from __future__ import annotations

import asyncio
import logging
import signal
from pathlib import Path

from dbus_next import Message, Variant
from dbus_next.aio import MessageBus
from dbus_next.constants import BusType, MessageType
from dbus_next.errors import DBusError
from dbus_next.service import ServiceInterface, method


AGENT_PATH = "/org/sonos_bt_raop_bridge/agent"
AGENT_CAPABILITY = "NoInputNoOutput"
LEGACY_PAIRING_ERROR = "org.bluez.Error.Rejected"

LOGGER = logging.getLogger(__name__)


async def _set_device_trusted(bus: MessageBus, device: str) -> None:
    reply = await bus.call(
        Message(
            destination="org.bluez",
            path=device,
            interface="org.freedesktop.DBus.Properties",
            member="Set",
            signature="ssv",
            body=["org.bluez.Device1", "Trusted", Variant("b", True)],
        )
    )
    if reply.message_type == MessageType.ERROR:
        LOGGER.warning("Could not mark device %s trusted: %s", device, reply.body)


class Agent(ServiceInterface):
    def __init__(self, bus: MessageBus | None = None) -> None:
        super().__init__("org.bluez.Agent1")
        self._bus = bus

    def _trust_device(self, device: str) -> None:
        if self._bus is None:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        task = loop.create_task(_set_device_trusted(self._bus, device))
        task.add_done_callback(lambda completed: self._log_trust_result(device, completed))

    @staticmethod
    def _log_trust_result(device: str, task: asyncio.Task[None]) -> None:
        try:
            task.result()
        except Exception:
            LOGGER.exception("Could not mark device %s trusted", device)

    @method()
    def Release(self) -> "":
        LOGGER.info("BlueZ released agent registration")
        return None

    @method()
    def RequestAuthorization(self, device: "o") -> "":
        LOGGER.info("Authorizing device %s", device)
        self._trust_device(device)
        return None

    @method()
    def AuthorizeService(self, device: "o", uuid: "s") -> "":
        LOGGER.info("Authorizing service %s for device %s", uuid, device)
        self._trust_device(device)
        return None

    @method()
    def RequestConfirmation(self, device: "o", passkey: "u") -> "":
        LOGGER.info("Accepting numeric comparison for device %s with passkey %06d", device, passkey)
        self._trust_device(device)
        return None

    @method()
    def RequestPairingConsent(self, device: "o") -> "":
        LOGGER.info("Accepting pairing consent for device %s", device)
        self._trust_device(device)
        return None

    @method()
    def RequestPinCode(self, device: "o") -> "s":
        LOGGER.warning("Rejecting legacy PIN pairing request for device %s", device)
        raise DBusError(LEGACY_PAIRING_ERROR, "Legacy PIN pairing is not supported")

    @method()
    def DisplayPinCode(self, device: "o", pincode: "s") -> "":
        LOGGER.info("Displaying legacy PIN code %s for device %s", pincode, device)
        return None

    @method()
    def RequestPasskey(self, device: "o") -> "u":
        LOGGER.warning("Rejecting legacy passkey pairing request for device %s", device)
        raise DBusError(LEGACY_PAIRING_ERROR, "Legacy passkey pairing is not supported")

    @method()
    def DisplayPasskey(self, device: "o", passkey: "u", entered: "q") -> "":
        LOGGER.info(
            "Displaying passkey %06d for device %s with %d digits entered",
            passkey,
            device,
            entered,
        )
        return None

    @method()
    def Cancel(self) -> "":
        LOGGER.info("BlueZ cancelled the current pairing flow")
        return None


async def _register_agent() -> MessageBus:
    system_bus_socket = Path("/run/dbus/system_bus_socket")
    if system_bus_socket.exists():
        bus = await MessageBus(bus_address=f"unix:path={system_bus_socket}").connect()
    else:
        bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    introspection = await bus.introspect("org.bluez", "/org/bluez")
    manager = bus.get_proxy_object("org.bluez", "/org/bluez", introspection).get_interface(
        "org.bluez.AgentManager1"
    )

    agent = Agent(bus)
    bus.export(AGENT_PATH, agent)
    await manager.call_register_agent(AGENT_PATH, AGENT_CAPABILITY)
    await manager.call_request_default_agent(AGENT_PATH)
    LOGGER.info("Registered BlueZ agent at %s with capability %s", AGENT_PATH, AGENT_CAPABILITY)
    return bus


async def _main() -> int:
    bus = await _register_agent()
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)
    await stop_event.wait()
    LOGGER.info("Stopping BlueZ agent")
    bus.disconnect()
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return asyncio.run(_main())


if __name__ == "__main__":
    raise SystemExit(main())
