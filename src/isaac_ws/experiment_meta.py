from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Optional

from omegaconf import DictConfig, OmegaConf

CONFIG_GROUP_KEYS: tuple[str, ...] = (
    "task",
    "env",
    "robot",
    "obs",
    "action",
    "reward",
    "algo",
    "experiment",
    "runtime",
    "deploy",
)

CORE_ID_KEYS: tuple[str, ...] = ("task", "env", "robot", "algo", "experiment")
ASSET_SUFFIXES: tuple[str, ...] = (".usd", ".urdf", ".mjcf")
SAFE_NAME_PATTERN = re.compile(r"^[a-z0-9_]+$")


def node_to_plain(node: Any) -> Any:
    if isinstance(node, DictConfig):
        return OmegaConf.to_container(node, resolve=True)
    return node


def build_selection(cfg: DictConfig) -> dict[str, str]:
    selection: dict[str, str] = {}
    for key in CONFIG_GROUP_KEYS:
        node = getattr(cfg, key, None)
        if node is not None and "name" in node:
            selection[key] = str(node.name)
    return selection


def build_signature(cfg: DictConfig) -> dict[str, Any]:
    return {key: node_to_plain(getattr(cfg, key)) for key in CONFIG_GROUP_KEYS}


def get_seed(cfg: DictConfig) -> int:
    if hasattr(cfg, "experiment") and "seed" in cfg.experiment:
        return int(cfg.experiment.seed)
    if hasattr(cfg, "algo") and "seed" in cfg.algo:
        return int(cfg.algo.seed)
    return 0


def build_config_fingerprint(cfg: DictConfig, length: int = 8) -> str:
    signature_json = json.dumps(build_signature(cfg), sort_keys=True, ensure_ascii=True)
    return hashlib.sha1(signature_json.encode("utf-8")).hexdigest()[:length]


def build_experiment_id(cfg: DictConfig) -> str:
    selection = build_selection(cfg)
    parts = [selection[key] for key in CORE_ID_KEYS if key in selection]
    parts.append(f"s{get_seed(cfg)}")
    parts.append(f"cfg{build_config_fingerprint(cfg)}")
    return "__".join(parts)


def iter_asset_references(data: Any, prefix: str = "") -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            refs.extend(iter_asset_references(value, next_prefix))
        return refs
    if isinstance(data, list):
        for index, value in enumerate(data):
            refs.extend(iter_asset_references(value, f"{prefix}[{index}]"))
        return refs
    if isinstance(data, str) and data.endswith(ASSET_SUFFIXES):
        refs.append((prefix, data))
    return refs


def resolve_module_path(module_name: str, project_root: Path) -> Optional[Path]:
    src_root = project_root / "src"
    module_parts = module_name.split(".")
    package_init = src_root.joinpath(*module_parts, "__init__.py")
    if package_init.exists():
        return package_init
    module_file = src_root.joinpath(*module_parts).with_suffix(".py")
    if module_file.exists():
        return module_file
    return None


def module_declares_symbol(module_path: Path, symbol_name: str) -> bool:
    tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol_name:
            return True
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == symbol_name:
                    return True
    return False


def validate_python_entry_point(entry_point: str, project_root: Path) -> list[str]:
    errors: list[str] = []
    module_name, _, symbol_name = entry_point.partition(":")
    if not module_name or not symbol_name:
        return [f"invalid python entry point: {entry_point}"]

    module_path = resolve_module_path(module_name, project_root)
    if module_path is None:
        return [f"missing module for entry point: {entry_point}"]
    if not module_declares_symbol(module_path, symbol_name):
        return [f"missing symbol '{symbol_name}' in entry point module: {entry_point}"]
    return errors


def validate_resource_entry_point(entry_point: str, project_root: Path) -> list[str]:
    module_name, _, resource_name = entry_point.partition(":")
    if not module_name or not resource_name:
        return [f"invalid resource entry point: {entry_point}"]

    module_path = resolve_module_path(module_name, project_root)
    if module_path is None:
        return [f"missing module for resource entry point: {entry_point}"]

    resource_path = module_path.parent / resource_name
    if not resource_path.exists():
        return [f"missing resource for entry point: {entry_point}"]
    return []


def validate_config(cfg: DictConfig, project_root: Path) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    selection = build_selection(cfg)
    for key in CONFIG_GROUP_KEYS:
        node = getattr(cfg, key, None)
        if node is None:
            errors.append(f"missing config group: {key}")
            continue
        if "name" not in node:
            errors.append(f"missing 'name' in config group: {key}")
            continue
        name = str(node.name)
        if not SAFE_NAME_PATTERN.fullmatch(name):
            warnings.append(f"{key}.name is not slug-safe: {name}")
        if selection.get(key) != name:
            warnings.append(f"{key}.name differs from selected value: {selection.get(key)} != {name}")

    if hasattr(cfg, "experiment") and "seed" not in cfg.experiment:
        errors.append("experiment.seed is required for deterministic experiment IDs")

    if "isaaclab_task_id" not in cfg.task:
        errors.append("task.isaaclab_task_id is required for Isaac Lab registration")

    implementation = getattr(cfg.task, "implementation", None)
    implementation_required = bool(getattr(cfg.task, "implementation_required", False))
    if implementation_required and implementation is None:
        errors.append("task.implementation is required for custom Isaac Lab task packages")
    elif implementation is not None:
        required_keys = (
            "module",
            "entry_point",
            "env_cfg_entry_point",
            "rl_games_cfg_entry_point",
            "rsl_rl_cfg_entry_point",
        )
        for key in required_keys:
            if key not in implementation:
                errors.append(f"task.implementation.{key} is required")

        module_name = str(implementation.get("module", ""))
        if module_name:
            module_path = resolve_module_path(module_name, project_root)
            if module_path is None:
                errors.append(f"missing task implementation module: {module_name}")

        for key in ("entry_point", "env_cfg_entry_point", "rsl_rl_cfg_entry_point"):
            value = str(implementation.get(key, ""))
            if value:
                errors.extend(validate_python_entry_point(value, project_root))

        rl_games_entry_point = str(implementation.get("rl_games_cfg_entry_point", ""))
        if rl_games_entry_point:
            errors.extend(validate_resource_entry_point(rl_games_entry_point, project_root))

    compatibility = getattr(cfg.task, "compatibility", None)
    if compatibility is not None:
        compatibility_checks = (
            ("robots", "robot"),
            ("envs", "env"),
            ("observations", "obs"),
            ("actions", "action"),
            ("rewards", "reward"),
        )
        for compatibility_key, selection_key in compatibility_checks:
            if compatibility_key not in compatibility:
                continue
            allowed_values = [str(item) for item in compatibility[compatibility_key]]
            selected_value = selection.get(selection_key)
            if selected_value is not None and selected_value not in allowed_values:
                errors.append(
                    f"incompatible selection: task '{cfg.task.name}' does not support "
                    f"{selection_key}='{selected_value}'"
                )

    for ref_key, ref_value in iter_asset_references(build_signature(cfg)):
        ref_path = project_root / ref_value
        if not ref_path.exists():
            warnings.append(f"missing asset reference: {ref_key} -> {ref_value}")

    return {"errors": errors, "warnings": warnings}
