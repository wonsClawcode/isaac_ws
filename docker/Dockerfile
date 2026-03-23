ARG ISAACSIM_BASE_IMAGE=nvcr.io/nvidia/isaac-sim:5.1.0
FROM ${ISAACSIM_BASE_IMAGE}

ARG DEBIAN_FRONTEND=noninteractive
ARG INSTALL_RL_GAMES=0

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV TZ=Etc/UTC
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONUNBUFFERED=1
ENV ISAAC_WS_ROOT=/workspace/isaac_ws
ENV ACCEPT_EULA=Y
ENV PRIVACY_CONSENT=Y
ENV OMNI_KIT_ACCEPT_EULA=YES

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY docker/requirements.runtime.txt /tmp/requirements.runtime.txt
COPY docker/requirements.rl.txt /tmp/requirements.rl.txt

RUN /isaac-sim/python.sh -m pip install -r /tmp/requirements.runtime.txt \
    && if [ "${INSTALL_RL_GAMES}" = "1" ]; then \
         /isaac-sim/python.sh -m pip install -r /tmp/requirements.rl.txt; \
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
