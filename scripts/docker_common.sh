#!/usr/bin/env bash

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

resolve_repo_path() {
  local path="$1"
  if [[ "${path}" = /* ]]; then
    printf '%s\n' "${path}"
  else
    printf '%s/%s\n' "${ROOT_DIR}" "${path}"
  fi
}

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  source "${ROOT_DIR}/.env"
  set +a
fi

DOCKER_ENV_FILE="$(resolve_repo_path "${DOCKER_ENV_FILE:-docker/env/hand_isaac.env}")"
DOCKER_COMPOSE_FILE="$(resolve_repo_path "${DOCKER_COMPOSE_FILE:-docker/docker-compose.yml}")"
ISAACLAB_SERVICE_NAME="${ISAACLAB_SERVICE_NAME:-isaac-lab}"
HOST_UID="${HOST_UID:-$(id -u)}"
HOST_GID="${HOST_GID:-$(id -g)}"
XAUTHORITY_PATH="${XAUTHORITY_PATH:-${XAUTHORITY:-${HOME}/.Xauthority}}"
X11_SOCKET_DIR="${X11_SOCKET_DIR:-/tmp/.X11-unix}"

export HOST_UID HOST_GID XAUTHORITY_PATH X11_SOCKET_DIR ISAACLAB_SERVICE_NAME

docker_compose() {
  local compose_files=("-f" "${DOCKER_COMPOSE_FILE}")
  if [[ -n "${DOCKER_COMPOSE_EXTRA_FILE:-}" ]]; then
    compose_files+=("-f" "$(resolve_repo_path "${DOCKER_COMPOSE_EXTRA_FILE}")")
  fi
  docker compose \
    --project-directory "${ROOT_DIR}" \
    --env-file "${DOCKER_ENV_FILE}" \
    "${compose_files[@]}" \
    "$@"
}

running_inside_container() {
  [[ -f "/.dockerenv" ]] || [[ -f "/run/.containerenv" ]]
}

compose_service_container_id() {
  docker_compose ps -q "${ISAACLAB_SERVICE_NAME}" 2>/dev/null || true
}

compose_service_running() {
  local container_id
  container_id="$(compose_service_container_id)"
  [[ -n "${container_id}" ]] && [[ "$(docker inspect -f '{{.State.Running}}' "${container_id}" 2>/dev/null || true)" == "true" ]]
}

start_compose_service() {
  local mode="${1:-headless}"

  case "${mode}" in
    gui)
      enable_gui_runtime
      ;;
    headless)
      unset DOCKER_COMPOSE_EXTRA_FILE
      export HEADLESS=1
      ;;
    *)
      echo "Unsupported compose service mode: ${mode}" >&2
      exit 1
      ;;
  esac

  docker_compose up -d "${ISAACLAB_SERVICE_NAME}"
}

ensure_compose_service_running() {
  if ! compose_service_running; then
    echo "Persistent container '${ISAACLAB_SERVICE_NAME}' is not running. Start it with ./scripts/docker_up.sh or ./scripts/docker_up.sh gui." >&2
    exit 1
  fi
}

docker_exec_service() {
  ensure_compose_service_running
  docker_compose exec "${ISAACLAB_SERVICE_NAME}" "$@"
}

requires_gui_runtime() {
  local arg
  for arg in "$@"; do
    case "${arg}" in
      runtime=gui|runtime=gui_*|runtime=gui-*|runtime=x11_compat|runtime=x11_*|runtime=x11-*|runtime.headless=false|headless=false|app.headless=false|runtime.ui_mode=x11|ui_mode=x11)
        return 0
        ;;
    esac
  done
  return 1
}

enable_gui_runtime() {
  if [[ -z "${DISPLAY:-}" ]]; then
    echo "DISPLAY is required for GUI runtime overrides." >&2
    exit 1
  fi

  if [[ ! -r "${XAUTHORITY_PATH}" ]]; then
    echo "Xauthority file not found or unreadable: ${XAUTHORITY_PATH}" >&2
    exit 1
  fi

  export DOCKER_COMPOSE_EXTRA_FILE="${ROOT_DIR}/docker/docker-compose.gui.yml"
  export HEADLESS=0
  export OMNI_KIT_ALLOW_ROOT="${OMNI_KIT_ALLOW_ROOT:-1}"
}

configure_runtime_compose() {
  if requires_gui_runtime "$@"; then
    enable_gui_runtime
  fi
}
