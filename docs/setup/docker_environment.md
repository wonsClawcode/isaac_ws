# Docker Setup

이 저장소는 Docker를 기본 실행 경로로 사용한다. 기준 환경은 Isaac Sim 5.1.0과 Isaac Lab 2.3.2다.

## 전제 조건

- Linux 호스트
- Docker Engine 26 이상
- Docker Compose 2.25 이상
- NVIDIA Container Toolkit
- NVIDIA RTX GPU

## 준비 순서

1. 호스트에서 [scripts/preflight_company.sh](../../scripts/preflight_company.sh)를 실행한다.
2. 필요하면 [.env.example](../../.env.example)를 참고해 `.env`를 만든다.
3. 기본값은 Isaac Sim `5.1.0`, Isaac Lab git tag `v2.3.2`다.

## 이미지 빌드

```bash
./scripts/docker_build.sh
```

상세 step 로그를 모두 보고 싶으면 아래처럼 `plain`으로 바꾼다.

```bash
BUILDKIT_PROGRESS=plain ./scripts/docker_build.sh
```

기본 build 경로는 `docker build` 직접 호출이다. `docker compose build` 흐름이 필요하면 아래처럼 바꿀 수 있다.

```bash
DOCKER_BUILD_METHOD=compose ./scripts/docker_build.sh
```

런타임 import 충돌을 수정한 뒤에는 아래처럼 캐시 없이 다시 빌드한다.

```bash
./scripts/docker_build.sh --no-cache
```

기본 알고리즘은 `rsl_rl_ppo`다. `rl_games`가 필요할 때만 별도로 설치하면 된다.

이 이미지는 아래 레이어를 사용한다.

- 베이스: `nvcr.io/nvidia/isaac-sim:5.1.0`
- Isaac Lab: `https://github.com/isaac-sim/IsaacLab.git` 의 `v2.3.2` tag를 clone한 뒤 공식 `isaaclab.sh --install` 경로로 설치
- PyTorch: Isaac Sim 5.1.0 베이스 이미지에 포함된 번들을 사용
- 기본 RL 라이브러리: `rsl_rl`
- 기본 RL 라이브러리: `isaaclab.sh --install rsl_rl`
- 선택 RL 라이브러리: `rl_games`는 `INSTALL_RL_GAMES=1`일 때만 `isaaclab.sh --install rl_games`

## 설치 확인

```bash
./scripts/verify_docker_stack.sh
```

우리 코드가 아니라 upstream Isaac Lab 공식 example 경로 자체를 검증하고 싶으면 아래 스크립트를 먼저 돌린다.

```bash
./scripts/prepare_x11.sh
./scripts/verify_isaaclab_official.sh gui
```

이 스크립트는 기본적으로 컨테이너 안에서 `isaacsim`, `isaaclab`, `isaaclab_tasks`, `isaaclab_rl`, `rsl-rl-lib`, `onnxscript`, `torch` 설치 상태를 경량 검증한다.

추가로 이미지에 기록된 `Isaac Sim version`, `Isaac Lab git ref`, `실제 commit`, `rl_games 설치 여부`도 `image_*` prefix로 같이 출력한다.

- `VERIFY_SIM_APP_SMOKE=1 ./scripts/verify_docker_stack.sh`
  공식 `isaac-sim.compatibility_check.sh --/app/quitAfter=10 --no-window --reset-user`를 실행한다.
- `VERIFY_APP_LAUNCHER_SMOKE=1 ./scripts/verify_docker_stack.sh`
  Isaac Lab `AppLauncher` 기반의 더 깊은 runtime smoke를 실행한다.

Kit 런타임 충돌이 반복되면 먼저 [scripts/docker_clear_caches.sh](../../scripts/docker_clear_caches.sh)로 named cache를 비운다.

## 컨테이너 진입

지속형 dev container를 사용하려면:

```bash
./scripts/docker_up.sh
./scripts/docker_exec.sh
```

GUI/X11이 필요한 지속형 컨테이너는:

```bash
./scripts/prepare_x11.sh
./scripts/docker_up.sh gui
./scripts/docker_exec.sh
```

정리할 때는:

```bash
./scripts/docker_down.sh
```

컨테이너 안에서 기본 Python 실행 경로는 `/usr/local/bin/isaaclabpy`다. 이 래퍼는 `IsaacLab/isaaclab.sh -p`를 통해 Isaac Sim Python과 Isaac Lab 환경 설정을 함께 적용한다. interactive shell에서는 `python`, `python3`, `isaacpy` alias가 모두 이 경로를 가리킨다. raw Isaac Sim Python이 필요하면 `simpy` alias를 사용한다.

