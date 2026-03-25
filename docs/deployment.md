# Deployment

실기 배포는 학습과 별도 단계로 본다. 이 디렉터리는 그 준비를 위한 자리다.

## 필요한 추가 요소

- 실기 로봇 드라이버
- ROS 2 인터페이스
- 정책 추론 노드
- 캘리브레이션과 좌표계 관리
- 제어 주기, 지연, 노이즈 보정
- 안전 정지와 워크스페이스 제한

## 권장 흐름

1. Isaac Lab에서 task와 reward를 정리한다.
2. 시뮬레이션에서 학습과 재현성을 확보한다.
3. 정책을 내보내기 가능한 형식으로 변환한다.
4. ROS 2 기반 추론 노드에서 정책을 감싼다.
5. 실기 센서/액추에이터 스펙에 맞게 observation/action 매핑을 재검증한다.
6. 안전 계층을 포함해 제한된 동작 범위에서 실기 검증을 시작한다.

## 앞으로 채울 항목

- 대상 로봇별 `deploy/ros2/<robot_name>/` 구조
- 정책 export 형식 결정
- 추론 주기와 제어 주기 정의
- 로봇별 bringup 절차 문서
- `Franka + Shadow Hand` 말단 조립체의 실제 질량, 관성, 오프셋 반영

## 참고

- Isaac Lab policy deployment guide: <https://isaac-sim.github.io/IsaacLab/main/source/policy_deployment/index.html>
- Isaac Sim ROS 2 bridge: <https://docs.isaacsim.omniverse.nvidia.com/5.1.0/py/source/extensions/isaacsim.ros2.bridge/docs/index.html>
