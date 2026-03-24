#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

docker_compose run --rm isaac-lab bash -lc 'cd /opt/IsaacLab && ./isaaclab.sh --generate-vscode-settings'
