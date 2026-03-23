from __future__ import annotations

import time

import hydra
from omegaconf import DictConfig, OmegaConf

from isaac_ws.runtime import (
    app_launcher_args,
    ensure_rsl_rl,
    make_env_and_agent_cfg,
    print_plan_summary,
    resolve_checkpoint_path,
)
from isaac_ws.task_registry import register_local_tasks


@hydra.main(version_base=None, config_path="../../configs", config_name="eval")
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

        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper

        env_cfg, agent_cfg = make_env_and_agent_cfg(cfg, app_launcher)
        checkpoint_path = resolve_checkpoint_path(cfg)
        env_cfg.log_dir = str(checkpoint_path.parent)

        env = gym.make(
            str(cfg.task.isaaclab_task_id),
            cfg=env_cfg,
            render_mode="rgb_array" if bool(cfg.run.record_video) else None,
        )
        if isinstance(env.unwrapped, DirectMARLEnv):
            env = multi_agent_to_single_agent(env)

        if bool(cfg.run.record_video):
            video_kwargs = {
                "video_folder": str(checkpoint_path.parent / "videos" / "eval"),
                "step_trigger": lambda step: step == 0,
                "video_length": int(cfg.run.video_length),
                "disable_logger": True,
            }
            print("[INFO] Recording videos during evaluation.")
            print_dict(video_kwargs, nesting=4)
            env = gym.wrappers.RecordVideo(env, **video_kwargs)

        env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
        runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
        runner.load(str(checkpoint_path))

        policy = runner.get_inference_policy(device=env.unwrapped.device)
        try:
            policy_nn = runner.alg.policy
        except AttributeError:
            policy_nn = runner.alg.actor_critic

        dt = env.unwrapped.step_dt
        obs = env.get_observations()
        max_steps = int(cfg.run.max_steps)
        if max_steps <= 0 and bool(cfg.runtime.headless):
            max_steps = 1000

        timestep = 0
        while simulation_app.is_running():
            start_time = time.time()
            with torch.inference_mode():
                actions = policy(obs)
                obs, _, dones, _ = env.step(actions)
                if hasattr(policy_nn, "reset"):
                    policy_nn.reset(dones)

            timestep += 1
            if bool(cfg.run.record_video) and timestep >= int(cfg.run.video_length):
                break
            if max_steps > 0 and timestep >= max_steps:
                break

            sleep_time = dt - (time.time() - start_time)
            if bool(cfg.run.real_time) and sleep_time > 0:
                time.sleep(sleep_time)

        env.close()
    finally:
        simulation_app.close()


if __name__ == "__main__":
    main()
