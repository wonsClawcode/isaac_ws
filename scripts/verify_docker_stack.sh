#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

VERIFY_SIM_APP_SMOKE="${VERIFY_SIM_APP_SMOKE:-0}"
VERIFY_APP_LAUNCHER_SMOKE="${VERIFY_APP_LAUNCHER_SMOKE:-0}"
VERIFY_APP_LAUNCHER_HEADLESS="${VERIFY_APP_LAUNCHER_HEADLESS:-1}"
VERIFY_APP_LAUNCHER_HIDE_UI="${VERIFY_APP_LAUNCHER_HIDE_UI:-0}"
VERIFY_APP_LAUNCHER_ENABLE_CAMERAS="${VERIFY_APP_LAUNCHER_ENABLE_CAMERAS:-0}"
VERIFY_APP_LAUNCHER_EXPERIENCE="${VERIFY_APP_LAUNCHER_EXPERIENCE:-}"
VERIFY_SMOKE_TIMEOUT_SEC="${VERIFY_SMOKE_TIMEOUT_SEC:-90}"
VERIFY_APP_LAUNCHER_KIT_ARGS="${VERIFY_APP_LAUNCHER_KIT_ARGS:---/rtx/verifyDriverVersion/enabled=false --/renderer/multiGpu/enabled=false --/renderer/multiGpu/autoEnable=false}"

RUN_DISPLAY=""
RUN_HEADLESS=1
RUN_GUI=0

if [[ "${VERIFY_APP_LAUNCHER_SMOKE}" == "1" && "${VERIFY_APP_LAUNCHER_HEADLESS}" != "1" ]]; then
  enable_gui_runtime
  RUN_DISPLAY="${DISPLAY}"
  RUN_HEADLESS=0
  RUN_GUI=1
fi

PYTHON_CODE=$(cat <<'PY'
import os
from importlib.metadata import PackageNotFoundError, distribution, version
from pathlib import Path

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


def package_file(dist_name: str, relative_path: str) -> str:
    try:
        return str(distribution(dist_name).locate_file(relative_path))
    except PackageNotFoundError:
        return "not-installed"


build_info_path = Path("/etc/isaac_ws-image-info")
if build_info_path.exists():
    for line in build_info_path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        print(f"image_{key.lower()}={value}")


isaacsim_version = version_or_fallback("isaacsim")
if isaacsim_version == "not-installed":
    version_file = Path("/isaac-sim/VERSION")
    if version_file.exists():
        isaacsim_version = version_file.read_text(encoding="utf-8").strip()

print(f"isaacsim={isaacsim_version}")
print(f"isaaclab={version_or_fallback('isaaclab', 'source-managed')}")
print(f"isaaclab_dist={dist_location('isaaclab')}")
print(f"isaaclab_tasks_version={version_or_fallback('isaaclab_tasks')}")
print(f"isaaclab_tasks_dist={dist_location('isaaclab_tasks')}")
print(f"isaaclab_rl_version={version_or_fallback('isaaclab_rl')}")
print(f"isaaclab_rl_dist={dist_location('isaaclab_rl')}")
print(f"rsl_rl_lib={version('rsl-rl-lib')}")
print(f"onnxscript={version('onnxscript')}")
print(f"torch={version_or_fallback('torch')}")
print(f"torch_dist={dist_location('torch')}")
print(f"torch_path={package_file('torch', 'torch/__init__.py')}")

import isaacsim

print(f"isaacsim_module={isaacsim.__file__}")
print(f"isaacsim_has_simulation_app={hasattr(isaacsim, 'SimulationApp')}")

run_smoke = os.getenv("VERIFY_SIM_APP_SMOKE", "0") == "1"
run_app_launcher_smoke = os.getenv("VERIFY_APP_LAUNCHER_SMOKE", "0") == "1"
if not run_smoke and not run_app_launcher_smoke:
    print("simulation_app_smoke=skipped (set VERIFY_SIM_APP_SMOKE=1 to run Isaac Sim compatibility check)")
    print("app_launcher_smoke=skipped (set VERIFY_APP_LAUNCHER_SMOKE=1 to run deeper Isaac Lab runtime smoke)")
elif run_app_launcher_smoke:
    from isaaclab.app import AppLauncher

    headless = os.getenv("VERIFY_APP_LAUNCHER_HEADLESS", "1") == "1"
    hide_ui = os.getenv("VERIFY_APP_LAUNCHER_HIDE_UI", "0") == "1"
    enable_cameras = os.getenv("VERIFY_APP_LAUNCHER_ENABLE_CAMERAS", "0") == "1"
    experience = os.getenv("VERIFY_APP_LAUNCHER_EXPERIENCE", "").strip()
    kit_args = os.getenv("VERIFY_APP_LAUNCHER_KIT_ARGS", "").strip()
    print(f"app_launcher_headless={headless}")
    print(f"app_launcher_hide_ui={hide_ui}")
    print(f"app_launcher_enable_cameras={enable_cameras}")
    print(f"app_launcher_experience={experience or 'default'}")
    print(f"app_launcher_kit_args={kit_args}")
    app_launcher_args = {
        "headless": headless,
        "hide_ui": hide_ui,
        "enable_cameras": enable_cameras,
        "device": "cuda:0",
        "distributed": False,
        "multi_gpu": False,
        "fast_shutdown": True,
        "kit_args": kit_args,
    }
    if experience:
        app_launcher_args["experience"] = experience
    app_launcher = AppLauncher(app_launcher_args)
    print("app_launcher_created=true")
    simulation_app = app_launcher.app
    try:
        from pxr import Usd
        print("app_launcher_import_pxr=true")
        import isaaclab_tasks
        print("app_launcher_import_isaaclab_tasks=true")
        import isaaclab_rl.rsl_rl as isaaclab_rsl_rl
        print("app_launcher_import_isaaclab_rl=true")
        from isaacsim.core.prims import Articulation

        print(f"pxr_usd={Usd.__module__}")
        print(f"isaaclab_tasks={isaaclab_tasks.__file__}")
        print(f"isaaclab_rsl_rl={isaaclab_rsl_rl.__file__}")
        print(f"isaacsim_core_prims={Articulation.__module__}")
        print("app_launcher_smoke=passed")
    finally:
        print("simulation_app_close=skipped in verify smoke")
PY
)

