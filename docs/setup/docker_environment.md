# Docker Environment

이 저장소의 기본 실행 경로는 Docker다. 목표는 사내 Linux GPU 머신에서 Isaac Sim 5.1.0과 Isaac Lab이 포함된 컨테이너를 빌드하고, 그 안에서 학습과 검증을 수행하는 것이다.

## 전제 조건

- Linux 호스트
- Docker Engine 26 이상
- Docker Compose 2.25 이상
- NVIDIA Container Toolkit
- NVIDIA RTX GPU

## 준비 순서

1. 호스트에서 [`scripts/preflight_company.sh`](/Users/wonnerky/workspace/isaac_ws/scripts/preflight_company.sh)를 실행한다.
2. 필요하면 [`.env.example`](/Users/wonnerky/workspace/isaac_ws/.env.example)를 참고해 `.env`를 만든다.
3. 기본값은 Isaac Sim `5.1.0`, Isaac Lab git tag `v2.3.2`다.

## 이미지 빌드

```bash
./scripts/docker_build.sh
```

런타임 import 충돌을 수정한 뒤에는 캐시된 레이어를 재사용하지 않도록 아래처럼 재빌드하는 편이 안전하다.

```bash
./scripts/docker_build.sh --no-cache
```

기본 알고리즘은 `rsl_rl_ppo`이므로, 회사망에서 GitHub 접근이 막혀 있으면 `rl_games`는 설치하지 않은 상태로 유지하는 편이 안전하다.

이 이미지는 아래 레이어를 사용한다.

- 베이스: `nvcr.io/nvidia/isaac-sim:5.1.0`
- Isaac Lab: `https://github.com/isaac-sim/IsaacLab.git` 의 `v2.3.2` tag를 clone해서 source install
- PyTorch: Isaac Sim 5.1.0 베이스 이미지에 포함된 번들을 사용
- 기본 RL 라이브러리: `rsl_rl`
- source install 패키지: `isaaclab`, `isaaclab_assets`, `isaaclab_tasks`, `isaaclab_rl[rsl-rl]`
- 선택 RL 라이브러리: `rl_games`는 `INSTALL_RL_GAMES=1`일 때만 별도 clone 후 `--no-build-isolation`으로 설치

## 설치 확인

```bash
./scripts/verify_docker_stack.sh
```

이 스크립트는 기본적으로 컨테이너 안에서 `isaacsim`, `isaaclab`, `isaaclab_tasks`, `rsl-rl-lib`, `onnxscript`, `torch` 경로와 source install된 `isaaclab_rl.rsl_rl` import를 경량 검증한다. `SimulationApp` smoke 테스트는 기본으로 건너뛰고, 필요하면 `VERIFY_SIM_APP_SMOKE=1 ./scripts/verify_docker_stack.sh`로 추가 실행한다.

## 컨테이너 진입

```bash
./scripts/docker_shell.sh
```

컨테이너 안에서 Python은 `/isaac-sim/python.sh`를 사용한다.

## Isaac Sim 실행

```bash
./scripts/run_isaacsim.sh
```

최초 실행 시 Omniverse 확장 캐시를 내려받는 데 시간이 오래 걸릴 수 있다.

## GUI 디버그

Isaac Lab 공식 문서 기준으로 기본 제공 Isaac Lab 컨테이너는 headless 전용이다. 이 저장소는 GUI가 필요한 경우를 위해 Isaac Sim 5.1.0 베이스 이미지 위에 커스텀 Docker 이미지를 만들고, 별도 Compose 오버라이드로 X11을 연결한다.

```bash
./scripts/prepare_x11.sh
./scripts/docker_shell_gui.sh
./scripts/run_isaacsim_gui.sh
```

필수 조건:

- Linux 호스트에서 X11 세션 사용
- `DISPLAY` 설정
- 읽기 가능한 `~/.Xauthority`
- 필요하면 `xhost`로 로컬 사용자 접근 허용

기본 컨테이너 유저는 root다. Isaac Sim 이미지 내부 `/isaac-sim` 경로 권한과 충돌하지 않게 하기 위한 선택이며, `prepare_x11.sh`는 host 사용자와 root 둘 다 X11 접근을 허용한다. 이 때문에 Kit 직접 실행 경로는 `OMNI_KIT_ALLOW_ROOT=1`과 `--allow-root`를 함께 사용한다.

GUI는 디버그, 자산 조립, contact 시각화 용도로만 쓰고, 대규모 학습은 별도 headless 프로파일로 분리하는 편이 안정적이다.

## 스케일 아웃 학습 프로파일

이 저장소는 GUI 확인용과 대규모 병렬 학습용 프로파일을 분리한다.

- GUI 디버그: `env=palm_up_workspace_debug runtime=gui_debug`
- 일반 headless: `env=palm_up_workspace runtime=headless`
- 대규모 단일 노드 학습: `env=palm_up_workspace_scaleout runtime=distributed_2gpu` 또는 `runtime=distributed_4gpu`

대규모 학습에서는 `num_envs`, `shm_size`, VRAM 사용량, checkpoint 주기를 함께 조정해야 한다.

## 학습 래퍼

```bash
./scripts/run_train.sh
./scripts/run_eval.sh
./scripts/run_export.sh
```

현재 이 래퍼들은 실제 실행 경로를 호출한다. 학습은 `rsl_rl` 러너를 사용하고, 분산 runtime에서는 `torch.distributed.run`으로 재실행된다. `runtime=gui_debug`가 포함되면 래퍼가 자동으로 X11 compose 오버라이드를 붙이며, 이때는 `./scripts/prepare_x11.sh`를 먼저 실행해 두는 편이 안전하다.
