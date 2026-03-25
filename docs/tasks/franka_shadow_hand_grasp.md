# Franka Shadow Hand Sphere Grasp

## 목표

손바닥이 하늘을 향한 `Franka + Shadow Hand`가 손바닥 안쪽에 놓인 구형 물체를 감싸 잡고 일정 시간 유지하는 policy를 학습한다.

## 태스크 정의

- 로봇: Franka arm + Shadow Hand
- 물체: 반지름 `3.5cm`, 질량 `0.12kg` 구형 물체
- 초기 상태: 손바닥이 위를 향한 고정 자세, 공은 손바닥 위쪽 오프셋에서 스폰
- 성공 조건:
  - 공이 초기 위치 대비 `4cm` 이상 들림
  - `0.75s` 이상 안정적으로 유지
  - 접촉점 `3개` 이상 유지
  - 공의 속도가 낮고 손바닥이 계속 위를 향함

## 관측

- Franka 관절 위치와 속도
- Shadow Hand 관절 위치와 속도
- palm frame 기준 공의 상대 pose
- 공의 선속도와 각속도
- fingertip contact flag 또는 force
- palm-up alignment

## 액션

- 기본은 normalized delta joint position
- 초기 stage에서는 arm 움직임을 거의 고정하고 hand 중심으로 학습
- curriculum 이후 wrist와 arm을 점진적으로 허용

## 보상 초안

- palm과 공 사이 거리 감소
- fingertip caging과 contact 형성
- 공 들기
- 안정적 hold 유지
- drop penalty
- 과도한 속도와 self-collision penalty

## 구현 메모

- 이것은 기본 제공 ready-made 환경이 아니라 커스텀 task다.
- 로봇 자산 조립이 끝나기 전까지는 실제 Isaac Lab 코드 연결 대신 설정과 문서 기준으로 진행한다.
- 첫 실험은 `num_envs=128`, headless, camera off, PPO baseline으로 시작한다.
