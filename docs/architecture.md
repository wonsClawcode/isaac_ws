# Architecture

이 저장소는 세 개의 층을 분리하는 것을 목표로 한다.

## 1. 인프라 층

- `docker/`
- `scripts/preflight_company.sh`
- `scripts/docker_build.sh`
- `scripts/docker_shell.sh`
- `docker/env/*.env`

이 층은 어떤 머신에서 어떻게 같은 실행 환경을 확보할지를 담당한다. 현재는 `Isaac Sim 5.1.0 공식 컨테이너 + Isaac Lab pip packages`를 기반으로 이미지를 빌드한다. 저사양 로컬에서는 정의만 유지하고, 실제 GPU 실행은 사내 Linux 머신에서 수행한다.

## 2. 실험 정의 층

- `configs/task/`
- `configs/env/`
- `configs/robot/`
- `configs/obs/`
- `configs/action/`
- `configs/reward/`
- `configs/algo/`
- `configs/experiment/`
- `configs/runtime/`
- `configs/deploy/`

Hydra 조합으로 실험을 정의한다. 코드 수정 없이 설정 조합만 바꿔 실험을 복제하거나 변형하는 것이 목적이다.

예시 조합:

```text
task=grasp_sphere_shadow_hand env=palm_up_workspace robot=franka_shadow_hand obs=grasp_proprio_contact action=franka_shadow_hand_delta_pos reward=grasp_sphere_dense algo=rsl_rl_ppo experiment=grasp_bootstrap runtime=headless deploy=ros2_shadow_grasp
```

## 3. 실행 및 배포 층

- `src/isaac_ws/train.py`
- `src/isaac_ws/eval.py`
- `src/isaac_ws/export.py`
- `scripts/run_train.sh`
- `scripts/run_eval.sh`
- `scripts/run_export.sh`
- `deploy/ros2/`

이 층은 실험 정의를 실제 실행 플랜과 배포 산출물로 연결한다. 현재는 Docker 컨테이너 안에서 `/isaac-sim/python.sh`를 통해 프로젝트 엔트리포인트를 호출하는 구조이며, 추후 Isaac Lab 실제 태스크 코드와 ROS 2 연동을 여기서 구체화한다.

## 운영 원칙

- 코드와 실험 산출물을 분리한다.
- 하드웨어 의존 요소는 `docker/env/` 또는 `configs/runtime/`으로 분리한다.
- sim-to-real 전환 시 관측, 액션, 제어 주기, 안전 제약을 명시적으로 문서화한다.
- `Franka + Shadow Hand`처럼 표준 조합이 아닌 로봇은 자산 조립 절차와 질량, 관성 가정을 별도 문서로 유지한다.
- 실험 식별자는 `task/env/robot/algo/experiment/seed + config fingerprint` 조합으로 관리한다.
- 새 config를 추가할 때는 `./scripts/check_config.sh --list-groups`와 `./scripts/check_config.sh`로 조합과 자산 참조를 확인한다.
