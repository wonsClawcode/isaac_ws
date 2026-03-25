#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker_common.sh"

echo "[info] removing stopped compose resources and named caches for project '${COMPOSE_PROJECT_NAME:-hand_isaac}'"
docker_compose down -v --remove-orphans
echo "[info] cache volumes removed"
