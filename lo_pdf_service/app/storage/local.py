from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from app.core.paths import ensure_child_path


@dataclass(frozen=True)
class Workspace:
    root: Path
    input_dir: Path
    output_dir: Path
    profile_dir: Path


class LocalStorage:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.work_root = base_dir / "work"
        self.result_root = base_dir / "results"
        self.job_root = base_dir / "jobs"

    def create_workspace(self, workspace_id: str) -> Workspace:
        root = ensure_child_path(self.work_root, self.work_root / workspace_id)
        input_dir = root / "input"
        output_dir = root / "output"
        profile_dir = root / "lo-profile"
        input_dir.mkdir(parents=True, exist_ok=False)
        output_dir.mkdir(parents=True, exist_ok=False)
        profile_dir.mkdir(parents=True, exist_ok=False)
        self.result_root.mkdir(parents=True, exist_ok=True)
        self.job_root.mkdir(parents=True, exist_ok=True)
        return Workspace(root=root, input_dir=input_dir, output_dir=output_dir, profile_dir=profile_dir)

    def cleanup_workspace(self, workspace: Workspace) -> None:
        ensure_child_path(self.work_root, workspace.root)
        shutil.rmtree(workspace.root, ignore_errors=True)
