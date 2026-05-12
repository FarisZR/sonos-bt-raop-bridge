from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
import os


DEFAULT_FRIENDLY_NAMES = (
    "Kitchen",
    "Küche",
    "Kuche",
    "Kueche",
    "Kitchen Stereo",
    "Küche Stereo",
    "Kuche Stereo",
    "Kueche Stereo",
)


@dataclass(frozen=True)
class BridgeConfig:
    android_serial: str | None
    ha_url: str | None
    ha_token: str | None
    ha_target_entity: str | None
    ha_target_friendly_names: tuple[str, ...]
    bridge_bt_alias: str
    sonos_raop_name_regex: str
    safe_test_volume: float
    max_test_volume: float
    test_http_port: int
    default_reported_delay_ms: int
    calibration_min_delay_ms: int
    calibration_max_delay_ms: int


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except PermissionError:
        return values

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _merge_env(
    base: Mapping[str, str],
    overlay: Mapping[str, str],
) -> dict[str, str]:
    merged = dict(base)
    merged.update({key: value for key, value in overlay.items() if value != ""})
    return merged


def _normalize_aliases(values: Mapping[str, str]) -> dict[str, str]:
    normalized = dict(values)
    if normalized.get("HASS_SERVER") and not normalized.get("HA_URL"):
        normalized["HA_URL"] = normalized["HASS_SERVER"]
    if normalized.get("HASS_TOKEN") and not normalized.get("HA_TOKEN"):
        normalized["HA_TOKEN"] = normalized["HASS_TOKEN"]
    return normalized


def _parse_names(raw_value: str | None) -> tuple[str, ...]:
    if not raw_value:
        return DEFAULT_FRIENDLY_NAMES
    parts = tuple(part.strip() for part in raw_value.split(",") if part.strip())
    return parts or DEFAULT_FRIENDLY_NAMES


def _optional_string(values: Mapping[str, str], key: str) -> str | None:
    value = values.get(key)
    return value if value else None


def load_config(
    env: Mapping[str, str] | None = None,
    dotenv_paths: tuple[Path, ...] | None = None,
) -> BridgeConfig:
    env_values = dict(os.environ if env is None else env)
    repo_root = Path(__file__).resolve().parents[2]
    search_paths = dotenv_paths or (
        repo_root / ".env",
        Path("/etc/sonos-bt-raop-bridge/env"),
        Path("/etc/sonos-bt-bridge-lab/env"),
    )

    merged: dict[str, str] = {}
    for path in search_paths:
        merged = _merge_env(merged, _parse_env_file(path))
    merged = _merge_env(merged, env_values)
    merged = _normalize_aliases(merged)

    return BridgeConfig(
        android_serial=_optional_string(merged, "ANDROID_SERIAL"),
        ha_url=_optional_string(merged, "HA_URL"),
        ha_token=_optional_string(merged, "HA_TOKEN"),
        ha_target_entity=_optional_string(merged, "HA_TARGET_ENTITY"),
        ha_target_friendly_names=_parse_names(merged.get("HA_TARGET_FRIENDLY_NAMES")),
        bridge_bt_alias=merged.get("BRIDGE_BT_ALIAS", "SonosBridge"),
        sonos_raop_name_regex=merged.get("SONOS_RAOP_NAME_REGEX", "Kitchen|Küche|Kueche"),
        safe_test_volume=float(merged.get("SAFE_TEST_VOLUME", "0.20")),
        max_test_volume=float(merged.get("MAX_TEST_VOLUME", "0.65")),
        test_http_port=int(merged.get("TEST_HTTP_PORT", "8765")),
        default_reported_delay_ms=int(merged.get("DEFAULT_REPORTED_DELAY_MS", "1800")),
        calibration_min_delay_ms=int(merged.get("CALIBRATION_MIN_DELAY_MS", "800")),
        calibration_max_delay_ms=int(merged.get("CALIBRATION_MAX_DELAY_MS", "3000")),
    )
