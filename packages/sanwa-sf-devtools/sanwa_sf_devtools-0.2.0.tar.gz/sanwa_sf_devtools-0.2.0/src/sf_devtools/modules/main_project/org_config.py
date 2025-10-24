from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from ...core.common import config, logger, sf_cli, ui

ORG_TOML_FILE = ".sf-devtools/org-config.toml"
LEGACY_JSON_FILE = "scripts/org-config.json"


@dataclass
class OrgConfigData:
    alias: str
    orgName: str
    sourceDir: str
    createdAt: str


class OrgConfig:
    """org-config のTOML設定を管理。なくても運用できるが、あると便利。"""

    def __init__(self) -> None:
        self.project_root = config.project_root
        self.toml_path = self.project_root / ORG_TOML_FILE

    # ---- Public API ----
    def load(self) -> Optional[OrgConfigData]:
        if not self.toml_path.exists():
            return None
        try:
            data = self._parse_toml(self.toml_path.read_text(encoding="utf-8"))
            org = data.get("org", {})
            paths = data.get("paths", {})
            alias = str(org.get("alias", "")).strip()
            org_name = str(org.get("orgName", "")).strip()
            created_at = str(org.get("createdAt", "")).strip()
            source_dir = str(paths.get("sourceDir", f"{alias}-source"))
            return OrgConfigData(
                alias=alias,
                orgName=org_name,
                sourceDir=source_dir,
                createdAt=created_at,
            )
        except Exception as e:
            logger.warn(f"org-config.toml の読み込みに失敗しました: {e}")
            return None

    def ensure(self) -> OrgConfigData:
        data = self.load()
        if data:
            return data

        # 旧JSONがあればマイグレーション
        migrated = self.migrate_from_legacy()
        if migrated:
            return migrated

        # 対話で新規作成
        alias = ui.get_user_input(
            "認証済みSandbox組織のエイリアスを入力してください (例: sbakimoto)",
            default="",
        )
        if not alias:
            # 最低限、aliasは必要
            raise RuntimeError("エイリアスが未入力です")

        # sf org display から orgName を取得してみる
        org_name = alias
        try:
            result = sf_cli.run_command(
                ["sf", "org", "display", "--target-org", alias, "--json"],
                capture_output=True,
                check=False,
            )
            output = result.stdout
            if output:
                # 先頭からJSON抽出
                lines = output.split("\n")
                start = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith("{"):
                        start = i
                        break
                import json as _json

                parsed = _json.loads("\n".join(lines[start:]))
                org_name = (
                    parsed.get("result", {}).get("alias")
                    or parsed.get("result", {}).get("username")
                    or alias
                )
        except Exception:
            pass

        source_dir = f"{alias}-source"
        created_at = datetime.utcnow().isoformat() + "Z"
        data = OrgConfigData(
            alias=alias,
            orgName=org_name,
            sourceDir=source_dir,
            createdAt=created_at,
        )

        source_path = Path(source_dir)
        if not source_path.is_absolute():
            source_path = self.project_root / source_path
        if source_path.exists():
            logger.info(f"source ディレクトリは既に存在します: {source_path}")
        else:
            if ui.confirm(
                f"Convert / Deploy メニューで利用する source ディレクトリを作成しますか？\n"
                f"（不要であれば [いいえ] を選択してください）\n"
                f"作成対象: {source_path}",
                default=False,
            ):
                source_path.mkdir(parents=True, exist_ok=True)
                logger.success(f"source ディレクトリを作成しました: {source_path}")
            else:
                logger.warn(
                    (
                        "source ディレクトリは作成しませんでした。"
                        "Convert / Deploy を利用する場合は後から手動で準備してください。"
                    )
                )

        self.save(data)
        return data

    def save(self, data: OrgConfigData) -> None:
        self.toml_path.parent.mkdir(parents=True, exist_ok=True)
        content = self._to_toml(data)
        self.toml_path.write_text(content, encoding="utf-8")
        logger.success(f"org-config を保存しました: {self.toml_path}")

    def migrate_from_legacy(self) -> Optional[OrgConfigData]:
        legacy = self.project_root / LEGACY_JSON_FILE
        if not legacy.exists():
            return None
        try:
            raw = json.loads(legacy.read_text(encoding="utf-8"))
            alias = raw.get("alias", "")
            org_name = raw.get("orgName", alias)
            source_dir = raw.get("sourceDir", f"{alias}-source")
            created_at = raw.get("createdAt") or datetime.utcnow().isoformat() + "Z"
            data = OrgConfigData(
                alias=alias,
                orgName=org_name,
                sourceDir=source_dir,
                createdAt=created_at,
            )
            # 保存
            self.save(data)
            # 退避
            backup = legacy.with_suffix(".json.bak")
            legacy.rename(backup)
            logger.warn(
                f"旧設定を {backup.name} にバックアップし、org-config.toml に移行しました。"
            )
            return data
        except Exception as e:
            logger.warn(f"旧設定の移行に失敗しました: {e}")
            return None

    # ---- Minimal TOML utilities ----
    def _to_toml(self, data: OrgConfigData) -> str:
        lines = [
            "# org-config for Sanwa Main",
            "[org]",
            f'alias = "{data.alias}"',
            f'orgName = "{data.orgName}"',
            f'createdAt = "{data.createdAt}"',
            "",
            "[paths]",
            f'sourceDir = "{data.sourceDir}"',
            "",
        ]
        return "\n".join(lines)

    def _parse_toml(self, content: str) -> dict:
        result: dict = {}
        section: Optional[str] = None
        for raw in content.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1].strip()
                result.setdefault(section, {})
                continue
            if "=" in line and section:
                k, v = line.split("=", 1)
                key = k.strip()
                val = v.strip().strip('"')
                result[section][key] = val
        return result
