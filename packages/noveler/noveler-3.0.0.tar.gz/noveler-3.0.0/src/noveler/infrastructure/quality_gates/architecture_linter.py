"""Infrastructure.quality_gates.architecture_linter
Where: Infrastructure quality gate checking architectural constraints.
What: Inspects imports and dependencies to enforce layering rules.
Why: Prevents architectural drift by catching violations early.
"""

from __future__ import annotations

from noveler.presentation.shared.shared_utilities import console

"\nアーキテクチャリンター: B20違反の自動検出システム\n\nこのモジュールはB20開発作業指示書に定義された\nアーキテクチャ原則の違反を自動検出します。\n"
import ast
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

import yaml


class ViolationSeverity(Enum):
    """違反の重要度レベル"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ArchitectureLayer(Enum):
    """アーキテクチャ層の定義"""

    DOMAIN = "domain"
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"
    PRESENTATION = "presentation"


@dataclass(frozen=True)
class ArchitectureViolation:
    """アーキテクチャ違反の詳細情報"""

    file_path: Path
    line_number: int
    violation_type: str
    severity: ViolationSeverity
    message: str
    rule_id: str
    suggested_fix: str | None = None


class ArchitectureLinter:
    """
    B20アーキテクチャ原則違反を検出するリンター

    検出対象:
    - レイヤー間の不適切な依存関係
    - 統合インポート管理システム違反
    - ハードコーディング違反
    - 3コミット開発サイクル違反
    - NIH症候群パターン検出
    """

    LAYER_DEPENDENCY_RULES: ClassVar[dict[ArchitectureLayer, set[ArchitectureLayer]]] = {
        ArchitectureLayer.DOMAIN: {ArchitectureLayer.DOMAIN},
        ArchitectureLayer.APPLICATION: {ArchitectureLayer.DOMAIN, ArchitectureLayer.APPLICATION},
        ArchitectureLayer.INFRASTRUCTURE: {ArchitectureLayer.DOMAIN, ArchitectureLayer.INFRASTRUCTURE},
        ArchitectureLayer.PRESENTATION: {
            ArchitectureLayer.DOMAIN,
            ArchitectureLayer.APPLICATION,
            ArchitectureLayer.INFRASTRUCTURE,
            ArchitectureLayer.PRESENTATION,
        },
    }
    FORBIDDEN_IMPORT_PATTERNS: ClassVar[list[dict[str, Any]]] = [
        {
            "pattern": "^from \\.",
            "severity": ViolationSeverity.ERROR,
            "rule_id": "ARCH-001",
            "message": "相対インポートは禁止です。noveler.プレフィックスを使用してください",
            "suggested_fix": "from noveler.domain.entities import ...",
        },
        {
            "pattern": "^from (?!scripts\\.)[\\w.]+",
            "severity": ViolationSeverity.ERROR,
            "rule_id": "ARCH-002",
            "message": "noveler.プレフィックスなしのインポートは禁止です",
            "suggested_fix": "from noveler.domain.entities import ...",
        },
        {
            "pattern": "from rich\\.console import Console",
            "severity": ViolationSeverity.ERROR,
            "rule_id": "ARCH-003",
            "message": "Console重複インスタンス化は禁止です。shared_utilitiesを使用してください",
            "suggested_fix": "# DDD準拠: Infrastructure→Presentation依存を除去\n# from noveler.presentation.shared.shared_utilities import console",
        },
    ]
    HARDCODING_PATTERNS: ClassVar[list[dict[str, Any]]] = [
        {
            "pattern": "Path\\(['\\\"].*?/(40_原稿|30_設定集|20_プロット)['\\\"]",
            "severity": ViolationSeverity.WARNING,
            "rule_id": "ARCH-004",
            "message": "ディレクトリパスのハードコーディングは禁止です。CommonPathServiceを使用してください",
            "suggested_fix": "path_service.get_manuscript_dir()",
        },
        {
            "pattern": "['\\\"]/(tmp|temp)/",
            "severity": ViolationSeverity.WARNING,
            "rule_id": "ARCH-005",
            "message": "一時ディレクトリのハードコーディングは推奨されません",
            "suggested_fix": "tempfile.mkdtemp()を使用",
        },
    ]

    def __init__(self, project_root: Path, logger_service=None, console_service=None) -> None:
        """
        Args:
            project_root: プロジェクトルートディレクトリ
        """
        self.project_root = project_root
        self.scripts_root = project_root / "scripts"
        self.violations: list[ArchitectureViolation] = []
        self.logger_service = logger_service
        self.console_service = console_service

    def lint_project(self) -> list[ArchitectureViolation]:
        """
        プロジェクト全体のアーキテクチャ違反を検出

        Returns:
            検出された違反のリスト
        """
        self.violations.clear()
        python_files = list(self.scripts_root.rglob("*.py"))
        for python_file in python_files:
            self._lint_file(python_file)
        return self.violations

    def _lint_file(self, file_path: Path) -> None:
        """
        単一ファイルの違反検出

        Args:
            file_path: 検査対象のPythonファイル
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                self.violations.append(
                    ArchitectureViolation(
                        file_path=file_path,
                        line_number=e.lineno or 1,
                        violation_type="syntax_error",
                        severity=ViolationSeverity.ERROR,
                        message=f"構文エラー: {e.msg}",
                        rule_id="ARCH-SYNTAX",
                    )
                )
                return
            self._check_import_violations(file_path, content)
            self._check_layer_dependencies(file_path, tree)
            self._check_hardcoding_violations(file_path, content)
            self._check_existing_api_duplication(file_path, content)
        except Exception as e:
            self.violations.append(
                ArchitectureViolation(
                    file_path=file_path,
                    line_number=1,
                    violation_type="file_error",
                    severity=ViolationSeverity.WARNING,
                    message=f"ファイル読み込みエラー: {e}",
                    rule_id="ARCH-FILE",
                )
            )

    def _check_import_violations(self, file_path: Path, content: str) -> None:
        """インポート違反の検出"""
        lines = content.split("\n")
        STANDARD_LIBRARY_MODULES = {
            "__future__",
            "abc",
            "argparse",
            "ast",
            "asyncio",
            "collections",
            "concurrent",
            "dataclasses",
            "datetime",
            "decimal",
            "enum",
            "functools",
            "itertools",
            "json",
            "logging",
            "os",
            "pathlib",
            "pprint",
            "re",
            "shutil",
            "sys",
            "tempfile",
            "time",
            "traceback",
            "typing",
            "unittest",
            "uuid",
            "warnings",
            "weakref",
            "xml",
            "yaml",
            "math",
            "pytest",
            "rich",
            "pydantic",
            "click",
            "jinja2",
            "ruamel",
        }
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            for pattern_rule in self.FORBIDDEN_IMPORT_PATTERNS:
                if re.match(pattern_rule["pattern"], line_stripped):
                    if pattern_rule["rule_id"] == "ARCH-002":
                        match = re.match("^from (\\w+(?:\\.\\w+)*) import", line_stripped)
                        if match:
                            module = match.group(1)
                            base_module = module.split(".")[0]
                            if base_module in STANDARD_LIBRARY_MODULES:
                                continue
                    self.violations.append(
                        ArchitectureViolation(
                            file_path=file_path,
                            line_number=i,
                            violation_type="import_violation",
                            severity=pattern_rule["severity"],
                            message=pattern_rule["message"],
                            rule_id=pattern_rule["rule_id"],
                            suggested_fix=pattern_rule["suggested_fix"],
                        )
                    )

    def _check_layer_dependencies(self, file_path: Path, tree: ast.AST) -> None:
        """レイヤー間依存関係の違反検出"""
        current_layer = self._determine_layer(file_path)
        if not current_layer:
            return
        for node in ast.walk(tree):
            if isinstance(node, ast.Import | ast.ImportFrom):
                imported_layer = self._extract_imported_layer(node)
                if imported_layer and (not self._is_dependency_allowed(current_layer, imported_layer)):
                    self.violations.append(
                        ArchitectureViolation(
                            file_path=file_path,
                            line_number=node.lineno,
                            violation_type="layer_dependency_violation",
                            severity=ViolationSeverity.ERROR,
                            message=f"{current_layer.value}層から{imported_layer.value}層への依存は禁止されています",
                            rule_id="ARCH-LAYER",
                            suggested_fix="アーキテクチャ依存関係を確認してください",
                        )
                    )

    def _check_hardcoding_violations(self, file_path: Path, content: str) -> None:
        """ハードコーディング違反の検出"""
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern_rule in self.HARDCODING_PATTERNS:
                if re.search(pattern_rule["pattern"], line):
                    self.violations.append(
                        ArchitectureViolation(
                            file_path=file_path,
                            line_number=i,
                            violation_type="hardcoding_violation",
                            severity=pattern_rule["severity"],
                            message=pattern_rule["message"],
                            rule_id=pattern_rule["rule_id"],
                            suggested_fix=pattern_rule["suggested_fix"],
                        )
                    )

    def _check_existing_api_duplication(self, file_path: Path, content: str) -> None:
        """
        既存API重複実装の検出（NIH症候群対策）

        共通的な機能パターンを検出し、既存実装の調査を促す
        """
        common_patterns = [
            {
                "pattern": "class \\w*Repository",
                "message": "新しいRepositoryクラスです。既存のRepositoryパターンを確認してください",
                "rule_id": "NIH-001",
            },
            {
                "pattern": "def create_\\w+\\(",
                "message": "createメソッドです。既存のFactoryパターンを確認してください",
                "rule_id": "NIH-002",
            },
            {
                "pattern": "class \\w*Manager",
                "message": "新しいManagerクラスです。既存の管理クラスを確認してください",
                "rule_id": "NIH-003",
            },
        ]
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern_rule in common_patterns:
                if re.search(pattern_rule["pattern"], line):
                    self.violations.append(
                        ArchitectureViolation(
                            file_path=file_path,
                            line_number=i,
                            violation_type="nih_syndrome_warning",
                            severity=ViolationSeverity.INFO,
                            message=pattern_rule["message"],
                            rule_id=pattern_rule["rule_id"],
                            suggested_fix="noveler/を検索して既存実装を確認してください",
                        )
                    )

    def _determine_layer(self, file_path: Path) -> ArchitectureLayer | None:
        """ファイルパスからアーキテクチャ層を判定"""
        relative_path = file_path.relative_to(self.scripts_root)
        path_parts = relative_path.parts
        if not path_parts:
            return None
        layer_name = path_parts[0]
        try:
            return ArchitectureLayer(layer_name)
        except ValueError:
            return None

    def _extract_imported_layer(self, node: ast.Import | ast.ImportFrom) -> ArchitectureLayer | None:
        """インポート文からインポート先の層を抽出"""
        if isinstance(node, ast.ImportFrom) and node.module:
            module_parts = node.module.split(".")
            if len(module_parts) >= 2 and module_parts[0] == "scripts":
                try:
                    return ArchitectureLayer(module_parts[1])
                except ValueError:
                    pass
        elif isinstance(node, ast.Import):
            for alias in node.names:
                module_parts = alias.name.split(".")
                if len(module_parts) >= 2 and module_parts[0] == "scripts":
                    try:
                        return ArchitectureLayer(module_parts[1])
                    except ValueError:
                        pass
        return None

    def _is_dependency_allowed(self, from_layer: ArchitectureLayer, to_layer: ArchitectureLayer) -> bool:
        """依存関係が許可されているかチェック"""
        allowed_dependencies = self.LAYER_DEPENDENCY_RULES.get(from_layer, set())
        return to_layer in allowed_dependencies

    def export_violations_yaml(self, output_path: Path) -> None:
        """違反結果をYAML形式でエクスポート"""
        violations_data: dict[str, Any] = {
            "metadata": {
                "project_root": str(self.project_root),
                "total_violations": len(self.violations),
                "severity_counts": {
                    "error": len([v for v in self.violations if v.severity == ViolationSeverity.ERROR]),
                    "warning": len([v for v in self.violations if v.severity == ViolationSeverity.WARNING]),
                    "info": len([v for v in self.violations if v.severity == ViolationSeverity.INFO]),
                },
            },
            "violations": [
                {
                    "file_path": str(v.file_path),
                    "line_number": v.line_number,
                    "violation_type": v.violation_type,
                    "severity": v.severity.value,
                    "message": v.message,
                    "rule_id": v.rule_id,
                    "suggested_fix": v.suggested_fix,
                }
                for v in self.violations
            ],
        }
        with output_path.Path("w").open(encoding="utf-8") as f:
            yaml.dump(violations_data, f, allow_unicode=True, sort_keys=False)


