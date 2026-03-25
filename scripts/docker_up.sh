#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

MODE="${1:-headless}"

case "${MODE}" in
  headless)
    shift || true
    ;;
  gui)
    shift || true
    enable_gui_runtime
    ;;
  *)
    echo "Usage: ./scripts/docker_up.sh [headless|gui]" >&2
    exit 1
    ;;
esac

docker_compose up -d "${ISAACLAB_SERVICE_NAME}"
docker_compose ps "${ISAACLAB_SERVICE_NAME}"
