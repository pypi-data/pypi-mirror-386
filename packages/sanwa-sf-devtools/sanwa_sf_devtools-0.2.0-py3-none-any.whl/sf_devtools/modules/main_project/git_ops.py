from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from subprocess import CompletedProcess
from typing import Optional

from ...core.common import Logger, logger, ui


@dataclass
class GitActionResult:
    """Git 操作の結果をUIに共有するためのシンプルなDTO"""

    success: bool
    message: str = ""
    conflicts: bool = False
    needs_force_push: bool = False
    details: Optional[str] = None


class GitOps:
    """Git 操作用の薄いラッパ"""

    def __init__(self, repo_root: Optional[Path] = None) -> None:
        self.repo_root = (repo_root or Path.cwd()).resolve()

    def _run(
        self,
        args: list[str],
        check: bool = True,
    ) -> CompletedProcess[str]:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=check,
            cwd=self.repo_root,
        )

    def _ensure_git_repo(self) -> bool:
        try:
            self._run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            logger.error(
                "ここは Git リポジトリではありません。プロジェクトルートで実行してください。"
            )
        except FileNotFoundError:
            logger.error(
                "git コマンドが見つかりません。Git のインストールを確認してください。"
            )
        return False

    def _current_branch(self) -> Optional[str]:
        try:
            result = self._run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                check=True,
            )
            branch = result.stdout.strip()
            if branch:
                return branch
        except subprocess.CalledProcessError:
            logger.error("現在のブランチを取得できませんでした。")
        return None

    def _has_uncommitted_changes(self) -> bool:
        status = self._run(["git", "status", "--porcelain"], check=False)
        return bool(status.stdout.strip())

    def _rebase_in_progress(self) -> bool:
        git_dir = self.repo_root / ".git"
        return (git_dir / "rebase-merge").exists() or (
            git_dir / "rebase-apply"
        ).exists()

    def _print_conflict_tips(self) -> None:
        Logger.step("コンフリクト解消のヒント")
        tips = [
            "git status で競合ファイルを確認します。",
            "競合を解消したら各ファイルに対して `git add <ファイル>` を実行します。",
            "`git rebase --continue` でリベースを再開します。",
            "中断したい場合は `git rebase --abort` で元の状態に戻せます。",
        ]
        for tip in tips:
            logger.info(f"  • {tip}")

    def print_status_short(self) -> None:
        short = self._run(["git", "status", "--short"], check=False)
        output = short.stdout.strip()
        if output:
            Logger.step("現在の変更一覧")
            for line in output.splitlines():
                logger.info(f"  {line}")

    def stage_and_commit(
        self, target_dir: Path, *, default_message: Optional[str] = None
    ) -> bool:
        Logger.step("Git ステータス表示")
        try:
            self._run(["git", "status"], check=False)
        except Exception:
            logger.warn("git status の実行に失敗しました")

        Logger.step("ステージング")
        self._run(["git", "add", str(target_dir)])

        default_msg = default_message
        if default_msg is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            default_msg = f"Update production metadata {date_str}"
        message = ui.get_user_input(
            "コミットメッセージを入力してください", default=default_msg
        )

        Logger.step("コミット実行")
        result = self._run(
            ["git", "commit", "--no-verify", "-m", message],
            check=False,
        )
        if result.returncode != 0:
            logger.warn("コミットできる変更がない、またはコミットに失敗しました。")
            if not ui.confirm("続行しますか？", default=False):
                return False

        if ui.confirm("リモートリポジトリにプッシュしますか？", default=False):
            Logger.step("プッシュ実行")
            self._run(["git", "push"], check=False)
            logger.success("プッシュが完了しました。")

        if ui.confirm("タグを作成しますか？", default=False):
            tag_name = f"prod-snapshot-{datetime.now().strftime('%Y%m%d')}"
            tag_message = ui.get_user_input(
                "タグメッセージを入力してください",
                default="Production metadata snapshot",
            )
            Logger.step(f"タグ '{tag_name}' を作成")
            tag_result = self._run(
                ["git", "tag", "-a", tag_name, "-m", tag_message], check=False
            )
            if tag_result.returncode != 0:
                logger.warn("タグ作成に失敗しました（既存の可能性）。")
                if not ui.confirm("続行しますか？", default=False):
                    return False
            if ui.confirm("タグをリモートにプッシュしますか？", default=False):
                self._run(["git", "push", "origin", tag_name], check=False)
                logger.success("タグのプッシュが完了しました。")

        return True

    def rebase_onto_main(self, target_branch: str = "main") -> GitActionResult:
        if not self._ensure_git_repo():
            return GitActionResult(False, "Git リポジトリ外で実行されました。")

        if self._rebase_in_progress():
            logger.warn(
                (
                    "既にリベースが進行中です。コンフリクトを解消するか "
                    "`git rebase --abort` を実行してください。"
                )
            )
            self.print_status_short()
            return GitActionResult(
                False, "進行中のリベースがあります。", conflicts=True
            )

        current_branch = self._current_branch()
        if not current_branch:
            return GitActionResult(False, "現在のブランチを特定できませんでした。")

        if current_branch == target_branch:
            logger.warn(
                (
                    f"現在 {target_branch} ブランチ上です。作業ブランチ "
                    "(例: dev/feature) に切り替えてから実行してください。"
                )
            )
            return GitActionResult(
                False, f"{target_branch} ブランチ上でのリベースは行いません。"
            )

        if not current_branch.startswith("dev/"):
            logger.warn(
                (
                    "ブランチ名が dev/ から始まっていません。標準の開発ブランチ"
                    "形式 (dev/〇〇) か確認してください。"
                )
            )
            if not ui.confirm(
                f"{current_branch} を対象にリベースを続行しますか？", default=False
            ):
                return GitActionResult(False, "ユーザーがキャンセルしました。")

        if self._has_uncommitted_changes():
            logger.warn(
                (
                    "未コミットの変更があります。リベース前にコミットまたは"
                    "スタッシュすることを推奨します。"
                )
            )
            self.print_status_short()
            if not ui.confirm(
                "未コミットのままリベースを実行しますか？", default=False
            ):
                return GitActionResult(
                    False, "未コミットの変更によりリベースを中止しました。"
                )

        Logger.step(f"origin/{target_branch} の最新を取得します")
        fetch_result = self._run(
            ["git", "fetch", "origin", target_branch],
            check=False,
        )
        if fetch_result.returncode != 0:
            logger.error(
                "リモートの取得に失敗しました。ネットワークや認証情報を確認してください。"
            )
            error_detail = (
                fetch_result.stderr or fetch_result.stdout or ""
            ).strip() or None
            return GitActionResult(
                False,
                "git fetch に失敗しました。",
                details=error_detail,
            )

        Logger.step(f"{current_branch} を {target_branch} に追従させます (rebase)")
        rebase_result = self._run(
            ["git", "rebase", f"origin/{target_branch}"], check=False
        )
        combined_output = (rebase_result.stderr or "") + (rebase_result.stdout or "")
        output: Optional[str] = combined_output.strip() or None

        if rebase_result.returncode == 0:
            logger.success(
                f"{current_branch} を最新の {target_branch} に追従させました。"
            )
            status_line = self._run(
                ["git", "status", "-sb"], check=False
            ).stdout.strip()
            if status_line:
                logger.info(status_line)
            return GitActionResult(True, "リベースが完了しました。", details=output)

        if self._rebase_in_progress():
            logger.warn(
                "リベース中にコンフリクトが発生しました。次の手順で解消してください。"
            )
            self._print_conflict_tips()
            self.print_status_short()
            return GitActionResult(
                False,
                "コンフリクトを解消してください。",
                conflicts=True,
                details=output,
            )

        logger.error("リベースの実行に失敗しました。")
        if output:
            logger.error(output)
        return GitActionResult(False, "リベースに失敗しました。", details=output)

    def push_current_branch(self) -> GitActionResult:
        if not self._ensure_git_repo():
            return GitActionResult(False, "Git リポジトリ外で実行されました。")

        current_branch = self._current_branch()
        if not current_branch:
            return GitActionResult(False, "現在のブランチを特定できませんでした。")

        if current_branch == "main":
            logger.warn(
                (
                    "main ブランチからの直接 push は想定していません。"
                    "開発ブランチから実行してください。"
                )
            )
            if not ui.confirm(
                "main ブランチのまま push を実行しますか？", default=False
            ):
                return GitActionResult(False, "ユーザーがキャンセルしました。")

        if self._has_uncommitted_changes():
            logger.warn(
                (
                    "未コミットの変更があります。push の前にコミットすることを"
                    "推奨します。"
                )
            )
            self.print_status_short()
            if not ui.confirm("未コミットのまま push を試みますか？", default=False):
                return GitActionResult(
                    False, "未コミットの変更により push を中止しました。"
                )

        upstream = self._run(
            ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
            check=False,
        )
        if upstream.returncode != 0:
            logger.warn(
                (
                    "リモート追跡ブランチが設定されていません。"
                    "初回 push を実行します。"
                )
            )
            if not ui.confirm(
                f"origin に {current_branch} を作成して push しますか？", default=True
            ):
                return GitActionResult(
                    False, "ユーザーが初回 push をキャンセルしました。"
                )
            Logger.step("初回 push を実行します")
            first_push = self._run(
                ["git", "push", "-u", "origin", current_branch], check=False
            )
            if first_push.returncode == 0:
                logger.success(
                    "push が完了しました。これでリモートと同期されています。"
                )
                return GitActionResult(True, "初回 push が完了しました。")
            logger.error("push に失敗しました。出力を確認してください。")
            details = (first_push.stderr or first_push.stdout or "").strip() or None
            if details:
                logger.error(details)
            return GitActionResult(False, "push に失敗しました。", details=details)

        upstream_ref = upstream.stdout.strip()
        Logger.step("リモートとの差分を確認します")
        ahead_behind = self._run(
            ["git", "rev-list", "--left-right", "--count", f"{upstream_ref}...HEAD"],
            check=False,
        )
        if ahead_behind.returncode != 0:
            logger.error("リモートとの差分を取得できませんでした。")
            details = (ahead_behind.stderr or ahead_behind.stdout or "").strip() or None
            if details:
                logger.error(details)
            return GitActionResult(False, "差分の取得に失敗しました。", details=details)

        counts = ahead_behind.stdout.strip().split()
        ahead = int(counts[1]) if len(counts) > 1 else 0
        behind = int(counts[0]) if counts else 0

        if ahead == 0 and behind == 0:
            logger.info("リモートと完全に同期しています。push の必要はありません。")
            return GitActionResult(True, "すでに同期済みです。")

        if behind > 0 and ahead == 0:
            logger.warn(
                (
                    "リモートに新しい変更があります。push の前に"
                    "リベースまたは pull を実行してください。"
                )
            )
            logger.info(f"  • 推奨: git pull --rebase origin {current_branch}")
            return GitActionResult(
                False, "リモートが進んでいます。先に取り込みが必要です。"
            )

        needs_force_push = behind > 0 and ahead > 0
        if needs_force_push:
            logger.warn(
                (
                    "リモートと履歴が分岐しています（おそらくリベース済み）。"
                    "安全な強制 push (--force-with-lease) が必要です。"
                )
            )
            if not ui.confirm(
                "現在のローカル履歴で --force-with-lease を実行しますか？", default=True
            ):
                return GitActionResult(
                    False,
                    "force push をキャンセルしました。",
                    needs_force_push=True,
                )

        if ahead > 0:
            Logger.step("リモートへ送信予定のコミット")
            preview = self._run(
                [
                    "git",
                    "log",
                    "--oneline",
                    "--graph",
                    "--decorate",
                    f"{upstream_ref}..HEAD",
                ],
                check=False,
            ).stdout.strip()
            if preview:
                for line in preview.splitlines():
                    logger.info(f"  {line}")

        push_cmd = ["git", "push"]
        if needs_force_push:
            push_cmd = ["git", "push", "--force-with-lease"]

        Logger.step("push を実行します")
        push_result = self._run(push_cmd, check=False)
        details = (push_result.stderr or push_result.stdout or "").strip() or None

        if push_result.returncode == 0:
            logger.success("リモートへの push が完了しました。")
            status_line = self._run(
                ["git", "status", "-sb"], check=False
            ).stdout.strip()
            if status_line:
                logger.info(status_line)
            return GitActionResult(
                True,
                "push が完了しました。",
                needs_force_push=needs_force_push,
                details=details,
            )

        logger.error("push に失敗しました。")
        if details:
            logger.error(details)
        return GitActionResult(
            False,
            "push に失敗しました。",
            needs_force_push=needs_force_push,
            details=details,
        )

    # --- Branch & Tag utilities ---
    def _validate_name(self, value: str, field: str) -> None:
        import re

        if not value:
            raise ValueError(f"{field} を入力してください")
        if not re.match(r"^[a-zA-Z0-9_-]+$", value):
            raise ValueError(
                f"{field} は英数字・ハイフン・アンダースコアのみ使用できます"
            )
        if value[0] in "-_" or value[-1] in "-_":
            raise ValueError(
                f"{field} の先頭・末尾にハイフン/アンダースコアは使えません"
            )

    def _branch_exists(self, name: str) -> bool:
        res_local = self._run(
            ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{name}"],
            check=False,
        )
        res_remote = self._run(
            ["git", "show-ref", "--verify", "--quiet", f"refs/remotes/origin/{name}"],
            check=False,
        )
        return res_local.returncode == 0 or res_remote.returncode == 0

    def create_feature_branch(self) -> bool:
        """feat/{sandbox}/{feature} のブランチを作成し、必要に応じてpushする"""
        try:
            self._run(["git", "rev-parse", "--git-dir"], check=True)
        except Exception:
            logger.error("現在のディレクトリはGitリポジトリではありません")
            return False

        # 未コミット警告
        dirty = (
            self._run(
                ["git", "diff-index", "--quiet", "HEAD", "--"], check=False
            ).returncode
            != 0
        )
        if dirty:
            logger.warn(
                (
                    "未コミットの変更があります。新しいブランチを作成する前に"
                    "コミットまたは破棄することを推奨します。"
                )
            )
            if not ui.confirm("続行しますか？", default=False):
                return False

        # 入力
        sandbox = ui.get_user_input("サンドボックス名 (例: dev, staging)")
        feature = ui.get_user_input("機能名 (例: user-management)")
        try:
            self._validate_name(sandbox, "サンドボックス名")
            self._validate_name(feature, "機能名")
        except ValueError as e:
            logger.error(str(e))
            return False

        branch = f"feat/{sandbox}/{feature}"
        if self._branch_exists(branch):
            logger.error(f"ブランチ '{branch}' は既に存在します")
            return False

        Logger.step("ブランチ作成")
        checkout_result = self._run(
            ["git", "checkout", "-b", branch],
            check=False,
        )
        if checkout_result.returncode != 0:
            logger.error("ブランチの作成に失敗しました")
            return False
        logger.success(f"ブランチを作成しました: {branch}")

        if ui.confirm("リモートにpushしますか？", default=True):
            if (
                self._run(
                    ["git", "push", "-u", "origin", branch], check=False
                ).returncode
                == 0
            ):
                logger.success("リモートにpushしました")
            else:
                logger.warn(
                    (
                        "リモートへのpushに失敗しました。"
                        "手動で実行してください: git push -u origin {branch}"
                    )
                )
        return True

    def create_manual_tag(self) -> bool:
        """任意のタグ名とメッセージで注釈付きタグを作成し、pushするか確認"""
        tag_name = ui.get_user_input(
            "作成するタグ名を入力してください (例: release-20251015)"
        )
        if not tag_name:
            logger.error("タグ名が入力されていません")
            return False
        tag_message = ui.get_user_input(
            "タグメッセージを入力してください", default="Manual tag"
        )

        Logger.step(f"タグ '{tag_name}' を作成")
        if (
            self._run(
                ["git", "tag", "-a", tag_name, "-m", tag_message], check=False
            ).returncode
            != 0
        ):
            logger.error("タグ作成に失敗しました（既存の可能性）")
            return False
        logger.success(f"タグを作成しました: {tag_name}")
        if ui.confirm("タグをリモートにpushしますか？", default=True):
            if (
                self._run(["git", "push", "origin", tag_name], check=False).returncode
                == 0
            ):
                logger.success("タグをpushしました")
            else:
                logger.warn("タグのpushに失敗しました")
        return True
