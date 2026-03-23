#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

if [[ -f "${DOCKER_ENV_FILE}" ]]; then
  set -a
  source "${DOCKER_ENV_FILE}"
  set +a
fi

DOCKER_IMAGE="${DOCKER_IMAGE:-isaac-ws:5.1.0-lab2.3.2}"
ISAACSIM_BASE_IMAGE="${ISAACSIM_BASE_IMAGE:-nvcr.io/nvidia/isaac-sim:5.1.0}"
ISAACLAB_GIT_URL="${ISAACLAB_GIT_URL:-https://github.com/isaac-sim/IsaacLab.git}"
ISAACLAB_GIT_REF="${ISAACLAB_GIT_REF:-v2.3.2}"
INSTALL_RL_GAMES="${INSTALL_RL_GAMES:-0}"
BUILDKIT_PROGRESS="${BUILDKIT_PROGRESS:-plain}"
DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-1}"

export BUILDKIT_PROGRESS DOCKER_BUILDKIT INSTALL_RL_GAMES ISAACLAB_GIT_URL ISAACLAB_GIT_REF

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage: ./scripts/docker_build.sh [docker build options]

Examples:
  ./scripts/docker_build.sh
  ./scripts/docker_build.sh --no-cache
  ISAACLAB_GIT_REF=v2.3.2 ./scripts/docker_build.sh
  INSTALL_RL_GAMES=1 ./scripts/docker_build.sh
  BUILDKIT_PROGRESS=tty ./scripts/docker_build.sh
  DOCKER_BUILDKIT=0 ./scripts/docker_build.sh
EOF
  exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[error] docker command not found." >&2
  exit 1
fi

echo "[info] root: ${ROOT_DIR}"
echo "[info] env file: ${DOCKER_ENV_FILE}"
echo "[info] image: ${DOCKER_IMAGE}"
echo "[info] base image: ${ISAACSIM_BASE_IMAGE}"
echo "[info] isaaclab git url: ${ISAACLAB_GIT_URL}"
echo "[info] isaaclab git ref: ${ISAACLAB_GIT_REF}"
echo "[info] install rl_games: ${INSTALL_RL_GAMES}"
echo "[info] dockerfile: ${ROOT_DIR}/docker/Dockerfile"
echo "[info] buildkit progress: ${BUILDKIT_PROGRESS}"
echo "[info] docker buildkit: ${DOCKER_BUILDKIT}"

docker_args=(
  --file "${ROOT_DIR}/docker/Dockerfile"
  --tag "${DOCKER_IMAGE}"
  --build-arg "ISAACSIM_BASE_IMAGE=${ISAACSIM_BASE_IMAGE}"
  --build-arg "ISAACLAB_GIT_URL=${ISAACLAB_GIT_URL}"
  --build-arg "ISAACLAB_GIT_REF=${ISAACLAB_GIT_REF}"
  --build-arg "INSTALL_RL_GAMES=${INSTALL_RL_GAMES}"
)

if [[ "${DOCKER_BUILDKIT}" != "0" ]]; then
  docker_args+=(--progress "${BUILDKIT_PROGRESS}")
fi

docker build \
  "${docker_args[@]}" \
  "$@" \
  "${ROOT_DIR}"
