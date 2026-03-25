from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SuccessCriteria:
    min_height_above_grasp_center_m: float
    max_object_speed_mps: float
    min_contact_sites: int
    hold_duration_s: float
    max_grasp_center_distance_m: float


@dataclass(frozen=True)
class RobotSpec:
    hand_dof: int
    actuated_joint_names: tuple[str, ...]
    curl_joint_names: tuple[str, ...]
    fingertip_frames: tuple[str, ...]


@dataclass(frozen=True)
class TaskSpec:
    name: str
    object_radius_m: float
    object_mass_kg: float
    robot: RobotSpec
    success: SuccessCriteria
    curriculum: tuple[str, ...]


SHADOW_HAND_SPHERE_GRASP_SPEC = TaskSpec(
    name="grasp_sphere_shadow_hand_only",
    object_radius_m=0.035,
    object_mass_kg=0.08,
    robot=RobotSpec(
        hand_dof=20,
        actuated_joint_names=(
            "robot0_WRJ1",
            "robot0_WRJ0",
            "robot0_FFJ3",
            "robot0_FFJ2",
            "robot0_FFJ1",
            "robot0_MFJ3",
            "robot0_MFJ2",
            "robot0_MFJ1",
            "robot0_RFJ3",
            "robot0_RFJ2",
            "robot0_RFJ1",
            "robot0_LFJ4",
            "robot0_LFJ3",
            "robot0_LFJ2",
            "robot0_LFJ1",
            "robot0_THJ4",
            "robot0_THJ3",
            "robot0_THJ2",
            "robot0_THJ1",
            "robot0_THJ0",
        ),
        curl_joint_names=(
            "robot0_FFJ3",
            "robot0_FFJ2",
            "robot0_FFJ1",
            "robot0_MFJ3",
            "robot0_MFJ2",
            "robot0_MFJ1",
            "robot0_RFJ3",
            "robot0_RFJ2",
            "robot0_RFJ1",
            "robot0_LFJ3",
            "robot0_LFJ2",
            "robot0_LFJ1",
            "robot0_THJ3",
            "robot0_THJ2",
            "robot0_THJ1",
            "robot0_THJ0",
        ),
        fingertip_frames=(
            "robot0_ffdistal",
            "robot0_mfdistal",
            "robot0_rfdistal",
            "robot0_lfdistal",
            "robot0_thdistal",
        ),
    ),
    success=SuccessCriteria(
        min_height_above_grasp_center_m=0.015,
        max_object_speed_mps=0.15,
        min_contact_sites=3,
        hold_duration_s=0.75,
        max_grasp_center_distance_m=0.10,
    ),
    curriculum=(
        "fixed_hand_pose",
        "sphere_jitter",
        "joint_noise",
        "mass_friction_randomization",
    ),
)
