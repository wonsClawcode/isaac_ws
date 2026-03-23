#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

PYTHON_CODE=$(cat <<'PY'
from importlib.metadata import version

import torch
from isaacsim import SimulationApp

print(f"isaacsim={version('isaacsim')}")
print(f"isaaclab={version('isaaclab')}")
print(f"rsl_rl_lib={version('rsl-rl-lib')}")
print(f"onnxscript={version('onnxscript')}")
print(f"torch={torch.__version__}")
print(f"torch_path={torch.__file__}")

simulation_app = SimulationApp({"headless": True})

try:
    from isaacsim.core.prims import Articulation

    print(f"isaacsim_core_prims={Articulation.__module__}")

    try:
        import isaaclab_rl.rsl_rl as isaaclab_rsl_rl

        print(f"isaaclab_rsl_rl={isaaclab_rsl_rl.__file__}")
    except Exception as exc:
        print(f"isaaclab_rsl_rl_error={type(exc).__name__}: {exc}")
        raise
finally:
    simulation_app.close()
PY
)

docker_compose run --rm isaac-lab /isaac-sim/python.sh -c "${PYTHON_CODE}"
