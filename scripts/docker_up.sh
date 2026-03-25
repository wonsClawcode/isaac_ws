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
    ;;
  *)
    echo "Usage: ./scripts/docker_up.sh [headless|gui]" >&2
    exit 1
    ;;
esac

start_compose_service "${MODE}"
docker_compose ps "${ISAACLAB_SERVICE_NAME}"
