"""Tools.ddd_violation_fixer
Where: Tool that fixes detected DDD violations automatically.
What: Applies safe rewrites to resolve layered architecture issues.
Why: Reduces effort needed to maintain DDD compliance.
"""

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from noveler.presentation.shared.shared_utilities import console

"DDD違反自動修正ツール\n\nDDD準拠性違反の自動検出・修正\nアーキテクチャ品質向上対応\n"

from noveler.domain.value_objects.project_time import project_now

try:
    from noveler.infrastructure.logging.unified_logger import get_logger

    logger = get_logger(__name__)
except ImportError:
    pass


@dataclass
class DDDViolation:
    """DDD違反情報"""

    file_path: Path
    line_number: int
    violation_type: str
    severity: str
    description: str
    current_code: str
    suggested_fix: str
    confidence: float


@dataclass
class FixResult:
    """修正結果"""

    violations_fixed: list[DDDViolation]
    violations_skipped: list[DDDViolation]
    errors: list[str]
    backup_created: bool
    execution_time_seconds: float


class DDDViolationFixer:
    """DDD違反自動修正器

    責務:
    - DDD違反パターンの自動検出
    - TYPE_CHECKING パターン適用
    - 依存性注入パターン修正
    - レイヤー分離違反修正
    """

    def __init__(self, project_root: Path) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス
        """
        self.project_root = project_root
        self.scripts_dir = project_root / "scripts"
        self.violation_patterns = {
            "domain_infrastructure_dependency": {
                "pattern": "from noveler\\.infrastructure\\.",
                "severity": "high",
                "fix_method": "apply_type_checking_pattern",
            },
            "missing_dependency_injection": {
                "pattern": "def __init__\\(self[^)]*\\):",
                "severity": "medium",
                "fix_method": "add_dependency_injection",
            },
            "direct_concrete_dependency": {
                "pattern": "from noveler\\.infrastructure\\..*import.*Service",
                "severity": "high",
                "fix_method": "replace_with_interface",
            },
            "circular_import": {
                "pattern": "import.*scripts\\..*",
                "severity": "critical",
                "fix_method": "apply_lazy_import",
            },
        }
        self.layer_dependencies = {
            "domain": [],
            "application": ["domain"],
            "infrastructure": ["domain", "application"],
            "presentation": ["application"],
        }

    def fix_violations_batch(self, target_files: list[Path] | None = None) -> FixResult:
        """DDD違反一括修正

        Args:
            target_files: 対象ファイル（Noneで全ファイル）

        Returns:
            FixResult: 修正結果
        """
        start_time = project_now().datetime
        self.logger_service.info("DDD違反一括修正開始")
        try:
            if target_files is None:
                target_files = self._discover_python_files()
            self.logger_service.info(f"対象ファイル数: {len(target_files)}")
            all_violations = []
            for file_path in target_files:
                violations = self._detect_violations(file_path)
                all_violations.extend(violations)
            self.logger_service.info(f"検出された違反数: {len(all_violations)}")
            violations_fixed = []
            violations_skipped = []
            errors = []
            backup_created = False
            for violation in all_violations:
                try:
                    if violation.confidence >= 0.8:
                        success = self._apply_fix(violation)
                        if success:
                            violations_fixed.append(violation)
                            if not backup_created:
                                self._create_backup_snapshot()
                                backup_created = True
                        else:
                            violations_skipped.append(violation)
                    else:
                        violations_skipped.append(violation)
                except Exception as e:
                    error_msg = f"{violation.file_path}:{violation.line_number} - {e!s}"
                    errors.append(error_msg)
                    logger.exception("修正エラー: %s", error_msg)
            end_time = project_now().datetime
            execution_time = (end_time - start_time).total_seconds()
            result = FixResult(
                violations_fixed=violations_fixed,
                violations_skipped=violations_skipped,
                errors=errors,
                backup_created=backup_created,
                execution_time_seconds=execution_time,
            )
            self.logger_service.info(
                f"DDD違反修正完了: {len(violations_fixed)}件修正、{len(violations_skipped)}件スキップ"
            )
            return result
        except Exception:
            logger.exception("一括修正エラー")
            raise

    def _discover_python_files(self) -> list[Path]:
        """Python ファイル発見"""
        python_files = []
        for py_file in self.scripts_dir.rglob("*.py"):
            if self._should_process_file(py_file):
                python_files.append(py_file)
        return sorted(python_files)

    def _should_process_file(self, file_path: Path) -> bool:
        """ファイル処理対象判定"""
        exclude_patterns = ["__pycache__", ".pyc", "__init__.py", "migrations/", "temp/"]
        file_str = str(file_path)
        return not any(pattern in file_str for pattern in exclude_patterns)

    def _detect_violations(self, file_path: Path) -> list[DDDViolation]:
        """DDD違反検出"""
        violations = []
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            layer_violations = self._detect_layer_violations(file_path, lines)
            violations.extend(layer_violations)
            di_violations = self._detect_dependency_injection_violations(file_path, lines)
            violations.extend(di_violations)
            type_check_violations = self._detect_type_checking_violations(file_path, lines)
            violations.extend(type_check_violations)
            circular_violations = self._detect_circular_imports(file_path, lines)
            violations.extend(circular_violations)
        except Exception as e:
            self.logger_service.warning(f"違反検出エラー {file_path}: {e}")
        return violations

    def _detect_layer_violations(self, file_path: Path, lines: list[str]) -> list[DDDViolation]:
        """レイヤー違反検出"""
        violations = []
        current_layer = self._determine_layer(file_path)
        if not current_layer:
            return violations
        self.layer_dependencies.get(current_layer, [])
        for line_num, line in enumerate(lines, 1):
            import_match = re.match("from noveler\\.(\\w+)\\.", line.strip())
            if import_match:
                imported_layer = import_match.group(1)
                if current_layer == "domain" and imported_layer in ["infrastructure", "application", "presentation"]:
                    violation = DDDViolation(
                        file_path=file_path,
                        line_number=line_num,
                        violation_type="domain_infrastructure_dependency",
                        severity="high",
                        description=f"ドメイン層から{imported_layer}層への不正な依存",
                        current_code=line.strip(),
                        suggested_fix=self._generate_type_checking_fix(line.strip()),
                        confidence=0.9,
                    )
                    violations.append(violation)
                elif current_layer == "application" and imported_layer == "infrastructure":
                    if "interface" not in line.lower():
                        violation = DDDViolation(
                            file_path=file_path,
                            line_number=line_num,
                            violation_type="direct_concrete_dependency",
                            severity="medium",
                            description="アプリケーション層から具象実装への直接依存",
                            current_code=line.strip(),
                            suggested_fix=self._generate_interface_fix(line.strip()),
                            confidence=0.8,
                        )
                        violations.append(violation)
        return violations

    def _detect_dependency_injection_violations(self, file_path: Path, lines: list[str]) -> list[DDDViolation]:
        """依存性注入違反検出"""
        violations = []
        in_class = False
        class_name = None
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            class_match = re.match("class (\\w+)", stripped)
            if class_match:
                in_class = True
                class_name = class_match.group(1)
                continue
            if in_class and stripped.startswith("def __init__("):
                if (
                    ("Service" in class_name or "Orchestrator" in class_name)
                    and "self" in stripped
                    and (len(stripped.split(",")) == 1)
                ):
                    violation = DDDViolation(
                        file_path=file_path,
                        line_number=line_num,
                        violation_type="missing_dependency_injection",
                        severity="medium",
                        description=f"{class_name}で依存性注入パターンが不足",
                        current_code=stripped,
                        suggested_fix=self._generate_di_fix(stripped, class_name),
                        confidence=0.7,
                    )
                    violations.append(violation)
        return violations

    def _detect_type_checking_violations(self, file_path: Path, lines: list[str]) -> list[DDDViolation]:
        """TYPE_CHECKING違反検出"""
        violations = []
        if "domain" in str(file_path):
            has_type_checking = any("TYPE_CHECKING" in line for line in lines)
            for line_num, line in enumerate(lines, 1):
                if re.match("from noveler\\.infrastructure\\.", line.strip()):
                    if not has_type_checking:
                        violation = DDDViolation(
                            file_path=file_path,
                            line_number=line_num,
                            violation_type="missing_type_checking",
                            severity="high",
                            description="ドメイン層でTYPE_CHECKINGパターンが必要",
                            current_code=line.strip(),
                            suggested_fix=self._generate_type_checking_block(line.strip()),
                            confidence=0.95,
                        )
                        violations.append(violation)
        return violations

    def _detect_circular_imports(self, file_path: Path, lines: list[str]) -> list[DDDViolation]:
        """循環インポート検出"""
        return []

    def _determine_layer(self, file_path: Path) -> str | None:
        """ファイルのレイヤー判定"""
        path_str = str(file_path)
        if "noveler/domain/" in path_str:
            return "domain"
        if "noveler/application/" in path_str:
            return "application"
        if "noveler/infrastructure/" in path_str:
            return "infrastructure"
        if "noveler/presentation/" in path_str:
            return "presentation"
        return None

    def _apply_fix(self, violation: DDDViolation) -> bool:
        """修正適用"""
        try:
            with violation.file_path.open(encoding="utf-8") as f:
                content = f.read()
            content.split("\n")
            if violation.violation_type == "domain_infrastructure_dependency":
                updated_content = self._apply_type_checking_pattern(content, violation)
            elif violation.violation_type == "missing_dependency_injection":
                updated_content = self._add_dependency_injection(content, violation)
            elif violation.violation_type == "direct_concrete_dependency":
                updated_content = self._replace_with_interface(content, violation)
            else:
                return False
            with violation.file_path.open("w", encoding="utf-8") as f:
                f.write(updated_content)
            self.logger_service.info(f"修正適用: {violation.file_path}:{violation.line_number}")
            return True
        except Exception:
            logger.exception("修正適用エラー %s", violation.file_path)
            return False

    def _apply_type_checking_pattern(self, content: str, violation: DDDViolation) -> str:
        """TYPE_CHECKING パターン適用"""
        lines = content.split("\n")
        if "from typing import TYPE_CHECKING" not in content:
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.startswith(("from typing import", "import typing")):
                    lines[i] = line.replace("from typing import", "from typing import TYPE_CHECKING,").replace(
                        ",,", ","
                    )
                    break
                if line.startswith(("import ", "from ")):
                    insert_pos = i + 1
            else:
                lines.insert(insert_pos, "from typing import TYPE_CHECKING")
        target_line_num = violation.line_number - 1
        if target_line_num < len(lines):
            import_line = lines[target_line_num]
            type_check_block_start = -1
            for i, line in enumerate(lines):
                if "if TYPE_CHECKING:" in line:
                    type_check_block_start = i
                    break
            if type_check_block_start == -1:
                lines.insert(insert_pos + 1, "")
                lines.insert(insert_pos + 2, "if TYPE_CHECKING:")
                lines.insert(insert_pos + 3, f"    {import_line}")
                type_check_block_start = insert_pos + 2
            else:
                lines.insert(type_check_block_start + 1, f"    {import_line}")
            if target_line_num < type_check_block_start:
                lines.pop(target_line_num)
            else:
                lines.pop(target_line_num + 1)
        return "\n".join(lines)

    def _add_dependency_injection(self, content: str, violation: DDDViolation) -> str:
        """依存性注入追加"""
        lines = content.split("\n")
        return "\n".join(lines)

    def _replace_with_interface(self, content: str, violation: DDDViolation) -> str:
        """インターフェース置換"""
        lines = content.split("\n")
        target_line_num = violation.line_number - 1
        if target_line_num < len(lines):
            current_line = lines[target_line_num]
            if "Service" in current_line:
                updated_line = current_line.replace("Service", "IService")
                updated_line = updated_line.replace("infrastructure.services", "domain.interfaces")
                lines[target_line_num] = updated_line
        return "\n".join(lines)

    def _generate_type_checking_fix(self, current_code: str) -> str:
        """TYPE_CHECKING 修正案生成"""
        return f"from typing import TYPE_CHECKING\n\nif TYPE_CHECKING:\n    {current_code}"

    def _generate_interface_fix(self, current_code: str) -> str:
        """インターフェース修正案生成"""
        fixed = current_code.replace("infrastructure.services", "domain.interfaces")
        return fixed.replace("Service", "IService")

    def _generate_di_fix(self, current_code: str, class_name: str) -> str:
        """依存性注入修正案生成"""
        return 'def __init__(self, dependency_service: IDependencyService, logger: ILogger = None):\n    """初期化\n\n    Args:\n        dependency_service: 依存サービス\n        logger: ロガー（オプション）\n    """\n    self.dependency_service = dependency_service\n    self._logger = logger'

    def _generate_type_checking_block(self, import_line: str) -> str:
        """TYPE_CHECKING ブロック生成"""
        return f"from typing import TYPE_CHECKING\n\nif TYPE_CHECKING:\n    {import_line}"

    def _create_backup_snapshot(self) -> Path:
        """バックアップスナップショット作成"""
        timestamp = project_now().datetime.strftime("%Y%m%d_%H%M%S")
        backup_dir = self.project_root / "temp" / "ddd_fix_backups" / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)

        shutil.copytree(self.scripts_dir, backup_dir / "scripts")
        self.logger_service.info(f"バックアップ作成完了: {backup_dir}")
        return backup_dir

    def generate_fix_report(self, result: FixResult) -> str:
        """修正レポート生成"""
        report_lines = [
            "# DDD違反自動修正レポート",
            f"実行日時: {project_now().datetime.isoformat()}",
            "",
            "## 修正結果",
            f"- 修正された違反: {len(result.violations_fixed)}件",
            f"- スキップされた違反: {len(result.violations_skipped)}件",
            f"- エラー: {len(result.errors)}件",
            f"- 実行時間: {result.execution_time_seconds:.2f}秒",
            f"- バックアップ作成: {('Yes' if result.backup_created else 'No')}",
            "",
        ]
        if result.violations_fixed:
            report_lines.extend(["## 修正された違反", ""])
            for violation in result.violations_fixed:
                report_lines.extend(
                    [
                        f"### {violation.file_path}:{violation.line_number}",
                        f"- タイプ: {violation.violation_type}",
                        f"- 重要度: {violation.severity}",
                        f"- 説明: {violation.description}",
                        f"- 信頼度: {violation.confidence:.2f}",
                        "",
                    ]
                )
        if result.violations_skipped:
            report_lines.extend(["## スキップされた違反（手動修正推奨）", ""])
            for violation in result.violations_skipped[:10]:
                report_lines.extend(
                    [
                        f"### {violation.file_path}:{violation.line_number}",
                        f"- タイプ: {violation.violation_type}",
                        f"- 説明: {violation.description}",
                        f"- 推奨修正: {violation.suggested_fix}",
                        "",
                    ]
                )
        if result.errors:
            report_lines.extend(["## エラー", ""])
            for error in result.errors:
                report_lines.append(f"- {error}")
            report_lines.append("")
        report_lines.extend(
            [
                "## 推奨事項",
                "1. 修正内容をレビューし、テストを実行する",
                "2. スキップされた違反を手動で修正する",
                "3. DDD準拠性チェックツールで検証する",
                "4. 必要に応じてバックアップから復元する",
            ]
        )
        return "\n".join(report_lines)


def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(description="DDD違反自動修正ツール")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="プロジェクトルートディレクトリ")
    parser.add_argument("--files", nargs="*", type=Path, help="対象ファイル（指定しない場合は全ファイル）")
    parser.add_argument("--dry-run", action="store_true", help="実際の修正を行わずに違反検出のみ")
    parser.add_argument("--confidence-threshold", type=float, default=0.8, help="自動修正を実行する信頼度の閾値")
    parser.add_argument("--output-report", type=Path, help="レポート出力パス")
    args = parser.parse_args()
    try:
        from noveler.infrastructure.adapters.console_service_adapter import get_console_service  # noqa: PLC0415

        get_console_service()
        fixer = DDDViolationFixer(args.project_root)
        if args.dry_run:
            console.print("🔍 ドライランモード: 違反検出のみ実行")
            target_files = args.files or fixer._discover_python_files()
            all_violations = []
            for file_path in target_files:
                violations = fixer._detect_violations(file_path)
                all_violations.extend(violations)
            console.print(f"\n📋 検出された違反数: {len(all_violations)}")
            severity_counts = {}
            for violation in all_violations:
                severity_counts[violation.severity] = severity_counts.get(violation.severity, 0) + 1
            for severity, count in severity_counts.items():
                console.print(f"   {severity}: {count}件")
            return 0
        result = fixer.fix_violations_batch(args.files)
        report = fixer.generate_fix_report(result)
        if args.output_report:
            with Path(args.output_report).open("w", encoding="utf-8") as f:
                f.write(report)
            console.print(f"📝 レポート出力: {args.output_report}")
        else:
            console.print(report)
        console.print("\n🎉 DDD違反修正完了!")
        console.print(f"✅ 修正完了: {len(result.violations_fixed)}件")
        console.print(f"⏭️  スキップ: {len(result.violations_skipped)}件")
        console.print(f"⏱️  実行時間: {result.execution_time_seconds:.2f}秒")
        if result.errors:
            console.print(f"⚠️  エラー数: {len(result.errors)}")
            return 1
        return 0
    except Exception:
        logger.exception("DDD違反修正エラー")
        return 1


if __name__ == "__main__":
    sys.exit(main())
