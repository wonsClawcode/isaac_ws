#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="${ISAAC_WS_ROOT:-/workspace/isaac_ws}"
ISAAC_PYTHON="${ISAACSIM_PYTHON_EXE:-/isaac-sim/python.sh}"

export ISAACSIM_PATH="${ISAACSIM_PATH:-/isaac-sim}"
export ISAACSIM_PYTHON_EXE="${ISAAC_PYTHON}"
export PYTHONPATH="${WORKSPACE_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

mkdir -p \
  "${WORKSPACE_ROOT}/runs" \
  "${WORKSPACE_ROOT}/logs" \
  "${WORKSPACE_ROOT}/checkpoints"

if [[ -f "${WORKSPACE_ROOT}/pyproject.toml" ]]; then
  "${ISAAC_PYTHON}" -m pip install -e "${WORKSPACE_ROOT}" --no-deps >/tmp/isaac_ws_pip.log 2>&1 || {
    cat /tmp/isaac_ws_pip.log
    exit 1
  }
fi

exec "$@"
