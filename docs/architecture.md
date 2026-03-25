# Architecture

이 저장소는 실행 환경, 실험 설정, 학습 코드 세 층으로 나뉜다.

## 1. 인프라 층

- `docker/`
- `scripts/preflight_company.sh`
- `scripts/docker_build.sh`
- `scripts/docker_up.sh`
- `scripts/docker_exec.sh`
- `scripts/docker_down.sh`
- `scripts/run_isaaclab_example.sh`
- `scripts/run_isaacsim_example.sh`
- `scripts/run_task_smoke.sh`
- `docker/env/*.env`

이 층은 같은 실행 환경을 재현하는 역할을 맡는다. 현재는 `Isaac Sim 5.1.0` 컨테이너 위에 `Isaac Lab` source install을 얹는 방식이다. GUI는 `docker-compose.gui.yml` 오버라이드로 분리하고, 기본 compose service는 idle 상태로 유지해 `docker_up.sh`와 `docker_exec.sh`로 재진입할 수 있게 했다.

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
task=grasp_sphere_shadow_hand_only env=shadow_hand_palm_up robot=shadow_hand obs=shadow_hand_grasp_proprio action=shadow_hand_delta_pos reward=shadow_hand_grasp_dense algo=rsl_rl_ppo experiment=shadow_hand_grasp_bootstrap runtime=headless deploy=ros2_shadow_grasp
```

운영 프로파일 예시:

```text
task=grasp_sphere_shadow_hand_only env=shadow_hand_palm_up_debug runtime=gui_debug
task=grasp_sphere_shadow_hand_only env=shadow_hand_palm_up_scaleout runtime=distributed_4gpu
```

## 3. 실행 및 배포 층

- `src/isaac_ws/train.py`
- `src/isaac_ws/eval.py`
- `src/isaac_ws/export.py`
- `scripts/run_train.sh`
- `scripts/run_eval.sh`
- `scripts/run_export.sh`
- `deploy/ros2/`

이 층은 실험 정의를 실제 학습, 평가, export 실행으로 연결한다. 분산 runtime을 선택하면 내부에서 `torch.distributed.run`으로 다시 실행한다.

## 운영 원칙

- 코드와 실험 산출물을 분리한다.
- 하드웨어 의존 요소는 `docker/env/` 또는 `configs/runtime/`으로 분리한다.
- sim-to-real 전환 시 관측, 액션, 제어 주기, 안전 제약을 명시적으로 문서화한다.
- `Franka + Shadow Hand`처럼 표준 조합이 아닌 로봇은 자산 조립 절차와 질량, 관성 가정을 별도 문서로 유지한다.
- 실험 식별자는 `task/env/robot/algo/experiment/seed + config fingerprint` 조합으로 관리한다.
- 새 config를 추가할 때는 `./scripts/check_config.sh --list-groups`와 `./scripts/check_config.sh`로 조합과 자산 참조를 확인한다.
