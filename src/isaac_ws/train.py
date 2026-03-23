from __future__ import annotations

import os

import hydra
from omegaconf import DictConfig, OmegaConf

from isaac_ws.runtime import (
    app_launcher_args,
    create_log_dir,
    ensure_rsl_rl,
    make_env_and_agent_cfg,
    print_plan_summary,
)
from isaac_ws.task_registry import register_local_tasks


@hydra.main(version_base=None, config_path="../../configs", config_name="train")
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
        import torch
        from rsl_rl.runners import OnPolicyRunner

        from isaaclab.envs import DirectMARLEnv, multi_agent_to_single_agent
        from isaaclab.utils.dict import print_dict
        from isaaclab.utils.io import dump_yaml

        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper

        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        torch.backends.cudnn.deterministic = False
        torch.backends.cudnn.benchmark = False

        env_cfg, agent_cfg = make_env_and_agent_cfg(cfg, app_launcher)
        log_dir = create_log_dir(cfg)
        env_cfg.log_dir = str(log_dir)

        env = gym.make(
            str(cfg.task.isaaclab_task_id),
            cfg=env_cfg,
            render_mode="rgb_array" if bool(cfg.run.record_video) else None,
        )
        if isinstance(env.unwrapped, DirectMARLEnv):
            env = multi_agent_to_single_agent(env)

        if bool(cfg.run.record_video):
            video_kwargs = {
                "video_folder": str(log_dir / "videos" / "train"),
                "step_trigger": lambda step: step % int(cfg.run.video_interval) == 0,
                "video_length": int(cfg.run.video_length),
                "disable_logger": True,
            }
            print("[INFO] Recording videos during training.")
            print_dict(video_kwargs, nesting=4)
            env = gym.wrappers.RecordVideo(env, **video_kwargs)

        env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
        runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=str(log_dir), device=agent_cfg.device)

        if int(os.environ.get("LOCAL_RANK", "0")) == 0:
            runner.add_git_repo_to_log(__file__)
            dump_yaml(str(log_dir / "params" / "env.yaml"), env_cfg)
            dump_yaml(str(log_dir / "params" / "agent.yaml"), agent_cfg)

        runner.learn(num_learning_iterations=agent_cfg.max_iterations, init_at_random_ep_len=True)
        env.close()
    finally:
        simulation_app.close()


if __name__ == "__main__":
    main()
