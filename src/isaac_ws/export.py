from __future__ import annotations

from pathlib import Path

import hydra
from hydra.core.hydra_config import HydraConfig
from omegaconf import DictConfig, OmegaConf

from isaac_ws.runtime import (
    app_launcher_args,
    ensure_rsl_rl,
    make_env_and_agent_cfg,
    print_plan_summary,
    resolve_checkpoint_path,
)
from isaac_ws.task_registry import register_local_tasks


@hydra.main(version_base=None, config_path="../../configs", config_name="export")
def main(cfg: DictConfig) -> None:
    ensure_rsl_rl(cfg)
    print(OmegaConf.to_yaml(cfg, resolve=True))
    print_plan_summary(cfg)

    from isaaclab.app import AppLauncher

    app_launcher = AppLauncher(app_launcher_args(cfg))
    simulation_app = app_launcher.app

    try:
        register_local_tasks(required=True)

        import gymnasium as gym
        from rsl_rl.runners import OnPolicyRunner

        from isaaclab.envs import DirectMARLEnv, multi_agent_to_single_agent

        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper, export_policy_as_jit, export_policy_as_onnx

        env_cfg, agent_cfg = make_env_and_agent_cfg(cfg, app_launcher)
        env_cfg.scene.num_envs = 1
        checkpoint_path = resolve_checkpoint_path(cfg)
        env_cfg.log_dir = str(checkpoint_path.parent)

        env = gym.make(str(cfg.task.isaaclab_task_id), cfg=env_cfg, render_mode=None)
        if isinstance(env.unwrapped, DirectMARLEnv):
            env = multi_agent_to_single_agent(env)

        env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
        runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
        runner.load(str(checkpoint_path))

        try:
            policy_nn = runner.alg.policy
        except AttributeError:
            policy_nn = runner.alg.actor_critic

        if hasattr(policy_nn, "actor_obs_normalizer"):
            normalizer = policy_nn.actor_obs_normalizer
        elif hasattr(policy_nn, "student_obs_normalizer"):
            normalizer = policy_nn.student_obs_normalizer
        else:
            normalizer = None

        export_dir = Path(str(cfg.run.export_dir))
        if not export_dir.is_absolute():
            export_dir = Path(HydraConfig.get().runtime.output_dir) / export_dir
        export_dir.mkdir(parents=True, exist_ok=True)

        export_policy_as_jit(policy_nn, normalizer=normalizer, path=str(export_dir), filename="policy.pt")
        export_policy_as_onnx(policy_nn, normalizer=normalizer, path=str(export_dir), filename="policy.onnx")

        print(f"checkpoint_path: {checkpoint_path}")
        print(f"export_dir: {export_dir}")
        env.close()
    finally:
        simulation_app.close()


if __name__ == "__main__":
    main()
