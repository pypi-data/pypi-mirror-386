"""
SF DevTools CLI共通ユーティリティ

ログ、設定、Salesforce CLI操作、UIコンポーネントを提供。
"""

import json
import subprocess
import sys
import time
from contextlib import nullcontext
from pathlib import Path
from shutil import which
from threading import Thread
from typing import IO, Dict, Iterable, List, Optional, Tuple

import typer
from inquirer import List as InquirerList
from inquirer import prompt
from rich.console import Console

# アプリケーション全体で共有するコンソールインスタンス
console = Console()


class Logger:
    """色分けされたログメッセージ出力"""

    @staticmethod
    def info(message: str) -> None:
        """情報メッセージ（青）を出力します。

        Args:
            message: 出力するメッセージ文字列。
        """
        console.print(f"[blue][INFO][/blue] {message}")

    @staticmethod
    def success(message: str) -> None:
        """成功メッセージ（緑）を出力します。

        Args:
            message: 出力するメッセージ文字列。
        """
        console.print(f"[green][SUCCESS][/green] {message}")

    @staticmethod
    def warn(message: str) -> None:
        """警告メッセージ（黄）を出力します。

        Args:
            message: 出力するメッセージ文字列。
        """
        console.print(f"[yellow][WARN][/yellow] {message}")

    @staticmethod
    def error(message: str) -> None:
        """エラーメッセージ（赤）を出力します。

        Args:
            message: 出力するメッセージ文字列。
        """
        console.print(f"[red][ERROR][/red] {message}")

    @staticmethod
    def step(message: str) -> None:
        """実行ステップ（シアン）を出力します。

        Args:
            message: 出力するステップの説明。
        """
        console.print(f"[cyan]➤[/cyan] {message}")


class Config:
    """プロジェクト設定とパス管理"""

    def __init__(self) -> None:
        """コンフィグを初期化します。

        - プロジェクトルート（sfdx-project.json の所在）
        - スクリプト/設定/マニフェスト/一時ディレクトリ
        - デフォルトのスクラッチ有効日数/待機時間
        を解決して属性として保持します。
        """
        # 先にデフォルト値をセットしておく（初期化中の自動生成で参照するため）
        self.default_scratch_duration = 30
        self.default_wait_time = 30

        self.project_root = self._find_project_root()
        self.script_dir = self.project_root / "scripts/mes-dev-cli"
        self.config_dir = self.project_root / "config"
        self.manifest_dir = self.project_root / "manifest"
        self.temp_dir = self.project_root / "temp-mes-dev"

    def _find_project_root(self) -> Path:
        """プロジェクトルートを解決します。

        優先順位:
          1) CWD から上方探索して最寄りの .sf-devtools/config.toml を含む親ディレクトリ
          2) CWD から上方探索して最寄りの sfdx-project.json の親ディレクトリ
          3) どちらも無ければ CWD を暫定採用し、対話可能なら初期化を促す

        Returns:
            Path: プロジェクトルートとみなすディレクトリパス。
        """
        cwd = Path.cwd().resolve()

        # 1) 最寄りの .sf-devtools/config.toml を探す
        marker = self._find_upwards(cwd, Path(".sf-devtools/config.toml"))
        if marker is not None:
            # marker = <root>/.sf-devtools/config.toml
            # プロジェクトルートは .sf-devtools の親ディレクトリ
            return marker.parent.parent

        # 2) 最寄りの sfdx-project.json を探す
        sfdx = self._find_upwards(cwd, Path("sfdx-project.json"))
        if sfdx is not None:
            # 非対話環境でも自動初期化（安全な空設定）を試みる
            parent = sfdx.parent
            self._ensure_project_config(parent, interactive=False)
            return parent

        # 3) フォールバック: CWD を暫定採用し、可能なら初期化
        Logger.warn(
            (
                ".sf-devtools/config.toml も sfdx-project.json も見つかりません。"
                "現在のディレクトリを暫定ルートとして扱います。"
            )
        )
        # 明示的に非対話で初期化（ユーザーの手動実行なしで安定化）
        self._ensure_project_config(cwd, interactive=False)
        return cwd

    @staticmethod
    def _find_upwards(start: Path, relative: Path) -> Optional[Path]:
        """start から親に向かって relative パスを探索し、見つかれば絶対パスを返します。"""
        current = start
        while True:
            candidate = current / relative
            if candidate.exists():
                return candidate.resolve()
            if current == current.parent:
                return None
            current = current.parent

    def _ensure_project_config(self, root: Path, *, interactive: bool) -> None:
        """プロジェクト設定(.sf-devtools/config.toml)を確保します。

        - 既に存在すれば何もしない
        - 存在しなければ、interactive なら確認の上で生成、非対話なら静かに安全な既定値で生成
        """
        cfg_dir = root / ".sf-devtools"
        cfg_file = cfg_dir / "config.toml"
        if cfg_file.exists():
            return

        try:
            if interactive:
                Logger.info(f"プロジェクトルート候補: {root}")
                if not ui.confirm(
                    "この場所をプロジェクトルートとして初期化しますか？", default=True
                ):
                    Logger.warn(
                        "初期化をスキップしました。実行ディレクトリに .sf-devtools/config.toml を作成すると安定します。"
                    )
                    return

            cfg_dir.mkdir(parents=True, exist_ok=True)
            # 最小 TOML を生成
            created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            content = (
                "schema_version = 1\n\n"
                "[settings]\n"
                f"default_scratch_duration = {self.default_scratch_duration}\n"
                f"default_wait_time = {self.default_wait_time}\n\n"
                "[meta]\n"
                f'created_at = "{created_at}"\n'
            )
            cfg_file.write_text(content, encoding="utf-8")
            Logger.success(f"初期化しました: {cfg_file}")
        except Exception as e:
            Logger.warn(f"プロジェクト設定の初期化に失敗しました: {e}")


