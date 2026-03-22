# Asset Assembly

이 프로젝트의 기본 로봇은 `Franka arm + Shadow Hand` 조합이다. 공식 자산은 각각 존재하지만, 이 조합 자체는 기본 제공 태스크로 보이지 않으므로 커스텀 로봇 자산이 필요하다.

## 필요한 작업

1. Franka 말단 gripper를 제거하거나 비활성화한다.
2. Shadow Hand를 Franka flange 기준으로 부착한다.
3. 실제 어댑터가 있다면 그 CAD와 동일한 오프셋을 반영한다.
4. 결합 후 전체 articulation의 질량, 관성, joint limit, self-collision, PD gain을 재조정한다.

## 권장 산출물

- `assets/robots/franka_shadow_hand/franka_shadow_hand.usd`
- 부착 오프셋과 프레임 정의 문서
- 실제 하드웨어 기준 질량과 관성 메모

## 리스크

- 말단 질량 증가로 Franka 기본 gain이 맞지 않을 수 있다.
- Shadow Hand tendon/coupling을 단순 관절 구동으로 근사하면 실기와 차이가 커질 수 있다.
- palm frame과 실제 센서 또는 도구 프레임이 어긋나면 sim-to-real 오차가 커진다.

## 참고

- Isaac Sim robot schema: <https://docs.isaacsim.omniverse.nvidia.com/5.1.0/omniverse_usd/robot_schema.html>
- Isaac Sim URDF importer: <https://docs.isaacsim.omniverse.nvidia.com/latest/robot_setup/ext_isaacsim_asset_importer_urdf.html>
