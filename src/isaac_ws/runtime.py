from __future__ import annotations

import importlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from hydra.core.hydra_config import HydraConfig
from omegaconf import DictConfig

from isaac_ws.experiment_meta import build_experiment_id, get_seed
from isaac_ws.plan import build_execution_plan, write_plan_artifact
from isaac_ws.task_registry import register_local_tasks


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def hydra_output_dir() -> Path:
    return Path(HydraConfig.get().runtime.output_dir)


def write_plan_if_primary(cfg: DictConfig) -> Path | None:
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    if local_rank != 0:
        return None
    return write_plan_artifact(cfg)


def print_plan_summary(cfg: DictConfig) -> None:
    artifact_path = write_plan_if_primary(cfg)
    plan = build_execution_plan(cfg)
    if artifact_path is not None:
        print(f"plan_artifact: {artifact_path}")
    print(f"suggested_host_command: {plan['suggested_host_command']}")
    print(f"suggested_inside_container_command: {plan['suggested_inside_container_command']}")


def load_symbol(entry_point: str) -> Any:
    module_name, _, symbol_name = entry_point.partition(":")
    if not module_name or not symbol_name:
        raise ValueError(f"Invalid entry point: {entry_point}")
    module = importlib.import_module(module_name)
    return getattr(module, symbol_name)


def instantiate_cfg(entry_point: str) -> Any:
    symbol = load_symbol(entry_point)
    return symbol()


def run_stamp() -> str:
    return os.environ.get("ISAAC_WS_RUN_TIMESTAMP", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))


def experiment_root(cfg: DictConfig) -> Path:
    return Path(str(cfg.run.checkpoint_root)) / str(cfg.algo.library) / build_experiment_id(cfg)


def create_log_dir(cfg: DictConfig) -> Path:
    log_dir = experiment_root(cfg) / run_stamp()
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def resolve_checkpoint_path(cfg: DictConfig) -> Path:
    explicit_path = str(getattr(cfg.run, "checkpoint_path", "")).strip()
    if explicit_path:
        path = Path(explicit_path)
        if not path.is_absolute():
            path = project_root() / path
        return path

    candidates = sorted(experiment_root(cfg).rglob("*.pt"), key=lambda path: path.stat().st_mtime)
    if not candidates:
        raise FileNotFoundError(
            f"No checkpoint was found under {experiment_root(cfg)}. "
            "Set run.checkpoint_path to an explicit .pt file if needed."
        )
    return candidates[-1]


def app_launcher_args(cfg: DictConfig) -> dict[str, Any]:
    return {
        "headless": bool(cfg.runtime.headless),
        "enable_cameras": bool(cfg.runtime.enable_cameras or cfg.env.enable_cameras or cfg.run.record_video),
        "hide_ui": bool(cfg.runtime.headless),
        "livestream": 0,
        "device": str(cfg.runtime.device),
        "distributed": bool(cfg.runtime.distributed),
        # Isaac Lab RL uses one process per GPU for scale-out; renderer multi-GPU is unnecessary here
        # and has proven unstable on some container/runtime combinations.
        "multi_gpu": False,
    }


def runtime_device(cfg: DictConfig, app_launcher: Any) -> str:
    if bool(cfg.runtime.distributed):
        return f"cuda:{app_launcher.local_rank}"
    return str(cfg.runtime.device)


