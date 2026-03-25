from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SuccessCriteria:
    min_lift_height_m: float
    hold_duration_s: float
    max_object_speed_mps: float
    min_contact_sites: int


@dataclass(frozen=True)
class RobotSpec:
    arm_dof: int
    hand_dof: int
    palm_frame: str
    fingertip_frames: tuple[str, ...]


@dataclass(frozen=True)
class TaskSpec:
    name: str
    object_radius_m: float
    object_mass_kg: float
    robot: RobotSpec
    success: SuccessCriteria
    curriculum: tuple[str, ...]


FRANKA_SHADOW_HAND_GRASP_SPEC = TaskSpec(
    name="grasp_sphere_shadow_hand",
    object_radius_m=0.035,
    object_mass_kg=0.12,
    robot=RobotSpec(
        arm_dof=7,
        hand_dof=24,
        palm_frame="shadow_palm",
        fingertip_frames=("ffdistal", "mfdistal", "rfdistal", "lfdistal", "thdistal"),
    ),
    success=SuccessCriteria(
        min_lift_height_m=0.04,
        hold_duration_s=0.75,
        max_object_speed_mps=0.12,
        min_contact_sites=3,
    ),
    curriculum=(
        "fixed_pose",
        "sphere_jitter",
        "joint_noise",
        "friction_mass_randomization",
        "vision_enable",
    ),
)
