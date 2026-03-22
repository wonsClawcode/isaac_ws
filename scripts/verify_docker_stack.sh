#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

docker_compose run --rm isaac-lab /isaac-sim/python.sh -c \
  "from importlib.metadata import version; print(f'isaacsim={version(\"isaacsim\")}'); print(f'isaaclab={version(\"isaaclab\")}')"
