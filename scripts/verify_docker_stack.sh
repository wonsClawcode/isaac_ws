#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

VERIFY_SIM_APP_SMOKE="${VERIFY_SIM_APP_SMOKE:-0}"

PYTHON_CODE=$(cat <<'PY'
import os
from importlib.metadata import PackageNotFoundError, distribution, version
from pathlib import Path

import torch

def version_or_fallback(dist_name: str, fallback: str = "not-installed") -> str:
    try:
        return version(dist_name)
    except PackageNotFoundError:
        return fallback


def dist_location(dist_name: str) -> str:
    try:
        return str(distribution(dist_name).locate_file(""))
    except PackageNotFoundError:
        return "not-installed"


isaacsim_version = version_or_fallback("isaacsim")
if isaacsim_version == "not-installed":
    version_file = Path("/isaac-sim/VERSION")
    if version_file.exists():
        isaacsim_version = version_file.read_text(encoding="utf-8").strip()

print(f"isaacsim={isaacsim_version}")
print(f"isaaclab={version('isaaclab')}")
print(f"isaaclab_dist={dist_location('isaaclab')}")
print(f"isaaclab_tasks_version={version_or_fallback('isaaclab_tasks')}")
print(f"isaaclab_tasks_dist={dist_location('isaaclab_tasks')}")
print(f"isaaclab_rl_version={version_or_fallback('isaaclab_rl')}")
print(f"isaaclab_rl_dist={dist_location('isaaclab_rl')}")
print(f"rsl_rl_lib={version('rsl-rl-lib')}")
print(f"onnxscript={version('onnxscript')}")
print(f"torch={torch.__version__}")
print(f"torch_path={torch.__file__}")

import isaacsim

print(f"isaacsim_module={isaacsim.__file__}")
print(f"isaacsim_has_simulation_app={hasattr(isaacsim, 'SimulationApp')}")

run_smoke = os.getenv("VERIFY_SIM_APP_SMOKE", "0") == "1"
if not run_smoke:
    print("simulation_app_smoke=skipped (set VERIFY_SIM_APP_SMOKE=1 to enable runtime imports)")
else:
    from isaacsim import SimulationApp

    simulation_app = SimulationApp({"headless": True})
    try:
        from pxr import Usd
        import isaaclab_tasks
        import isaaclab_rl.rsl_rl as isaaclab_rsl_rl
        from isaacsim.core.prims import Articulation

        print(f"pxr_usd={Usd.__module__}")
        print(f"isaaclab_tasks={isaaclab_tasks.__file__}")
        print(f"isaaclab_rsl_rl={isaaclab_rsl_rl.__file__}")
        print(f"isaacsim_core_prims={Articulation.__module__}")
        print("simulation_app_smoke=passed")
    finally:
        simulation_app.close()
PY
)

docker_compose run --rm -e VERIFY_SIM_APP_SMOKE="${VERIFY_SIM_APP_SMOKE}" isaac-lab /isaac-sim/python.sh -c "${PYTHON_CODE}"
