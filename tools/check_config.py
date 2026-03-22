from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from isaac_ws.experiment_meta import (  # noqa: E402
    CONFIG_GROUP_KEYS,
    build_config_fingerprint,
    build_experiment_id,
    build_selection,
    validate_config,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compose and validate a Hydra experiment config.")
    parser.add_argument("--config-name", default="train")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--list-groups", action="store_true")
    parser.add_argument("--fail-on-warning", action="store_true")
    parser.add_argument("overrides", nargs="*")
    return parser.parse_args()


def list_groups(config_dir: Path) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for key in CONFIG_GROUP_KEYS:
        group_dir = config_dir / key
        if group_dir.is_dir():
            groups[key] = sorted(path.stem for path in group_dir.glob("*.yaml"))
    return groups


def validate_layout(config_dir: Path) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for key in CONFIG_GROUP_KEYS:
        group_dir = config_dir / key
        if not group_dir.is_dir():
            continue
        seen_names: dict[str, Path] = {}
        for path in sorted(group_dir.glob("*.yaml")):
            data = OmegaConf.load(path)
            if "name" not in data:
                errors.append(f"{key}/{path.name}: missing top-level 'name'")
                continue
            declared_name = str(data.name)
            if declared_name != path.stem:
                errors.append(f"{key}/{path.name}: name '{declared_name}' does not match filename '{path.stem}'")
            if declared_name in seen_names:
                errors.append(
                    f"{key}/{path.name}: duplicate name '{declared_name}' also used by '{seen_names[declared_name].name}'"
                )
            else:
                seen_names[declared_name] = path
    return {"errors": errors, "warnings": warnings}


def main() -> None:
    args = parse_args()
    config_dir = ROOT / "configs"

    if args.list_groups:
        payload = list_groups(config_dir)
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            for key, values in payload.items():
                print(f"{key}: {', '.join(values)}")
        return

    with initialize_config_dir(version_base=None, config_dir=str(config_dir)):
        cfg = compose(config_name=args.config_name, overrides=list(args.overrides))

    layout_validation = validate_layout(config_dir)
    validation = validate_config(cfg, ROOT)
    payload = {
        "experiment_id": build_experiment_id(cfg),
        "config_fingerprint": build_config_fingerprint(cfg),
        "selection": build_selection(cfg),
        "errors": [*layout_validation["errors"], *validation["errors"]],
        "warnings": [*layout_validation["warnings"], *validation["warnings"]],
        "resolved_groups": {key: OmegaConf.to_container(getattr(cfg, key), resolve=True) for key in CONFIG_GROUP_KEYS},
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"experiment_id: {payload['experiment_id']}")
        print(f"config_fingerprint: {payload['config_fingerprint']}")
        print(f"selection: {json.dumps(payload['selection'], ensure_ascii=False)}")
        if payload["errors"]:
            print("errors:")
            for item in payload["errors"]:
                print(f"  - {item}")
        if payload["warnings"]:
            print("warnings:")
            for item in payload["warnings"]:
                print(f"  - {item}")
        print("resolved_groups:")
        print(OmegaConf.to_yaml(OmegaConf.create(payload["resolved_groups"]), resolve=True))

    if payload["errors"] or (args.fail_on_warning and payload["warnings"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
