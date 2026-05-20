from __future__ import annotations

from pathlib import Path


def ensure_child_path(parent: Path, child: Path) -> Path:
    resolved_parent = parent.resolve()
    resolved_child = child.resolve()
    if resolved_child != resolved_parent and resolved_parent not in resolved_child.parents:
        raise ValueError(f"Path {resolved_child} is not inside {resolved_parent}")
    return resolved_child
