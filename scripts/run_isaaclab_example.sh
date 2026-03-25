#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

MODE="${1:-gui}"
SCRIPT_PATH="${2:-scripts/tutorials/00_sim/create_empty.py}"

if [[ "$#" -ge 1 ]]; then
  shift
fi
if [[ "$#" -ge 1 ]]; then
  shift
fi

case "${MODE}" in
  gui)
    start_compose_service gui
    docker_exec_service bash -lc 'cd /opt/IsaacLab && script_path="$1"; shift; ./isaaclab.sh -p "$script_path" "$@"' bash "${SCRIPT_PATH}" "$@"
    ;;
  headless)
    start_compose_service headless
    docker_exec_service bash -lc 'cd /opt/IsaacLab && script_path="$1"; shift; ./isaaclab.sh -p "$script_path" --headless "$@"' bash "${SCRIPT_PATH}" "$@"
    ;;
  *)
    echo "Usage: ./scripts/run_isaaclab_example.sh [gui|headless] [script_path] [extra args...]" >&2
    exit 1
    ;;
esac
