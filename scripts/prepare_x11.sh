#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DISPLAY:-}" ]]; then
  echo "DISPLAY is not set." >&2
  exit 1
fi

if ! command -v xhost >/dev/null 2>&1; then
  echo "xhost is required to prepare X11 access." >&2
  exit 1
fi

LOCAL_USER="$(id -un)"
xhost "+si:localuser:${LOCAL_USER}" >/dev/null

echo "X11 access granted for local user '${LOCAL_USER}'."
echo "DISPLAY=${DISPLAY}"
echo "XAUTHORITY=${XAUTHORITY:-${HOME}/.Xauthority}"
