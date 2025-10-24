from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..core.common import SalesforceCliError, config, logger, sf_cli, ui
from ..modules.main_project.convert_deploy_ops import ConvertDeployOps
from ..modules.main_project.git_ops import GitOps
from ..modules.main_project.manifest_ops import ManifestOps
from ..modules.main_project.org_config import OrgConfig
from ..modules.main_project.retrieve_ops import RetrieveOps

console = Console()


class _SanwaBaseUI:
    """共通の Sanwa 操作用ベースクラス"""

    def __init__(self) -> None:
        self.manifest = ManifestOps()
        self.retrieve = RetrieveOps()
        self.git = GitOps()
        self.orgcfg = OrgConfig()
        self.convdep = ConvertDeployOps()

        self.project_root = config.project_root
        self.manifest_dir = self.project_root / "manifest"
        self.default_manifest = self.manifest_dir / "prod-full.xml"
        self.default_target_dir = self.project_root / "prod-full"

    # === Actions ===
    def _action_generate_manifest(self) -> None:
        alias = ui.get_user_input(
            "本番 org のエイリアス（例: prod）を入力", default="prod"
        )
        try:
            self.manifest.generate_manifest(
                from_org=alias,
                name=self.default_manifest.name,
                output_dir=self.manifest_dir,
            )
        except Exception as e:
            logger.error(f"マニフェスト生成に失敗しました: {e}")

    def _action_retrieve(self) -> None:
        if not self.default_manifest.exists():
            logger.warn(f"マニフェストがありません: {self.default_manifest}")
            if ui.confirm("先にマニフェストを生成しますか？", default=True):
                self._action_generate_manifest()
                if not self.default_manifest.exists():
                    return
            else:
                return

        alias = ui.get_user_input(
            "取得元 org のエイリアス（例: prod）を入力", default="prod"
        )
        try:
            self.retrieve.retrieve_and_expand(
                manifest_file=self.default_manifest,
                target_org=alias,
                target_dir=self.default_target_dir,
            )
        except Exception as e:
            logger.error(f"メタデータ取得に失敗しました: {e}")

    def _action_git(self) -> None:
        try:
            self.git.stage_and_commit(self.default_target_dir)
        except Exception as e:
            logger.error(f"Git 操作に失敗しました: {e}")

    def _action_full_workflow(self) -> None:
        alias = ui.get_user_input(
            "本番 org のエイリアス（例: prod）を入力", default="prod"
        )
        try:
            self.manifest.generate_manifest(
                from_org=alias,
                name=self.default_manifest.name,
                output_dir=self.manifest_dir,
            )
            self.retrieve.retrieve_and_expand(
                manifest_file=self.default_manifest,
                target_org=alias,
                target_dir=self.default_target_dir,
            )
            self.git.stage_and_commit(self.default_target_dir)
        except Exception as e:
            logger.error(f"全体フロー中に失敗しました: {e}")

    def _action_init_orgcfg(self) -> None:
        try:
            data = self.orgcfg.ensure()
            logger.success(
                f"org-config 準備完了: alias={data.alias}, sourceDir={data.sourceDir}"
            )
        except Exception as e:
            logger.error(f"org-config 初期化に失敗しました: {e}")

    def _action_convert(self) -> None:
        data = self.orgcfg.load()
        if not data:
            logger.warn("org-config が見つかりません。初期化を実行します。")
            try:
                data = self.orgcfg.ensure()
            except Exception as e:
                logger.error(f"org-config 初期化に失敗: {e}")
                return
        src = Path(data.sourceDir)
        out = Path(f"{data.alias}-meta")
        try:
            self.convdep.convert_source(
                source_dir=src,
                output_dir=out,
                package_name=f"Init_{data.alias}",
            )
        except Exception as e:
            logger.error(f"Convert に失敗しました: {e}")

    def _action_deploy(self, *, dry_run: bool) -> None:
        data = self.orgcfg.load()
        if not data:
            logger.warn("org-config が見つかりません。初期化を実行します。")
            try:
                data = self.orgcfg.ensure()
            except Exception as e:
                logger.error(f"org-config 初期化に失敗: {e}")
                return
        target = ui.get_user_input(
            "デプロイ先 org エイリアスを入力", default=data.alias
        )
        src = Path(data.sourceDir)
        try:
            self.convdep.deploy(
                source_dir=src,
                target_org=target,
                run_tests="RunLocalTests",
                dry_run=dry_run,
            )
            if not dry_run:
                # 成功時は簡易タグ作成（feat/{sandbox}/{feature} 構文は今後拡張）
                if ui.confirm("デプロイ完了タグを作成しますか？", default=True):
                    self.git.stage_and_commit(
                        Path(".")
                    )  # 変更がなくてもタグフローへ誘導
        except Exception as e:
            logger.error(f"Deploy に失敗しました: {e}")

    def _action_create_branch(self) -> None:
        try:
            self.git.create_feature_branch()
        except Exception as e:
            logger.error(f"ブランチ作成に失敗しました: {e}")

    def _action_create_manual_tag(self) -> None:
        try:
            self.git.create_manual_tag()
        except Exception as e:
            logger.error(f"手動タグ作成に失敗しました: {e}")


