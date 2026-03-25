from __future__ import annotations

import time

import hydra
from omegaconf import DictConfig, OmegaConf

from isaac_ws.runtime import (
    app_launcher_args,
    close_simulation_app,
    ensure_rsl_rl,
    make_env_and_agent_cfg,
    print_plan_summary,
)
from isaac_ws.task_registry import register_local_tasks


def _extract_obs(reset_output):
    if isinstance(reset_output, tuple):
        return reset_output[0]
    return reset_output


def _build_smoke_actions(
    step: int,
    num_envs: int,
    action_dim: int,
    device,
    mode: str,
    amplitude: float,
):
    import torch

    if mode == "zero":
        return torch.zeros((num_envs, action_dim), device=device)

    env_ids = torch.arange(num_envs, device=device, dtype=torch.float32).unsqueeze(-1)
    joint_ids = torch.arange(action_dim, device=device, dtype=torch.float32).unsqueeze(0)

    if mode == "random":
        phase = 0.37 * float(step) + 0.13 * env_ids + 0.07 * joint_ids
        return amplitude * torch.sign(torch.sin(phase))

    phase = 0.10 * float(step) + 0.23 * env_ids + 0.11 * joint_ids
    return amplitude * torch.sin(phase)


@hydra.main(version_base=None, config_path="../../configs", config_name="smoke")
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
        from isaaclab.envs import DirectMARLEnv, multi_agent_to_single_agent

        env_cfg, _ = make_env_and_agent_cfg(cfg, app_launcher)
        env = gym.make(str(cfg.task.isaaclab_task_id), cfg=env_cfg)
        if isinstance(env.unwrapped, DirectMARLEnv):
            env = multi_agent_to_single_agent(env)

        reset_output = env.reset()
        _extract_obs(reset_output)

        action_dim = int(cfg.action.arm.dof) + int(cfg.action.hand.dof)
        step_dt = float(env.unwrapped.step_dt)
        device = env.unwrapped.device
        num_envs = int(env.unwrapped.num_envs)
        max_steps = int(cfg.run.max_steps)
        real_time = bool(cfg.run.real_time)
        action_mode = str(cfg.smoke.action_mode)
        action_amplitude = float(cfg.smoke.action_amplitude)
        print_every = max(1, int(cfg.smoke.print_every))

        print(f"smoke_task_id: {cfg.task.isaaclab_task_id}")
        print(f"smoke_num_envs: {num_envs}")
        print(f"smoke_action_dim: {action_dim}")
        print(f"smoke_action_mode: {action_mode}")
        print(f"smoke_action_amplitude: {action_amplitude}")
        print(f"smoke_max_steps: {max_steps}")
        print("[INFO] Smoke run started.")

        step = 0
        while simulation_app.is_running():
            start_time = time.time()
            actions = _build_smoke_actions(
                step=step,
                num_envs=num_envs,
                action_dim=action_dim,
                device=device,
                mode=action_mode,
                amplitude=action_amplitude,
            )
            step_output = env.step(actions)
            if len(step_output) == 5:
                _, rewards, terminated, truncated, _ = step_output
                done_count = int(torch.count_nonzero(terminated | truncated).item())
            else:
                _, rewards, dones, _ = step_output
                done_count = int(torch.count_nonzero(dones).item())

            step += 1
            if step % print_every == 0:
                mean_reward = float(torch.mean(rewards).item())
                print(f"smoke_step={step} mean_reward={mean_reward:.4f} done_envs={done_count}")

            if max_steps > 0 and step >= max_steps:
                break

            sleep_time = step_dt - (time.time() - start_time)
            if real_time and sleep_time > 0:
                time.sleep(sleep_time)

        env.close()
    finally:
        close_simulation_app(cfg, simulation_app)


if __name__ == "__main__":
    main()
