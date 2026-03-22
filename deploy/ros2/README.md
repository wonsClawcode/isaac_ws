# ROS 2 Deployment Placeholder

이 디렉터리는 실제 로봇 배포 구성을 담기 위한 자리다.

권장 하위 구조:

- `bringup/`: 로봇 드라이버 및 launch 파일
- `inference/`: 정책 추론 노드
- `interfaces/`: 메시지 또는 서비스 정의
- `config/`: 로봇별 파라미터

실제 로봇이 정해지면 다음을 먼저 확정해야 한다.

- ROS 2 배포 타깃 머신
- 제어 주기
- 관측 토픽과 액션 토픽
- 안전 정지와 상태 전이 정책
