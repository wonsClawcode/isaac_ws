# Requirements

공식 문서 기준으로 이 프로젝트의 실제 실행 타깃은 Linux GPU 머신이며, 기본 설치 경로는 Docker다.

## 호스트 요구사항

- Ubuntu 22.04 또는 24.04 권장
- NVIDIA RTX GPU 권장
- 16GB 이상 VRAM 권장
- 32GB 이상 시스템 메모리 권장
- Docker Engine 26 이상
- Docker Compose 2.25 이상
- NVIDIA Container Toolkit 설치

Isaac Sim 컨테이너는 Linux 기반 원격 헤드리스 또는 클라우드 배포에 적합하고, RTX 계열 GPU를 전제로 한다. 공식 문서 기준으로 컨테이너는 Linux만 지원되며, RT Core가 없는 GPU인 A100, H100은 지원되지 않는다.

## 이 노트북에서 가능한 일

- 디렉터리 구조 설계
- Hydra 설정 정의
- Dockerfile 및 compose 작성
- 학습 스크립트와 배포 문서 정리

## 이 노트북에서 하지 않는 일

- Isaac Sim GUI 실행
- 대규모 병렬 학습
- 실제 렌더링 성능 검증
- 실기 로봇 연결 테스트

## 사내 머신 준비 체크리스트

1. `nvidia-smi`가 정상 동작하는지 확인
2. `docker version`과 `docker compose version` 확인
3. `docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi` 확인
4. 이 저장소를 클론하고 `docker/env/company.env` 또는 `.env` 값 검토
5. `./scripts/docker_build.sh`로 이미지 빌드
6. `./scripts/verify_docker_stack.sh`로 Isaac Sim 5.1.0 / Isaac Lab 2.3.2 확인
7. `./scripts/run_train.sh`로 설정 조합 점검

## 참고

- Isaac Sim container installation: <https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_container.html>
- Isaac Sim requirements: <https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html>
- Isaac Lab Docker guide: <https://isaac-sim.github.io/IsaacLab/main/source/deployment/docker.html>
- Isaac Lab pip packages: <https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/isaaclab_pip_installation.html>
