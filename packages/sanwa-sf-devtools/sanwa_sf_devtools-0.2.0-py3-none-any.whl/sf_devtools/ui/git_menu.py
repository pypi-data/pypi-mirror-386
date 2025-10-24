from __future__ import annotations

from ..core.common import logger, ui
from ..modules.main_project.git_ops import GitActionResult, GitOps


class GitSupportUI:
    """Git リベース／プッシュを案内するメニュー"""

    def __init__(self) -> None:
        self.git = GitOps()

    def show_menu(self) -> None:
        while True:
            logger.info("Git 支援メニュー")
            options = [
                "1) 新しい Feature ブランチを作成",
                "2) main ブランチに追従（rebase）",
                "3) リモート履歴を同期（push）",
                "4) 手動タグを作成",
                "戻る",
            ]
            try:
                choice = ui.select_from_menu("実行する操作を選択してください:", options)
            except Exception:
                return

            if choice == 0:
                self._create_feature_branch()
            elif choice == 1:
                self._run_rebase()
            elif choice == 2:
                self._run_push()
            elif choice == 3:
                self._create_manual_tag()
            else:
                return

            if not ui.confirm("Git 支援メニューを続けますか？", default=True):
                return

    def _run_rebase(self) -> None:
        result = self.git.rebase_onto_main()
        self._handle_result(result)

        if result.success:
            if ui.confirm(
                "リベースが完了しました。続けて push を実行しますか？", default=True
            ):
                self._run_push()
        elif result.conflicts:
            if ui.confirm(
                "コンフリクト状況を確認するために git status を表示しますか？",
                default=True,
            ):
                self.git.print_status_short()

    def _run_push(self) -> None:
        result = self.git.push_current_branch()
        self._handle_result(result)

        if not result.success and result.needs_force_push:
            logger.warn(
                "force push を実行する場合は、リモート側の最新状況も必ず確認してください。"
            )

    def _handle_result(self, result: GitActionResult) -> None:
        if result.success:
            return
        if result.conflicts:
            logger.warn(result.message or "コンフリクトが残っています。")
        else:
            logger.error(result.message or "処理に失敗しました。")

    def _create_feature_branch(self) -> None:
        self.git.create_feature_branch()

    def _create_manual_tag(self) -> None:
        self.git.create_manual_tag()
