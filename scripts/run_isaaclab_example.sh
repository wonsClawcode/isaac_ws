#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

MODE="${1:-gui}"
DEFAULT_GUI_EXAMPLE="scripts/tutorials/00_sim/spawn_prims.py"
DEFAULT_HEADLESS_EXAMPLE="scripts/tutorials/00_sim/create_empty.py"
SCRIPT_PATH="${2:-}"

if [[ -z "${SCRIPT_PATH}" ]]; then
  if [[ "${MODE}" == "gui" ]]; then
    SCRIPT_PATH="${DEFAULT_GUI_EXAMPLE}"
  else
    SCRIPT_PATH="${DEFAULT_HEADLESS_EXAMPLE}"
  fi
fi

if [[ "$#" -ge 1 ]]; then
  shift
fi
if [[ "$#" -ge 1 ]]; then
  shift
fi

case "${SCRIPT_PATH}" in
  empty)
    SCRIPT_PATH="scripts/tutorials/00_sim/create_empty.py"
    ;;
  spawn_prims)
    SCRIPT_PATH="scripts/tutorials/00_sim/spawn_prims.py"
    ;;
esac

case "${MODE}" in
  gui)
    if running_inside_container; then
      cd /opt/IsaacLab
      ./isaaclab.sh -p "${SCRIPT_PATH}" "$@"
    else
      start_compose_service gui
      docker_exec_service bash -lc 'cd /opt/IsaacLab && script_path="$1"; shift; ./isaaclab.sh -p "$script_path" "$@"' bash "${SCRIPT_PATH}" "$@"
    fi
    ;;
  headless)
    if running_inside_container; then
      cd /opt/IsaacLab
      ./isaaclab.sh -p "${SCRIPT_PATH}" --headless "$@"
    else
      start_compose_service headless
      docker_exec_service bash -lc 'cd /opt/IsaacLab && script_path="$1"; shift; ./isaaclab.sh -p "$script_path" --headless "$@"' bash "${SCRIPT_PATH}" "$@"
    fi
    ;;
  *)
    echo "Usage: ./scripts/run_isaaclab_example.sh [gui|headless] [script_path|empty|spawn_prims] [extra args...]" >&2
    exit 1
    ;;
esac