class SalesforceCliError(Exception):
    """Salesforce CLI実行エラー"""

    pass


class SalesforceCli:
    """Salesforce CLIコマンドのラッパー"""

    def __init__(self) -> None:
        self._org_cache: Optional[Dict] = None

    def run_command(
        self,
        command: List[str],
        capture_output: bool = True,
        check: bool = True,
        cwd: Optional[Path] = None,
        stream_output: Optional[bool] = None,
        status_message: Optional[str] = None,
    ) -> subprocess.CompletedProcess:
        """Salesforce CLI コマンドを実行します。

        Args:
            command: 実行するコマンドと引数のリスト（例: ["sf", "org", "list"...]）。
            capture_output: 標準出力/エラーをキャプチャするか。
            check: 非ゼロ終了コードで例外を送出するか。
            cwd: コマンド実行時の作業ディレクトリ。
            stream_output: True の場合はリアルタイムで標準出力/標準エラーを表示する。
                None の場合は `--json` を含むかどうかで自動判定する。

        Returns:
            subprocess.CompletedProcess: 実行結果オブジェクト。

        Raises:
            SalesforceCliError: コマンドが失敗した場合。
        """
        stream_output = (
            False if stream_output is None and "--json" in command else stream_output
        )
        if stream_output is None:
            stream_output = True

        use_pipes = capture_output or stream_output
        command_str = " ".join(command)

        try:
            if not use_pipes:
                Logger.step(f"Running: {command_str}")
                result = subprocess.run(
                    command,
                    capture_output=False,
                    text=True,
                    check=check,
                    cwd=cwd,
                )
                return result

            Logger.step(f"Running: {command_str}")
            stdout_lines: List[str] = []
            stderr_lines: List[str] = []
            process: Optional[subprocess.Popen[str]] = None
            threads: List[Thread] = []

            def _emit(raw: str) -> None:
                if stream_output:
                    target = getattr(console, "file", sys.stdout)
                    try:
                        target.write(raw)
                        target.flush()
                    except Exception:
                        sys.stdout.write(raw)
                        sys.stdout.flush()

            try:
                status_ctx = (
                    console.status(status_message, spinner="dots")
                    if status_message and not stream_output
                    else nullcontext()
                )

                with status_ctx:
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=cwd,
                        bufsize=1,
                        universal_newlines=True,
                    )

                    if process.stdout is not None:
                        stdout_stream: IO[str] = process.stdout

                        def _read_stdout(stream: IO[str]) -> None:
                            try:
                                for raw in iter(stream.readline, ""):
                                    stdout_lines.append(raw)
                                    _emit(raw)
                            finally:
                                stream.close()

                        threads.append(
                            Thread(
                                target=_read_stdout, args=(stdout_stream,), daemon=True
                            )
                        )

                    if process.stderr is not None:
                        stderr_stream: IO[str] = process.stderr

                        def _read_stderr(stream: IO[str]) -> None:
                            try:
                                for raw in iter(stream.readline, ""):
                                    stderr_lines.append(raw)
                                    _emit(raw)
                            finally:
                                stream.close()

                        threads.append(
                            Thread(
                                target=_read_stderr, args=(stderr_stream,), daemon=True
                            )
                        )

                    for thread in threads:
                        thread.start()

                    returncode = process.wait()

                    for thread in threads:
                        thread.join()
            except KeyboardInterrupt:
                if process and process.poll() is None:
                    try:
                        process.terminate()
                    except Exception:
                        pass
                    try:
                        process.wait(timeout=3)
                    except Exception:
                        try:
                            process.kill()
                        except Exception:
                            pass
                raise

            stdout_text = "".join(stdout_lines)
            stderr_text = "".join(stderr_lines)

            completed = subprocess.CompletedProcess(
                command,
                returncode,
                stdout_text if capture_output else None,
                stderr_text if capture_output else None,
            )

            if check and returncode != 0:
                Logger.error(f"Command failed: {command_str}")
                if stdout_text:
                    Logger.error(f"STDOUT: {stdout_text}")
                if stderr_text:
                    Logger.error(f"STDERR: {stderr_text}")
                raise SalesforceCliError(
                    f"Command failed with exit code {returncode}: {command_str}"
                )

            return completed

        except SalesforceCliError:
            raise
        except FileNotFoundError as e:
            Logger.error(f"Command not found: {command[0]}")
            raise SalesforceCliError(f"Command not found: {command[0]}") from e
        except KeyboardInterrupt:
            raise
        except Exception as e:
            Logger.error(f"Failed to run command: {command_str}")
            raise SalesforceCliError(f"Failed to run command: {e}") from e

    def load_org_cache(self) -> None:
        """`sf org list --json --all` の結果を読み込み、内部キャッシュに保持します。

        備考:
            - CLI のメッセージが混入するケースに備えて、JSON 開始行を検出してパースします。
            - パースに失敗した場合は空の構造をセットします。
        """
        if self._org_cache is not None:
            return

        try:
            result = self.run_command(
                ["sf", "org", "list", "--json", "--all"],
                capture_output=True,
                check=False,
            )

            # JSON開始位置を探す
            output = result.stdout
            lines = output.split("\n")
            json_start = 0

            for i, line in enumerate(lines):
                if line.strip().startswith("{"):
                    json_start = i
                    break

            json_output = "\n".join(lines[json_start:])

            try:
                self._org_cache = json.loads(json_output)
            except json.JSONDecodeError:
                Logger.error("Failed to parse sf org list JSON output")
                self._org_cache = {
                    "result": {
                        "nonScratchOrgs": [],
                        "scratchOrgs": [],
                        "devHubs": [],
                        "sandboxes": [],
                    }
                }

        except Exception as e:
            Logger.error(f"Failed to load org cache: {e}")
            self._org_cache = {
                "result": {
                    "nonScratchOrgs": [],
                    "scratchOrgs": [],
                    "devHubs": [],
                    "sandboxes": [],
                }
            }

    def get_all_orgs(self) -> List[Tuple[str, Optional[str], bool]]:
        """全認証済み組織情報を取得します。

        Returns:
            List[Tuple[str, Optional[str], bool]]: 各要素は (username, alias, is_scratch)。
        """
        self.load_org_cache()

        orgs: List[Tuple[str, Optional[str], bool]] = []
        cache = self._org_cache
        if cache is None:
            return orgs

        def get_orgs_from_key(
            key: str, is_scratch: bool = False
        ) -> List[Tuple[str, Optional[str], bool]]:
            """キャッシュから組織情報を抽出"""
            org_list = []
            data = cache.get("result", {}).get(key, cache.get(key, []))
            if data:
                for org in data:
                    username = org.get("username")
                    alias = org.get("alias")
                    if username:
                        org_list.append((username, alias, is_scratch))
            return org_list

        orgs.extend(get_orgs_from_key("nonScratchOrgs", False))
        orgs.extend(get_orgs_from_key("sandboxes", False))
        orgs.extend(get_orgs_from_key("devHubs", False))
        orgs.extend(get_orgs_from_key("scratchOrgs", True))

        return orgs

    def alias_to_username(self, alias: str) -> Optional[str]:
        """エイリアスからユーザー名に変換します。

        Args:
            alias: 組織エイリアス。

        Returns:
            Optional[str]: 対応するユーザー名。見つからない場合は None。
        """
        if not alias:
            return None

        self.load_org_cache()

        for username, org_alias, _ in self.get_all_orgs():
            if org_alias == alias:
                return username

        return None

    def get_orgs(self, include_scratch: bool = False) -> List[str]:
        """組織エイリアス（なければユーザー名）一覧を取得します。

        Args:
            include_scratch: True にするとスクラッチ組織も対象に含めます。

        Returns:
            List[str]: 表示用の組織識別子（alias 優先、なければ username）。
        """
        orgs = []
        for username, alias, is_scratch in self.get_all_orgs():
            if is_scratch and not include_scratch:
                continue
            orgs.append(alias or username)
        return orgs

    def get_scratch_orgs(self) -> List[str]:
        """スクラッチ組織エイリアス一覧を取得します。"""
        return self.get_orgs(include_scratch=True)


