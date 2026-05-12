from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


A2DP_SINK_UUID = "0000110b-0000-1000-8000-00805f9b34fb"
A2DP_SOURCE_UUID = "0000110a-0000-1000-8000-00805f9b34fb"


@dataclass(frozen=True)
class MediaTransport:
    path: str
    device: str
    state: str
    uuid: str | None = None
    codec: int | None = None
    delay: int | None = None


def clamp_delay_units(units: int) -> int:
    return max(0, min(65535, units))


def ms_to_delay_units(delay_ms: float) -> int:
    return clamp_delay_units(round(delay_ms * 10))


def delay_units_to_ms(units: int) -> float:
    return units / 10.0


def select_active_transport(
    transports: Iterable[MediaTransport],
    device_path: str | None = None,
) -> MediaTransport | None:
    candidates = [
        transport
        for transport in transports
        if transport.state in {"active", "pending"}
        and (device_path is None or transport.device == device_path)
    ]
    if not candidates:
        return None

    def sort_key(transport: MediaTransport) -> tuple[int, int]:
        state_score = 0 if transport.state == "active" else 1
        uuid_score = 0 if transport.uuid in {A2DP_SOURCE_UUID, A2DP_SINK_UUID, None} else 1
        return (state_score, uuid_score)

    return sorted(candidates, key=sort_key)[0]
