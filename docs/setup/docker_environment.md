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
3. 기본값은 Isaac Sim `5.1.0`, Isaac Lab `2.3.2.post1`이다.

## 이미지 빌드

```bash
./scripts/docker_build.sh
```

이 이미지는 아래 레이어를 사용한다.

- 베이스: `nvcr.io/nvidia/isaac-sim:5.1.0`
- Isaac Lab: `isaaclab[isaacsim,all]==2.3.2.post1`
- PyTorch: CUDA 12.8용 `torch==2.7.0`, `torchvision==0.22.0`
- RL 라이브러리: `rl_games` Python 3.11 포크

## 설치 확인

```bash
./scripts/verify_docker_stack.sh
```

이 스크립트는 컨테이너 안에서 `isaacsim`과 `isaaclab` 패키지 버전을 확인한다.

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

## 학습 래퍼

```bash
./scripts/run_train.sh
./scripts/run_eval.sh
./scripts/run_export.sh
```

현재 이 래퍼들은 실제 학습 전 단계의 실행 계획 확인용 엔트리포인트를 호출한다. 실제 Isaac Lab task 코드가 연결되면 같은 래퍼 경로를 유지한 채 내부 구현만 바꾸면 된다.
