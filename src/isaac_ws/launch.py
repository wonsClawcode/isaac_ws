from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from hydra import compose, initialize_config_dir


ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "configs"
ACTOR_TO_CONFIG = {"train": "train", "eval": "eval", "export": "export"}
ACTOR_TO_MODULE = {"train": "isaac_ws.train", "eval": "isaac_ws.eval", "export": "isaac_ws.export"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch isaac_ws train/eval/export entrypoints.")
    parser.add_argument("actor", choices=sorted(ACTOR_TO_CONFIG))
    parser.add_argument("overrides", nargs="*")
    return parser.parse_args()


def compose_cfg(config_name: str, overrides: list[str]):
    with initialize_config_dir(version_base=None, config_dir=str(CONFIG_DIR)):
        return compose(config_name=config_name, overrides=overrides)


def main() -> None:
    args = parse_args()
    cfg = compose_cfg(ACTOR_TO_CONFIG[args.actor], list(args.overrides))

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
                *args.overrides,
            ]
        )
    else:
        cmd = [sys.executable, "-m", module_name, *args.overrides]

    os.execvpe(cmd[0], cmd, env)


if __name__ == "__main__":
    main()
