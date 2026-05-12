from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from .config import load_config
from .homeassistant import HomeAssistantClient, select_target_entity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sonos-bt-bridge")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("discover")
    subparsers.add_parser("ha-probe")
    subparsers.add_parser("pipewire-probe")
    subparsers.add_parser("bluez-probe")
    subparsers.add_parser("calibrate")
    subparsers.add_parser("status")
    subparsers.add_parser("doctor")
    subparsers.add_parser("install-systemd")

    set_delay = subparsers.add_parser("set-delay")
    set_delay.add_argument("--ms", type=float, required=True)
    return parser


def _run_script(path: Path) -> int:
    completed = subprocess.run([str(path)], check=False)
    return completed.returncode


def _ha_probe() -> int:
    config = load_config()
    result = {
        "ha_url": config.ha_url,
        "configured": bool(config.ha_url and config.ha_token),
    }
    if not result["configured"]:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    client = HomeAssistantClient(config.ha_url or "", config.ha_token or "")
    states = client.get_states()
    target = select_target_entity(
        states,
        override_entity_id=config.ha_target_entity,
        preferred_names=config.ha_target_friendly_names,
    )
    result.update(
        {
            "state_count": len(states),
            "target": None
            if target is None
            else {
                "entity_id": target.entity_id,
                "friendly_name": target.friendly_name,
                "state": target.state,
            },
        }
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if target is not None else 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config()
    project_root = Path(__file__).resolve().parents[2]

    if args.command == "discover":
        return _run_script(project_root / "scripts" / "discover_environment.sh")

    if args.command == "ha-probe":
        return _ha_probe()

    if args.command in {"pipewire-probe", "bluez-probe", "status", "doctor"}:
        print(
            json.dumps(
                {
                    "command": args.command,
                    "ha_url": config.ha_url,
                    "bridge_bt_alias": config.bridge_bt_alias,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.command == "set-delay":
        print(json.dumps({"delay_ms": args.ms}, indent=2, sort_keys=True))
        return 0

    if args.command in {"calibrate", "install-systemd"}:
        print(json.dumps({"command": args.command, "status": "pending"}, indent=2, sort_keys=True))
        return 0

    parser.error(f"unhandled command: {args.command}")
    return 2