def apply_env_overrides(cfg: DictConfig, env_cfg: Any, app_launcher: Any) -> Any:
    env_cfg.decimation = int(cfg.task.control_decimation)
    env_cfg.episode_length_s = float(cfg.task.episode_length_s)
    env_cfg.scene.num_envs = int(cfg.env.num_envs)
    env_cfg.scene.env_spacing = float(cfg.env.env_spacing)
    env_cfg.sim.dt = float(cfg.env.physics.timestep_s)
    env_cfg.sim.render_interval = int(cfg.task.control_decimation)
    env_cfg.sim.device = runtime_device(cfg, app_launcher)

    asset_usd = str(getattr(cfg.robot, "asset_usd", "")).strip()
    if asset_usd and hasattr(env_cfg, "robot_cfg") and hasattr(env_cfg.robot_cfg, "spawn"):
        env_cfg.robot_cfg.spawn.usd_path = asset_usd
    if hasattr(env_cfg, "object_cfg") and hasattr(env_cfg.object_cfg, "spawn"):
        if hasattr(env_cfg.object_cfg.spawn, "radius"):
            env_cfg.object_cfg.spawn.radius = float(cfg.task.object.radius_m)
        if hasattr(env_cfg.object_cfg.spawn, "mass_props") and hasattr(env_cfg.object_cfg.spawn.mass_props, "mass"):
            env_cfg.object_cfg.spawn.mass_props.mass = float(cfg.task.object.mass_kg)
    if hasattr(env_cfg, "arm_dof"):
        env_cfg.arm_dof = int(cfg.robot.arm.dof)
    if hasattr(env_cfg, "hand_dof"):
        env_cfg.hand_dof = int(cfg.robot.hand.dof)
    if hasattr(env_cfg, "palm_body_name"):
        env_cfg.palm_body_name = str(cfg.robot.arm.end_effector_frame)
    if hasattr(env_cfg, "fingertip_body_names"):
        env_cfg.fingertip_body_names = list(cfg.robot.hand.fingertip_frames)

    if hasattr(env_cfg, "arm_action_scale"):
        env_cfg.arm_action_scale = float(cfg.action.arm.scale)
    if hasattr(env_cfg, "hand_action_scale"):
        env_cfg.hand_action_scale = float(cfg.action.hand.scale)
    if hasattr(env_cfg, "freeze_arm_during_bootstrap"):
        env_cfg.freeze_arm_during_bootstrap = bool(cfg.action.arm.freeze_base_arm_by_default)

    if hasattr(env_cfg, "table_height_m"):
        env_cfg.table_height_m = float(cfg.env.table.height_m)
    if hasattr(env_cfg, "hand_root_position") and "hand_root_position_m" in cfg.env.workspace:
        env_cfg.hand_root_position = tuple(float(value) for value in cfg.env.workspace.hand_root_position_m)
    if hasattr(env_cfg, "hand_root_rotation") and "hand_root_rotation_wxyz" in cfg.env.workspace:
        env_cfg.hand_root_rotation = tuple(float(value) for value in cfg.env.workspace.hand_root_rotation_wxyz)
    if hasattr(env_cfg, "grasp_center_position") and "grasp_center_position_m" in cfg.env.workspace:
        env_cfg.grasp_center_position = tuple(float(value) for value in cfg.env.workspace.grasp_center_position_m)
    if hasattr(env_cfg, "object_spawn_center") and "sphere_spawn_center_m" in cfg.env.workspace:
        env_cfg.object_spawn_center = tuple(float(value) for value in cfg.env.workspace.sphere_spawn_center_m)
    if hasattr(env_cfg, "palm_target_position"):
        env_cfg.palm_target_position = tuple(float(value) for value in cfg.env.workspace.palm_target_position_m)
    if hasattr(env_cfg, "object_spawn_offset"):
        env_cfg.object_spawn_offset = tuple(float(value) for value in cfg.task.object.spawn_offset_m)
    if hasattr(env_cfg, "object_spawn_jitter"):
        env_cfg.object_spawn_jitter = tuple(float(value) for value in cfg.env.workspace.sphere_spawn_jitter_m)
    if hasattr(env_cfg, "object_nominal_spawn_height_m"):
        if hasattr(env_cfg, "object_spawn_center"):
            env_cfg.object_nominal_spawn_height_m = float(env_cfg.object_spawn_center[2])
        else:
            env_cfg.object_nominal_spawn_height_m = env_cfg.palm_target_position[2] + env_cfg.object_spawn_offset[2]
    if hasattr(env_cfg, "min_success_lift_height_m"):
        env_cfg.min_success_lift_height_m = float(cfg.task.success.min_lift_height_m)
    if hasattr(env_cfg, "max_success_object_speed_mps"):
        env_cfg.max_success_object_speed_mps = float(cfg.task.success.max_object_speed_mps)
    if hasattr(env_cfg, "min_success_contact_sites"):
        env_cfg.min_success_contact_sites = int(cfg.task.success.min_contact_sites)
    if hasattr(env_cfg, "success_hold_duration_s"):
        env_cfg.success_hold_duration_s = float(cfg.task.success.hold_duration_s)
    if hasattr(env_cfg, "success_palm_up_cosine"):
        env_cfg.success_palm_up_cosine = float(cfg.task.success.require_palm_up_cosine)

    if hasattr(env_cfg, "reward_palm_to_object"):
        env_cfg.reward_palm_to_object = float(cfg.reward.terms.palm_to_object_distance)
    if hasattr(env_cfg, "reward_fingertip_contact"):
        env_cfg.reward_fingertip_contact = float(cfg.reward.terms.fingertip_contact)
    if hasattr(env_cfg, "reward_fingertip_caging"):
        env_cfg.reward_fingertip_caging = float(cfg.reward.terms.fingertip_caging)
    if hasattr(env_cfg, "reward_object_lift"):
        env_cfg.reward_object_lift = float(cfg.reward.terms.object_lift)
    if hasattr(env_cfg, "reward_stable_hold"):
        env_cfg.reward_stable_hold = float(cfg.reward.terms.stable_hold)
    if hasattr(env_cfg, "reward_palm_up_alignment"):
        env_cfg.reward_palm_up_alignment = float(cfg.reward.terms.palm_up_alignment)
    if hasattr(env_cfg, "penalty_action_rate"):
        env_cfg.penalty_action_rate = float(cfg.reward.penalties.action_rate)
    if hasattr(env_cfg, "penalty_joint_velocity"):
        env_cfg.penalty_joint_velocity = float(cfg.reward.penalties.joint_velocity)
    if hasattr(env_cfg, "penalty_object_drop"):
        env_cfg.penalty_object_drop = float(cfg.reward.penalties.object_drop)
    if hasattr(env_cfg, "penalty_self_collision"):
        env_cfg.penalty_self_collision = float(cfg.reward.penalties.self_collision)

    return env_cfg


