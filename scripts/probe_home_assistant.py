#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib import error

from sonos_bt_raop_bridge.config import load_config
from sonos_bt_raop_bridge.homeassistant import HomeAssistantClient, select_target_entity


def build_result() -> dict[str, object]:
    config = load_config()
    result: dict[str, object] = {
        "configured": bool(config.ha_url and config.ha_token),
        "ha_url": config.ha_url,
        "preferred_names": list(config.ha_target_friendly_names),
        "target_override": config.ha_target_entity,
    }
    if not result["configured"]:
        result["reachable"] = False
        result["error"] = "HA_URL/HA_TOKEN not configured"
        return result

    client = HomeAssistantClient(config.ha_url or "", config.ha_token or "")
    try:
        api_info = client.api_health()
        states = client.get_states()
    except error.URLError as exc:
        result["reachable"] = False
        result["error"] = f"URLError: {exc.reason}"
        return result
    except TimeoutError as exc:
        result["reachable"] = False
        result["error"] = f"TimeoutError: {exc}"
        return result
    except Exception as exc:  # pragma: no cover - defensive runtime path
        result["reachable"] = False
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    media_players = [state for state in states if state.entity_id.startswith("media_player.")]
    target = select_target_entity(
        media_players,
        override_entity_id=config.ha_target_entity,
        preferred_names=config.ha_target_friendly_names,
    )
    result.update(
        {
            "reachable": True,
            "api_message": api_info.get("message") if isinstance(api_info, dict) else None,
            "state_count": len(states),
            "media_player_count": len(media_players),
            "media_players": [
                {
                    "entity_id": player.entity_id,
                    "friendly_name": player.friendly_name,
                    "state": player.state,
                }
                for player in media_players
            ],
            "selected_target": None
            if target is None
            else {
                "entity_id": target.entity_id,
                "friendly_name": target.friendly_name,
                "state": target.state,
            },
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path)
    args = parser.parse_args()

    result = build_result()
    payload = json.dumps(result, indent=2, sort_keys=True)
    print(payload)

    if args.artifact_dir is not None:
        args.artifact_dir.mkdir(parents=True, exist_ok=True)
        (args.artifact_dir / "homeassistant-probe.json").write_text(payload + "\n", encoding="utf-8")

    return 0 if result.get("reachable") else 1


if __name__ == "__main__":
    raise SystemExit(main())
