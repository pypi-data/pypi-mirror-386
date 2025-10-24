from pathlib import Path
from typing import Any, Dict, List, Type

import pytest


class DummyCompleted:
    def __init__(self, returncode: int = 0, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = ""


@pytest.fixture()
def tmp_project_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Provide an isolated project root and patch config.project_root"""
    from sf_devtools.core.common import config

    # minimal project files
    (tmp_path / "sfdx-project.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(config, "project_root", tmp_path, raising=False)
    return tmp_path


@pytest.fixture()
def mock_sf_run(
    monkeypatch: pytest.MonkeyPatch,
) -> List[Dict[str, Any]]:
    """common.sf_cli.run_command を成功扱いに差し替え、呼び出しを記録します。"""
    calls: List[Dict[str, Any]] = []

    def _runner(
        args: List[str],
        capture_output: bool = True,
        check: bool = True,
        cwd: Path | None = None,
        stream_output: Any = None,
        status_message: str | None = None,
    ) -> DummyCompleted:
        calls.append(
            {
                "args": args,
                "cwd": cwd,
                "status_message": status_message,
                "stream_output": stream_output,
            }
        )
        return DummyCompleted(
            returncode=0, stdout='{"status":0,"result":{"success":true}}'
        )

    from sf_devtools.core.common import sf_cli

    monkeypatch.setattr(sf_cli, "run_command", _runner, raising=False)
    return calls


@pytest.fixture()
def fixed_datetime(monkeypatch: pytest.MonkeyPatch) -> Type[Any]:
    """Monkeypatch datetime.now().strftime to return a fixed timestamp."""

    class _Fixed:
        @classmethod
        def now(cls) -> "_Fixed":
            return cls()

        def strftime(self, fmt: str) -> str:
            return "20250101_000000"

    import sf_devtools.modules.main_project.retrieve_ops as retrieve_ops

    monkeypatch.setattr(retrieve_ops, "datetime", _Fixed, raising=False)
    return _Fixed
