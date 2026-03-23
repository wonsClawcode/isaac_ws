# isaac_ws

Isaac Sim + Isaac Lab 기반 로봇 강화학습 프로젝트의 초기 골격이다. 현재 기본 목표는 `Franka arm + Shadow Hand` 조합으로 손바닥이 하늘을 향한 상태에서 구형 물체를 grasp하는 policy를 학습하는 것이다. 기본 실행 경로는 `Docker + Isaac Sim 5.1.0 + Isaac Lab 2.3.2`이며, 실제 학습과 검증은 사내 Linux RTX 머신에서 수행하는 흐름을 전제로 설계했다.

## 목표

- 실험 구성을 `task`, `env`, `robot`, `obs`, `action`, `reward`, `algo`, `experiment` 단위로 분리
- Docker 이미지로 Isaac Sim 5.1.0과 Isaac Lab 스택을 고정
- 실험 로그, 체크포인트, 캐시, 배포 자산을 코드와 분리
- 추후 ROS 2 기반 실기 배포 경로를 자연스럽게 확장

## 현재 포함된 것

- Isaac Sim 5.1.0 공식 컨테이너 기반 Dockerfile
- Isaac Lab 2.3.2 및 `rl_games` 설치 레이어
- Hydra 설정 조합 뼈대
- `Franka + Shadow Hand` palm-up grasp용 Isaac Lab Direct RL task skeleton
- GUI 디버그용 X11 Docker 오버라이드와 대규모 학습용 runtime/env 프로파일
- 학습/평가/내보내기용 Docker 래퍼 스크립트
- 사내 GPU 머신 사전 점검 스크립트
- sim-to-real 전개를 위한 문서 초안

## 디렉터리 요약

- `configs/`: 실험 조합을 위한 설정 그룹
- `docker/`: 이미지 빌드, compose, 런타임 requirements
- `src/isaac_ws/`: 엔트리포인트와 공통 유틸리티
- `scripts/`: Docker 빌드, 셸 진입, 학습 실행 래퍼
- `docs/`: 아키텍처, 요구사항, Docker setup, 배포 메모
- `deploy/ros2/`: ROS 2 연동 확장 지점
- `runs/`, `logs/`, `checkpoints/`: 실험 산출물

## 빠른 시작

1. 사내 Linux GPU 머신에서 [`docs/requirements.md`](/Users/wonnerky/workspace/isaac_ws/docs/requirements.md)와 [`docs/setup/docker_environment.md`](/Users/wonnerky/workspace/isaac_ws/docs/setup/docker_environment.md)를 따라 Docker, Docker Compose, NVIDIA Container Toolkit 상태를 준비한다.
2. 필요하면 [`.env.example`](/Users/wonnerky/workspace/isaac_ws/.env.example)를 참고해 `.env`를 만든다.
3. 호스트 GPU와 Docker 런타임 상태를 확인한다.

```bash
./scripts/preflight_company.sh
```

4. Isaac Sim 5.1.0 + Isaac Lab 이미지 레이어를 빌드한다.

```bash
./scripts/docker_build.sh
./scripts/verify_docker_stack.sh
```

5. 필요하면 컨테이너 셸에 들어가거나 Isaac Sim을 직접 띄운다.

```bash
./scripts/docker_shell.sh
./scripts/run_isaacsim.sh
```

GUI 디버그가 필요하면 X11 접근을 열고 GUI 전용 래퍼를 사용한다.

```bash
./scripts/prepare_x11.sh
./scripts/docker_shell_gui.sh
./scripts/run_isaacsim_gui.sh
```

6. 설정 조합이 올바른지 dry-run 성격의 학습 계획을 확인한다.

```bash
./scripts/check_config.sh
./scripts/check_config.sh task=grasp_sphere_shadow_hand env=palm_up_workspace robot=franka_shadow_hand
./scripts/run_train.sh
./scripts/run_train.sh task=grasp_sphere_shadow_hand env=palm_up_workspace robot=franka_shadow_hand experiment=grasp_bootstrap
```

실제 운용에서는 GUI 디버그와 대규모 학습을 분리해서 쓰는 편이 낫다.

```bash
./scripts/check_config.sh task=grasp_sphere_shadow_hand env=palm_up_workspace_debug runtime=gui_debug
./scripts/check_config.sh task=grasp_sphere_shadow_hand env=palm_up_workspace_scaleout runtime=distributed_4gpu
```

## 현재 가정

- 실제 실행 타깃은 Linux + NVIDIA RTX GPU 머신이다.
- 이 노트북에서는 Isaac Sim GUI, 대규모 병렬 학습, 렌더링 성능 검증을 하지 않는다.
- Isaac Sim 5.1.0과 Isaac Lab은 Docker 이미지 안에서 설치된다.
- GUI 디버그는 커스텀 Docker Compose X11 오버라이드를 통해 수행한다.
- 대규모 학습은 headless + scaleout env/runtime 조합을 기본값으로 삼는다.

## 다음으로 채워야 할 것

- `Franka + Shadow Hand` 조합용 단일 USD 또는 articulation assembly
- 실제 fingertip contact sensor와 self-collision proxy 제거
- Shadow Hand용 joint mapping, tendon/coupling, PD gain
- ROS 2 브리지와 실기 안전 계층

## 참고 문서

- [`docs/architecture.md`](/Users/wonnerky/workspace/isaac_ws/docs/architecture.md)
- [`docs/requirements.md`](/Users/wonnerky/workspace/isaac_ws/docs/requirements.md)
- [`docs/deployment.md`](/Users/wonnerky/workspace/isaac_ws/docs/deployment.md)
- [`docs/setup/docker_environment.md`](/Users/wonnerky/workspace/isaac_ws/docs/setup/docker_environment.md)
- [`docs/tasks/franka_shadow_hand_grasp.md`](/Users/wonnerky/workspace/isaac_ws/docs/tasks/franka_shadow_hand_grasp.md)
- [`docs/asset_assembly.md`](/Users/wonnerky/workspace/isaac_ws/docs/asset_assembly.md)
