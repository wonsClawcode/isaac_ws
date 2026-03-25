from __future__ import annotations

from collections.abc import Sequence
from typing import Optional, Tuple

import torch

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, RigidObject
from isaaclab.envs import DirectRLEnv
from isaaclab.sim.spawners.from_files import GroundPlaneCfg, spawn_ground_plane
from isaaclab.utils.math import sample_uniform

from .env_cfg import ShadowHandSphereGraspEnvCfg


def _quat_mul(lhs: torch.Tensor, rhs: torch.Tensor) -> torch.Tensor:
    lw, lx, ly, lz = lhs.unbind(dim=-1)
    rw, rx, ry, rz = rhs.unbind(dim=-1)
    return torch.stack(
        (
            lw * rw - lx * rx - ly * ry - lz * rz,
            lw * rx + lx * rw + ly * rz - lz * ry,
            lw * ry - lx * rz + ly * rw + lz * rx,
            lw * rz + lx * ry - ly * rx + lz * rw,
        ),
        dim=-1,
    )


def _quat_from_euler_xyz(roll: torch.Tensor, pitch: torch.Tensor, yaw: torch.Tensor) -> torch.Tensor:
    half_roll = roll * 0.5
    half_pitch = pitch * 0.5
    half_yaw = yaw * 0.5

    cr = torch.cos(half_roll)
    sr = torch.sin(half_roll)
    cp = torch.cos(half_pitch)
    sp = torch.sin(half_pitch)
    cy = torch.cos(half_yaw)
    sy = torch.sin(half_yaw)

    return torch.stack(
        (
            cr * cp * cy + sr * sp * sy,
            sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy,
        ),
        dim=-1,
    )


