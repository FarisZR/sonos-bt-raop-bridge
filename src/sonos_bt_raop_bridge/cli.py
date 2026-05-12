from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from .android import probe_android_status
from .config import load_config
from .homeassistant import HomeAssistantClient, select_target_entity
from .pipewire import probe_sinks, select_target_sink, set_default_sink


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sonos-bt-bridge")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("discover")
    subparsers.add_parser("ha-probe")
    subparsers.add_parser("pipewire-probe")
    subparsers.add_parser("bluez-probe")
    subparsers.add_parser("calibrate")
    subparsers.add_parser("set-default-sink")
    subparsers.add_parser("status")
    subparsers.add_parser("doctor")
    subparsers.add_parser("install-systemd")

    set_delay = subparsers.add_parser("set-delay")
    set_delay.add_argument("--ms", type=float, required=True)
    return parser


def _run_script(path: Path) -> int:
    command = [str(path)]
    if path.suffix == ".sh":
        command = ["bash", str(path)]
    completed = subprocess.run(command, check=False)
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


def _pipewire_status() -> dict[str, object]:
    config = load_config()
    try:
        sinks = probe_sinks()
    except FileNotFoundError as exc:
        return {"pipewire_error": f"FileNotFoundError: {exc}"}
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        detail = stderr or stdout or str(exc)
        return {"pipewire_error": f"CalledProcessError: {detail}"}
    except json.JSONDecodeError as exc:
        return {"pipewire_error": f"JSONDecodeError: {exc}"}

    raop_sinks = [sink for sink in sinks if sink.session_media == "raop"]
    target = select_target_sink(raop_sinks, config.sonos_raop_name_regex)
    return {
        "pipewire_sink_count": len(sinks),
        "pipewire_raop_sink_count": len(raop_sinks),
        "pipewire_target": None
        if target is None
        else {
            "id": target.id,
            "name": target.name,
            "description": target.description,
        },
    }


def _set_default_pipewire_sink() -> int:
    config = load_config()
    try:
        sinks = probe_sinks()
    except FileNotFoundError as exc:
        print(json.dumps({"pipewire_error": f"FileNotFoundError: {exc}"}, indent=2, sort_keys=True))
        return 1
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        detail = stderr or stdout or str(exc)
        print(json.dumps({"pipewire_error": f"CalledProcessError: {detail}"}, indent=2, sort_keys=True))
        return 1
    except json.JSONDecodeError as exc:
        print(json.dumps({"pipewire_error": f"JSONDecodeError: {exc}"}, indent=2, sort_keys=True))
        return 1

    raop_sinks = [sink for sink in sinks if sink.session_media == "raop"]
    target = select_target_sink(raop_sinks, config.sonos_raop_name_regex)
    if target is None:
        print(json.dumps({"pipewire_error": "No matching RAOP sink found"}, indent=2, sort_keys=True))
        return 1

    try:
        set_default_sink(target.id)
    except FileNotFoundError as exc:
        print(json.dumps({"pipewire_error": f"FileNotFoundError: {exc}"}, indent=2, sort_keys=True))
        return 1
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        detail = stderr or stdout or str(exc)
        print(json.dumps({"pipewire_error": f"CalledProcessError: {detail}"}, indent=2, sort_keys=True))
        return 1

    print(
        json.dumps(
            {
                "pipewire_default_sink": {
                    "id": target.id,
                    "name": target.name,
                    "description": target.description,
                }
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config()
    project_root = Path(__file__).resolve().parents[2]
    script_commands = {
        "discover": "discover_environment.sh",
        "pipewire-probe": "probe_pipewire_raop.sh",
        "bluez-probe": "probe_bluez_a2dp.sh",
    }

    if args.command in script_commands:
        return _run_script(project_root / "scripts" / script_commands[args.command])

    if args.command == "ha-probe":
        return _ha_probe()

    if args.command == "set-default-sink":
        return _set_default_pipewire_sink()

    if args.command in {"status", "doctor"}:
        payload = {
            "command": args.command,
            "ha_url": config.ha_url,
            "bridge_bt_alias": config.bridge_bt_alias,
            "android": probe_android_status(),
        }
        payload.update(_pipewire_status())
        print(
            json.dumps(payload, indent=2, sort_keys=True)
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
