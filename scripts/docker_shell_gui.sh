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

if compose_service_running; then
  docker_exec_service bash "$@"
else
  docker_compose run --rm "${ISAACLAB_SERVICE_NAME}" bash "$@"
fi
