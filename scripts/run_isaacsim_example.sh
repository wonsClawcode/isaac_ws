#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

MODE="${1:-gui}"
EXAMPLE_PATH="${2:-standalone_examples/api/isaacsim.simulation_app/hello_world.py}"

if [[ "$#" -ge 1 ]]; then
  shift
fi
if [[ "$#" -ge 1 ]]; then
  shift
fi

case "${MODE}" in
  gui)
    if running_inside_container; then
      cd /isaac-sim
      /isaac-sim/python.sh "${EXAMPLE_PATH}" "$@"
    else
      start_compose_service gui
      docker_exec_service bash -lc 'cd /isaac-sim && example_path="$1"; shift; /isaac-sim/python.sh "$example_path" "$@"' bash "${EXAMPLE_PATH}" "$@"
    fi
    ;;
  headless)
    if running_inside_container; then
      cd /isaac-sim
      /isaac-sim/python.sh "${EXAMPLE_PATH}" "$@"
    else
      start_compose_service headless
      docker_exec_service bash -lc 'cd /isaac-sim && example_path="$1"; shift; /isaac-sim/python.sh "$example_path" "$@"' bash "${EXAMPLE_PATH}" "$@"
    fi
    ;;
  *)
    echo "Usage: ./scripts/run_isaacsim_example.sh [gui|headless] [example_path] [extra args...]" >&2
    exit 1
    ;;
esac
