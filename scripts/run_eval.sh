#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

configure_runtime_compose "$@"

docker_compose run --rm isaac-lab /usr/local/bin/isaaclabpy -m isaac_ws.launch eval "$@"