class UserInterface:
    """対話型UI操作"""

    @staticmethod
    def get_user_input(prompt: str, default: Optional[str] = None) -> str:
        """ユーザーからテキスト入力を取得します。

        Args:
            prompt: 入力プロンプトの文言。
            default: 入力が空だった場合に採用する既定値。

        Returns:
            str: ユーザー入力。空入力時は default（指定があれば）を返却。

        Raises:
            typer.Exit: 入力が中断（Ctrl+C/Ctrl+D）された場合。
        """
        if default:
            full_prompt = f"{prompt} [{default}]: "
        else:
            full_prompt = f"{prompt}: "

        try:
            response = input(full_prompt)
            return response.strip() if response.strip() else (default or "")
        except (KeyboardInterrupt, EOFError):
            raise typer.Exit(1)

    @staticmethod
    def select_from_menu(prompt_text: str, choices: List[str]) -> int:
        """メニューから項目を 1 つ選択します。

        Args:
            prompt_text: メニューの説明テキスト。
            choices: 選択肢のリスト。

        Returns:
            int: 選択されたインデックス（0 起点）。

        Raises:
            typer.Exit: 選択肢が空、または入力が中断された場合。
        """
        if not choices:
            Logger.error("No choices available")
            raise typer.Exit(1)

        try:
            questions = [
                InquirerList(
                    "choice",
                    message=prompt_text,
                    choices=choices,
                ),
            ]
            answers = prompt(questions)
            if not answers:
                raise typer.Exit(1)

            return choices.index(answers["choice"])
        except (KeyboardInterrupt, EOFError):
            raise typer.Exit(1)

    @staticmethod
    def confirm(message: str, default: bool = False) -> bool:
        """Yes/No 確認を行います。

        Args:
            message: 確認メッセージ。
            default: 何も入力しなかった場合に採用する既定値。

        Returns:
            bool: ユーザーが Yes を選択した場合 True。未入力時は default。

        Raises:
            typer.Exit: 入力が中断（Ctrl+C/Ctrl+D）された場合。
        """
        suffix = " [Y/n]" if default else " [y/N]"
        try:
            response = input(f"{message}{suffix}: ").strip().lower()
            if not response:
                return default
            return response in ("y", "yes")
        except (KeyboardInterrupt, EOFError):
            raise typer.Exit(1)

    @staticmethod
    def select_org(
        purpose: str, include_scratch: bool = False, return_type: str = "alias"
    ) -> Optional[str]:
        """組織を対話的に選択します。

        Args:
            purpose: 選択の目的（表示用）。
            include_scratch: True の場合、スクラッチ組織も選択対象に含めます。
            return_type: "alias" または "username"。返却する識別子の種類。

        Returns:
            Optional[str]: 選択された組織の alias もしくは username。失敗時 None。
        """
        sf_cli = SalesforceCli()
        Logger.info(f"{purpose} 組織を選択してください")

        orgs = sf_cli.get_all_orgs()

        if not orgs:
            Logger.error("認証済み組織が見つかりません")
            return None

        menu_choices = []
        org_data = []

        for username, alias, is_scratch in orgs:
            if is_scratch and not include_scratch:
                continue

            scratch_tag = " (scratch)" if is_scratch else ""
            if alias:
                display_name = f"{alias} ({username}){scratch_tag}"
            else:
                display_name = f"{username}{scratch_tag}"

            menu_choices.append(display_name)
            org_data.append((username, alias, is_scratch))

        if not menu_choices:
            Logger.error("利用可能な組織がありません")
            return None

        try:
            choice_index = UserInterface.select_from_menu(
                "利用可能な組織:", menu_choices
            )

            selected_org = org_data[choice_index]
            username, alias, _ = selected_org

            if return_type == "username":
                return username
            else:
                return alias or username

        except Exception as e:
            Logger.error(f"組織選択でエラーが発生しました: {e}")
            return None