def apply_agent_overrides(cfg: DictConfig, agent_cfg: Any, app_launcher: Any) -> Any:
    agent_cfg.seed = get_seed(cfg)
    agent_cfg.device = runtime_device(cfg, app_launcher)
    agent_cfg.num_steps_per_env = int(cfg.algo.steps_per_env)
    agent_cfg.max_iterations = int(cfg.algo.max_iterations)
    agent_cfg.save_interval = int(cfg.experiment.checkpoint_interval)
    agent_cfg.experiment_name = build_experiment_id(cfg)
    agent_cfg.run_name = str(cfg.experiment.name)
    arm_clip = float(getattr(cfg.action.arm, "clip", 0.0))
    hand_clip = float(getattr(cfg.action.hand, "clip", 0.0))
    agent_cfg.clip_actions = max(arm_clip, hand_clip, 1.0)

    if bool(cfg.runtime.distributed):
        seed = agent_cfg.seed + int(app_launcher.local_rank)
        agent_cfg.seed = seed

    if hasattr(agent_cfg, "algorithm"):
        agent_cfg.algorithm.learning_rate = float(cfg.algo.learning_rate)
        agent_cfg.algorithm.gamma = float(cfg.algo.gamma)
        agent_cfg.algorithm.lam = float(cfg.algo.lam)
        agent_cfg.algorithm.clip_param = float(cfg.algo.clip_range)
        agent_cfg.algorithm.entropy_coef = float(cfg.algo.entropy_coef)

    return agent_cfg


def make_env_and_agent_cfg(cfg: DictConfig, app_launcher: Any) -> tuple[Any, Any]:
    task_impl = cfg.task.implementation
    env_cfg = instantiate_cfg(str(task_impl.env_cfg_entry_point))
    agent_cfg = instantiate_cfg(str(task_impl.rsl_rl_cfg_entry_point))
    env_cfg = apply_env_overrides(cfg, env_cfg, app_launcher)
    agent_cfg = apply_agent_overrides(cfg, agent_cfg, app_launcher)
    env_cfg.seed = agent_cfg.seed
    return env_cfg, agent_cfg


def ensure_rsl_rl(cfg: DictConfig) -> None:
    if str(cfg.algo.library) != "rsl_rl":
        raise NotImplementedError(
            f"Only algo.library='rsl_rl' is supported right now. Received: {cfg.algo.library}"
        )
