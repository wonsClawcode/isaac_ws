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

DOCKER_ENV_FILE="$(resolve_repo_path "${DOCKER_ENV_FILE:-docker/env/company.env}")"
DOCKER_COMPOSE_FILE="$(resolve_repo_path "${DOCKER_COMPOSE_FILE:-docker/docker-compose.yml}")"
HOST_UID="${HOST_UID:-$(id -u)}"
HOST_GID="${HOST_GID:-$(id -g)}"
XAUTHORITY_PATH="${XAUTHORITY_PATH:-${XAUTHORITY:-${HOME}/.Xauthority}}"
X11_SOCKET_DIR="${X11_SOCKET_DIR:-/tmp/.X11-unix}"

export HOST_UID HOST_GID XAUTHORITY_PATH X11_SOCKET_DIR

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

requires_gui_runtime() {
  local arg
  for arg in "$@"; do
    case "${arg}" in
      runtime=gui_debug|runtime=x11_compat|runtime.headless=false|runtime.ui_mode=x11)
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