class SanwaMainUI(_SanwaBaseUI):
    """汎用（Sanwa Main）用の対話メニュー"""

    def show_menu(self) -> None:
        while True:
            logger.info("汎用（Sanwa Main）メニュー")
            options = [
                "1) 初期化（org-config 作成/TOML）",
                "2) package.xmlからソースデータの取得（retrieve）",
                "3) Convert（source→mdapi）",
                "4) Deploy (Dry Run)",
                "5) Deploy（本番）＋タグ作成",
                "戻る",
            ]
            try:
                choice = ui.select_from_menu("実行する操作を選択してください:", options)
            except Exception:
                return

            if choice == 0:
                self._action_init_orgcfg()
            elif choice == 1:
                self._action_retrieve_package_xml()
            elif choice == 2:
                self._action_convert()
            elif choice == 3:
                self._action_deploy(dry_run=True)
            elif choice == 4:
                self._action_deploy(dry_run=False)
            else:
                return

            if not ui.confirm("汎用メニューを続けますか？", default=True):
                return

    def _action_retrieve_package_xml(self) -> None:
        manifest_path = self.manifest_dir / "package.xml"
        if not manifest_path.exists():
            logger.error(f"manifest/package.xml が見つかりません: {manifest_path}")
            logger.info(
                "Package.xml Generator で manifest/package.xml を作成してください。"
            )
            return

        target_org = ui.select_org(
            "メタデータ取得元 org", include_scratch=False, return_type="alias"
        )
        if not target_org:
            logger.error("組織が選択されませんでした")
            return

        output_dir_name = f"{target_org}-source"
        output_dir = self.project_root / output_dir_name

        logger.info("メタデータ取得設定:")
        print("  マニフェスト: manifest/package.xml")
        print(f"  取得元組織: {target_org}")
        print(f"  出力先: {output_dir_name}")

        if output_dir.exists():
            try:
                has_contents = any(output_dir.iterdir())
            except Exception:
                has_contents = False
            if has_contents:
                logger.warn(f"{output_dir_name} は既に存在し、内容が上書きされます。")
                if not ui.confirm(
                    "既存の内容を上書きして続行しますか？", default=False
                ):
                    logger.info("取得をキャンセルしました")
                    return
        else:
            output_dir.mkdir(parents=True, exist_ok=True)

        if not ui.confirm("この設定でメタデータを取得しますか？", default=True):
            logger.info("取得をキャンセルしました")
            return

        command = [
            "sf",
            "project",
            "retrieve",
            "start",
            "--manifest",
            str(manifest_path.relative_to(self.project_root)),
            "--target-org",
            target_org,
            "--output-dir",
            output_dir_name,
            "--json",
        ]

        result = None
        with Progress(
            SpinnerColumn(style="bright_cyan"),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("[dim]{task.fields[msg]}"),
            transient=True,
            console=console,
        ) as progress:
            task_id = progress.add_task(
                "メタデータ取得中",
                total=None,
                msg="Salesforce CLI を起動しています",
            )
            try:
                progress.update(task_id, msg="sf project retrieve start 実行中")
                result = sf_cli.run_command(
                    command,
                    capture_output=True,
                    check=True,
                    cwd=self.project_root,
                )
                progress.update(task_id, msg="取得結果を整形しています")
            except SalesforceCliError as exc:
                progress.update(task_id, msg="失敗しました")
                logger.error(f"メタデータ取得に失敗しました: {exc}")
                return

        try:
            display_dir = output_dir.relative_to(self.project_root)
        except ValueError:
            display_dir = output_dir

        payload = {}
        raw_output = (result.stdout or "").strip() if result else ""
        if not raw_output:
            logger.warn("Salesforce CLI からの JSON 出力が取得できませんでした。")
        else:
            try:
                payload = json.loads(raw_output)
            except json.JSONDecodeError:
                logger.error("CLI 出力の JSON 解析に失敗しました。")
                console.print(
                    Panel.fit(
                        raw_output,
                        title="CLI 出力 (解析失敗)",
                        border_style="red",
                        box=ROUNDED,
                    )
                )
                return

        result_data = payload.get("result", {}) if isinstance(payload, dict) else {}
        files = result_data.get("files") or []
        warnings = payload.get("warnings") or []
        status_text = result_data.get("status") or payload.get("status")
        success = result_data.get("success")
        retrieve_id = result_data.get("id") or "-"
        file_count = len(files)

        logger.success(f"メタデータの取得が完了しました: {display_dir}")

        summary_table = Table(
            title="取得結果概要",
            box=ROUNDED,
            header_style="bold",
        )
        summary_table.add_column("項目", style="cyan", no_wrap=True)
        summary_table.add_column("値", style="white")
        summary_table.add_row("Retrieve ID", str(retrieve_id))
        summary_table.add_row("ステータス", str(status_text))
        success_label = (
            "はい" if success is True else "いいえ" if success is False else "不明"
        )
        summary_table.add_row("成功", success_label)
        summary_table.add_row("取得ファイル数", str(file_count))
        summary_table.add_row("出力ディレクトリ", str(display_dir))
        console.print(summary_table)

        if files:
            type_counts = Counter(str(item.get("type") or "Unknown") for item in files)
            top_types = type_counts.most_common(6)
            type_table = Table(
                title="メタデータタイプ上位",
                box=ROUNDED,
                header_style="bold",
            )
            type_table.add_column("タイプ", style="magenta")
            type_table.add_column("件数", style="white", justify="right")
            for meta_type, count in top_types:
                type_table.add_row(meta_type, str(count))
            console.print(type_table)

            sample_entries = files[:5]
            sample_lines = [
                f"[green]{entry.get('type')}[/green]  {entry.get('filePath')}"
                for entry in sample_entries
            ]
            console.print(
                Panel.fit(
                    "\n".join(sample_lines),
                    title="取得ファイル サンプル (最大5件)",
                    border_style="bright_blue",
                    box=ROUNDED,
                )
            )

        if warnings:
            warning_lines = "\n".join(str(w) for w in warnings)
            console.print(
                Panel.fit(
                    warning_lines,
                    title="CLI 警告",
                    border_style="yellow",
                    box=ROUNDED,
                )
            )


class ProductionBackupUI(_SanwaBaseUI):
    """本番環境バックアップ用の対話メニュー"""

    def show_menu(self) -> None:
        while True:
            logger.info("本番環境バックアップメニュー")
            options = [
                "1) マニフェスト生成 (prod-full.xml)",
                "2) メタデータ取得・展開",
                "3) Git操作 (commit/push/tag)",
                "4) 全体フロー (1→2→3)",
                "戻る",
            ]
            try:
                choice = ui.select_from_menu("実行する操作を選択してください:", options)
            except Exception:
                return

            if choice == 0:
                self._action_generate_manifest()
            elif choice == 1:
                self._action_retrieve()
            elif choice == 2:
                self._action_git()
            elif choice == 3:
                self._action_full_workflow()
            else:
                return

            if not ui.confirm(
                "本番環境バックアップメニューを続けますか？", default=True
            ):
                return
