#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

if [[ "$#" -eq 0 ]]; then
  set -- bash
fi

docker_exec_service "$@"
