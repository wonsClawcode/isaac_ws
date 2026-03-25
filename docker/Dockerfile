# syntax=docker/dockerfile:1.6

ARG ISAACSIM_BASE_IMAGE=nvcr.io/nvidia/isaac-sim
ARG ISAACSIM_VERSION=5.1.0
FROM ${ISAACSIM_BASE_IMAGE}:${ISAACSIM_VERSION}

SHELL ["/bin/bash", "-lc"]

ARG DEBIAN_FRONTEND=noninteractive
ARG ISAACSIM_BASE_IMAGE
ARG ISAACSIM_VERSION
ARG ISAACLAB_GIT_URL=https://github.com/isaac-sim/IsaacLab.git
ARG ISAACLAB_GIT_REF=v2.3.2
ARG INSTALL_RL_GAMES=0

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=Etc/UTC \
    TERM=xterm \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=0 \
    PIP_CACHE_DIR=/root/.cache/pip \
    PYTHONUNBUFFERED=1 \
    ISAACSIM_PATH=/isaac-sim \
    ISAACSIM_PYTHON_EXE=/isaac-sim/python.sh \
    ISAACLAB_PYTHON_EXE=/usr/local/bin/isaaclabpy \
    ISAACLAB_SOURCE_PATHS=/opt/IsaacLab/source/isaaclab:/opt/IsaacLab/source/isaaclab_tasks:/opt/IsaacLab/source/isaaclab_rl:/opt/IsaacLab/source/isaaclab_assets \
    ISAAC_WS_ROOT=/workspace/isaac_ws \
    ISAACLAB_ROOT=/opt/IsaacLab \
    ACCEPT_EULA=Y \
    PRIVACY_CONSENT=Y \
    OMNI_KIT_ACCEPT_EULA=YES \
    OMNI_KIT_ALLOW_ROOT=1 \
    QT_X11_NO_MITSHM=1

USER root

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      git \
      ca-certificates \
      curl \
      git-lfs \
      less \
      mesa-utils \
      rsync \
      unzip \
      vim \
      libglib2.0-0 \
      libgl1 \
      libsm6 \
      libxext6 \
      libxrender1

RUN git lfs install --system \
    && mkdir -p "${ISAAC_WS_ROOT}" /workspace

COPY docker/requirements.runtime.txt /tmp/requirements.runtime.txt

RUN git clone --branch "${ISAACLAB_GIT_REF}" --depth 1 "${ISAACLAB_GIT_URL}" "${ISAACLAB_ROOT}"

RUN ln -sfn "${ISAACSIM_PATH}" "${ISAACLAB_ROOT}/_isaac_sim"

RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    "${ISAACSIM_PYTHON_EXE}" -m pip install --no-build-isolation "flatdict==4.0.1"

RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    cd "${ISAACLAB_ROOT}" \
    && ./isaaclab.sh --install rsl_rl

RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    cd "${ISAACLAB_ROOT}" \
    && if [ "${INSTALL_RL_GAMES}" = "1" ]; then \
         ./isaaclab.sh --install rl_games; \
       else \
         echo "Skipping optional rl_games install"; \
       fi

RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    if grep -Eq '^[[:space:]]*[^#[:space:]]' /tmp/requirements.runtime.txt; then \
      "${ISAACSIM_PYTHON_EXE}" -m pip install -r /tmp/requirements.runtime.txt; \
    else \
      echo "Skipping additional runtime requirements"; \
    fi

RUN ISAACLAB_GIT_COMMIT="$(git -C "${ISAACLAB_ROOT}" rev-parse HEAD)" \
    && ISAACLAB_GIT_DESCRIBE="$(git -C "${ISAACLAB_ROOT}" describe --tags --always)" \
    && cat > /etc/isaac_ws-image-info <<EOF
ISAACSIM_BASE_IMAGE=${ISAACSIM_BASE_IMAGE}
ISAACSIM_VERSION=${ISAACSIM_VERSION}
ISAACLAB_GIT_URL=${ISAACLAB_GIT_URL}
ISAACLAB_GIT_REF=${ISAACLAB_GIT_REF}
ISAACLAB_GIT_COMMIT=${ISAACLAB_GIT_COMMIT}
ISAACLAB_GIT_DESCRIBE=${ISAACLAB_GIT_DESCRIBE}
RL_GAMES_INSTALL_METHOD=isaaclab.sh
INSTALL_RL_GAMES=${INSTALL_RL_GAMES}
EOF

WORKDIR ${ISAAC_WS_ROOT}
COPY pyproject.toml README.md /tmp/project/
COPY src /tmp/project/src
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    "${ISAACSIM_PYTHON_EXE}" -m pip install -e /tmp/project

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN cat > /usr/local/bin/isaaclabpy <<'EOF'
#!/bin/bash
set -euo pipefail
cd "${ISAACLAB_ROOT:-/opt/IsaacLab}"
export ISAACLAB_SOURCE_PATHS="${ISAACLAB_SOURCE_PATHS:-/opt/IsaacLab/source/isaaclab:/opt/IsaacLab/source/isaaclab_tasks:/opt/IsaacLab/source/isaaclab_rl:/opt/IsaacLab/source/isaaclab_assets}"
export PYTHONPATH="${ISAACLAB_SOURCE_PATHS}${PYTHONPATH:+:${PYTHONPATH}}"
exec ./isaaclab.sh -p "$@"
EOF

RUN chmod +x /usr/local/bin/isaaclabpy

RUN cat > /usr/local/bin/isaacsimpy <<'EOF'
#!/bin/bash
exec /isaac-sim/python.sh "$@"
EOF

RUN chmod +x /usr/local/bin/isaacsimpy

RUN cat > /etc/profile.d/isaac_ws.sh <<'EOF'
export ISAACSIM_PATH="${ISAACSIM_PATH:-/isaac-sim}"
export ISAACSIM_PYTHON_EXE="${ISAACSIM_PYTHON_EXE:-/isaac-sim/python.sh}"
export ISAACLAB_PYTHON_EXE="${ISAACLAB_PYTHON_EXE:-/usr/local/bin/isaaclabpy}"
export ISAACLAB_SOURCE_PATHS="${ISAACLAB_SOURCE_PATHS:-/opt/IsaacLab/source/isaaclab:/opt/IsaacLab/source/isaaclab_tasks:/opt/IsaacLab/source/isaaclab_rl:/opt/IsaacLab/source/isaaclab_assets}"
export ISAAC_WS_ROOT="${ISAAC_WS_ROOT:-/workspace/isaac_ws}"
export PYTHONPATH="${ISAAC_WS_ROOT}/src:${ISAACLAB_SOURCE_PATHS}${PYTHONPATH:+:${PYTHONPATH}}"
alias isaacpy='/usr/local/bin/isaaclabpy'
alias python='/usr/local/bin/isaaclabpy'
alias python3='/usr/local/bin/isaaclabpy'
alias simpy='/usr/local/bin/isaacsimpy'
alias islab='cd /opt/IsaacLab'
alias iws='cd /workspace/isaac_ws'
EOF

RUN printf '\nsource /etc/profile.d/isaac_ws.sh\n' >> /root/.bashrc

LABEL org.opencontainers.image.title="isaac-ws" \
      org.opencontainers.image.description="Isaac Sim 5.1.0 + Isaac Lab source install workspace" \
      org.opencontainers.image.source="https://github.com/wonsClawcode/isaac_ws"

WORKDIR ${ISAAC_WS_ROOT}
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
