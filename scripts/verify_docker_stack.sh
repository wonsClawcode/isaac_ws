#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

docker_compose run --rm isaac-lab /isaac-sim/python.sh -c \
  "from importlib.metadata import version; import torch; from isaacsim.core.prims import Articulation; print(f'isaacsim={version(\"isaacsim\")}'); print(f'isaaclab={version(\"isaaclab\")}'); print(f'torch={torch.__version__}'); print(f'torch_path={torch.__file__}'); print(f'isaacsim_core_prims={Articulation.__module__}')"
