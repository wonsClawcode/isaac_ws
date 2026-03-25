#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

usage() {
  cat <<'EOF'
Usage: ./scripts/run_task_smoke.sh [hydra overrides...]

Examples
  ./scripts/run_task_smoke.sh
  ./scripts/run_task_smoke.sh env.num_envs=49
  ./scripts/run_task_smoke.sh runtime=gui_debug env.num_envs=49 run.max_steps=0
  ./scripts/run_task_smoke.sh runtime=headless run.max_steps=300

Notes
  - 기본값은 Shadow Hand + sphere task를 gui_debug로 49 env 띄우는 smoke다.
  - host와 container 안에서 둘 다 실행할 수 있다.
  - smoke는 빠른 통합 확인용이라 기본 max_steps는 1500이다.
EOF
}

if [[ "${1:-}" == "help" || "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

should_use_gui=1
for arg in "$@"; do
  case "${arg}" in
    runtime=headless|runtime=headless_cameras|runtime=distributed_2gpu|runtime=distributed_4gpu|headless=true|app.headless=true)
      should_use_gui=0
      ;;
    runtime=gui|runtime=gui_*|runtime=gui-*|runtime=x11_compat|runtime=x11_*|runtime=x11-*|runtime.headless=false|headless=false|app.headless=false|ui_mode=x11|runtime.ui_mode=x11)
      should_use_gui=1
      ;;
  esac
done

if running_inside_container; then
  /usr/local/bin/isaaclabpy -m isaac_ws.launch smoke "$@"
else
  if [[ "${should_use_gui}" == "1" ]]; then
    start_compose_service gui
  else
    start_compose_service headless
  fi
  docker_exec_service /usr/local/bin/isaaclabpy -m isaac_ws.launch smoke "$@"
fi
