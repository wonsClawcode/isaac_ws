ARG ISAACSIM_BASE_IMAGE=nvcr.io/nvidia/isaac-sim:5.1.0
FROM ${ISAACSIM_BASE_IMAGE}

ARG DEBIAN_FRONTEND=noninteractive
ARG ISAACLAB_GIT_URL=https://github.com/isaac-sim/IsaacLab.git
ARG ISAACLAB_GIT_REF=v2.3.2
ARG INSTALL_RL_GAMES=0

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV TZ=Etc/UTC
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONUNBUFFERED=1
ENV ISAAC_WS_ROOT=/workspace/isaac_ws
ENV ISAACLAB_ROOT=/opt/IsaacLab
ENV ACCEPT_EULA=Y
ENV PRIVACY_CONSENT=Y
ENV OMNI_KIT_ACCEPT_EULA=YES

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY docker/requirements.runtime.txt /tmp/requirements.runtime.txt

RUN git clone --branch "${ISAACLAB_GIT_REF}" --depth 1 "${ISAACLAB_GIT_URL}" "${ISAACLAB_ROOT}" \
    && /isaac-sim/python.sh -m pip install -r /tmp/requirements.runtime.txt \
    && /isaac-sim/python.sh -m pip install -e "${ISAACLAB_ROOT}/source/isaaclab" \
    && /isaac-sim/python.sh -m pip install -e "${ISAACLAB_ROOT}/source/isaaclab_assets" \
    && /isaac-sim/python.sh -m pip install -e "${ISAACLAB_ROOT}/source/isaaclab_tasks" \
    && /isaac-sim/python.sh -m pip install -e "${ISAACLAB_ROOT}/source/isaaclab_rl[rsl-rl]" \
    && if [ "${INSTALL_RL_GAMES}" = "1" ]; then \
         /isaac-sim/python.sh -m pip install -e "${ISAACLAB_ROOT}/source/isaaclab_rl[rl-games]"; \
       else \
         echo "Skipping optional rl_games install"; \
       fi

WORKDIR ${ISAAC_WS_ROOT}
COPY pyproject.toml README.md /tmp/project/
COPY src /tmp/project/src
RUN /isaac-sim/python.sh -m pip install -e /tmp/project

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR ${ISAAC_WS_ROOT}
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
