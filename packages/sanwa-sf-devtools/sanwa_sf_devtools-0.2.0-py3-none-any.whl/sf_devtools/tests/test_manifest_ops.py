from pathlib import Path
from typing import Any

from sf_devtools.modules.main_project.manifest_ops import ManifestOps


def test_generate_manifest_invokes_sf(
    tmp_project_root: Path,
    mock_sf_run: list[dict[str, Any]],
) -> None:
    mo = ManifestOps()
    # auto confirm overwrite by skipping prompt via confirm_overwrite=False
    out = mo.generate_manifest(
        from_org="prod", name="prod-full.xml", confirm_overwrite=False
    )
    assert out.name == "prod-full.xml"
    # first call should be sf project generate manifest
    assert mock_sf_run
    args = mock_sf_run[-1]["args"]
    assert args[:4] == ["sf", "project", "generate", "manifest"]
    assert mock_sf_run[-1]["status_message"] == "Generating manifest for prod"
    assert mock_sf_run[-1]["stream_output"] is False
