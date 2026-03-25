# Requirements

이 프로젝트의 기본 실행 환경은 Linux GPU 호스트와 Docker다.

## 호스트 요구사항

- Ubuntu 22.04 또는 24.04 권장
- NVIDIA RTX GPU 권장
- GUI 디버그 전용이면 16GB 이상 VRAM 권장
- Shadow Hand grasp 대규모 병렬 학습이면 24GB 이상 VRAM 권장
- 64GB 이상 시스템 메모리 권장
- Docker Engine 26 이상
- Docker Compose 2.25 이상
- NVIDIA Container Toolkit 설치

Isaac Sim 컨테이너는 Linux 기반 원격 헤드리스 또는 클라우드 배포에 적합하고, RTX 계열 GPU를 전제로 한다. 공식 문서 기준으로 컨테이너는 Linux만 지원되며, RT Core가 없는 GPU인 A100, H100은 지원되지 않는다.

## 준비 체크리스트

1. `nvidia-smi`가 정상 동작하는지 확인
2. `docker version`과 `docker compose version` 확인
3. `docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi` 확인
4. 이 저장소를 클론하고 `docker/env/hand_isaac.env` 또는 `.env` 값 검토
5. `./scripts/docker_build.sh`로 이미지 빌드
6. 런타임 import 관련 에러가 있었다면 `./scripts/docker_build.sh --no-cache`로 재빌드
7. `./scripts/verify_docker_stack.sh`로 Isaac Sim 5.1.0 / Isaac Lab source install, 기본 `rsl_rl` 경량 import 확인
8. `./scripts/check_config.sh task=grasp_sphere_shadow_hand_only env=shadow_hand_palm_up_scaleout runtime=distributed_4gpu`로 대규모 조합 확인
9. `./scripts/prepare_x11.sh`와 `./scripts/run_task_smoke.sh runtime=gui_debug env.num_envs=49 run.max_steps=300`으로 GUI 경로 확인

참고:
- 기본 빌드는 `rsl_rl` 기준이다.
- Isaac Lab은 PyPI wheel이 아니라 Git source install 기준이다.
- `verify_docker_stack.sh` 기본 동작은 경량 검증이며, `VERIFY_SIM_APP_SMOKE=1`일 때만 headless `SimulationApp` smoke를 실행한다.
- `rl_games`는 GitHub clone이 필요하므로 네트워크 제약이 있는 환경에서는 설치가 실패할 수 있다.
- `rl_games`가 꼭 필요하면 `INSTALL_RL_GAMES=1 ./scripts/docker_build.sh --no-cache`로 별도 시도한다.

## 참고

- Isaac Sim container installation: <https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_container.html>
- Isaac Sim requirements: <https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html>
- Isaac Lab Docker guide: <https://isaac-sim.github.io/IsaacLab/main/source/deployment/docker.html>
- Isaac Lab source installation: <https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/source_installation.html>