# ========================================
# グローバルインスタンス
# ========================================

logger = Logger()
config = Config()
sf_cli = SalesforceCli()
ui = UserInterface()


# ========================================
# 後方互換性のための関数
# ========================================


def log_info(message: str) -> None:
    """情報メッセージ出力（後方互換性）。

    Args:
        message: 出力するメッセージ。
    """
    logger.info(message)


def log_success(message: str) -> None:
    """成功メッセージ出力（後方互換性）。

    Args:
        message: 出力するメッセージ。
    """
    logger.success(message)


def log_warn(message: str) -> None:
    """警告メッセージ出力（後方互換性）。

    Args:
        message: 出力するメッセージ。
    """
    logger.warn(message)


def log_error(message: str) -> None:
    """エラーメッセージ出力（後方互換性）。

    Args:
        message: 出力するメッセージ。
    """
    logger.error(message)


def log_step(message: str) -> None:
    """実行ステップ出力（後方互換性）。

    Args:
        message: 出力するメッセージ。
    """
    logger.step(message)


# ========================================
# 前提条件チェック機能
# ========================================

REQUIRED_COMMANDS: Iterable[str] = ("sf", "jq", "rsync")


def check_prerequisites(
    *,
    interactive: Optional[bool] = None,
    raise_on_error: bool = False,
) -> bool:
    """必要コマンドとプロジェクトファイルをチェックします。

    Args:
        interactive: 対話モードで実行するかどうか。None の場合は端末状態から推定。
        raise_on_error: True の場合、エラー時に :class:`typer.Exit` を送出します。

    Returns:
        bool: すべての前提条件を満たす場合は True、それ以外は False。
    """
    logger.step("前提条件チェック")

    interactive_mode = (
        interactive
        if interactive is not None
        else (sys.stdin.isatty() and sys.stdout.isatty())
    )

    errors: List[str] = []

    # 必要なコマンドの存在確認
    missing = [cmd for cmd in REQUIRED_COMMANDS if which(cmd) is None]
    if missing:
        errors.extend(f"{dep} がインストールされていません" for dep in missing)

    # プロジェクトファイルの確認
    sfdx_project_path = config.project_root / "sfdx-project.json"
    if not sfdx_project_path.exists():
        logger.warn("sfdx-project.json が見つかりません")

        if interactive_mode:
            try:
                if ui.confirm("基本的なsfdx-project.jsonを作成しますか？"):
                    try:
                        create_basic_sfdx_project()
                    except Exception as exc:  # pragma: no cover - 例外情報を補足
                        errors.append(f"sfdx-project.json の作成に失敗しました: {exc}")
                else:
                    errors.append("sfdx-project.json が必要です")
            except typer.Exit:
                errors.append("sfdx-project.json の作成がキャンセルされました")
        else:
            logger.warn("非対話環境のため自動作成をスキップします")

    success = not errors

    if success:
        logger.success("前提条件チェック完了")
        return True

    logger.error("前提条件エラー:")
    for error in errors:
        console.print(f"  - {error}")
    console.print()
    logger.info("セットアップ手順については documents/DEV_README.md を参照してください")

    if raise_on_error:
        raise typer.Exit(1)

    return False


