#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

docker_compose run --rm isaac-lab /isaac-sim/python.sh -m isaac_ws.train "$@"
