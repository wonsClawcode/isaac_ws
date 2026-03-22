#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  source "${ROOT_DIR}/.env"
  set +a
fi

warn() {
  printf '[warn] %s\n' "$1"
}

info() {
  printf '[info] %s\n' "$1"
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    warn "missing command: $1"
    return 1
  fi
  return 0
}

if [[ "$(uname -s)" != "Linux" ]]; then
  warn "Isaac Sim container target host should be Linux."
fi

need_cmd docker || true
need_cmd nvidia-smi || true
need_cmd nvidia-ctk || warn "nvidia-ctk not found; NVIDIA Container Toolkit may be missing."

if command -v docker >/dev/null 2>&1; then
  info "docker server version: $(docker version --format '{{.Server.Version}}' 2>/dev/null || echo unknown)"
  info "docker compose version: $(docker compose version --short 2>/dev/null || echo unknown)"
fi

info "isaac sim base image: ${ISAACSIM_BASE_IMAGE:-nvcr.io/nvidia/isaac-sim:5.1.0}"

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi || true
fi

if command -v docker >/dev/null 2>&1; then
  if docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi >/dev/null 2>&1; then
    info "docker GPU passthrough check: ok"
  else
    warn "docker GPU passthrough check failed. Verify Docker + NVIDIA Container Toolkit."
  fi
fi
