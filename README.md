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
./scripts/run_eval.sh task=grasp_sphere_shadow_hand_only run.checkpoint_path=/workspace/hand_isaac/checkpoints/rsl_rl/your_experiment/model.pt
./scripts/run_export.sh task=grasp_sphere_shadow_hand_only run.checkpoint_path=/workspace/hand_isaac/checkpoints/rsl_rl/your_experiment/model.pt
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

## 커스터마이징

이 저장소는 Hydra config로 조합을 바꾸는 부분과, Isaac Lab task 코드를 직접 바꾸는 부분이 나뉜다.

먼저 어떤 조합이 있는지 보고 싶으면:

```bash
./scripts/check_config.sh --list-groups
./scripts/check_config.sh task=grasp_sphere_shadow_hand_only env=shadow_hand_palm_up robot=shadow_hand
```

### 1. Custom env

배치 수, env 간격, workspace, 카메라, 기본 physics 값은 `configs/env/`에서 고친다.

- [configs/env/shadow_hand_palm_up.yaml](configs/env/shadow_hand_palm_up.yaml)
- [configs/env/shadow_hand_palm_up_debug.yaml](configs/env/shadow_hand_palm_up_debug.yaml)
- [configs/env/shadow_hand_palm_up_scaleout.yaml](configs/env/shadow_hand_palm_up_scaleout.yaml)

예:

```bash
./scripts/run_train.sh \
  env=shadow_hand_palm_up_debug \
  env.num_envs=4 \
  env.env_spacing=1.75 \
  env.workspace.sphere_spawn_center_m=[0.0,0.3,0.96]
```

현재 `runtime.py`가 env config에서 실제 Isaac Lab env cfg로 넘겨주는 항목은 아래 파일에서 확인할 수 있다.

- [src/isaac_ws/runtime.py](src/isaac_ws/runtime.py)

만약 scene에 새 센서, 새 물체, 새 reset 규칙, 새로운 done 조건을 넣고 싶다면 YAML만으로는 부족하고 아래 task 구현을 같이 바꿔야 한다.

- [src/isaac_ws/lab_tasks/direct/shadow_hand_sphere/env_cfg.py](src/isaac_ws/lab_tasks/direct/shadow_hand_sphere/env_cfg.py)
- [src/isaac_ws/lab_tasks/direct/shadow_hand_sphere/env.py](src/isaac_ws/lab_tasks/direct/shadow_hand_sphere/env.py)

### 2. Custom reward

기존 reward 항목의 가중치와 penalty는 `configs/reward/`에서 조절한다.

- [configs/reward/shadow_hand_grasp_dense.yaml](configs/reward/shadow_hand_grasp_dense.yaml)

예:

```bash
./scripts/run_train.sh \
  reward=shadow_hand_grasp_dense \
  reward.terms.object_lift=4.0 \
  reward.terms.stable_hold=12.0 \
  reward.penalties.object_drop=12.0
```

새 reward term을 추가하려면 세 군데를 같이 수정해야 한다.

1. `configs/reward/*.yaml`에 항목 추가
2. [src/isaac_ws/runtime.py](src/isaac_ws/runtime.py) 에서 env cfg로 값 전달
3. task env 구현에서 실제 reward 계산 추가
   - [src/isaac_ws/lab_tasks/direct/shadow_hand_sphere/env.py](src/isaac_ws/lab_tasks/direct/shadow_hand_sphere/env.py)
   - [src/isaac_ws/lab_tasks/direct/shadow_hand_sphere/env_cfg.py](src/isaac_ws/lab_tasks/direct/shadow_hand_sphere/env_cfg.py)

### 3. Custom assets

로봇 자산 경로와 메타데이터는 `configs/robot/`에서 관리한다.

- [configs/robot/shadow_hand.yaml](configs/robot/shadow_hand.yaml)
- [configs/robot/franka_shadow_hand.yaml](configs/robot/franka_shadow_hand.yaml)

예를 들어 custom USD를 쓰려면 새 robot config를 만들고 `asset_usd`를 지정하면 된다.

```yaml
name: shadow_hand_custom
asset_usd: assets/robots/shadow_hand_custom/shadow_hand_custom.usd
source_asset: custom
arm:
  dof: 0
  control_frequency_hz: 60
  end_effector_frame: ""
hand:
  dof: 20
  fingertip_frames:
    - robot0_ffdistal
    - robot0_mfdistal
    - robot0_rfdistal
    - robot0_lfdistal
    - robot0_thdistal
```

그리고 실행할 때:

```bash
./scripts/run_train.sh robot=shadow_hand_custom
```

현재 구조에서는 `robot.asset_usd`가 [src/isaac_ws/runtime.py](src/isaac_ws/runtime.py) 에서 `env_cfg.robot_cfg.spawn.usd_path`로 들어간다. 따라서 같은 joint 이름, fingertip frame, DOF를 유지하는 자산이면 config만 바꿔도 된다.

