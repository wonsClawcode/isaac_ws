# hand_isaac

Isaac Sim 5.1.0과 Isaac Lab 2.3.2를 기준으로 `Shadow Hand`가 구를 집는 정책을 학습하는 저장소다. 실행 환경은 Docker를 기본으로 두고, 학습 코드는 `isaac_ws` 모듈 아래에 유지한다.

## 구성

- Isaac Sim 5.1.0 기반 Docker 이미지
- Isaac Lab 2.3.2 source install
- `Shadow Hand + sphere grasp` Direct RL task
- Hydra 기반 실험 조합
- 학습, 평가, export, smoke 실행 스크립트

## 빠른 시작

1. 호스트 준비 상태를 확인한다.

```bash
./scripts/preflight_company.sh
```

2. 이미지를 빌드하고 설치 상태를 확인한다.

```bash
./scripts/docker_build.sh
./scripts/verify_docker_stack.sh
```

3. GUI가 필요하면 X11 접근을 준비한다.

```bash
./scripts/prepare_x11.sh
```

4. 지속형 컨테이너를 올리고 들어간다.

```bash
./scripts/docker_up.sh
./scripts/docker_exec.sh
```

GUI 컨테이너는 아래처럼 올린다.

```bash
./scripts/docker_up.sh gui
./scripts/docker_exec.sh
```

5. smoke 또는 학습을 실행한다.

```bash
./scripts/run_task_smoke.sh
./scripts/run_train.sh
```

## 자주 쓰는 명령

컨테이너 관리:

```bash
./scripts/docker_up.sh
./scripts/docker_up.sh gui
./scripts/docker_exec.sh
./scripts/docker_down.sh
```

예제 실행:

```bash
./scripts/list_examples.sh
./scripts/run_isaaclab_example.sh gui
./scripts/run_isaaclab_example.sh headless
./scripts/run_isaacsim_example.sh gui
```

커스텀 task 확인:

```bash
./scripts/run_task_smoke.sh
./scripts/run_task_smoke.sh env.num_envs=49
./scripts/run_task_smoke.sh runtime=headless run.max_steps=300
```

학습, 평가, export:

```bash
./scripts/check_config.sh
./scripts/run_train.sh task=grasp_sphere_shadow_hand_only env=shadow_hand_palm_up robot=shadow_hand experiment=shadow_hand_grasp_bootstrap
./scripts/run_eval.sh task=grasp_sphere_shadow_hand_only checkpoint_path=/workspace/hand_isaac/checkpoints/rsl_rl/your_experiment/model.pt
./scripts/run_export.sh task=grasp_sphere_shadow_hand_only checkpoint_path=/workspace/hand_isaac/checkpoints/rsl_rl/your_experiment/model.pt
```

학습 smoke:

```bash
./scripts/run_train.sh runtime=gui_debug env=shadow_hand_palm_up_debug env.num_envs=1 algo.max_iterations=1
```

## 디렉터리

- `configs/`: task, env, reward, runtime, experiment 설정
- `src/isaac_ws/`: 실행 엔트리포인트와 task 코드
- `scripts/`: 빌드, 컨테이너, smoke, train/eval/export 래퍼
- `docker/`: Dockerfile, compose, 환경 변수 파일
- `docs/`: setup, requirements, architecture, deployment 문서

## 문서

- [docs/requirements.md](docs/requirements.md)
- [docs/setup/docker_environment.md](docs/setup/docker_environment.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/deployment.md](docs/deployment.md)
- [docs/tasks/franka_shadow_hand_grasp.md](docs/tasks/franka_shadow_hand_grasp.md)
- [docs/asset_assembly.md](docs/asset_assembly.md)
