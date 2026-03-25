from __future__ import annotations

import gymnasium as gym

from . import agents


gym.register(
    id="Isaac-Grasp-Sphere-Franka-Shadow-Direct-v0",
    entry_point=f"{__name__}.env:FrankaShadowHandGraspEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.env_cfg:FrankaShadowHandGraspEnvCfg",
        "rl_games_cfg_entry_point": f"{agents.__name__}:rl_games_ppo_cfg.yaml",
        "rsl_rl_cfg_entry_point": f"{agents.__name__}.rsl_rl_ppo_cfg:FrankaShadowHandGraspPPORunnerCfg",
    },
)

__all__ = ["agents"]