반대로 아래가 달라지면 task 코드도 같이 바꿔야 한다.

- joint 이름
- fingertip body 이름
- 손가락 수나 DOF
- root prim 구조

이 경우에는 task spec과 env cfg를 함께 수정한다.

- [src/isaac_ws/task_specs/shadow_hand_sphere_grasp.py](src/isaac_ws/task_specs/shadow_hand_sphere_grasp.py)
- [src/isaac_ws/lab_tasks/direct/shadow_hand_sphere/env_cfg.py](src/isaac_ws/lab_tasks/direct/shadow_hand_sphere/env_cfg.py)

### 4. Custom policy

`configs/algo/`는 현재 PPO의 scalar hyperparameter를 조절하는 용도다.

- [configs/algo/rsl_rl_ppo.yaml](configs/algo/rsl_rl_ppo.yaml)

예:

```bash
./scripts/run_train.sh \
  algo=rsl_rl_ppo \
  algo.learning_rate=0.0001 \
  algo.steps_per_env=32 \
  algo.max_iterations=2000
```

하지만 네트워크 구조, activation, normalization, obs group 같은 policy 구조는 YAML이 아니라 runner cfg 클래스에 있다.

- [src/isaac_ws/lab_tasks/direct/shadow_hand_sphere/agents/rsl_rl_ppo_cfg.py](src/isaac_ws/lab_tasks/direct/shadow_hand_sphere/agents/rsl_rl_ppo_cfg.py)

즉 custom policy를 넣는 방법은 두 가지다.

1. 기존 runner cfg 클래스를 직접 수정
2. 새 runner cfg 클래스를 만들고 task config에서 그 entry point를 가리키기

현재 task가 어느 policy cfg를 쓰는지는 아래에서 정한다.

- [configs/task/grasp_sphere_shadow_hand_only.yaml](configs/task/grasp_sphere_shadow_hand_only.yaml)

여기서 중요한 키는:

- `implementation.entry_point`
- `implementation.env_cfg_entry_point`
- `implementation.rsl_rl_cfg_entry_point`

예를 들어 새로운 policy cfg 클래스를 만들었다면 `implementation.rsl_rl_cfg_entry_point`를 새 클래스로 바꾸면 된다.

### 5. Custom task

새 task를 만들 때는 아래 순서로 가면 된다.

1. `src/isaac_ws/lab_tasks/direct/<new_task>/` 디렉터리 추가
2. `env.py`, `env_cfg.py`, `agents/rsl_rl_ppo_cfg.py` 작성
3. `__init__.py`에서 `gym.register(...)` 추가
4. `configs/task/<new_task>.yaml` 추가
5. 필요하면 `configs/env`, `configs/reward`, `configs/robot`, `configs/obs`, `configs/action`에 새 조합 추가

현재 등록 예시는 여기 있다.

- [src/isaac_ws/lab_tasks/direct/shadow_hand_sphere/__init__.py](src/isaac_ws/lab_tasks/direct/shadow_hand_sphere/__init__.py)
- [src/isaac_ws/lab_tasks/direct/franka_shadow_hand/__init__.py](src/isaac_ws/lab_tasks/direct/franka_shadow_hand/__init__.py)

task package는 [src/isaac_ws/task_registry.py](src/isaac_ws/task_registry.py) 에서 로드된다.

### 6. Custom observation / action

관측과 액션 조합 이름은 `configs/obs/`, `configs/action/`에서 바꾼다.

- [configs/obs/shadow_hand_grasp_proprio.yaml](configs/obs/shadow_hand_grasp_proprio.yaml)
- [configs/action/shadow_hand_delta_pos.yaml](configs/action/shadow_hand_delta_pos.yaml)

다만 지금 코드 기준으로 observation modality 이름 자체를 바꾼다고 env가 자동으로 새 tensor를 만들어 주지는 않는다. 새 관측 항목이나 새 action semantics를 넣으려면 task env 구현도 같이 바꿔야 한다.

### 7. 실전 기준

정리하면:

- 숫자, 가중치, 배치 크기, workspace, runtime 조합 변경
  - config만 수정
- 새 reward term, 새 observation, 새 action 방식, 새 env reset/done 규칙
  - config + Python 구현 수정
- 같은 구조의 custom USD로 교체
  - robot config 중심
- joint/body 구조가 다른 새 로봇
  - robot config + task spec + env 구현 수정
- 새 policy architecture
  - agent runner cfg 코드 수정

## 문서

- [docs/requirements.md](docs/requirements.md)
- [docs/setup/docker_environment.md](docs/setup/docker_environment.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/deployment.md](docs/deployment.md)
- [docs/tasks/franka_shadow_hand_grasp.md](docs/tasks/franka_shadow_hand_grasp.md)
- [docs/asset_assembly.md](docs/asset_assembly.md)
