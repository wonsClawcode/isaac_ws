#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

export COMPOSE_BAKE="${COMPOSE_BAKE:-false}"
export BUILDKIT_PROGRESS="${BUILDKIT_PROGRESS:-plain}"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage: ./scripts/docker_build.sh [docker compose build options]

Examples:
  ./scripts/docker_build.sh
  ./scripts/docker_build.sh --no-cache
  BUILDKIT_PROGRESS=tty ./scripts/docker_build.sh
EOF
  exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[error] docker command not found." >&2
  exit 1
fi

echo "[info] root: ${ROOT_DIR}"
echo "[info] env file: ${DOCKER_ENV_FILE}"
echo "[info] compose file: ${DOCKER_COMPOSE_FILE}"
echo "[info] compose bake: ${COMPOSE_BAKE}"
echo "[info] buildkit progress: ${BUILDKIT_PROGRESS}"

docker_compose config --quiet
docker_compose build --progress "${BUILDKIT_PROGRESS}" "$@" isaac-lab
