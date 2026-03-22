from __future__ import annotations

import hydra
from omegaconf import DictConfig, OmegaConf

from isaac_ws.plan import build_execution_plan, write_plan_artifact
from isaac_ws.task_registry import register_local_tasks


@hydra.main(version_base=None, config_path="../../configs", config_name="train")
def main(cfg: DictConfig) -> None:
    register_local_tasks(required=False)
    artifact_path = write_plan_artifact(cfg)
    plan = build_execution_plan(cfg)
    print(OmegaConf.to_yaml(cfg, resolve=True))
    print(f"plan_artifact: {artifact_path}")
    print(f"suggested_host_command: {plan['suggested_host_command']}")
    print(f"suggested_inside_container_command: {plan['suggested_inside_container_command']}")


if __name__ == "__main__":
    main()
