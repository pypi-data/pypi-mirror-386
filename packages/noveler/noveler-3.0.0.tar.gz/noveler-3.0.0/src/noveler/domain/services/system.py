"""Domain.services.system
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

"システム診断ドメインサービス - Command Pattern適用\n\nDDD設計とCommand Patternを使用して複雑度を削減\n"
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class DiagnosticResult:
    """診断結果"""

    status: str
    details: dict[str, Any]
    messages: list[str]

    def __post_init__(self) -> None:
        if self.details is None:
            self.details = {}
        if self.messages is None:
            self.messages = []


class DiagnosticCommand(ABC):
    """診断コマンドのインターフェース"""

    @abstractmethod
    def execute(self) -> DiagnosticResult:
        """診断を実行"""

    @abstractmethod
    def get_name(self) -> str:
        """診断名を取得"""


class EnvironmentDiagnosticCommand(DiagnosticCommand):
    """環境チェック診断コマンド"""

    def __init__(self, quiet: bool = False) -> None:
        self.quiet = quiet

    def execute(self) -> DiagnosticResult:
        """環境チェックを実行"""
        details: dict[str, Any] = {}
        messages: list[str] = []
        if not self.quiet:
            messages.append("📋 環境チェック...")
        status = "OK"
        py_version = sys.version_info
        details["python_version"] = f"{py_version.major}.{py_version.minor}.{py_version.micro}"
        if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 6):
            status = "ERROR"
            messages.append("Python 3.6以上が必要です")
        env_vars = {
            "PROJECT_ROOT": os.environ.get("PROJECT_ROOT"),
            "GUIDE_ROOT": os.environ.get("GUIDE_ROOT"),
            "PYTHONPATH": os.environ.get("PYTHONPATH"),
            "NOVEL_CONFIG_HOME": os.environ.get("NOVEL_CONFIG_HOME"),
        }
        details["environment_variables"] = env_vars
        if not env_vars["PROJECT_ROOT"]:
            status = "WARNING" if status == "OK" else status
            messages.append("PROJECT_ROOT環境変数が設定されていません")
        if not env_vars["GUIDE_ROOT"]:
            status = "WARNING" if status == "OK" else status
            messages.append("GUIDE_ROOT環境変数が設定されていません")
        return DiagnosticResult(status=status, details=details, messages=messages)

    def get_name(self) -> str:
        return "environment"


class DependencyDiagnosticCommand(DiagnosticCommand):
    """依存関係チェック診断コマンド"""

    def __init__(self, quiet: bool = False) -> None:
        self.quiet = quiet

    def execute(self) -> DiagnosticResult:
        """依存関係チェックを実行"""
        details: dict[str, Any] = {"required_packages": {}, "optional_packages": {}}
        messages: list[str] = []
        if not self.quiet:
            messages.append("📦 依存関係チェック...")
        status = "OK"
        required_packages = {"pyyaml": "yaml", "requests": "requests", "janome": "janome"}
        optional_packages = {"beautifulsoup4": "bs4", "lxml": "lxml", "markdown": "markdown", "jinja2": "jinja2"}
        for package, import_name in required_packages.items():
            try:
                __import__(import_name)
                details["required_packages"][package] = "OK"
            except ImportError:
                status = "ERROR"
                details["required_packages"][package] = "Missing"
                messages.append(
                    f"📦 必要なプログラム '{package}' が見つかりません。インストールしてください:pip install {package}"
                )
        for package, import_name in optional_packages.items():
            try:
                __import__(import_name)
                details["optional_packages"][package] = "OK"
            except ImportError:
                details["optional_packages"][package] = "Missing"
                messages.append(f"💡 オプション機能 '{package}' が利用できません(基本機能には影響しません)")
        return DiagnosticResult(status=status, details=details, messages=messages)

    def get_name(self) -> str:
        return "dependencies"


class ProjectStructureDiagnosticCommand(DiagnosticCommand):
    """プロジェクト構造チェック診断コマンド"""

    def __init__(self, project_root: Path, quiet: bool = False) -> None:
        self.project_root = project_root
        self.quiet = quiet

    def execute(self) -> DiagnosticResult:
        """プロジェクト構造チェックを実行"""
        details: dict[str, Any] = {}
        messages: list[str] = []
        if not self.quiet:
            messages.append("📁 プロジェクト構造チェック...")
        status = "OK"
        if self.project_root and self.project_root.exists():
            required_paths = [
                self.project_root / "manuscripts",
                self.project_root / "50_管理資料",
                self.project_root / "prompts",
            ]
            missing_dirs = [dir_path.name for dir_path in required_paths if not dir_path.exists()]
            if missing_dirs:
                status = "WARNING"
                messages.append(f"必須ディレクトリが不足: {', '.join(missing_dirs)}")
            details["missing_directories"] = missing_dirs
            details["project_root"] = str(self.project_root)
            if not (self.project_root / "プロジェクト設定.yaml").exists():
                status = "ERROR"
                messages.append("プロジェクト設定.yamlが見つかりません")
        else:
            status = "WARNING"
            messages.append("プロジェクトが見つかりません")
            details["project_root"] = "Not found"
        return DiagnosticResult(status=status, details=details, messages=messages)

    def get_name(self) -> str:
        return "project_structure"


class SystemDiagnosticsService:
    """システム診断ドメインサービス - Command Patternコーディネーター"""

    def __init__(self) -> None:
        self.commands: list[DiagnosticCommand] = []

    def add_command(self, command: DiagnosticCommand) -> None:
        """診断コマンドを追加"""
        self.commands.append(command)

    def execute_all(self) -> dict[str, DiagnosticResult]:
        """すべての診断コマンドを実行"""
        results: dict[str, Any] = {}
        for command in self.commands:
            try:
                result = command.execute()
                results[command.get_name()] = result
            except Exception as e:
                results[command.get_name()] = DiagnosticResult(
                    status="ERROR", details={"error": str(e)}, messages=[f"診断実行エラー: {e}"]
                )
        return results

    def determine_overall_status(self, results: dict[str, DiagnosticResult]) -> str:
        """全体ステータスを決定"""
        has_error = any(result.status == "ERROR" for result in results.values())
        has_warning = any(result.status == "WARNING" for result in results.values())
        if has_error:
            return "ERROR"
        if has_warning:
            return "WARNING"
        return "OK"
