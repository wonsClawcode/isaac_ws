#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

EXAMPLE_PATH="${1:-standalone_examples/api/isaacsim.simulation_app/hello_world.py}"

if [[ "$#" -ge 1 ]]; then
  shift
fi

ensure_compose_service_running
docker_exec_service bash -lc 'cd /isaac-sim && example_path="$1"; shift; /isaac-sim/python.sh "$example_path" "$@"' bash "${EXAMPLE_PATH}" "$@"
