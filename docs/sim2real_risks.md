# Sim2Real Risks

`Franka + Shadow Hand` 구형 물체 grasp는 contact-rich 태스크라 sim-to-real 리스크가 높다.

## 우선순위 높은 리스크

- 말단 조립체의 질량, 관성, COM 오차
- Shadow Hand tendon/coupling 모델 단순화
- sphere 재질, 마찰, 탄성 오차
- fingertip contact와 충돌 안정성
- 제어 주기와 지연 차이
- 실제 grasp force 제한과 안전 정책 부재

## 실기 전 필수 점검

1. palm frame과 실기 기준 좌표계 일치 여부
2. 손가락 joint limit과 saturation
3. emergency stop과 workspace limit
4. 저속 정책 추론부터 검증
5. 실기에서 관측 가능한 값만 policy 입력에 남기기

## 권장 순서

1. 시뮬레이션에서 fixed reset으로 grasp 형성을 확인
2. sphere jitter와 마찰 randomization을 단계적으로 추가
3. ONNX 또는 추론용 형식으로 정책 export
4. ROS 2 추론 노드에서 저속 검증
5. grasp force와 충돌 제한을 둔 상태로 실기 테스트
