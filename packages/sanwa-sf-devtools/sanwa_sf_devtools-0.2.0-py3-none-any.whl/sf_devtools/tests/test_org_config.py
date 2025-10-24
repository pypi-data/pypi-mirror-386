from pathlib import Path

import pytest

from sf_devtools.modules.main_project.org_config import (
    LEGACY_JSON_FILE,
    ORG_TOML_FILE,
    OrgConfig,
)


def test_org_config_migration(
    tmp_project_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    legacy = tmp_project_root / LEGACY_JSON_FILE
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy_json = (
        '{"alias":"dev","orgName":"DevOrg","sourceDir":"dev-source",'
        '"createdAt":"2024-01-01T00:00:00Z"}'
    )
    legacy.write_text(legacy_json, encoding="utf-8")

    oc = OrgConfig()
    data = oc.ensure()
    assert data.alias == "dev"
    assert data.sourceDir == "dev-source"

    toml = tmp_project_root / ORG_TOML_FILE
    assert toml.exists()
    assert (tmp_project_root / "scripts" / "org-config.json.bak").exists()

    # reload
    loaded = oc.load()
    assert loaded is not None
    assert loaded.alias == "dev"