def main() -> None:
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="B20アーキテクチャ違反検出ツール")
    parser.add_argument("--project-root", type=Path, default=Path(), help="プロジェクトルートディレクトリ")
    parser.add_argument("--output", type=Path, default=Path("architecture_violations.yaml"), help="出力ファイルパス")
    parser.add_argument("--fail-on-error", action="store_true", help="エラーレベル違反がある場合に終了コード1で終了")
    args = parser.parse_args()
    linter = ArchitectureLinter(args.project_root)
    violations: Any = linter.lint_project()
    if violations:
        console.print(f"🔍 検出された違反: {len(violations)}件")
        error_count = len([v for v in violations if v.severity == ViolationSeverity.ERROR])
        warning_count = len([v for v in violations if v.severity == ViolationSeverity.WARNING])
        info_count = len([v for v in violations if v.severity == ViolationSeverity.INFO])
        console.print(f"  🔴 ERROR: {error_count}件")
        console.print(f"  🟡 WARNING: {warning_count}件")
        console.print(f"  🔵 INFO: {info_count}件")
        linter.export_violations_yaml(args.output)
        console.print(f"📄 結果をエクスポート: {args.output}")
        if args.fail_on_error and error_count > 0:
            sys.exit(1)
    else:
        console.print("✅ アーキテクチャ違反は検出されませんでした")


if __name__ == "__main__":
    main()
