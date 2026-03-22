from __future__ import annotations

from collections.abc import Sequence
from typing import Optional, Tuple

import torch

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, RigidObject
from isaaclab.envs import DirectRLEnv
from isaaclab.sim.spawners.from_files import GroundPlaneCfg, spawn_ground_plane
from isaaclab.utils.math import quat_apply, quat_apply_inverse, sample_uniform

from .env_cfg import FrankaShadowHandGraspEnvCfg


class FrankaShadowHandGraspEnv(DirectRLEnv):
    cfg: FrankaShadowHandGraspEnvCfg

    def __init__(self, cfg: FrankaShadowHandGraspEnvCfg, render_mode: Optional[str] = None, **kwargs):
        self.actions = None
        self.previous_actions = None
        self.joint_position_targets = None
        self.hold_steps = None
        self.palm_body_idx = None
        self.fingertip_body_indices = None
        self.arm_joint_indices = None
        self.hand_joint_indices = None
        self._world_up = None
        self._success_hold_steps = max(1, int(round(cfg.success_hold_duration_s / (cfg.sim.dt * cfg.decimation))))
        super().__init__(cfg, render_mode, **kwargs)

        # The combined USD is expected to order arm joints first, followed by Shadow Hand joints.
        self.arm_joint_indices = torch.arange(self.cfg.arm_dof, device=self.device, dtype=torch.long)
        self.hand_joint_indices = torch.arange(
            self.cfg.arm_dof,
            self.cfg.arm_dof + self.cfg.hand_dof,
            device=self.device,
            dtype=torch.long,
        )

        palm_body_indices, _ = self.robot.find_bodies(self.cfg.palm_body_name)
        self.palm_body_idx = int(palm_body_indices[0])
        self.fingertip_body_indices = torch.tensor(
            [int(self.robot.find_bodies(name)[0][0]) for name in self.cfg.fingertip_body_names],
            device=self.device,
            dtype=torch.long,
        )

        self.actions = torch.zeros(self.num_envs, self.cfg.action_space, device=self.device)
        self.previous_actions = torch.zeros_like(self.actions)
        self.joint_position_targets = self.robot.data.default_joint_pos.clone()
        self.hold_steps = torch.zeros(self.num_envs, device=self.device, dtype=torch.long)
        self._world_up = torch.tensor((0.0, 0.0, 1.0), device=self.device).repeat(self.num_envs, 1)

    def _setup_scene(self) -> None:
        self.robot = Articulation(self.cfg.robot_cfg)
        self.object = RigidObject(self.cfg.object_cfg)

        spawn_ground_plane(prim_path="/World/ground", cfg=GroundPlaneCfg())

        self.scene.clone_environments(copy_from_source=False)
        if self.device == "cpu":
            self.scene.filter_collisions(global_prim_paths=["/World/ground"])

        self.scene.articulations["robot"] = self.robot
        self.scene.rigid_objects["object"] = self.object

        light_cfg = sim_utils.DomeLightCfg(intensity=2500.0, color=(0.92, 0.92, 0.92))
        light_cfg.func("/World/Light", light_cfg)

    def _pre_physics_step(self, actions: torch.Tensor) -> None:
        clipped_actions = torch.clamp(actions, -1.0, 1.0)
        self.previous_actions.copy_(self.actions)
        self.actions.copy_(clipped_actions)

        delta_targets = torch.zeros_like(clipped_actions)
        delta_targets[:, self.arm_joint_indices] = clipped_actions[:, self.arm_joint_indices] * self.cfg.arm_action_scale
        delta_targets[:, self.hand_joint_indices] = clipped_actions[:, self.hand_joint_indices] * self.cfg.hand_action_scale

        if self.cfg.freeze_arm_during_bootstrap:
            delta_targets[:, self.arm_joint_indices] = 0.0

        joint_limits = self.robot.data.soft_joint_pos_limits
        lower_limits = joint_limits[:, :, 0]
        upper_limits = joint_limits[:, :, 1]
        self.joint_position_targets = torch.clamp(
            self.joint_position_targets + delta_targets,
            min=lower_limits,
            max=upper_limits,
        )

    def _apply_action(self) -> None:
        self.robot.set_joint_position_target(self.joint_position_targets)

    def _get_observations(self) -> dict:
        joint_pos = self.robot.data.joint_pos
        joint_vel = self.robot.data.joint_vel

        palm_state = self._get_palm_state()
        palm_pos = palm_state[:, :3]
        palm_quat = palm_state[:, 3:7]

        object_state = self.object.data.root_state_w
        object_pos = object_state[:, :3]
        object_lin_vel = object_state[:, 7:10]
        object_ang_vel = object_state[:, 10:13]

        object_pos_in_palm = quat_apply_inverse(palm_quat, object_pos - palm_pos)
        contact_flags, contact_force_proxy = self._compute_contact_proxy(object_pos)
        palm_up_alignment = self._compute_palm_up_alignment(palm_quat).unsqueeze(-1)

        obs = torch.cat(
            (
                joint_pos[:, self.arm_joint_indices],
                joint_vel[:, self.arm_joint_indices],
                joint_pos[:, self.hand_joint_indices],
                joint_vel[:, self.hand_joint_indices],
                palm_pos,
                object_pos_in_palm,
                object_lin_vel,
                object_ang_vel,
                contact_flags.float(),
                contact_force_proxy,
                palm_up_alignment,
            ),
            dim=-1,
        )
        return {"policy": obs}

    def _get_rewards(self) -> torch.Tensor:
        joint_vel = self.robot.data.joint_vel
        palm_state = self._get_palm_state()
        fingertip_pos = self._get_fingertip_positions()
        object_state = self.object.data.root_state_w

        palm_pos = palm_state[:, :3]
        palm_quat = palm_state[:, 3:7]
        object_pos = object_state[:, :3]
        object_lin_vel = object_state[:, 7:10]
        object_speed = torch.linalg.norm(object_lin_vel, dim=-1)

        palm_to_object = torch.linalg.norm(object_pos - palm_pos, dim=-1)
        contact_flags, contact_force_proxy = self._compute_contact_proxy(object_pos)
        contact_count = torch.sum(contact_flags, dim=-1)
        caging_score = torch.mean(contact_force_proxy, dim=-1)
        palm_up_alignment = self._compute_palm_up_alignment(palm_quat)

        lift_height = torch.clamp(object_pos[:, 2] - self.cfg.object_nominal_spawn_height_m, min=0.0)
        lifted = lift_height >= self.cfg.min_success_lift_height_m
        stable_hold = lifted & (object_speed <= self.cfg.max_success_object_speed_mps)
        stable_hold = stable_hold & (contact_count >= self.cfg.min_success_contact_sites)
        stable_hold = stable_hold & (palm_up_alignment >= self.cfg.success_palm_up_cosine)
        self.hold_steps = torch.where(stable_hold, self.hold_steps + 1, torch.zeros_like(self.hold_steps))

        reward = torch.zeros(self.num_envs, device=self.device)
        reward += self.cfg.reward_palm_to_object * torch.exp(-8.0 * palm_to_object)
        reward += self.cfg.reward_fingertip_contact * contact_count.float()
        reward += self.cfg.reward_fingertip_caging * caging_score
        reward += self.cfg.reward_object_lift * lift_height
        reward += self.cfg.reward_stable_hold * (self.hold_steps >= self._success_hold_steps).float()
        reward += self.cfg.reward_palm_up_alignment * torch.clamp(palm_up_alignment, min=0.0)

        action_rate = torch.sum(torch.square(self.actions - self.previous_actions), dim=-1)
        joint_velocity_penalty = torch.sum(torch.square(joint_vel), dim=-1)
        dropped = object_pos[:, 2] < (self.cfg.table_height_m - 0.02)

        reward -= self.cfg.penalty_action_rate * action_rate
        reward -= self.cfg.penalty_joint_velocity * joint_velocity_penalty
        reward -= self.cfg.penalty_object_drop * dropped.float()
        # TODO: Replace this proxy term with an actual self-collision sensor once the combined USD is finalized.
        reward -= self.cfg.penalty_self_collision * torch.zeros_like(reward)
        return reward

    def _get_dones(self) -> Tuple[torch.Tensor, torch.Tensor]:
        palm_state = self._get_palm_state()
        object_state = self.object.data.root_state_w

        palm_pos = palm_state[:, :3]
        object_pos = object_state[:, :3]

        dropped = object_pos[:, 2] < (self.cfg.table_height_m - 0.02)
        too_far = torch.linalg.norm(object_pos - palm_pos, dim=-1) > self.cfg.max_palm_object_distance_m
        success = self.hold_steps >= self._success_hold_steps
        time_out = self.episode_length_buf >= self.max_episode_length - 1
        return dropped | too_far | success, time_out

    def _reset_idx(self, env_ids: Optional[Sequence[int]]) -> None:
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES
        super()._reset_idx(env_ids)

        joint_pos = self.robot.data.default_joint_pos[env_ids].clone()
        joint_vel = self.robot.data.default_joint_vel[env_ids].clone()
        joint_limits = self.robot.data.soft_joint_pos_limits[env_ids]

        joint_pos[:, self.arm_joint_indices] += sample_uniform(
            -self.cfg.arm_joint_reset_noise,
            self.cfg.arm_joint_reset_noise,
            joint_pos[:, self.arm_joint_indices].shape,
            self.device,
        )
        joint_pos[:, self.hand_joint_indices] += sample_uniform(
            -self.cfg.hand_joint_reset_noise,
            self.cfg.hand_joint_reset_noise,
            joint_pos[:, self.hand_joint_indices].shape,
            self.device,
        )
        joint_pos = torch.clamp(joint_pos, min=joint_limits[:, :, 0], max=joint_limits[:, :, 1])

        robot_root_state = self.robot.data.default_root_state[env_ids].clone()
        robot_root_state[:, :3] += self.scene.env_origins[env_ids]
        self.robot.write_root_pose_to_sim(robot_root_state[:, :7], env_ids)
        self.robot.write_root_velocity_to_sim(robot_root_state[:, 7:], env_ids)
        self.robot.write_joint_state_to_sim(joint_pos, joint_vel, None, env_ids)

        object_root_state = self.object.data.default_root_state[env_ids].clone()
        object_root_state[:, :3] = self._sample_object_spawn_positions(len(env_ids), env_ids)
        object_root_state[:, :3] += self.scene.env_origins[env_ids]
        object_root_state[:, 3:7] = torch.tensor((1.0, 0.0, 0.0, 0.0), device=self.device).repeat(len(env_ids), 1)
        object_root_state[:, 7:] = 0.0
        self.object.write_root_pose_to_sim(object_root_state[:, :7], env_ids)
        self.object.write_root_velocity_to_sim(object_root_state[:, 7:], env_ids)

        self.joint_position_targets[env_ids] = joint_pos
        self.actions[env_ids] = 0.0
        self.previous_actions[env_ids] = 0.0
        self.hold_steps[env_ids] = 0

    def _get_palm_state(self) -> torch.Tensor:
        return self.robot.data.body_state_w[:, self.palm_body_idx, :]

    def _get_fingertip_positions(self) -> torch.Tensor:
        return self.robot.data.body_state_w[:, self.fingertip_body_indices, :3]

    def _compute_contact_proxy(self, object_pos: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        # TODO: Replace with ContactSensor outputs once fingertip collision geometry is fixed in the assembled USD.
        fingertip_pos = self._get_fingertip_positions()
        fingertip_distance = torch.linalg.norm(fingertip_pos - object_pos.unsqueeze(1), dim=-1)
        contact_flags = fingertip_distance <= self.cfg.contact_proxy_radius_m
        contact_force_proxy = torch.clamp(self.cfg.contact_proxy_radius_m - fingertip_distance, min=0.0)
        contact_force_proxy = contact_force_proxy / self.cfg.contact_proxy_radius_m
        return contact_flags, contact_force_proxy

    def _compute_palm_up_alignment(self, palm_quat: torch.Tensor) -> torch.Tensor:
        palm_up_vector = quat_apply(palm_quat, self._world_up)
        return torch.sum(palm_up_vector * self._world_up, dim=-1)

    def _sample_object_spawn_positions(self, count: int, env_ids: Sequence[int]) -> torch.Tensor:
        del env_ids
        center = torch.tensor(
            (
                self.cfg.palm_target_position[0] + self.cfg.object_spawn_offset[0],
                self.cfg.palm_target_position[1] + self.cfg.object_spawn_offset[1],
                self.cfg.palm_target_position[2] + self.cfg.object_spawn_offset[2],
            ),
            device=self.device,
        ).repeat(count, 1)
        jitter = torch.stack(
            (
                sample_uniform(
                    -self.cfg.object_spawn_jitter[0],
                    self.cfg.object_spawn_jitter[0],
                    (count,),
                    self.device,
                ),
                sample_uniform(
                    -self.cfg.object_spawn_jitter[1],
                    self.cfg.object_spawn_jitter[1],
                    (count,),
                    self.device,
                ),
                sample_uniform(
                    -self.cfg.object_spawn_jitter[2],
                    self.cfg.object_spawn_jitter[2],
                    (count,),
                    self.device,
                ),
            ),
            dim=-1,
        )
        return center + jitter
