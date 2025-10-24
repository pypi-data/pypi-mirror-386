from __future__ import annotations

from pathlib import Path
from typing import Optional

from ...core.common import Logger, config, logger, sf_cli, ui


class ManifestOps:
    """Sanwa Main 向けのマニフェスト操作"""

    def __init__(self) -> None:
        # 利用する CLI は共通インスタンスを使用
        self.project_root = config.project_root
        self.manifest_dir = self.project_root / "manifest"

    def generate_manifest(
        self,
        *,
        from_org: str,
        name: str = "prod-full.xml",
        output_dir: Optional[Path] = None,
        confirm_overwrite: bool = True,
    ) -> Path:
        """sf project generate manifest を実行して manifest を生成する。

        Args:
            from_org: 取得元 org の alias または username
            name: 出力ファイル名（prod-full.xml 既定）
            output_dir: 出力ディレクトリ（既定: <root>/manifest）
            confirm_overwrite: 既存ファイルがある場合の確認を行うか

        Returns:
            生成された manifest のパス
        """
        out_dir = output_dir or self.manifest_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / name

        if target.exists() and confirm_overwrite:
            if not ui.confirm(
                f"既存の {target.name} を上書きしますか？", default=False
            ):
                logger.warn("マニフェスト生成をキャンセルしました。")
                return target

        Logger.step("マニフェスト生成を実行")
        spinner_label = f"Generating manifest for {from_org}"
        # JSON出力は使わず、処理の成否のみチェックするため共通の sf_cli を使う
        result = sf_cli.run_command(
            [
                "sf",
                "project",
                "generate",
                "manifest",
                "--from-org",
                from_org,
                "--output-dir",
                str(out_dir),
                "--name",
                name,
            ],
            capture_output=True,
            check=True,
            status_message=spinner_label,
            stream_output=False,
        )
        if result.stdout:
            for line in result.stdout.strip().splitlines():
                if line.strip():
                    logger.info(line)
        if result.returncode != 0:
            raise RuntimeError("manifest の生成に失敗しました")

        logger.success(f"マニフェストを生成しました: {target}")
        return target