class ShadowHandSphereGraspEnv(DirectRLEnv):
    cfg: ShadowHandSphereGraspEnvCfg

    def __init__(self, cfg: ShadowHandSphereGraspEnvCfg, render_mode: Optional[str] = None, **kwargs):
        self.actions = None
        self.previous_actions = None
        self.joint_position_targets = None
        self.hold_steps = None
        self.actuated_joint_indices = None
        self.curl_joint_indices = None
        self.fingertip_body_indices = None
        self._success_hold_steps = max(1, int(round(cfg.success_hold_duration_s / (cfg.sim.dt * cfg.decimation))))
        super().__init__(cfg, render_mode, **kwargs)

        self.actuated_joint_indices = torch.tensor(
            [self.robot.joint_names.index(name) for name in self.cfg.actuated_joint_names],
            device=self.device,
            dtype=torch.long,
        )
        self.curl_joint_indices = torch.tensor(
            [self.robot.joint_names.index(name) for name in self.cfg.curl_joint_names],
            device=self.device,
            dtype=torch.long,
        )
        self.fingertip_body_indices = torch.tensor(
            [self.robot.body_names.index(name) for name in self.cfg.fingertip_body_names],
            device=self.device,
            dtype=torch.long,
        )

        self.actions = torch.zeros(self.num_envs, self.cfg.action_space, device=self.device)
        self.previous_actions = torch.zeros_like(self.actions)
        self.joint_position_targets = self.robot.data.default_joint_pos.clone()
        self.hold_steps = torch.zeros(self.num_envs, device=self.device, dtype=torch.long)

    def _setup_scene(self) -> None:
        self.robot = Articulation(self.cfg.robot_cfg)
        self.object = RigidObject(self.cfg.object_cfg)

        spawn_ground_plane(prim_path="/World/ground", cfg=GroundPlaneCfg())

        self.scene.clone_environments(copy_from_source=False)
        self.scene.articulations["robot"] = self.robot
        self.scene.rigid_objects["object"] = self.object

        light_cfg = sim_utils.DomeLightCfg(intensity=2000.0, color=(0.92, 0.92, 0.92))
        light_cfg.func("/World/Light", light_cfg)

    def _pre_physics_step(self, actions: torch.Tensor) -> None:
        clipped_actions = torch.clamp(actions, -1.0, 1.0)
        self.previous_actions.copy_(self.actions)
        self.actions.copy_(clipped_actions)

        delta_targets = clipped_actions * self.cfg.hand_action_scale
        joint_limits = self.robot.data.soft_joint_pos_limits
        lower_limits = joint_limits[:, :, 0]
        upper_limits = joint_limits[:, :, 1]

        self.joint_position_targets[:, self.actuated_joint_indices] = torch.clamp(
            self.joint_position_targets[:, self.actuated_joint_indices] + delta_targets,
            min=lower_limits[:, self.actuated_joint_indices],
            max=upper_limits[:, self.actuated_joint_indices],
        )

    def _apply_action(self) -> None:
        self.robot.set_joint_position_target(
            self.joint_position_targets[:, self.actuated_joint_indices],
            joint_ids=self.actuated_joint_indices,
        )

    def _get_observations(self) -> dict:
        joint_pos = self.robot.data.joint_pos[:, self.actuated_joint_indices]
        joint_vel = self.robot.data.joint_vel[:, self.actuated_joint_indices]

        object_pos = self.object.data.root_pos_w - self.scene.env_origins
        object_lin_vel = self.object.data.root_lin_vel_w
        object_ang_vel = self.object.data.root_ang_vel_w
        contact_flags, contact_force_proxy = self._compute_contact_proxy(object_pos)
        object_height = (object_pos[:, 2] - self.cfg.grasp_center_position[2]).unsqueeze(-1)

        grasp_center = torch.tensor(self.cfg.grasp_center_position, device=self.device).unsqueeze(0)
        object_rel_pos = object_pos - grasp_center

        obs = torch.cat(
            (
                joint_pos,
                joint_vel,
                object_rel_pos,
                object_lin_vel,
                object_ang_vel,
                contact_flags.float(),
                contact_force_proxy,
                object_height,
            ),
            dim=-1,
        )
        return {"policy": obs}

    def _get_rewards(self) -> torch.Tensor:
        joint_vel = self.robot.data.joint_vel[:, self.actuated_joint_indices]
        object_pos = self.object.data.root_pos_w - self.scene.env_origins
        object_lin_vel = self.object.data.root_lin_vel_w
        object_speed = torch.linalg.norm(object_lin_vel, dim=-1)

        grasp_center = torch.tensor(self.cfg.grasp_center_position, device=self.device).unsqueeze(0)
        grasp_distance = torch.linalg.norm(object_pos - grasp_center, dim=-1)
        object_height = torch.clamp(object_pos[:, 2] - self.cfg.grasp_center_position[2], min=0.0)

        contact_flags, contact_force_proxy = self._compute_contact_proxy(object_pos)
        contact_count = torch.sum(contact_flags, dim=-1)
        caging_score = torch.mean(contact_force_proxy, dim=-1)
        finger_curl = self._compute_finger_curl()

        stable_hold = grasp_distance <= self.cfg.max_grasp_center_distance_m
        stable_hold = stable_hold & (object_height >= self.cfg.min_success_lift_height_m)
        stable_hold = stable_hold & (object_speed <= self.cfg.max_success_object_speed_mps)
        stable_hold = stable_hold & (contact_count >= self.cfg.min_success_contact_sites)
        stable_hold = stable_hold & (finger_curl >= self.cfg.min_success_finger_curl)
        self.hold_steps = torch.where(stable_hold, self.hold_steps + 1, torch.zeros_like(self.hold_steps))

        reward = torch.zeros(self.num_envs, device=self.device)
        reward += self.cfg.reward_palm_to_object * torch.exp(-10.0 * grasp_distance)
        reward += self.cfg.reward_fingertip_contact * contact_count.float()
        reward += self.cfg.reward_fingertip_caging * caging_score
        reward += self.cfg.reward_finger_curl * finger_curl * torch.exp(-8.0 * grasp_distance)
        reward += self.cfg.reward_object_lift * object_height
        reward += self.cfg.reward_stable_hold * (self.hold_steps >= self._success_hold_steps).float()

        action_rate = torch.sum(torch.square(self.actions - self.previous_actions), dim=-1)
        joint_velocity_penalty = torch.sum(torch.square(joint_vel), dim=-1)
        dropped = object_pos[:, 2] < self.cfg.drop_height_m

        reward -= self.cfg.penalty_action_rate * action_rate
        reward -= self.cfg.penalty_joint_velocity * joint_velocity_penalty
        reward -= self.cfg.penalty_object_drop * dropped.float()
        return reward

    def _get_dones(self) -> Tuple[torch.Tensor, torch.Tensor]:
        object_pos = self.object.data.root_pos_w - self.scene.env_origins
        grasp_center = torch.tensor(self.cfg.grasp_center_position, device=self.device).unsqueeze(0)
        grasp_distance = torch.linalg.norm(object_pos - grasp_center, dim=-1)

        dropped = object_pos[:, 2] < self.cfg.drop_height_m
        too_far = grasp_distance > (self.cfg.max_grasp_center_distance_m * 2.0)
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

        actuated_noise = sample_uniform(
            -self.cfg.hand_joint_reset_noise,
            self.cfg.hand_joint_reset_noise,
            (len(env_ids), len(self.actuated_joint_indices)),
            self.device,
        )
        joint_pos[:, self.actuated_joint_indices] += actuated_noise
        joint_pos = torch.clamp(joint_pos, min=joint_limits[:, :, 0], max=joint_limits[:, :, 1])

        robot_root_state = self.robot.data.default_root_state[env_ids].clone()
        robot_root_state[:, :3] = torch.tensor(self.cfg.hand_root_position, device=self.device).repeat(len(env_ids), 1)
        robot_root_state[:, :3] += self.scene.env_origins[env_ids]
        robot_root_state[:, 3:7] = self._sample_root_quaternions(len(env_ids))
        robot_root_state[:, 7:] = 0.0
        self.robot.write_root_pose_to_sim(robot_root_state[:, :7], env_ids)
        self.robot.write_root_velocity_to_sim(robot_root_state[:, 7:], env_ids)
        self.robot.write_joint_state_to_sim(joint_pos, joint_vel, None, env_ids)

        object_root_state = self.object.data.default_root_state[env_ids].clone()
        object_root_state[:, :3] = self._sample_object_spawn_positions(len(env_ids))
        object_root_state[:, :3] += self.scene.env_origins[env_ids]
        object_root_state[:, 3:7] = torch.tensor((1.0, 0.0, 0.0, 0.0), device=self.device).repeat(len(env_ids), 1)
        object_root_state[:, 7:] = 0.0
        self.object.write_root_pose_to_sim(object_root_state[:, :7], env_ids)
        self.object.write_root_velocity_to_sim(object_root_state[:, 7:], env_ids)

        self.joint_position_targets[env_ids] = joint_pos
        self.robot.set_joint_position_target(self.joint_position_targets[env_ids], env_ids=env_ids)
        self.actions[env_ids] = 0.0
        self.previous_actions[env_ids] = 0.0
        self.hold_steps[env_ids] = 0

    def _compute_contact_proxy(self, object_pos: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        fingertip_pos = self.robot.data.body_pos_w[:, self.fingertip_body_indices] - self.scene.env_origins.unsqueeze(1)
        fingertip_distance = torch.linalg.norm(fingertip_pos - object_pos.unsqueeze(1), dim=-1)
        contact_flags = fingertip_distance <= self.cfg.contact_proxy_radius_m
        contact_force_proxy = torch.clamp(self.cfg.contact_proxy_radius_m - fingertip_distance, min=0.0)
        contact_force_proxy = contact_force_proxy / self.cfg.contact_proxy_radius_m
        return contact_flags, contact_force_proxy

    def _compute_finger_curl(self) -> torch.Tensor:
        joint_pos = self.robot.data.joint_pos[:, self.curl_joint_indices]
        joint_limits = self.robot.data.soft_joint_pos_limits[:, self.curl_joint_indices]
        lower_limits = joint_limits[:, :, 0]
        upper_limits = joint_limits[:, :, 1]
        normalized = (joint_pos - lower_limits) / torch.clamp(upper_limits - lower_limits, min=1.0e-6)
        normalized = torch.clamp(normalized, 0.0, 1.0)
        return torch.mean(normalized, dim=-1)

    def _sample_root_quaternions(self, count: int) -> torch.Tensor:
        base_quat = torch.tensor(self.cfg.hand_root_rotation, device=self.device).repeat(count, 1)
        jitter_deg = self.cfg.hand_root_rotation_jitter_deg
        if not any(abs(float(component)) > 0.0 for component in jitter_deg):
            return base_quat

        deg_to_rad = torch.pi / 180.0
        roll = sample_uniform(-float(jitter_deg[0]), float(jitter_deg[0]), (count,), self.device) * deg_to_rad
        pitch = sample_uniform(-float(jitter_deg[1]), float(jitter_deg[1]), (count,), self.device) * deg_to_rad
        yaw = sample_uniform(-float(jitter_deg[2]), float(jitter_deg[2]), (count,), self.device) * deg_to_rad
        jitter_quat = _quat_from_euler_xyz(roll, pitch, yaw)
        root_quat = _quat_mul(base_quat, jitter_quat)
        return root_quat / torch.linalg.norm(root_quat, dim=-1, keepdim=True).clamp_min(1.0e-6)

    def _sample_object_spawn_positions(self, count: int) -> torch.Tensor:
        center = torch.tensor(self.cfg.object_spawn_center, device=self.device).repeat(count, 1)
        jitter = torch.stack(
            (
                sample_uniform(-self.cfg.object_spawn_jitter[0], self.cfg.object_spawn_jitter[0], (count,), self.device),
                sample_uniform(-self.cfg.object_spawn_jitter[1], self.cfg.object_spawn_jitter[1], (count,), self.device),
                sample_uniform(-self.cfg.object_spawn_jitter[2], self.cfg.object_spawn_jitter[2], (count,), self.device),
            ),
            dim=-1,
        )
        return center + jitter
