#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/example_catalog.sh"

usage() {
  cat <<'EOF'
Usage: ./scripts/run_isaaclab_example.sh [gui|headless] [script_path|alias] [extra args...]

Examples
  ./scripts/run_isaaclab_example.sh gui
  ./scripts/run_isaaclab_example.sh gui spawn_prims
  ./scripts/run_isaaclab_example.sh headless empty
  ./scripts/run_isaaclab_example.sh list

Notes
  - gui 기본값은 spawn_prims.py다.
  - headless 기본값은 create_empty.py다.
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
SCRIPT_PATH=""

case "${MODE}" in
  gui|headless)
    shift || true
    SCRIPT_PATH="${1:-}"
    ;;
  *)
    SCRIPT_PATH="${MODE}"
    MODE="gui"
    ;;
esac

if [[ "$#" -ge 1 ]]; then
  shift
fi

SCRIPT_PATH="$(resolve_isaaclab_example "${SCRIPT_PATH}" "${MODE}")"
EXAMPLE_ALIAS="$(isaaclab_example_alias "${SCRIPT_PATH}")"
EXAMPLE_SUMMARY="$(isaaclab_example_summary "${SCRIPT_PATH}")"

echo "[INFO] Isaac Lab example (${MODE}): ${EXAMPLE_ALIAS} -> ${SCRIPT_PATH}"
echo "[INFO] Expected scene: ${EXAMPLE_SUMMARY}"

case "${MODE}" in
  gui)
    if running_inside_container; then
      cd /opt/IsaacLab
      ./isaaclab.sh -p "${SCRIPT_PATH}" "$@"
    else
      start_compose_service gui
      docker_exec_service bash -lc 'cd /opt/IsaacLab && script_path="$1"; shift; exec ./isaaclab.sh -p "$script_path" "$@"' bash "${SCRIPT_PATH}" "$@"
    fi
    ;;
  headless)
    if running_inside_container; then
      cd /opt/IsaacLab
      ./isaaclab.sh -p "${SCRIPT_PATH}" --headless "$@"
    else
      start_compose_service headless
      docker_exec_service bash -lc 'cd /opt/IsaacLab && script_path="$1"; shift; exec ./isaaclab.sh -p "$script_path" --headless "$@"' bash "${SCRIPT_PATH}" "$@"
    fi
    ;;
  *)
    usage >&2
    exit 1
    ;;
esac
