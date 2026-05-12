from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
import json
import re
import subprocess


@dataclass(frozen=True)
class PipeWireSink:
    id: int
    name: str
    description: str | None = None
    media_class: str | None = None
    session_media: str | None = None


def _item_props(item: dict[str, Any]) -> dict[str, Any]:
    return dict(item.get("info", {}).get("props") or {})


def list_sinks(payload: Iterable[dict[str, Any]]) -> list[PipeWireSink]:
    sinks: list[PipeWireSink] = []
    for item in payload:
        if item.get("type") != "PipeWire:Interface:Node":
            continue

        props = _item_props(item)
        if props.get("media.class") != "Audio/Sink":
            continue

        name = props.get("node.name")
        if not isinstance(name, str) or not name:
            continue

        sink_id = item.get("id")
        if not isinstance(sink_id, int):
            continue

        sinks.append(
            PipeWireSink(
                id=sink_id,
                name=name,
                description=props.get("node.description"),
                media_class=props.get("media.class"),
                session_media=props.get("sess.media"),
            )
        )
    return sinks


def probe_sinks(command: tuple[str, ...] = ("pw-dump",)) -> list[PipeWireSink]:
    completed = subprocess.run(command, capture_output=True, text=True, check=True)
    return list_sinks(json.loads(completed.stdout))


def set_default_sink(sink_id: int, command: tuple[str, ...] = ("wpctl", "set-default")) -> None:
    subprocess.run([*command, str(sink_id)], check=True)


def select_target_sink(
    sinks: Iterable[PipeWireSink],
    name_pattern: str,
) -> PipeWireSink | None:
    regex = re.compile(name_pattern, re.IGNORECASE)
    candidates = [
        sink
        for sink in sinks
        if sink.session_media == "raop"
        and regex.search(" ".join(part for part in (sink.description, sink.name) if part))
    ]
    if not candidates:
        return None

    def sort_key(sink: PipeWireSink) -> tuple[int, str, str, int]:
        description = sink.description or ""
        exact_description_match = 0 if regex.fullmatch(description) else 1
        return (exact_description_match, description.casefold(), sink.name.casefold(), sink.id)

    return sorted(candidates, key=sort_key)[0]
