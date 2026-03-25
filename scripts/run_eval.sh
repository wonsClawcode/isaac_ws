#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

usage() {
  cat <<'EOF'
Usage: ./scripts/run_eval.sh [hydra overrides...]

Examples
  ./scripts/run_eval.sh task=grasp_sphere_shadow_hand_only checkpoint_path=/workspace/isaac_ws/checkpoints/rsl_rl/your_experiment/model.pt
  ./scripts/run_eval.sh runtime=gui_debug task=grasp_sphere_shadow_hand_only checkpoint_path=/workspace/isaac_ws/checkpoints/rsl_rl/your_experiment/model.pt

Notes
  - host에서 실행하면 persistent container를 자동으로 올리거나 재사용한다.
  - container 안에서 실행하면 Docker CLI 없이 바로 launcher를 호출한다.
EOF
}

if [[ "${1:-}" == "help" || "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if running_inside_container; then
  /usr/local/bin/isaaclabpy -m isaac_ws.launch eval "$@"
else
  if requires_gui_runtime "$@"; then
    start_compose_service gui
  else
    start_compose_service headless
  fi
  docker_exec_service /usr/local/bin/isaaclabpy -m isaac_ws.launch eval "$@"
fi
