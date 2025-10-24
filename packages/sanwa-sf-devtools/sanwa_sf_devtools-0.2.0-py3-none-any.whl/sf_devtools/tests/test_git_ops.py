from pathlib import Path
from typing import Sequence

import pytest

from sf_devtools.modules.main_project.git_ops import GitOps


class _DummyResult:
    def __init__(self, returncode: int = 0, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout


def _fake_repo(tmp: Path) -> None:
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp, check=True)
    # CI環境ではユーザー情報が未設定だとコミットできないため、テスト用の名前とメールを設定する
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp, check=True
    )
    (tmp / "README.md").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp, check=True)


def test_create_feature_branch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_repo(tmp_path)
    go = GitOps(repo_root=tmp_path)

    # Simulate clean working tree and accept push=false
    def fake_run(
        args: Sequence[str],
        capture_output: bool = False,
        text: bool = True,
        check: bool = True,
        cwd: str | Path | None = None,
    ) -> _DummyResult:
        # emulate commands
        if args[:2] == ["git", "diff-index"]:
            return _DummyResult(0)
        if args[:2] == ["git", "show-ref"]:
            return _DummyResult(1)  # not exists
        if args[:2] == ["git", "checkout"]:
            return _DummyResult(0)
        if args[:2] == ["git", "push"]:
            return _DummyResult(0)
        return _DummyResult(0)

    import sf_devtools.modules.main_project.git_ops as mod

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    # UI inputs
    from sf_devtools.core.common import ui

    def fake_input(prompt: str, default: object = None) -> str:
        return "dev" if "サンドボックス" in prompt else "feature"

    monkeypatch.setattr(ui, "get_user_input", fake_input)
    monkeypatch.setattr(ui, "confirm", lambda msg, default=False: False)

    assert go.create_feature_branch() is True


def test_manual_tag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_repo(tmp_path)
    go = GitOps(repo_root=tmp_path)

    def fake_run(
        args: Sequence[str],
        capture_output: bool = False,
        text: bool = True,
        check: bool = True,
        cwd: str | Path | None = None,
    ) -> _DummyResult:
        return _DummyResult(0)

    import sf_devtools.modules.main_project.git_ops as mod

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    from sf_devtools.core.common import ui

    monkeypatch.setattr(ui, "get_user_input", lambda prompt, default=None: "tag-1")
    monkeypatch.setattr(ui, "confirm", lambda msg, default=True: False)

    assert go.create_manual_tag() is True
