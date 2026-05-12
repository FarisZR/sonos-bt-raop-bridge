#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
CAPTURE_DIR=${BTMON_CAPTURE_DIR:-"$ROOT_DIR/artifacts"}
CAPTURE_SECONDS=${BTMON_CAPTURE_SECONDS:-20}
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
CAPTURE_PATH=${1:-"$CAPTURE_DIR/btmon-$TIMESTAMP.log"}

mkdir -p "$CAPTURE_DIR"

if ! command -v btmon >/dev/null 2>&1; then
  printf 'btmon is not installed\n' >&2
  exit 1
fi

printf 'Capturing btmon output for %ss to %s\n' "$CAPTURE_SECONDS" "$CAPTURE_PATH" >&2

status=0
if ! sudo -n timeout --signal INT "${CAPTURE_SECONDS}s" btmon >"$CAPTURE_PATH" 2>&1; then
  status=$?
fi

case "$status" in
  0|124|130)
    printf '%s\n' "$CAPTURE_PATH"
    ;;
  *)
    exit "$status"
    ;;
esac
