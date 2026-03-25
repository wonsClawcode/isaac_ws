#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

if compose_service_running; then
  docker_exec_service bash "$@"
else
  docker_compose run --rm "${ISAACLAB_SERVICE_NAME}" bash "$@"
fi
