import types
from pathlib import Path
from typing import Any, List, Type

import pytest

from sf_devtools.modules.main_project.retrieve_ops import RetrieveOps


def test_retrieve_and_expand_unpacked(
    tmp_project_root: Path,
    mock_sf_run: list[dict[str, Any]],
    fixed_datetime: Type[Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ro = RetrieveOps()
    manifest = tmp_project_root / "manifest" / "prod-full.xml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("<Package></Package>", encoding="utf-8")

    # Prepare temp retrieve structure (simulate after sf run)
    # We patch subprocess.run (rsync) to raise so that shutil fallback runs
    import sf_devtools.modules.main_project.retrieve_ops as mod

    def fake_run(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("rsync not available")

    patched_subprocess = types.SimpleNamespace(run=fake_run)
    monkeypatch.setattr(mod, "subprocess", patched_subprocess)

    # Also patch to create unpackaged structure after sf_cli.run_command call
    from sf_devtools.core.common import sf_cli

    real_runner = sf_cli.run_command

    def _runner(
        args: List[str],
        capture_output: bool = True,
        check: bool = True,
        cwd: Path | None = None,
        stream_output: Any = None,
    ) -> object:
        real_runner(
            args,
            capture_output=capture_output,
            check=False,
            cwd=cwd,
            stream_output=stream_output,
        )
        # create temp dir structure based on fixed timestamp
        temp = tmp_project_root / "temp_retrieve_20250101_000000" / "unpackaged"
        (temp / "classes").mkdir(parents=True, exist_ok=True)
        (temp / "classes" / "A.cls").write_text("// apex", encoding="utf-8")

        class Dummy:
            returncode: int = 0
            stdout: str = ""

        return Dummy()

    monkeypatch.setattr(sf_cli, "run_command", _runner, raising=False)

    target = tmp_project_root / "prod-full"
    out = ro.retrieve_and_expand(
        manifest_file=manifest, target_org="prod", target_dir=target
    )
    assert out == target
    assert (target / "classes" / "A.cls").exists()
