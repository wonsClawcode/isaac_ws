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
