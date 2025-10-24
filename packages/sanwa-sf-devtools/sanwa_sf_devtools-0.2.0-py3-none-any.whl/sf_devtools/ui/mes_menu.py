from __future__ import annotations

from ..core.common import logger, ui
from ..modules.core_package import CorePackageManager
from ..modules.manifest_manager import ManifestManager
from ..modules.mes_package import MesPackageManager
from ..modules.package_deploy import PackageDeployManager
from ..modules.sfdmu_sync import SfdmuSyncManager


class MesMenuUI:
    """MES向け機能をネストメニューとして提供"""

    def show_menu(self) -> None:
        while True:
            logger.info("MES メニュー")
            options = [
                "1) Manifest(Package.xml)管理",
                "2) Core パッケージ管理",
                "3) MES パッケージ管理",
                "4) パッケージテスト・デプロイ",
                "5) SFDMU データ同期",
                "戻る",
            ]

            try:
                choice = ui.select_from_menu("実行する操作を選択してください:", options)
            except Exception:
                return

            if choice == 0:
                ManifestManager().show_menu()
            elif choice == 1:
                CorePackageManager().show_menu()
            elif choice == 2:
                MesPackageManager().show_menu()
            elif choice == 3:
                PackageDeployManager().show_menu()
            elif choice == 4:
                SfdmuSyncManager().show_menu()
            else:
                return

            # 余計な確認は行わず、そのままメニューに戻る（"戻る"選択時のみループ終了）
