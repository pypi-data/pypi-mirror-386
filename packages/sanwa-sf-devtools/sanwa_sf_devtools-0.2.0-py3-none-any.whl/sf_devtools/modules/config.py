"""
設定・環境確認（ConfigManager）

config.toml 実装に基づく環境チェックや設定ファイル操作、
Salesforce CLI の認証状態や Org リストの確認などを提供します。
"""

import shutil

from rich.console import Console
from rich.table import Table

from ..core.common import config, logger, sf_cli, ui

console = Console()


class ConfigManager:
    """設定・環境確認メニューの実装。"""

    def show_menu(self) -> None:
        """設定・環境確認メニューを表示。"""
        while True:
            logger.info("設定・環境確認")

            options = [
                "環境チェック",
                "組織一覧表示",
                "戻る",
            ]

            try:
                choice = ui.select_from_menu("操作を選択してください:", options)

                if choice == 0:
                    self._check_environment()
                elif choice == 1:
                    self._list_orgs()
                elif choice == 2:
                    return

                if not ui.confirm("設定・環境確認を続けますか？", default=True):
                    return

            except Exception as e:
                logger.error(f"操作中にエラーが発生しました: {e}")
                if not ui.confirm("設定・環境確認を続けますか？", default=True):
                    return

    # --- Actions ---
    def _check_environment(self) -> None:
        """config.toml と必要コマンド、プロジェクトファイルの存在を確認。"""
        logger.step("環境チェック")

        # 1) config.toml の確認
        cfg_dir = config.project_root / ".sf-devtools"
        cfg_file = cfg_dir / "config.toml"
        cfg_exists = cfg_file.exists()

        # 2) sfdx-project.json
        sfdx = config.project_root / "sfdx-project.json"

        # 3) 必須コマンド
        required_cmds = ["sf", "jq", "rsync"]
        cmd_status = {cmd: (shutil.which(cmd) is not None) for cmd in required_cmds}

        # 出力
        table = Table(title="環境チェック結果")
        table.add_column("項目", style="cyan", no_wrap=True)
        table.add_column("状態/詳細", style="white")
        table.add_row("project_root", str(config.project_root))
        table.add_row("config.toml", str(cfg_file) + (" ✅" if cfg_exists else " ❌"))
        table.add_row(
            "sfdx-project.json", str(sfdx) + (" ✅" if sfdx.exists() else " ❌")
        )
        for cmd, ok in cmd_status.items():
            table.add_row(f"cmd:{cmd}", "OK" if ok else "NOT FOUND")

        console.print(table)

        # config.toml が無ければ初期化を提案
        if not cfg_exists and ui.confirm(
            ".sf-devtools/config.toml を初期化しますか？", default=True
        ):
            try:
                # 非対話で生成（既定値）
                config._ensure_project_config(config.project_root, interactive=False)
            except Exception as e:
                logger.error(f"config.toml 初期化に失敗: {e}")

    def _list_orgs(self) -> None:
        """sf org list の情報をテーブル表示。"""
        logger.step("組織一覧表示")

        try:
            sf = sf_cli  # 共有インスタンス
            orgs = sf.get_all_orgs()
        except Exception as e:
            logger.error(f"組織情報の取得に失敗しました: {e}")
            return

        if not orgs:
            logger.warn("認証済みの組織が見つかりませんでした")
            return

        table = Table(title="認証済み組織一覧")
        table.add_column("#", justify="right")
        table.add_column("ユーザー名")
        table.add_column("エイリアス")
        table.add_column("種類")

        for idx, (username, alias, is_scratch) in enumerate(orgs):
            table.add_row(
                str(idx + 1),
                username or "-",
                alias or "-",
                "scratch" if is_scratch else "normal",
            )

        console.print(table)


# Module instance for convenient access
config_manager = ConfigManager()
