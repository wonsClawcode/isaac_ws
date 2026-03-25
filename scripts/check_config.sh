#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

docker_compose run --rm isaac-lab /usr/local/bin/isaaclabpy tools/check_config.py "$@"
