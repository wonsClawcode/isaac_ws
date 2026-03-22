#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="${ISAAC_WS_ROOT:-/workspace/isaac_ws}"
ISAAC_PYTHON="/isaac-sim/python.sh"

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
