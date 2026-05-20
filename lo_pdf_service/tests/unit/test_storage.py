from __future__ import annotations

from pathlib import Path

from app.storage.local import LocalStorage


def test_create_workspace_makes_isolated_directories(tmp_path: Path) -> None:
    storage = LocalStorage(base_dir=tmp_path)

    workspace = storage.create_workspace("job-1")

    assert workspace.root == tmp_path / "work" / "job-1"
    assert workspace.input_dir.is_dir()
    assert workspace.output_dir.is_dir()
    assert workspace.profile_dir.is_dir()


def test_cleanup_workspace_removes_only_workspace(tmp_path: Path) -> None:
    storage = LocalStorage(base_dir=tmp_path)
    workspace = storage.create_workspace("job-1")
    outside = tmp_path / "outside.txt"
    outside.write_text("keep", encoding="utf-8")

    storage.cleanup_workspace(workspace)

    assert not workspace.root.exists()
    assert outside.read_text(encoding="utf-8") == "keep"
