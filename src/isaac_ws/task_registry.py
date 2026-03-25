from __future__ import annotations


def register_local_tasks(required: bool = False) -> bool:
    try:
        import isaac_ws.lab_tasks  # noqa: F401
    except ModuleNotFoundError as exc:
        if exc.name == "gymnasium":
            if required:
                raise RuntimeError("gymnasium is required to register local Isaac Lab task packages.") from exc
            return False
        raise
    return True
