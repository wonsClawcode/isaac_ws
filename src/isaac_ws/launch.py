from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from hydra import compose, initialize_config_dir


ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "configs"
ACTOR_TO_CONFIG = {"train": "train", "eval": "eval", "export": "export", "smoke": "smoke"}
ACTOR_TO_MODULE = {
    "train": "isaac_ws.train",
    "eval": "isaac_ws.eval",
    "export": "isaac_ws.export",
    "smoke": "isaac_ws.smoke",
}
LEGACY_RUN_OVERRIDE_KEYS = {
    "train": {"checkpoint_path", "record_video", "video_length", "video_interval", "max_steps", "real_time"},
    "eval": {"checkpoint_path", "record_video", "video_length", "video_interval", "max_steps", "real_time"},
    "export": {"checkpoint_path", "export_dir"},
    "smoke": {"max_steps", "real_time"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch isaac_ws train/eval/export entrypoints.")
    parser.add_argument("actor", choices=sorted(ACTOR_TO_CONFIG))
    parser.add_argument("overrides", nargs="*")
    return parser.parse_args()


def compose_cfg(config_name: str, overrides: list[str]):
    with initialize_config_dir(version_base=None, config_dir=str(CONFIG_DIR)):
        return compose(config_name=config_name, overrides=overrides)


def normalize_overrides(actor: str, overrides: list[str]) -> list[str]:
    normalized: list[str] = []
    remapped: list[str] = []
    run_keys = LEGACY_RUN_OVERRIDE_KEYS.get(actor, set())

    for override in overrides:
        if "=" not in override:
            normalized.append(override)
            continue

        key, value = override.split("=", 1)
        if key.startswith("run.") or "." in key or key.startswith("+"):
            normalized.append(override)
            continue

        if key in run_keys:
            normalized_key = f"run.{key}"
            normalized.append(f"{normalized_key}={value}")
            remapped.append(f"{key} -> {normalized_key}")
        else:
            normalized.append(override)

    if remapped:
        print(f"[INFO] Remapped legacy overrides for {actor}: {', '.join(remapped)}")
    return normalized


def main() -> None:
    args = parse_args()
    overrides = normalize_overrides(args.actor, list(args.overrides))
    cfg = compose_cfg(ACTOR_TO_CONFIG[args.actor], overrides)

    env = os.environ.copy()
    env.setdefault("ISAAC_WS_RUN_TIMESTAMP", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

    module_name = ACTOR_TO_MODULE[args.actor]
    if args.actor == "train" and bool(cfg.runtime.distributed) and int(cfg.runtime.num_gpus) > 1:
        cmd = [sys.executable, "-m", "torch.distributed.run"]
        if int(cfg.runtime.nnodes) == 1:
            cmd.append("--standalone")
        else:
            cmd.extend(
                [
                    f"--nnodes={int(cfg.runtime.nnodes)}",
                    f"--node_rank={int(cfg.runtime.node_rank)}",
                    f"--master_addr={str(cfg.runtime.master_addr)}",
                    f"--master_port={int(cfg.runtime.master_port)}",
                ]
            )
        cmd.extend(
            [
                f"--nproc_per_node={int(cfg.runtime.num_gpus)}",
                "-m",
                module_name,
                *overrides,
            ]
        )
    else:
        cmd = [sys.executable, "-m", module_name, *overrides]

    os.execvpe(cmd[0], cmd, env)


if __name__ == "__main__":
    main()
