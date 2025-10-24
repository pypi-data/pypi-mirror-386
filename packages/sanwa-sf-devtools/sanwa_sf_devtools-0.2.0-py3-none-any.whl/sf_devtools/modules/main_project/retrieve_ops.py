from __future__ import annotations

import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from ...core.common import Logger, config, logger, sf_cli


class RetrieveOps:
    """本番orgからメタデータを取得し、指定ディレクトリに展開する。"""

    def __init__(self) -> None:
        self.project_root = config.project_root

    def retrieve_and_expand(
        self,
        *,
        manifest_file: Path,
        target_org: str,
        target_dir: Path,
    ) -> Path:
        """sf project retrieve start を実行し、展開先へ同期する。

        unpackaged/unpackaged の二重構造にも対応。
        既存の target_dir 内容は削除してから配置。
        """
        if not manifest_file.is_file():
            raise FileNotFoundError(f"manifest が見つかりません: {manifest_file}")

        # 一時ディレクトリ
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = self.project_root / f"temp_retrieve_{ts}"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        Logger.step("Salesforce からメタデータを取得")
        result = sf_cli.run_command(
            [
                "sf",
                "project",
                "retrieve",
                "start",
                "--manifest",
                str(manifest_file),
                "--target-org",
                target_org,
                "--target-metadata-dir",
                str(temp_dir),
                "--unzip",
            ],
            capture_output=True,
            check=True,
        )
        if result.returncode != 0:
            raise RuntimeError("メタデータの取得に失敗しました")

        # unpackaged/unpackaged 構造検知
        source = None
        if (temp_dir / "unpackaged" / "unpackaged").is_dir():
            source = temp_dir / "unpackaged" / "unpackaged"
        elif (temp_dir / "unpackaged").is_dir():
            source = temp_dir / "unpackaged"
        else:
            # 期待外構造
            logger.error("期待しないディレクトリ構造です。")
            raise RuntimeError("retrieve 結果が unpackaged 配下に見つかりません")

        # 既存 target_dir のクリーン
        target_dir.mkdir(parents=True, exist_ok=True)
        for child in target_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink(missing_ok=True)  # type: ignore

        Logger.step(f"{source} から {target_dir} へ同期")
        # rsync があれば高速に、無ければ shutil.copytree で代替
        try:
            subprocess.run(
                [
                    "rsync",
                    "-av",
                    "--delete",
                    f"{source}/",
                    f"{target_dir}/",
                ],
                check=True,
            )
        except Exception:
            # フォールバック
            for item in source.iterdir():
                dest = target_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)

        # 後片付け
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass

        logger.success("メタデータの取得と展開が完了しました。")
        return target_dir
