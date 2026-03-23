from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hydra.core.hydra_config import HydraConfig
from omegaconf import DictConfig, OmegaConf

from isaac_ws.experiment_meta import (
    build_config_fingerprint,
    build_experiment_id,
    build_selection,
    get_seed,
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def hydra_output_dir() -> Path:
    return Path(HydraConfig.get().runtime.output_dir)


def to_plain_object(cfg: DictConfig) -> dict[str, Any]:
    plain = OmegaConf.to_container(cfg, resolve=True)
    if not isinstance(plain, dict):
        raise TypeError("Expected a dictionary-like configuration after composition.")
    return plain


def build_override_summary(cfg: DictConfig) -> list[str]:
    selection = build_selection(cfg)
    return [f"{key}={value}" for key, value in selection.items()]


def build_inside_container_command(cfg: DictConfig) -> list[str]:
    overrides = build_override_summary(cfg)
    command = [
        str(cfg.run.container_python),
        "-m",
        str(cfg.run.python_entrypoint),
        *overrides,
    ]
    return command


def build_execution_plan(cfg: DictConfig) -> dict[str, Any]:
    overrides = build_override_summary(cfg)
    actor = str(cfg.run.actor)
    script_name = f"run_{actor}.sh"
    experiment_id = build_experiment_id(cfg)
    config_fingerprint = build_config_fingerprint(cfg)

    return {
        "actor": actor,
        "experiment_id": experiment_id,
        "config_fingerprint": config_fingerprint,
        "selection": {
            "task": cfg.task.name,
            "env": cfg.env.name,
            "robot": cfg.robot.name,
            "experiment": cfg.experiment.name,
            "algo": cfg.algo.name,
        },
        "runtime": {
            "headless": bool(cfg.runtime.headless),
            "device": str(cfg.runtime.device),
            "num_envs": int(cfg.env.num_envs),
            "distributed": bool(cfg.runtime.distributed),
            "num_gpus": int(cfg.runtime.num_gpus),
            "nnodes": int(cfg.runtime.nnodes),
            "node_rank": int(cfg.runtime.node_rank),
            "master_addr": str(cfg.runtime.master_addr),
            "master_port": int(cfg.runtime.master_port),
            "ui_mode": str(cfg.runtime.ui_mode),
        },
        "seed": get_seed(cfg),
        "storage": {
            "output_root": str(cfg.run.output_root),
            "log_root": str(cfg.run.log_root),
            "checkpoint_root": str(cfg.run.checkpoint_root),
        },
        "hydra_overrides": overrides,
        "suggested_host_command": " ".join(
            [f"./scripts/{script_name}", *overrides]
        ),
        "suggested_inside_container_command": " ".join(build_inside_container_command(cfg)),
        "resolved_config": to_plain_object(cfg),
    }


def write_plan_artifact(cfg: DictConfig) -> Path:
    output_dir = hydra_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = output_dir / f"{cfg.run.actor}_plan.json"
    artifact_path.write_text(
        json.dumps(build_execution_plan(cfg), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return artifact_path
