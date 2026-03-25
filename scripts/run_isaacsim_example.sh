#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/example_catalog.sh"

usage() {
  cat <<'EOF'
Usage: ./scripts/run_isaacsim_example.sh [gui|headless] [example_path|alias] [extra args...]

Examples
  ./scripts/run_isaacsim_example.sh gui
  ./scripts/run_isaacsim_example.sh hello_world
  ./scripts/run_isaacsim_example.sh list

Notes
  - 기본 example은 hello_world.py다.
  - host와 container 안에서 둘 다 실행할 수 있다.
EOF
}

if [[ "${1:-}" == "help" || "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "list" || "${1:-}" == "--list" ]]; then
  print_examples_catalog
  exit 0
fi

MODE="${1:-gui}"
EXAMPLE_PATH=""

case "${MODE}" in
  gui|headless)
    shift || true
    EXAMPLE_PATH="${1:-}"
    ;;
  *)
    EXAMPLE_PATH="${MODE}"
    MODE="gui"
    ;;
esac

if [[ "$#" -ge 1 ]]; then
  shift
fi

EXAMPLE_PATH="$(resolve_isaacsim_example "${EXAMPLE_PATH}")"
EXAMPLE_ALIAS="$(isaacsim_example_alias "${EXAMPLE_PATH}")"
EXAMPLE_SUMMARY="$(isaacsim_example_summary "${EXAMPLE_PATH}")"

echo "[INFO] Isaac Sim example (${MODE}): ${EXAMPLE_ALIAS} -> ${EXAMPLE_PATH}"
echo "[INFO] Expected scene: ${EXAMPLE_SUMMARY}"

case "${MODE}" in
  gui)
    if running_inside_container; then
      cd /isaac-sim
      /isaac-sim/python.sh "${EXAMPLE_PATH}" "$@"
    else
      start_compose_service gui
      docker_exec_service bash -lc 'cd /isaac-sim && example_path="$1"; shift; /isaac-sim/python.sh "$example_path" "$@"' bash "${EXAMPLE_PATH}" "$@"
    fi
    ;;
  headless)
    if running_inside_container; then
      cd /isaac-sim
      /isaac-sim/python.sh "${EXAMPLE_PATH}" "$@"
    else
      start_compose_service headless
      docker_exec_service bash -lc 'cd /isaac-sim && example_path="$1"; shift; /isaac-sim/python.sh "$example_path" "$@"' bash "${EXAMPLE_PATH}" "$@"
    fi
    ;;
  *)
    usage >&2
    exit 1
    ;;
esac