docker_compose run --rm -T \
  -e DISPLAY="${RUN_DISPLAY}" \
  -e HEADLESS="${RUN_HEADLESS}" \
  -e ISAAC_WS_GUI="${RUN_GUI}" \
  -e VERIFY_SIM_APP_SMOKE="${VERIFY_SIM_APP_SMOKE}" \
  -e VERIFY_APP_LAUNCHER_SMOKE="${VERIFY_APP_LAUNCHER_SMOKE}" \
  -e VERIFY_APP_LAUNCHER_HEADLESS="${VERIFY_APP_LAUNCHER_HEADLESS}" \
  -e VERIFY_APP_LAUNCHER_HIDE_UI="${VERIFY_APP_LAUNCHER_HIDE_UI}" \
  -e VERIFY_APP_LAUNCHER_ENABLE_CAMERAS="${VERIFY_APP_LAUNCHER_ENABLE_CAMERAS}" \
  -e VERIFY_APP_LAUNCHER_EXPERIENCE="${VERIFY_APP_LAUNCHER_EXPERIENCE}" \
  -e VERIFY_APP_LAUNCHER_KIT_ARGS="${VERIFY_APP_LAUNCHER_KIT_ARGS}" \
  isaac-lab /usr/local/bin/isaaclabpy -c "${PYTHON_CODE}"

if [[ "${VERIFY_SIM_APP_SMOKE}" == "1" ]]; then
  docker_compose run --rm -T \
    -e DISPLAY= \
    -e HEADLESS=1 \
    -e ISAAC_WS_GUI=0 \
    isaac-lab \
    timeout "${VERIFY_SMOKE_TIMEOUT_SEC}" \
    /isaac-sim/isaac-sim.compatibility_check.sh --/app/quitAfter=10 --no-window --reset-user
fi
