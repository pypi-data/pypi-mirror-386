from pathlib import Path
from typing import Any

from sf_devtools.modules.main_project.convert_deploy_ops import ConvertDeployOps


def test_convert_source_invokes_sf(
    tmp_project_root: Path, mock_sf_run: list[dict[str, Any]]
) -> None:
    src = tmp_project_root / "dev-source"
    src.mkdir()
    (src / "file.txt").write_text("x", encoding="utf-8")
    out = tmp_project_root / "dev-meta"

    c = ConvertDeployOps()
    c.convert_source(source_dir=src, output_dir=out, package_name="Init_dev")

    args = mock_sf_run[-1]["args"]
    assert args[:4] == ["sf", "project", "convert", "source"]


def test_deploy_invokes_sf(
    tmp_project_root: Path, mock_sf_run: list[dict[str, Any]]
) -> None:
    src = tmp_project_root / "dev-source"
    src.mkdir()
    (src / "file.txt").write_text("x", encoding="utf-8")

    c = ConvertDeployOps()
    c.deploy(source_dir=src, target_org="dev", run_tests="RunLocalTests", dry_run=True)
    args = mock_sf_run[-1]["args"]
    assert args[:3] == ["sf", "project", "deploy"]
    assert "--dry-run" in args
    assert "--json" in args
    assert "--verbose" not in args
    assert mock_sf_run[-1]["status_message"] == "Dry Run: dev"