## GUI 디버그

Isaac Lab 공식 문서 기준으로 기본 제공 Isaac Lab 컨테이너는 headless 전용이다. 이 저장소는 GUI가 필요한 경우를 위해 Isaac Sim 5.1.0 베이스 이미지 위에 커스텀 Docker 이미지를 만들고, 별도 Compose 오버라이드로 X11을 연결한다.

Isaac Lab 공식 tutorial smoke는 지속형 컨테이너 기준으로 이렇게 띄운다.

```bash
./scripts/docker_up.sh gui
./scripts/run_isaaclab_example.sh gui
./scripts/run_isaaclab_example.sh headless
./scripts/list_examples.sh
```

기본 GUI example은 `spawn_prims.py`, 기본 headless example은 `create_empty.py`다. 컨테이너 안에 진입한 뒤 같은 스크립트를 직접 실행해도 된다.

Isaac Sim standalone example은 이렇게 띄운다.

```bash
./scripts/docker_up.sh gui
./scripts/run_isaacsim_example.sh
```

persistent container를 쓰는 동안 GUI 창을 닫아도 컨테이너 자체는 계속 살아 있다. 일부 example은 창을 닫아도 exec 세션이 바로 끝나지 않을 수 있으니, 이런 경우에는 `Ctrl-C`로 세션을 정리한다.

무슨 example이 있는지, 실제 경로가 어디인지, 실행 후 무엇이 보여야 정상인지 먼저 보고 싶으면 아래 명령을 쓴다.

```bash
./scripts/list_examples.sh
```

우리 커스텀 task 자체를 빠르게 확인하려면 smoke를 쓴다.

```bash
./scripts/run_task_smoke.sh
./scripts/run_task_smoke.sh env.num_envs=49
./scripts/run_task_smoke.sh runtime=headless run.max_steps=300
```

기본 smoke는 `gui_debug + 49 env + sine action + 1500 step` 조합이다. 학습이 아니라 env 생성, reset, step, 렌더링 경로가 연결되는지 빠르게 보는 용도다.

필수 조건:

- Linux 호스트에서 X11 세션 사용
- `DISPLAY` 설정
- 읽기 가능한 `~/.Xauthority`
- 필요하면 `xhost`로 로컬 사용자 접근 허용

기본 컨테이너 유저는 root다. Isaac Sim 이미지 내부 `/isaac-sim` 경로 권한과 충돌하지 않게 하기 위한 선택이며, `prepare_x11.sh`는 host 사용자와 root 둘 다 X11 접근을 허용한다. 이 때문에 Kit 직접 실행 경로는 `OMNI_KIT_ALLOW_ROOT=1`과 `--allow-root`를 함께 사용한다.

GUI는 디버그, 자산 조립, contact 시각화 용도로만 쓰고, 대규모 학습은 별도 headless 프로파일로 분리하는 편이 안정적이다.

## 스케일 아웃 학습 프로파일

이 저장소는 GUI 확인용과 대규모 병렬 학습용 프로파일을 분리한다.

- GUI 디버그: `env=shadow_hand_palm_up_debug runtime=gui_debug`
- 일반 headless: `env=shadow_hand_palm_up runtime=headless`
- headless 호환 우회: `env=shadow_hand_palm_up runtime=x11_compat`
- 대규모 단일 노드 학습: `env=shadow_hand_palm_up_scaleout runtime=distributed_2gpu` 또는 `runtime=distributed_4gpu`

대규모 학습에서는 `num_envs`, `shm_size`, VRAM 사용량, checkpoint 주기를 함께 조정해야 한다.

특정 호스트에서 native headless `AppLauncher`가 세그폴트 나면, 먼저 X11을 켠 뒤 `runtime=x11_compat`로 우회해서 학습 smoke를 확인할 수 있다. 이 프로파일은 `isaaclab.python.kit`를 사용하고 UI를 숨긴다.

## 학습 래퍼

```bash
./scripts/run_train.sh
./scripts/run_eval.sh
./scripts/run_export.sh
```

학습은 `rsl_rl` 러너를 사용하고, 분산 runtime에서는 `torch.distributed.run`으로 재실행된다. `runtime=gui_debug`가 포함되면 래퍼가 자동으로 X11 compose 오버라이드를 붙인다. 이 경우에는 `./scripts/prepare_x11.sh`를 먼저 실행한다.

이 세 래퍼는 host와 container 안에서 같은 이름으로 실행할 수 있다. host에서는 persistent container를 자동으로 올리거나 재사용하고, container 안에서는 Docker CLI 없이 직접 launcher를 실행한다.
