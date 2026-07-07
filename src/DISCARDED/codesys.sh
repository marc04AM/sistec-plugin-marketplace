#!/usr/bin/env bash
# codesys.sh - manage the CODESYS / Portainer containers via per-container compose files.
#
# Usage:
#   ./codesys.sh <action> <name1,name2,...|all>
#   ./codesys.sh <name1,name2,...|all>          # action defaults to "up"
#
# Actions:
#   up        create & start the container(s)              (docker compose up -d)
#   down      stop & remove the container(s)               (docker compose down)
#   restart   restart in place - resets the 2h demo timer  (docker compose restart)
#   recreate  down + up: clean slate, also resets the demo
#   status    show container state                         (docker compose ps)
#   logs      tail the last 80 log lines                   (docker compose logs)
#   list      list the available compose files
#
# <names> are container names; each maps to "<name>.compose.yaml" next to this script.
# "all" expands to every *.compose.yaml found in that directory.
#
# The 2-hour CODESYS demo lives in the runtime PROCESS, so "restart" or "recreate"
# gives a fresh 2 hours - no need to terminate WSL.
#
# Examples:
#   ./codesys.sh up vPLC1,vPLC2          # start two PLCs
#   ./codesys.sh restart vPLC1,vPLC2,vPLC3   # renew the demo on all three
#   ./codesys.sh recreate all            # rebuild everything from the compose files
#   ./codesys.sh status all
#   ./codesys.sh logs vPLC1

set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NETWORK="codesys"
NET_SUBNET="172.40.0.0/16"
NET_GATEWAY="172.40.0.1"
NET_BRIDGE="codesys0"

# License-server IP handed to the CODESYS runtime (startup.sh -s). Default to the VM's
# current eth0 address so it survives WSL reboots; override by exporting HOST_IP.
if [ -z "${HOST_IP:-}" ]; then
  HOST_IP="$(ip -4 -o addr show eth0 2>/dev/null | awk '{print $4}' | cut -d/ -f1)"
  [ -z "$HOST_IP" ] && HOST_IP="172.24.139.190"
fi
export HOST_IP

die()   { echo "ERROR: $*" >&2; exit 1; }
usage() { sed -n '2,30p' "$0"; exit 1; }

ensure_network() {
  docker network inspect "$NETWORK" >/dev/null 2>&1 && return 0
  echo "[*] creating missing network '$NETWORK' ($NET_SUBNET)"
  docker network create \
    --subnet "$NET_SUBNET" --gateway "$NET_GATEWAY" \
    -o com.docker.network.bridge.name="$NET_BRIDGE" \
    "$NETWORK" >/dev/null
}

compose_file() {
  local f="$DIR/$1.compose.yaml"
  [ -f "$f" ] || die "no compose file for '$1' (expected $f)"
  printf '%s' "$f"
}

# Free the container name for our compose project before 'up'. Removes a same-named
# container that is either NOT compose-managed (e.g. one the CODESYS autostart service
# created with --rm) OR belongs to a DIFFERENT compose project than the one we are about
# to use (so an old project-naming scheme reconciles cleanly). A container already in the
# target project is left alone, keeping 'up' idempotent.
clear_stale() {
  local name="$1" want="${2:-}" proj
  docker container inspect "$name" >/dev/null 2>&1 || return 0
  proj="$(docker container inspect -f '{{ index .Config.Labels "com.docker.compose.project" }}' "$name" 2>/dev/null)"
  if [ -z "$proj" ] || [ "$proj" = "<no value>" ]; then
    echo "[*] removing non-compose container '$name' (freeing name/ports/IP)"
    docker rm -f "$name" >/dev/null 2>&1 || true
  elif [ -n "$want" ] && [ "$proj" != "$want" ]; then
    echo "[*] removing container '$name' from old project '$proj' (migrating to '$want')"
    docker rm -f "$name" >/dev/null 2>&1 || true
  fi
}

# ---- argument parsing ----
ACTIONS="up down restart recreate status logs list"
[ $# -ge 1 ] || usage

if [ $# -eq 1 ]; then
  case " $ACTIONS " in
    *" $1 "*) ACTION="$1"; NAMES="" ;;    # a bare action (meaningful only for 'list')
    *)        ACTION="up"; NAMES="$1" ;;  # a bare name list -> default action 'up'
  esac
else
  ACTION="$1"; NAMES="$2"
fi

case " $ACTIONS " in *" $ACTION "*) ;; *) die "unknown action '$ACTION'";; esac

if [ "$ACTION" = "list" ]; then
  echo "Available containers (compose files in $DIR):"
  for f in "$DIR"/*.compose.yaml; do [ -e "$f" ] && echo "  - $(basename "$f" .compose.yaml)"; done
  exit 0
fi

[ -n "${NAMES:-}" ] || usage

if [ "$NAMES" = "all" ]; then
  NAMES=""
  for f in "$DIR"/*.compose.yaml; do
    [ -e "$f" ] || continue
    NAMES="$NAMES,$(basename "$f" .compose.yaml)"
  done
  NAMES="${NAMES#,}"
fi

ensure_network

IFS=',' read -ra LIST <<< "$NAMES"
rc=0
for raw in "${LIST[@]}"; do
  name="$(echo "$raw" | xargs)"   # trim surrounding whitespace
  [ -n "$name" ] || continue
  f="$(compose_file "$name")" || { rc=1; continue; }
  # Give each container its own isolated compose project (lowercased, valid chars),
  # so files in the same directory don't treat each other as orphans.
  proj="codesys-$(printf '%s' "$name" | tr 'A-Z' 'a-z' | tr -c 'a-z0-9_-' '-')"
  # Build as an array so a compose-file path containing spaces (e.g. ".../Sistec 23/...")
  # is passed as a single argument rather than word-split.
  C=(docker compose -p "$proj" -f "$f")
  echo "=== ${ACTION}: ${name} (project=${proj}, HOST_IP=${HOST_IP}) ==="
  case "$ACTION" in
    up)       clear_stale "$name" "$proj"; "${C[@]}" up -d ;;
    down)     "${C[@]}" down ;;
    restart)  "${C[@]}" restart ;;
    recreate) "${C[@]}" down; clear_stale "$name" "$proj"; "${C[@]}" up -d ;;
    status)   "${C[@]}" ps ;;
    logs)     "${C[@]}" logs --tail 80 ;;
  esac || rc=1
  echo $(date -u)
done
exit $rc