def create_basic_sfdx_project() -> None:
    """基本的な sfdx-project.json を作成します。

    生成内容:
        - packageDirectories に "sanwa-mes-core" と "sanwa-mes" を登録
        - sanwa-mes がデフォルトかつ core に依存
        - sourceApiVersion などの基本項目
    """
    logger.step("基本的なsfdx-project.jsonの作成")

    sfdx_project = {
        "packageDirectories": [
            {"path": "sanwa-mes-core", "package": "sanwa-mes-core", "default": False},
            {
                "path": "sanwa-mes",
                "package": "sanwa-mes",
                "default": True,
                "dependencies": [{"package": "sanwa-mes-core"}],
            },
        ],
        "name": "sanwa-mes-development",
        "namespace": "",
        "sfdcLoginUrl": "https://login.salesforce.com",
        "sourceApiVersion": "63.0",
        "packageAliases": {},
    }

    sfdx_project_path = config.project_root / "sfdx-project.json"
    with open(sfdx_project_path, "w", encoding="utf-8") as f:
        json.dump(sfdx_project, f, indent=2, ensure_ascii=False)

    logger.success("基本的なsfdx-project.jsonを作成しました")


def check_dry_run(action: str) -> bool:
    """ドライラン実行の確認を行います。

    Args:
        action: 確認メッセージに表示する対象アクション名。

    Returns:
        bool: ユーザーが実行を選択した場合 True。
    """
    return ui.confirm(f"Dry run モードで実行しますか？ ({action})", default=False)
