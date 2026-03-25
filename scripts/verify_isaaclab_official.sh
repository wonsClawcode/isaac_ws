#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

MODE="${1:-gui}"
ISAACLAB_ROOT="${ISAACLAB_ROOT:-/opt/IsaacLab}"

if [[ "${MODE}" == "gui" ]]; then
  enable_gui_runtime
  docker_compose run --rm isaac-lab bash -lc '
    set -euo pipefail
    cd "'"${ISAACLAB_ROOT}"'"
    test_script="scripts/tutorials/00_sim/create_empty.py"
    if [[ ! -f "${test_script}" ]]; then
      test_script="source/standalone/tutorials/00_sim/create_empty.py"
    fi
    ./isaaclab.sh -p "${test_script}"
  '
elif [[ "${MODE}" == "headless" ]]; then
  docker_compose run --rm -T \
    -e DISPLAY= \
    -e HEADLESS=1 \
    -e ISAAC_WS_GUI=0 \
    isaac-lab bash -lc '
      set -euo pipefail
      cd "'"${ISAACLAB_ROOT}"'"
      test_script="scripts/tutorials/00_sim/create_empty.py"
      if [[ ! -f "${test_script}" ]]; then
        test_script="source/standalone/tutorials/00_sim/create_empty.py"
      fi
      ./isaaclab.sh -p "${test_script}" --headless
    '
else
  echo "Usage: ./scripts/verify_isaaclab_official.sh [gui|headless]" >&2
  exit 1
fi
