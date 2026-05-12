#!/usr/bin/env bash
set -euo pipefail

TARGET_USER=${1:-${SUDO_USER:-$USER}}
TARGET_UID=$(id -u "$TARGET_USER")
RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$TARGET_UID}
SESSION_BUS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=$RUNTIME_DIR/bus}

run_user() {
  if [[ $(id -un) == "$TARGET_USER" ]]; then
    env XDG_RUNTIME_DIR="$RUNTIME_DIR" DBUS_SESSION_BUS_ADDRESS="$SESSION_BUS" "$@"
    return
  fi

  sudo -u "$TARGET_USER" env XDG_RUNTIME_DIR="$RUNTIME_DIR" DBUS_SESSION_BUS_ADDRESS="$SESSION_BUS" "$@"
}

show_inotify_usage() {
  local pid fdinfo uid watch_count comm

  shopt -s nullglob
  for pid in /proc/[0-9]*; do
    uid=$(awk '/^Uid:/ {print $2}' "$pid/status" 2>/dev/null || true)
    [[ "$uid" == "$TARGET_UID" ]] || continue

    watch_count=0
    for fdinfo in "$pid"/fdinfo/*; do
      watch_count=$((watch_count + $(awk '/^inotify/ {count++} END {print count+0}' "$fdinfo" 2>/dev/null)))
    done

    if (( watch_count > 0 )); then
      comm=$(tr -d '\0' <"$pid/comm" 2>/dev/null || true)
      printf '%s %s %s\n' "${pid##*/}" "$watch_count" "$comm"
    fi
  done | sort -k2,2nr
  shopt -u nullglob
}

if [[ ! -S "$RUNTIME_DIR/bus" ]]; then
  printf 'Missing user session bus at %s\n' "$RUNTIME_DIR/bus" >&2
  exit 1
fi

printf 'Target user: %s (%s)\n' "$TARGET_USER" "$TARGET_UID"
printf 'Runtime dir: %s\n' "$RUNTIME_DIR"
printf 'Session bus: %s\n' "$SESSION_BUS"

printf '\n== Inotify limits ==\n'
sysctl fs.inotify.max_user_watches fs.inotify.max_user_instances fs.inotify.max_queued_events

printf '\n== Top inotify watch consumers ==\n'
show_inotify_usage || true

printf '\n== User services ==\n'
run_user systemctl --user --no-pager --full status pipewire.service wireplumber.service pipewire-pulse.service || true

printf '\n== wpctl status ==\n'
run_user wpctl status -n || true

printf '\n== PipeWire objects ==\n'
if command -v jq >/dev/null 2>&1; then
  run_user pw-dump | jq '[.[] | select(.type == "PipeWire:Interface:Node") | {id: .id, name: .info.props."node.name", description: .info.props."node.description", media_class: .info.props."media.class", sess_media: .info.props."sess.media"}]' || true
else
  run_user pw-cli ls Device Node Metadata || true
fi

printf '\n== RAOP services ==\n'
if command -v avahi-browse >/dev/null 2>&1; then
  avahi-browse -rt _raop._tcp || true
else
  printf 'avahi-browse not installed\n'
fi

printf '\n== Matching RAOP sink ==\n'
if command -v jq >/dev/null 2>&1; then
  run_user pw-dump | jq --arg regex "${SONOS_RAOP_NAME_REGEX:-Kitchen|Küche|Kueche}" '[
    .[]
    | select(.type == "PipeWire:Interface:Node")
    | select(.info.props."media.class" == "Audio/Sink")
    | select(.info.props."sess.media" == "raop")
    | {
        id: .id,
        name: .info.props."node.name",
        description: .info.props."node.description"
      }
    | select((((.description // "") + " " + (.name // "")) | test($regex; "i")))
  ] | sort_by(.description // "", .name) | .[0]' || true
else
  printf 'jq not installed\n'
fi

printf '\n== User service logs ==\n'
run_user journalctl --user -u pipewire.service -u wireplumber.service -u pipewire-pulse.service -n 80 --no-pager || true
