from __future__ import annotations

from statistics import median


def median_offset_ms(offsets_ms: list[float]) -> float:
    if not offsets_ms:
        raise ValueError("offset list must not be empty")
    return float(median(offsets_ms))
