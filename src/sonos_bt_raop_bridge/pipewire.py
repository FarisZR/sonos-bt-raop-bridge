from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PipeWireSink:
    id: str
    name: str
    description: str | None = None
