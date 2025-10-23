"""Domain.services.system_diagnostic_services
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import stat
import subprocess

from noveler.domain.value_objects.project_time import project_now


class _DiagnosticOutputMixin:
    """Utility mixin to collect diagnostic messages in the result payload."""

    @staticmethod
    def _add_info(results: dict, message: str) -> None:
        results.setdefault("info", []).append(message)


class DependencyDiagnosticService(_DiagnosticOutputMixin):
    """依存関係診断専用サービス"""

    def check_dependencies(self, results: dict, quiet: bool = False) -> None:
        """依存関係のチェック"""
        if not quiet:
            self._add_info(results, "📦 依存関係チェック...")
        deps_check = {"status": "OK", "details": {}}
        import sys

        deps_check["details"]["python_version"] = (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
        required_packages = ["typer", "pyyaml", "pathlib"]
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                deps_check["details"][f"package_{package}"] = "Available"
            except ImportError:
                deps_check["details"][f"package_{package}"] = "Missing"
                missing_packages.append(package)
        if missing_packages:
            deps_check["status"] = "ERROR"
            results["errors"].append(f"必須パッケージが不足: {', '.join(missing_packages)}")
        results["checks"]["dependencies"] = deps_check


class ConfigurationDiagnosticService(_DiagnosticOutputMixin):
    """設定診断専用サービス"""

    def __init__(self, guide_root: Path, project_root: Path | None = None) -> None:
        self.guide_root = guide_root
        self.project_root = project_root

    def check_configurations(self, results: dict, quiet: bool = False) -> None:
        """設定ファイルのチェック"""
        if not quiet:
            self._add_info(results, "⚙️ 設定チェック...")
        config_check = {"status": "OK", "details": {}}
        global_config_path = Path.home() / ".novel" / "config.yaml"
        if global_config_path.exists():
            config_check["details"]["global_config"] = "Found"
        else:
            config_check["details"]["global_config"] = "Not found"
            config_check["status"] = "WARNING"
            results["warnings"].append("グローバル設定ファイルが見つかりません")
        if self.project_root:
            project_config: dict[str, Any] = self.project_root / "プロジェクト設定.yaml"
            if project_config.exists():
                config_check["details"]["project_config"] = "Found"
            else:
                config_check["details"]["project_config"] = "Not found"
                results["warnings"].append("プロジェクト設定ファイルが見つかりません")
        results["checks"]["configurations"] = config_check


class ScriptDiagnosticService(_DiagnosticOutputMixin):
    """スクリプト診断専用サービス"""

    def __init__(self, guide_root: Path) -> None:
        self.guide_root = guide_root

    def check_scripts(self, results: dict, quiet: bool = False) -> None:
        """スクリプトファイルのチェック"""
        if not quiet:
            self._add_info(results, "📜 スクリプトチェック...")
        scripts_check = {"status": "OK", "details": {}}
        scripts_dir = self.guide_root / "scripts"
        if not scripts_dir.exists():
            scripts_check["status"] = "ERROR"
            scripts_check["details"]["scripts_directory"] = "Missing"
            results["errors"].append("scriptsディレクトリが見つかりません")
        else:
            scripts_check["details"]["scripts_directory"] = "Found"
            main_scripts = ["presentation/__main__.py", "presentation/cli/main.py", "presentation/cli/commands/"]
            missing_scripts = []
            for script_path in main_scripts:
                full_path = scripts_dir / script_path
                if full_path.exists():
                    scripts_check["details"][f"script_{script_path}"] = "Found"
                else:
                    scripts_check["details"][f"script_{script_path}"] = "Missing"
                    missing_scripts.append(script_path)
            if missing_scripts:
                scripts_check["status"] = "WARNING"
                results["warnings"].extend(
                    [f"スクリプトファイルが見つかりません: {script}" for script in missing_scripts]
                )
        results["checks"]["scripts"] = scripts_check


class TemplateDiagnosticService(_DiagnosticOutputMixin):
    """テンプレート診断専用サービス"""

    def __init__(self, guide_root: Path) -> None:
        self.guide_root = guide_root

    def check_templates(self, results: dict, quiet: bool = False) -> None:
        """テンプレートファイルのチェック"""
        if not quiet:
            self._add_info(results, "📄 テンプレートチェック...")
        templates_check = {"status": "OK", "details": {}}
        templates_dir = self.guide_root / "templates"
        if not templates_dir.exists():
            templates_check["status"] = "WARNING"
            templates_check["details"]["templates_directory"] = "Missing"
            results["warnings"].append("templatesディレクトリが見つかりません")
        else:
            templates_check["details"]["templates_directory"] = "Found"
            template_files = list(templates_dir.rglob("*.yaml")) + list(templates_dir.rglob("*.md"))
            templates_check["details"]["template_count"] = len(template_files)
            if len(template_files) == 0:
                templates_check["status"] = "WARNING"
                results["warnings"].append("テンプレートファイルが見つかりません")
        results["checks"]["templates"] = templates_check


class PermissionDiagnosticService(_DiagnosticOutputMixin):
    """権限診断専用サービス"""

    def __init__(self, guide_root: Path) -> None:
        self.guide_root = guide_root

    def check_permissions(self, results: dict, quiet: bool = False) -> None:
        """ファイル権限のチェック"""
        if not quiet:
            self._add_info(results, "🔐 権限チェック...")
        perms_check = {"status": "OK", "details": {}}
        executable_files = [self.guide_root / "bin" / "novel"]
        permission_issues = []
        for exe_file in executable_files:
            if exe_file.exists():
                is_executable = exe_file.stat().st_mode & stat.S_IEXEC
                if is_executable:
                    perms_check["details"][f"executable_{exe_file.name}"] = "OK"
                else:
                    perms_check["details"][f"executable_{exe_file.name}"] = "No execute permission"
                    permission_issues.append(str(exe_file))
            else:
                perms_check["details"][f"executable_{exe_file.name}"] = "Missing"
        if permission_issues:
            perms_check["status"] = "WARNING"
            results["warnings"].extend([f"実行権限がありません: {file}" for file in permission_issues])
        results["checks"]["permissions"] = perms_check


class GitDiagnosticService(_DiagnosticOutputMixin):
    """Git診断専用サービス"""

    def __init__(self, guide_root: Path) -> None:
        self.guide_root = guide_root

    def check_git_status(self, results: dict, quiet: bool = False) -> None:
        """Gitステータスのチェック"""
        if not quiet:
            self._add_info(results, "🌿 Gitステータスチェック...")
        git_check = {"status": "OK", "details": {}}
        git_dir = self.guide_root / ".git"
        if not git_dir.exists():
            git_check["status"] = "WARNING"
            git_check["details"]["git_repository"] = "Not a git repository"
            results["warnings"].append("Gitリポジトリではありません")
        else:
            git_check["details"]["git_repository"] = "Found"
            try:
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    check=False,
                    cwd=self.guide_root,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    modified_files = [line for line in result.stdout.strip().split("\n") if line.strip()]
                    git_check["details"]["modified_files_count"] = len(modified_files)
                    if len(modified_files) > 10:
                        git_check["status"] = "WARNING"
                        results["warnings"].append(f"多数の変更ファイルがあります: {len(modified_files)}件")
                else:
                    git_check["details"]["git_status"] = "Error getting status"
                    results["warnings"].append("Gitステータスの取得に失敗")
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
                git_check["details"]["git_status"] = f"Error: {e!s}"
                results["warnings"].append(f"Gitコマンドの実行に失敗: {e}")
        results["checks"]["git"] = git_check


class DiagnosticReportService:
    """診断レポート生成専用サービス"""

    def generate_text_report(self, results: dict, overall_status: str) -> str:
        """テキスト形式のレポートを生成"""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("🏥 小説執筆支援システム診断レポート")
        report_lines.append("=" * 80)
        report_lines.append(f"📅 実行日時: {results.get('timestamp', project_now().to_iso_string())}")
        report_lines.append(f"📊 総合ステータス: {overall_status}")
        report_lines.append("")
        checks = results.get("checks", {})
        for check_name, check_data in checks.items():
            status = check_data.get("status", "UNKNOWN")
            status_icon = "✅" if status == "OK" else "⚠️" if status == "WARNING" else "❌"
            report_lines.append(f"{status_icon} {check_name.upper()}: {status}")
            details: Any = check_data.get("details", {})
            for detail_key, detail_value in details.items():
                report_lines.append(f"   - {detail_key}: {detail_value}")
            report_lines.append("")
        errors: Any = results.get("errors", [])
        if errors:
            report_lines.append("❌ エラー:")
            for error in errors:
                report_lines.append(f"   • {error}")
            report_lines.append("")
        warnings = results.get("warnings", [])
        if warnings:
            report_lines.append("⚠️ 警告:")
            for warning in warnings:
                report_lines.append(f"   • {warning}")
            report_lines.append("")
        info = results.get("info", [])
        if info:
            report_lines.append("ℹ️ 情報:")
            for info_item in info:
                report_lines.append(f"   • {info_item}")
            report_lines.append("")
        report_lines.append("=" * 80)
        return "\n".join(report_lines)

    def save_results_to_file(
        self, output_file: Path, results: dict, overall_status: str, output_format: str = "json"
    ) -> None:
        """結果をファイルに保存"""
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            if output_format == "json":
                import json

                output_data: dict[str, Any] = {
                    "overall_status": overall_status,
                    "timestamp": results.get("timestamp"),
                    "checks": results.get("checks", {}),
                    "errors": results.get("errors", []),
                    "warnings": results.get("warnings", []),
                    "info": results.get("info", []),
                }
                with output_file.open("w", encoding="utf-8") as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
            elif output_format == "text":
                report_content = self.generate_text_report(results, overall_status)
                # バッチ書き込みを使用
                output_file.write_text(report_content, encoding="utf-8")
        except Exception as e:
            msg = f"ファイル保存に失敗: {e}"
            raise Exception(msg)
