from __future__ import annotations

import isaaclab.sim as sim_utils
from isaaclab.assets import RigidObjectCfg
from isaaclab.assets.articulation import ArticulationCfg
from isaaclab.envs import DirectRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sim import PhysxCfg, SimulationCfg
from isaaclab.sim.spawners.materials.physics_materials_cfg import RigidBodyMaterialCfg
from isaaclab.utils import configclass

from isaaclab_assets.robots.shadow_hand import SHADOW_HAND_CFG

from isaac_ws.task_specs.shadow_hand_sphere_grasp import SHADOW_HAND_SPHERE_GRASP_SPEC


@configclass
class ShadowHandSphereGraspEnvCfg(DirectRLEnvCfg):
    decimation = 2
    episode_length_s = 8.0
    action_space = SHADOW_HAND_SPHERE_GRASP_SPEC.robot.hand_dof
    observation_space = 60
    state_space = 0

    sim: SimulationCfg = SimulationCfg(
        dt=1.0 / 120.0,
        render_interval=decimation,
        physics_material=RigidBodyMaterialCfg(static_friction=1.1, dynamic_friction=1.1),
        physx=PhysxCfg(bounce_threshold_velocity=0.2),
    )
    scene: InteractiveSceneCfg = InteractiveSceneCfg(
        num_envs=256,
        env_spacing=1.25,
        replicate_physics=True,
        clone_in_fabric=True,
    )

    robot_cfg: ArticulationCfg = SHADOW_HAND_CFG.replace(
        prim_path="/World/envs/env_.*/Robot",
        spawn=SHADOW_HAND_CFG.spawn.replace(activate_contact_sensors=True),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.82),
            rot=(0.7071, -0.7071, 0.0, 0.0),
            joint_pos={".*": 0.0},
        ),
    )

    object_cfg: RigidObjectCfg = RigidObjectCfg(
        prim_path="/World/envs/env_.*/Object",
        spawn=sim_utils.SphereCfg(
            radius=SHADOW_HAND_SPHERE_GRASP_SPEC.object_radius_m,
            mass_props=sim_utils.MassPropertiesCfg(mass=SHADOW_HAND_SPHERE_GRASP_SPEC.object_mass_kg),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=False,
                enable_gyroscopic_forces=True,
                solver_position_iteration_count=8,
                solver_velocity_iteration_count=1,
                max_depenetration_velocity=1000.0,
            ),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            activate_contact_sensors=True,
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.82, 0.38, 0.16)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.96),
            rot=(1.0, 0.0, 0.0, 0.0),
        ),
    )

    actuated_joint_names = list(SHADOW_HAND_SPHERE_GRASP_SPEC.robot.actuated_joint_names)
    fingertip_body_names = list(SHADOW_HAND_SPHERE_GRASP_SPEC.robot.fingertip_frames)

    hand_action_scale = 0.18
    hand_joint_reset_noise = 0.15

    hand_root_position = (0.0, 0.0, 0.82)
    hand_root_rotation = (0.7071, -0.7071, 0.0, 0.0)
    grasp_center_position = (0.0, 0.0, 0.94)
    object_spawn_center = (0.0, 0.0, 0.96)
    object_spawn_jitter = (0.015, 0.015, 0.01)
    object_nominal_height_m = object_spawn_center[2]
    drop_height_m = 0.78
    contact_proxy_radius_m = 0.045
    max_grasp_center_distance_m = SHADOW_HAND_SPHERE_GRASP_SPEC.success.max_grasp_center_distance_m

    reward_palm_to_object = 2.0
    reward_fingertip_contact = 0.75
    reward_fingertip_caging = 1.5
    reward_object_lift = 2.5
    reward_stable_hold = 8.0
    reward_palm_up_alignment = 0.0

    penalty_action_rate = 0.0005
    penalty_joint_velocity = 0.0002
    penalty_object_drop = 8.0
    penalty_self_collision = 0.0

    min_success_lift_height_m = SHADOW_HAND_SPHERE_GRASP_SPEC.success.min_height_above_grasp_center_m
    max_success_object_speed_mps = SHADOW_HAND_SPHERE_GRASP_SPEC.success.max_object_speed_mps
    min_success_contact_sites = SHADOW_HAND_SPHERE_GRASP_SPEC.success.min_contact_sites
    success_hold_duration_s = SHADOW_HAND_SPHERE_GRASP_SPEC.success.hold_duration_s
