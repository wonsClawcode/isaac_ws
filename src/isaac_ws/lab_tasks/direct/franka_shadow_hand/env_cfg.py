from __future__ import annotations

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, RigidObjectCfg
from isaaclab.envs import DirectRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sim import SimulationCfg
from isaaclab.utils import configclass

from isaac_ws.task_specs.franka_shadow_hand_grasp import FRANKA_SHADOW_HAND_GRASP_SPEC


@configclass
class FrankaShadowHandGraspEnvCfg(DirectRLEnvCfg):
    decimation = 2
    episode_length_s = 10.0
    action_space = FRANKA_SHADOW_HAND_GRASP_SPEC.robot.arm_dof + FRANKA_SHADOW_HAND_GRASP_SPEC.robot.hand_dof
    observation_space = 85
    state_space = 0

    sim: SimulationCfg = SimulationCfg(dt=1.0 / 120.0, render_interval=decimation)
    scene: InteractiveSceneCfg = InteractiveSceneCfg(
        num_envs=128,
        env_spacing=2.8,
        replicate_physics=True,
        clone_in_fabric=True,
    )

    robot_cfg: ArticulationCfg = ArticulationCfg(
        prim_path="/World/envs/env_.*/Robot",
        spawn=sim_utils.UsdFileCfg(
            usd_path="assets/robots/franka_shadow_hand/franka_shadow_hand.usd",
            activate_contact_sensors=True,
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.78),
            rot=(1.0, 0.0, 0.0, 0.0),
        ),
        soft_joint_pos_limit_factor=0.95,
    )

    object_cfg: RigidObjectCfg = RigidObjectCfg(
        prim_path="/World/envs/env_.*/Object",
        spawn=sim_utils.SphereCfg(
            radius=FRANKA_SHADOW_HAND_GRASP_SPEC.object_radius_m,
            mass_props=sim_utils.MassPropertiesCfg(mass=FRANKA_SHADOW_HAND_GRASP_SPEC.object_mass_kg),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            activate_contact_sensors=True,
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.82, 0.38, 0.16)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.45, 0.0, 1.005),
            rot=(1.0, 0.0, 0.0, 0.0),
        ),
    )

    arm_dof = FRANKA_SHADOW_HAND_GRASP_SPEC.robot.arm_dof
    hand_dof = FRANKA_SHADOW_HAND_GRASP_SPEC.robot.hand_dof
    palm_body_name = FRANKA_SHADOW_HAND_GRASP_SPEC.robot.palm_frame
    fingertip_body_names = FRANKA_SHADOW_HAND_GRASP_SPEC.robot.fingertip_frames

    arm_action_scale = 0.08
    hand_action_scale = 0.2
    freeze_arm_during_bootstrap = True

    table_height_m = 0.78
    palm_target_position = (0.45, 0.0, 0.95)
    object_spawn_offset = (0.0, 0.0, 0.055)
    object_spawn_jitter = (0.01, 0.01, 0.005)
    object_nominal_spawn_height_m = palm_target_position[2] + object_spawn_offset[2]
    contact_proxy_radius_m = 0.045
    max_palm_object_distance_m = 0.25

    arm_joint_reset_noise = 0.02
    hand_joint_reset_noise = 0.05

    reward_palm_to_object = 1.5
    reward_fingertip_contact = 1.0
    reward_fingertip_caging = 1.0
    reward_object_lift = 4.0
    reward_stable_hold = 6.0
    reward_palm_up_alignment = 0.5

    penalty_action_rate = 0.0005
    penalty_joint_velocity = 0.0002
    penalty_object_drop = 5.0
    penalty_self_collision = 1.0

    min_success_lift_height_m = FRANKA_SHADOW_HAND_GRASP_SPEC.success.min_lift_height_m
    max_success_object_speed_mps = FRANKA_SHADOW_HAND_GRASP_SPEC.success.max_object_speed_mps
    min_success_contact_sites = FRANKA_SHADOW_HAND_GRASP_SPEC.success.min_contact_sites
    success_hold_duration_s = FRANKA_SHADOW_HAND_GRASP_SPEC.success.hold_duration_s
    success_palm_up_cosine = 0.9
