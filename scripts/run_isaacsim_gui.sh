#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

if [[ -z "${DISPLAY:-}" ]]; then
  echo "DISPLAY is required for GUI runs." >&2
  exit 1
fi

if [[ ! -r "${XAUTHORITY_PATH}" ]]; then
  echo "Xauthority file not found or unreadable: ${XAUTHORITY_PATH}" >&2
  exit 1
fi

export DOCKER_COMPOSE_EXTRA_FILE="${ROOT_DIR}/docker/docker-compose.gui.yml"
export HEADLESS=0
export OMNI_KIT_ALLOW_ROOT="${OMNI_KIT_ALLOW_ROOT:-1}"

docker_compose run --rm isaac-lab /isaac-sim/isaac-sim.sh --allow-root "$@"
