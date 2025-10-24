from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table

from ...core.common import Logger, console, logger, sf_cli


class ConvertDeployOps:
    """Source→MDAPI変換とDeploy（Dry/Real）操作"""

    def convert_source(
        self,
        *,
        source_dir: Path,
        output_dir: Path,
        package_name: str,
    ) -> Path:
        """Run `sf project convert source` and report success."""
        if not source_dir.is_dir():
            raise FileNotFoundError(f"source ディレクトリがありません: {source_dir}")

        if output_dir.exists():
            # UI側で確認する前提だが、ここでは上書き
            pass

        Logger.step("convert 実行")
        result = sf_cli.run_command(
            [
                "sf",
                "project",
                "convert",
                "source",
                "--root-dir",
                str(source_dir),
                "--output-dir",
                str(output_dir),
                "--package-name",
                package_name,
            ],
            capture_output=True,
            check=True,
        )
        if result.returncode != 0:
            raise RuntimeError("convert に失敗しました")
        logger.success(f"変換完了: {output_dir}")
        return output_dir

    def deploy(
        self,
        *,
        source_dir: Path,
        target_org: str,
        run_tests: str = "RunLocalTests",
        dry_run: bool = False,
    ) -> None:
        """Execute deploy/dry-run via the sf CLI and render formatted results."""
        deploy_sources = []
        if source_dir.is_dir():
            deploy_sources.append(str(source_dir))
            logger.info(
                f"source ディレクトリ {source_dir} と force-app の両方を Deploy 対象にします。"
            )
        else:
            logger.warn(
                f"org-config で指定された source ディレクトリが見つかりませんでした: {source_dir}\n"
                "force-app のみを対象に Deploy (Dry Run) を実行します。必要に応じて sourceDir を準備してください。"
            )
        deploy_sources.append("force-app")

        Logger.step("deploy 実行")
        args = [
            "sf",
            "project",
            "deploy",
            "start",
            "--source-dir",
            *deploy_sources,
            "--target-org",
            target_org,
            "--test-level",
            run_tests,
            "--json",
        ]
        if dry_run:
            args.append("--dry-run")

        status_label = (
            f"Dry Run: {target_org}" if dry_run else f"Deploying to {target_org}"
        )

        result = sf_cli.run_command(
            args,
            capture_output=True,
            check=False,
            status_message=status_label,
        )

        payload = self._parse_json_payload(result.stdout)
        deploy_result = payload.get("result", payload)
        success = bool(deploy_result.get("success", result.returncode == 0))

        if not success or result.returncode != 0:
            self._render_deploy_failure(deploy_result)
            raise RuntimeError("deploy に失敗しました")

        self._render_deploy_success(deploy_result, dry_run=dry_run)
        logger.success("deploy 完了")

    # ---- Rendering helpers ----
    def _parse_json_payload(self, raw: str) -> Dict[str, Any]:
        """Return parsed JSON output; log and fallback to {} on errors."""
        if not raw:
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error(f"JSON出力の解析に失敗しました: {exc}")
            return {}
        if not isinstance(data, dict):
            logger.error("JSON出力が辞書形式ではありません。")
            return {}
        return data

    def _render_deploy_success(self, result: Dict[str, Any], *, dry_run: bool) -> None:
        """Pretty-print the successful deploy summary, tests, coverage, files."""
        summary = Table(
            title="Deploy Summary", show_header=False, box=box.SIMPLE, pad_edge=True
        )
        status_text = result.get("status") or (
            "Succeeded" if result.get("success") else "Unknown"
        )
        status_style = "green" if result.get("success") else "red"
        summary.add_row(
            "Mode", "[cyan]Dry Run[/cyan]" if dry_run else "[cyan]Deploy[/cyan]"
        )
        summary.add_row("Status", f"[{status_style}]{status_text}[/{status_style}]")
        deployed = result.get("numberComponentsDeployed", 0)
        total_components = result.get("numberComponentsTotal", 0)
        component_ratio = f"[magenta]{deployed}/{total_components}[/magenta]"
        summary.add_row(
            "Components",
            component_ratio,
        )
        if result.get("numberTestsTotal") is not None:
            completed = result.get("numberTestsCompleted", 0)
            tests_total = result.get("numberTestsTotal", 0)
            tests_ratio = f"[magenta]{completed}/{tests_total}[/magenta]"
            summary.add_row(
                "Tests",
                tests_ratio,
            )
        if result.get("deployUrl"):
            summary.add_row("Deploy URL", f"[blue]{result['deployUrl']}[/blue]")
        console.print(summary)

        details = result.get("details", {}) or {}
        run_tests = details.get("runTestResult", {}) or {}
        panels: List[Any] = []
        tests_panel = self._build_test_panel(run_tests)
        if tests_panel is not None:
            panels.append(tests_panel)
        coverage_panel = self._build_coverage_panel(run_tests)
        if coverage_panel is not None:
            panels.append(coverage_panel)
        files_panel = self._build_files_panel(result.get("files", []) or [])
        if files_panel is not None:
            panels.append(files_panel)

        if panels:
            console.print(Group(*panels))

    def _render_deploy_failure(self, result: Dict[str, Any]) -> None:
        """Show key failure metrics along with component/test errors."""
        summary = Table(title="Deploy Failed", show_header=False, box=box.SIMPLE)
        summary.add_row("Status", result.get("status", "Failed"))
        summary.add_row(
            "Component Errors", str(result.get("numberComponentErrors", "-"))
        )
        summary.add_row("Test Errors", str(result.get("numberTestErrors", "-")))
        console.print(summary)

        details = result.get("details", {}) or {}
        failures = (
            details.get("componentFailures") or result.get("componentFailures") or []
        )
        if failures:
            table = Table(title="Component Failures", box=box.SIMPLE)
            table.add_column("Component")
            table.add_column("Type")
            table.add_column("Problem")
            for failure in failures[:10]:
                table.add_row(
                    failure.get("fullName", ""),
                    failure.get("componentType", failure.get("type", "")),
                    failure.get("problem", ""),
                )
            if len(failures) > 10:
                table.caption = f"Showing first 10 of {len(failures)} failures"
            console.print(table)

        run_tests = details.get("runTestResult", {}) or {}
        failures_table = self._build_test_failures_table(run_tests)
        if failures_table is not None:
            console.print(failures_table)

    def _build_test_panel(self, run_tests: Dict[str, Any]) -> Optional[Panel]:
        """Compose the overall test results panel, including failures/slow tests."""
        if not run_tests:
            return None

        summary = Table(show_header=False, box=box.MINIMAL_DOUBLE_HEAD)
        executed = run_tests.get("numTestsRun", run_tests.get("totalTests", 0))
        executed_text = f"[magenta]{executed}[/magenta]"
        summary.add_row(
            "Tests Run",
            executed_text,
        )
        failures_count = len(run_tests.get("failures", []))
        failure_style = "red" if failures_count else "green"
        summary.add_row(
            "Failures", f"[{failure_style}]{failures_count}[/{failure_style}]"
        )
        total_time = run_tests.get("totalTime")
        if total_time is not None:
            summary.add_row("Total Time (ms)", f"[yellow]{total_time}[/yellow]")

        failures_table = self._build_test_failures_table(run_tests)
        slow_table = self._build_slow_tests_table(run_tests)
        items: List[Any] = [summary]
        if failures_table is not None:
            items.append(failures_table)
        if slow_table is not None:
            items.append(slow_table)
        return Panel(Group(*items), title="Test Results", box=box.ROUNDED)

    def _build_test_failures_table(self, run_tests: Dict[str, Any]) -> Optional[Table]:
        """Render a failures table limited to the first 10 failing tests."""
        failures = run_tests.get("failures") or []
        if not failures:
            return None
        table = Table(title="Failures", box=box.SIMPLE, header_style="bold red")
        table.add_column("Class")
        table.add_column("Method")
        table.add_column("Message")
        for failure in failures[:10]:
            table.add_row(
                failure.get("name", ""),
                failure.get("methodName", ""),
                failure.get("message", ""),
            )
        if len(failures) > 10:
            table.caption = f"Showing first 10 of {len(failures)} failures"
        return table

    def _build_slow_tests_table(self, run_tests: Dict[str, Any]) -> Optional[Table]:
        """Highlight the slowest Apex tests so users can inspect hot spots."""
        tests = run_tests.get("tests") or []
        if not tests:
            return None
        sorted_tests = sorted(tests, key=lambda item: item.get("time", 0), reverse=True)
        top = sorted_tests[:5]
        if not top:
            return None
        table = Table(title="Slowest Tests", box=box.SIMPLE, header_style="bold yellow")
        table.add_column("Class")
        table.add_column("Method")
        table.add_column("Time (ms)", justify="right")
        for test in top:
            table.add_row(
                test.get("name", ""),
                test.get("methodName", ""),
                str(test.get("time", 0)),
            )
        return table

    def _build_coverage_panel(self, run_tests: Dict[str, Any]) -> Optional[Panel]:
        """Display all coverage entries with color-coded percentages."""
        coverages = run_tests.get("codeCoverage") or []
        if not coverages:
            return None

        table = Table(title="Code Coverage", box=box.SIMPLE, header_style="bold cyan")
        table.add_column("Name")
        table.add_column("Covered %", justify="right")
        table.add_column("Uncovered Lines")

        sorted_coverages = sorted(
            coverages,
            key=lambda item: item.get("numLocationsNotCovered", 0),
            reverse=True,
        )

        for entry in sorted_coverages:
            total = entry.get("numLocations", 0) or 0
            uncovered = entry.get("numLocationsNotCovered", 0) or 0
            covered = total - uncovered if total else 0
            percent = int(round((covered / total) * 100)) if total else 0
            lines = entry.get("lineNotCovered", []) or []
            if lines:
                preview = ",".join(str(x) for x in lines[:10])
                if len(lines) > 10:
                    preview += ",..."
            else:
                preview = ""
            color = "green" if percent >= 90 else "yellow" if percent >= 75 else "red"
            table.add_row(
                entry.get("name", ""), f"[{color}]{percent}%[/{color}]", preview
            )

        return Panel(table, title="Coverage", box=box.ROUNDED, border_style="cyan")

    def _build_files_panel(self, files: List[Dict[str, Any]]) -> Optional[Panel]:
        """List changed artifacts included in the deploy payload."""
        if not files:
            return None
        table = Table(title="Changed Files", box=box.SIMPLE)
        table.add_column("State")
        table.add_column("Type")
        table.add_column("Name")
        table.add_column("Path")
        for item in files[:10]:
            table.add_row(
                item.get("state", ""),
                item.get("type", ""),
                item.get("fullName", ""),
                item.get("filePath", ""),
            )
        if len(files) > 10:
            table.caption = f"Showing first 10 of {len(files)} files"
        return Panel(table, title="Files", box=box.ROUNDED)
