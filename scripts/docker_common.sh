#!/usr/bin/env bash

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  source "${ROOT_DIR}/.env"
  set +a
fi

DOCKER_ENV_FILE="${DOCKER_ENV_FILE:-${ROOT_DIR}/docker/env/company.env}"
DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-${ROOT_DIR}/docker/docker-compose.yml}"

docker_compose() {
  docker compose \
    --project-directory "${ROOT_DIR}" \
    --env-file "${DOCKER_ENV_FILE}" \
    -f "${DOCKER_COMPOSE_FILE}" \
    "$@"
}
