#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="${ISAAC_WS_ROOT:-/workspace/hand_isaac}"
ISAAC_PYTHON="${ISAACSIM_PYTHON_EXE:-/isaac-sim/python.sh}"
ISAACLAB_PYTHON="${ISAACLAB_PYTHON_EXE:-/usr/local/bin/isaaclabpy}"
ISAACLAB_SOURCE_PATHS="${ISAACLAB_SOURCE_PATHS:-/opt/IsaacLab/source/isaaclab:/opt/IsaacLab/source/isaaclab_tasks:/opt/IsaacLab/source/isaaclab_rl:/opt/IsaacLab/source/isaaclab_assets}"

if [[ ! -x "${ISAAC_PYTHON}" ]]; then
  ISAAC_PYTHON="/isaac-sim/python.sh"
fi

if [[ ! -x "${ISAAC_PYTHON}" ]]; then
  echo "Isaac Sim python executable not found: ${ISAAC_PYTHON}" >&2
  exit 1
fi

export ISAACSIM_PATH="/isaac-sim"
export ISAACSIM_PYTHON_EXE="${ISAAC_PYTHON}"
export ISAACLAB_PYTHON_EXE="${ISAACLAB_PYTHON}"
export ISAACLAB_SOURCE_PATHS="${ISAACLAB_SOURCE_PATHS}"
export PYTHONPATH="${WORKSPACE_ROOT}/src:${ISAACLAB_SOURCE_PATHS}${PYTHONPATH:+:${PYTHONPATH}}"

mkdir -p \
  "${WORKSPACE_ROOT}/runs" \
  "${WORKSPACE_ROOT}/logs" \
  "${WORKSPACE_ROOT}/checkpoints"

if [[ -f "${WORKSPACE_ROOT}/pyproject.toml" ]]; then
  "${ISAACLAB_PYTHON}" -m pip install -e "${WORKSPACE_ROOT}" --no-deps >/tmp/hand_isaac_pip.log 2>&1 || {
    cat /tmp/hand_isaac_pip.log
    exit 1
  }
fi

exec "$@"
