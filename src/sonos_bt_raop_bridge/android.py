from __future__ import annotations

from dataclasses import dataclass
import re
import subprocess

from .config import load_config


DEVICE_LINE_RE = re.compile(r"^(?P<serial>\S+)\s+(?P<state>\S+)(?:\s+(?P<details>.*))?$")
MODEL_TOKEN_RE = re.compile(r"(?:^|\s)model:(?P<model>\S+)")
RESUMED_ACTIVITY_PATTERNS = (
    re.compile(r"ResumedActivity:\s+ActivityRecord\{[^\s]+\s+u\d+\s+(?P<component>\S+)"),
    re.compile(r"mFocusedApp=ActivityRecord\{[^\s]+\s+u\d+\s+(?P<component>\S+)"),
)


@dataclass(frozen=True)
class AdbDevice:
    serial: str
    state: str
    model: str | None = None


def _parse_adb_devices(output: str) -> list[AdbDevice]:
    devices: list[AdbDevice] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("List of devices attached"):
            continue

        match = DEVICE_LINE_RE.match(line)
        if match is None:
            continue

        details = match.group("details") or ""
        model_match = MODEL_TOKEN_RE.search(details)
        devices.append(
            AdbDevice(
                serial=match.group("serial"),
                state=match.group("state"),
                model=model_match.group("model") if model_match is not None else None,
            )
        )
    return devices


def _select_device(devices: list[AdbDevice], configured_serial: str | None) -> AdbDevice | None:
    if configured_serial:
        for device in devices:
            if device.serial == configured_serial:
                return device
    for device in devices:
        if device.state == "device":
            return device
    return devices[0] if devices else None


def _parse_resumed_activity(output: str) -> str | None:
    for pattern in RESUMED_ACTIVITY_PATTERNS:
        match = pattern.search(output)
        if match is not None:
            return match.group("component")
    return None


def _adb_command(*args: str, serial: str | None = None) -> list[str]:
    command = ["adb"]
    if serial:
        command.extend(["-s", serial])
    command.extend(args)
    return command


def _run_adb(*args: str, serial: str | None = None) -> str:
    command = _adb_command(*args, serial=serial)
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if completed.returncode != 0:
        raise subprocess.CalledProcessError(
            completed.returncode,
            command,
            output=completed.stdout,
            stderr=completed.stderr,
        )
    return completed.stdout.strip()


def _describe_command_failure(exc: Exception) -> str:
    if isinstance(exc, FileNotFoundError):
        return f"FileNotFoundError: {exc}"
    if isinstance(exc, subprocess.TimeoutExpired):
        return f"TimeoutExpired: {' '.join(exc.cmd)}"
    if isinstance(exc, subprocess.CalledProcessError):
        detail = (exc.stderr or exc.output or "").strip()
        return f"CalledProcessError: {detail or exc.returncode}"
    return f"{type(exc).__name__}: {exc}"


def probe_android_status() -> dict[str, object]:
    config = load_config()
    status: dict[str, object] = {
        "adb_connected": False,
        "adb_serial": config.android_serial,
    }

    try:
        devices = _parse_adb_devices(_run_adb("devices", "-l"))
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        status["adb_error"] = _describe_command_failure(exc)
        return status

    device = _select_device(devices, config.android_serial)
    if device is None:
        status["adb_state"] = "missing"
        status["adb_error"] = "No adb devices attached"
        return status

    status.update(
        {
            "adb_serial": device.serial,
            "adb_state": device.state,
            "adb_connected": device.state == "device",
        }
    )
    if device.model:
        status["adb_model"] = device.model

    if device.state != "device":
        return status

    try:
        model = _run_adb("shell", "getprop", "ro.product.model", serial=device.serial)
        bluetooth_on = _run_adb("shell", "settings", "get", "global", "bluetooth_on", serial=device.serial)
        activities = _run_adb("shell", "dumpsys", "activity", "activities", serial=device.serial)
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        status["adb_error"] = _describe_command_failure(exc)
        return status

    if model:
        status["adb_model"] = model
    if bluetooth_on in {"0", "1"}:
        status["android_bluetooth_on"] = bluetooth_on == "1"

    focus = _parse_resumed_activity(activities)
    if focus:
        status["android_focus"] = focus

    return status


def adb_device_route_summary() -> str:
    status = probe_android_status()
    pieces = [f"adb_state={status.get('adb_state', 'missing')}"]

    serial = status.get("adb_serial")
    if isinstance(serial, str) and serial:
        pieces.append(f"serial={serial}")

    model = status.get("adb_model")
    if isinstance(model, str) and model:
        pieces.append(f"model={model}")

    bluetooth_on = status.get("android_bluetooth_on")
    if isinstance(bluetooth_on, bool):
        pieces.append(f"bluetooth={'on' if bluetooth_on else 'off'}")

    focus = status.get("android_focus")
    if isinstance(focus, str) and focus:
        pieces.append(f"focus={focus}")

    error = status.get("adb_error")
    if isinstance(error, str) and error:
        pieces.append(f"error={error}")

    return " ".join(pieces)
