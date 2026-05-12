from __future__ import annotations

import argparse
import json

from .config import load_config


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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config()

    if args.command in {"discover", "ha-probe", "pipewire-probe", "bluez-probe", "status", "doctor"}:
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
