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
ARG RL_GAMES_GIT_URL=https://github.com/isaac-sim/rl_games.git
ARG RL_GAMES_GIT_REF=python3.11
ARG INSTALL_RL_GAMES=0

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=Etc/UTC \
    TERM=xterm \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    ISAACSIM_PATH=/isaac-sim \
    ISAACSIM_PYTHON_EXE=/isaac-sim/python.sh \
    ISAAC_WS_ROOT=/workspace/isaac_ws \
    ISAACLAB_ROOT=/opt/IsaacLab \
    RL_GAMES_ROOT=/opt/rl_games \
    ACCEPT_EULA=Y \
    PRIVACY_CONSENT=Y \
    OMNI_KIT_ACCEPT_EULA=YES \
    OMNI_KIT_ALLOW_ROOT=1 \
    QT_X11_NO_MITSHM=1

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
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
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

RUN git lfs install --system \
    && mkdir -p "${ISAAC_WS_ROOT}" /workspace

COPY docker/requirements.runtime.txt /tmp/requirements.runtime.txt

RUN git clone --branch "${ISAACLAB_GIT_REF}" --depth 1 "${ISAACLAB_GIT_URL}" "${ISAACLAB_ROOT}" \
    && ln -sfn "${ISAACSIM_PATH}" "${ISAACLAB_ROOT}/_isaac_sim" \
    && if grep -Eq '^[[:space:]]*[^#[:space:]]' /tmp/requirements.runtime.txt; then \
         "${ISAACSIM_PYTHON_EXE}" -m pip install -r /tmp/requirements.runtime.txt; \
       else \
         echo "Skipping additional runtime requirements"; \
       fi \
    && "${ISAACSIM_PYTHON_EXE}" -m pip install --no-build-isolation -e "${ISAACLAB_ROOT}/source/isaaclab" \
    && "${ISAACSIM_PYTHON_EXE}" -m pip install --no-build-isolation -e "${ISAACLAB_ROOT}/source/isaaclab_assets" \
    && "${ISAACSIM_PYTHON_EXE}" -m pip install --no-build-isolation -e "${ISAACLAB_ROOT}/source/isaaclab_tasks" \
    && "${ISAACSIM_PYTHON_EXE}" -m pip install --no-build-isolation -e "${ISAACLAB_ROOT}/source/isaaclab_rl[rsl-rl]" \
    && if [ "${INSTALL_RL_GAMES}" = "1" ]; then \
         git clone --branch "${RL_GAMES_GIT_REF}" --depth 1 "${RL_GAMES_GIT_URL}" "${RL_GAMES_ROOT}" \
         && "${ISAACSIM_PYTHON_EXE}" -m pip install "poetry-core>=1.0.0" gym \
         && "${ISAACSIM_PYTHON_EXE}" -m pip install --no-build-isolation -e "${RL_GAMES_ROOT}"; \
       else \
         echo "Skipping optional rl_games install"; \
         mkdir -p "${RL_GAMES_ROOT}"; \
       fi

RUN ISAACLAB_GIT_COMMIT="$(git -C "${ISAACLAB_ROOT}" rev-parse HEAD)" \
    && ISAACLAB_GIT_DESCRIBE="$(git -C "${ISAACLAB_ROOT}" describe --tags --always)" \
    && RL_GAMES_GIT_COMMIT="$(git -C "${RL_GAMES_ROOT}" rev-parse HEAD 2>/dev/null || echo not-installed)" \
    && cat > /etc/isaac_ws-image-info <<EOF
ISAACSIM_BASE_IMAGE=${ISAACSIM_BASE_IMAGE}
ISAACSIM_VERSION=${ISAACSIM_VERSION}
ISAACLAB_GIT_URL=${ISAACLAB_GIT_URL}
ISAACLAB_GIT_REF=${ISAACLAB_GIT_REF}
ISAACLAB_GIT_COMMIT=${ISAACLAB_GIT_COMMIT}
ISAACLAB_GIT_DESCRIBE=${ISAACLAB_GIT_DESCRIBE}
RL_GAMES_GIT_URL=${RL_GAMES_GIT_URL}
RL_GAMES_GIT_REF=${RL_GAMES_GIT_REF}
RL_GAMES_GIT_COMMIT=${RL_GAMES_GIT_COMMIT}
INSTALL_RL_GAMES=${INSTALL_RL_GAMES}
EOF

WORKDIR ${ISAAC_WS_ROOT}
COPY pyproject.toml README.md /tmp/project/
COPY src /tmp/project/src
RUN "${ISAACSIM_PYTHON_EXE}" -m pip install -e /tmp/project

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
    && printf '#!/bin/bash\nexec /isaac-sim/python.sh "$@"\n' > /usr/local/bin/isaacpy \
    && chmod +x /usr/local/bin/isaacpy \
    && cat > /etc/profile.d/isaac_ws.sh <<'EOF'
export ISAACSIM_PATH="${ISAACSIM_PATH:-/isaac-sim}"
export ISAACSIM_PYTHON_EXE="${ISAACSIM_PYTHON_EXE:-/isaac-sim/python.sh}"
export ISAAC_WS_ROOT="${ISAAC_WS_ROOT:-/workspace/isaac_ws}"
export PYTHONPATH="${ISAAC_WS_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
alias isaacpy='/isaac-sim/python.sh'
alias islab='cd /opt/IsaacLab'
alias iws='cd /workspace/isaac_ws'
EOF

LABEL org.opencontainers.image.title="isaac-ws" \
      org.opencontainers.image.description="Isaac Sim 5.1.0 + Isaac Lab source install workspace" \
      org.opencontainers.image.source="https://github.com/wonsClawcode/isaac_ws"

WORKDIR ${ISAAC_WS_ROOT}
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
