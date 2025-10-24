"""
Enhanced interactive user interface for SF DevTools.
Integration with all migrated modules from shell scripts.
"""

import typer
from rich.align import Align
from rich.box import DOUBLE, ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from .. import __version__
from ..core.common import check_prerequisites, logger, ui
from .git_menu import GitSupportUI
from .help_views import show_help
from .mes_menu import MesMenuUI
from .sanwa_main import ProductionBackupUI, SanwaMainUI

console = Console()


class InteractiveUI:
    """Enhanced interactive user interface class."""

    def __init__(self) -> None:
        self.running = True

    def show_banner(self) -> None:
        """Show welcome banner with rich formatting."""
        console.clear()

        # パネルの作成
        # 豪華なパネルで表示
        banner_panel = Panel(
            Align.center(
                Text.assemble(
                    ("☁️  "),
                    ("Salesforce", "bold blue"),
                    (" 開発用 CLI", "bold cyan"),
                    (" | ", "dim"),
                    ("バージョン: ", "dim"),
                    (f"{__version__}", "bold green"),
                    "\n\n",
                    ("Salesforce 開発を効率化する対話型CLI", "italic bright_white"),
                    "\n\n",
                    ("⌨️  ", "cyan"),
                    ("Ctrl+C で終了", "red"),
                )
            ),
            title="[bold bright_blue]✨ SF DevTools へようこそ ✨[/bold bright_blue]",
            border_style="bright_blue",
            box=DOUBLE,
            padding=(1, 2),
            width=80,
        )

        console.print(banner_panel)
        console.print()

        # 装飾的な区切り線
        console.print(
            Rule(
                "[bold bright_blue]🎯 メインメニュー[/bold bright_blue]",
                style="bright_blue",
            )
        )
        console.print()

    def show_main_menu(self) -> int:
        """Show main menu with rich table formatting."""

        # メニューオプションの定義
        menu_items = [
            {
                "icon": "🌿",
                "name": "Git支援",
                "description": "Git開発支援メニュー rebase / push / ブランチ・タグ作成をガイド付きで実行",
            },
            {
                "icon": "🧭",
                "name": "汎用（Sanwa Main）",
                "description": "Salesforce一般開発リポジトリ向けメニュー メタデータの取得・展開などの汎用支援",
            },
            {
                "icon": "🏭",
                "name": "MES 機能メニュー",
                "description": "MES開発ブランチ向け機能",
            },
            {
                "icon": "🛡️",
                "name": "本番環境バックアップ",
                "description": "本番メタデータの取得・展開・Git 操作の一括実行",
            },
            {
                "icon": "⚙️",
                "name": "設定・環境確認",
                "description": "開発環境の設定と確認",
            },
            {
                "icon": "📚",
                "name": "ヘルプ・ドキュメント",
                "description": "ヘルプ情報とドキュメントの表示",
            },
            {
                "icon": "🚪",
                "name": "終了",
                "description": "アプリケーションを終了",
            },
        ]

        # テーブルの作成
        table = Table(
            title="[bold bright_cyan]📋 機能メニュー[/bold bright_cyan]",
            show_header=True,
            header_style="bold bright_blue",
            border_style="bright_blue",
            box=ROUNDED,
            padding=(0, 1),
            width=100,
        )

        table.add_column("#", style="bold bright_yellow", width=4, justify="center")
        table.add_column("機能", style="bold white", width=40)
        table.add_column("説明", style="dim", width=55)

        # テーブル行の追加
        for i, item in enumerate(menu_items):
            table.add_row(
                f"{i + 1}",
                f"{item['icon']} {item['name']}",
                item["description"],
            )

        console.print(table)
        console.print()

        # 選択用のオプションリスト（従来のinquirer用）
        options = [
            f"{i + 1}) {item['icon']} {item['name']}"
            for i, item in enumerate(menu_items)
        ]

        try:
            choice = ui.select_from_menu("🎯 実行する操作を選択してください:", options)
            return choice
        except (KeyboardInterrupt, EOFError):
            # 最終項目（終了）にフォールバック
            return len(menu_items) - 1

    def run(self) -> None:
        """Main loop execution."""
        # Show banner
        self.show_banner()

        # Check prerequisites
        try:
            if not check_prerequisites(interactive=True, raise_on_error=True):
                return
        except typer.Exit:
            return

        # Main menu loop
        while self.running:
            try:
                choice = self.show_main_menu()
                if choice == 0:  # Git支援
                    GitSupportUI().show_menu()

                elif choice == 1:  # 汎用（Sanwa Main）
                    SanwaMainUI().show_menu()

                elif choice == 2:  # MES 機能メニュー
                    MesMenuUI().show_menu()

                elif choice == 3:  # 本番環境バックアップ
                    ProductionBackupUI().show_menu()

                elif choice == 4:  # 設定・環境確認
                    # 設定・環境確認メニューを起動
                    try:
                        from ..modules.config import ConfigManager

                        cfg = ConfigManager()
                        cfg.show_menu()
                    except Exception as e:
                        logger.error(f"設定・環境確認メニューの起動に失敗しました: {e}")
                elif choice == 5:  # ヘルプ・ドキュメント
                    show_help()
                elif choice == 6:  # 終了
                    self.running = False
                    self._show_goodbye()
                    break

            except (KeyboardInterrupt, EOFError):
                self.running = False
                self._show_goodbye()
                break

    def _show_under_construction(self, feature_name: str, description: str) -> None:
        """Show under construction message with rich formatting."""
        console.print()

        construction_panel = Panel(
            Align.center(
                Text.assemble(
                    ("🚧 ", "bold yellow"),
                    ("実装中", "bold yellow"),
                    (" 🚧", "bold yellow"),
                    "\n\n",
                    (feature_name, "bold cyan"),
                    ("\n\n", ""),
                    (description, "dim"),
                    ("\n\n", ""),
                    ("この機能は現在開発中です。", "italic"),
                    ("\n", ""),
                    ("今後のアップデートをお待ちください！", "italic green"),
                )
            ),
            title="[bold bright_yellow]🚧 Coming Soon 🚧[/bold bright_yellow]",
            border_style="yellow",
            box=DOUBLE,
            padding=(1, 2),
            width=70,
        )

        console.print(construction_panel)
        console.print()

        if not ui.confirm("メインメニューに戻りますか？", default=True):
            self.running = False

    def _show_goodbye(self) -> None:
        """Show goodbye message with rich formatting."""
        console.print()

        goodbye_panel = Panel(
            Align.center(
                Text.assemble(
                    ("SF DevTools をご利用いただき、", "bright_white"),
                    ("\n", ""),
                    ("ありがとうございました。", "bright_white"),
                )
            ),
            title="[bold bright_green]🎉 See You Again! 🎉[/bold bright_green]",
            border_style="bright_green",
            box=DOUBLE,
            padding=(1, 2),
            width=60,
        )

        console.print(goodbye_panel)
        console.print()
