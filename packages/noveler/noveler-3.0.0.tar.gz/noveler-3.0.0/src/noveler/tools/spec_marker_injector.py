"""Tools.spec_marker_injector
Where: Tool injecting specification markers into files.
What: Adds or updates spec references to keep documentation synchronized.
Why: Ensures code/spec linkage stays current.
"""

from noveler.presentation.shared.shared_utilities import console

"SPEC準拠マーカー自動注入ツール\n\n既存テストファイルへのSPECマーカー自動付与\nDDD準拠・テスト品質標準化対応\n"
import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.adapters.console_service_adapter import get_console_service
from noveler.infrastructure.adapters.logger_service_adapter import get_logger_service

try:
    from noveler.infrastructure.logging.unified_logger import get_logger

    logger = get_logger(__name__)
except ImportError:
    pass


@dataclass
class SpecInjectionResult:
    """SPEC注入結果"""

    processed_files: list[str]
    updated_files: list[str]
    total_specs_added: int
    errors: list[str]
    execution_time_seconds: float


class SpecMarkerInjector:
    """SPEC準拠マーカー注入器

    責務:
    - 既存テストファイルの解析
    - SPECマーカーの自動生成・注入
    - テスト関数の分類・命名規約準拠
    - バックアップとロールバック機能
    """

    def __init__(self, project_root: Path) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス
        """
        self.project_root = project_root
        self.tests_dir = project_root / "tests"
        self.logger_service = get_logger_service()
        self.spec_mapping = {
            "error": "EH",
            "plot": "PG",
            "quality": "QC",
            "message": "MS",
            "entity": "EN",
            "differential": "DU",
            "compatibility": "CA",
            "orchestrator": "OR",
            "service": "SV",
            "checker": "CH",
            "factory": "FC",
        }
        self.test_patterns = {
            "initialization": "test_init",
            "success_case": "test_.*_success",
            "failure_case": "test_.*_(fail|error)",
            "validation": "test_.*_validation",
            "integration": "test_.*_integration",
            "performance": "test_.*_performance",
            "security": "test_.*_security",
            "async_operation": "test_.*async",
            "batch_operation": "test_.*batch",
            "edge_case": "test_.*_edge",
        }

    def inject_spec_markers_batch(self, test_files: list[Path] | None = None) -> SpecInjectionResult:
        """SPEC マーカー一括注入

        Args:
            test_files: 対象テストファイル（Noneで全ファイル）

        Returns:
            SpecInjectionResult: 注入結果
        """
        start_time = project_now().datetime
        self.logger_service.info("SPEC マーカー一括注入開始")
        try:
            target_files = self._discover_test_files() if test_files is None else test_files
            self.logger_service.info(f"対象テストファイル数: {len(target_files)}")
            processed_files = []
            updated_files = []
            total_specs_added = 0
            errors = []
            for test_file in target_files:
                try:
                    result = self._process_test_file(test_file)
                    processed_files.append(str(test_file))
                    if result["updated"]:
                        updated_files.append(str(test_file))
                        total_specs_added += result["specs_added"]
                        self.logger_service.info(f"更新完了: {test_file} ({result['specs_added']} SPEC追加)")
                    else:
                        self.logger_service.debug(f"変更なし: {test_file}")
                except Exception as e:
                    error_msg = f"{test_file}: {e!s}"
                    errors.append(error_msg)
                    logger.exception("処理エラー: %s", error_msg)
            end_time = project_now().datetime
            execution_time = (end_time - start_time).total_seconds()
            result = SpecInjectionResult(
                processed_files=processed_files,
                updated_files=updated_files,
                total_specs_added=total_specs_added,
                errors=errors,
                execution_time_seconds=execution_time,
            )
            self.logger_service.info(f"SPEC マーカー注入完了: {len(updated_files)}/{len(processed_files)} ファイル更新")
            return result
        except Exception:
            logger.exception("一括注入エラー")
            raise

    def _discover_test_files(self) -> list[Path]:
        """テストファイル発見"""
        test_files = []
        for test_file in self.tests_dir.rglob("test_*.py"):
            if self._should_process_file(test_file):
                test_files.append(test_file)
        return sorted(test_files)

    def _should_process_file(self, file_path: Path) -> bool:
        """ファイル処理対象判定"""
        exclude_patterns = ["__pycache__", ".pyc", "conftest.py"]
        file_str = str(file_path)
        return not any(pattern in file_str for pattern in exclude_patterns)

    def _process_test_file(self, test_file: Path) -> dict[str, Any]:
        """テストファイル処理"""
        try:
            original_content = test_file.read_text(encoding="utf-8")
            if self._has_spec_markers(original_content):
                return {"updated": False, "specs_added": 0, "reason": "already_has_specs"}
            tree = ast.parse(original_content)
            test_functions = self._extract_test_functions(tree)
            if not test_functions:
                return {"updated": False, "specs_added": 0, "reason": "no_test_functions"}
            spec_prefix = self._generate_spec_prefix(test_file)
            spec_assignments = self._assign_spec_ids(test_functions, spec_prefix)
            updated_content = self._inject_spec_markers(original_content, spec_assignments)
            backup_path = self._create_backup(test_file, original_content)
            # バッチ書き込みを使用
            test_file.write_text(updated_content, encoding="utf-8")
            return {
                "updated": True,
                "specs_added": len(spec_assignments),
                "backup_path": str(backup_path),
                "spec_prefix": spec_prefix,
            }
        except Exception:
            logger.exception("ファイル処理エラー %s", test_file)
            raise

    def _has_spec_markers(self, content: str) -> bool:
        """既存SPECマーカー確認"""
        spec_pattern = "@pytest\\.mark\\.spec\\(|@mark\\.spec\\("
        return bool(re.search(spec_pattern, content))

    def _extract_test_functions(self, tree: ast.AST) -> list[dict[str, Any]]:
        """テスト関数抽出"""
        test_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                test_info = {
                    "name": node.name,
                    "lineno": node.lineno,
                    "is_async": False,
                    "docstring": ast.get_docstring(node),
                    "decorators": [d.id if hasattr(d, "id") else str(d) for d in node.decorator_list],
                }
                test_functions.append(test_info)
            elif isinstance(node, ast.AsyncFunctionDef) and node.name.startswith("test_"):
                test_info = {
                    "name": node.name,
                    "lineno": node.lineno,
                    "is_async": True,
                    "docstring": ast.get_docstring(node),
                    "decorators": [d.id if hasattr(d, "id") else str(d) for d in node.decorator_list],
                }
                test_functions.append(test_info)
        return sorted(test_functions, key=lambda x: x["lineno"])

    def _generate_spec_prefix(self, test_file: Path) -> str:
        """SPECプレフィックス生成"""
        file_name = test_file.stem
        clean_name = file_name.replace("test_", "")
        for keyword, prefix in self.spec_mapping.items():
            if keyword in clean_name.lower():
                return f"SPEC-{prefix}"
        parts = clean_name.split("_")
        abbreviation = "".join([part[0].upper() for part in parts if part])[:3]
        return f"SPEC-{abbreviation}"

    def _assign_spec_ids(self, test_functions: list[dict[str, Any]], spec_prefix: str) -> list[dict[str, Any]]:
        """SPEC ID 割り当て"""
        spec_assignments = []
        for i, func in enumerate(test_functions, 1):
            func_name = func["name"]
            test_category = self._classify_test_function(func_name)
            spec_id = f"{spec_prefix}-{i:03d}"
            spec_assignments.append(
                {
                    "function_name": func_name,
                    "lineno": func["lineno"],
                    "spec_id": spec_id,
                    "category": test_category,
                    "is_async": func["is_async"],
                    "existing_decorators": func["decorators"],
                }
            )
        return spec_assignments

    def _classify_test_function(self, func_name: str) -> str:
        """テスト関数分類"""
        for category, pattern in self.test_patterns.items():
            if re.search(pattern, func_name, re.IGNORECASE):
                return category
        return "general"

    def _inject_spec_markers(self, content: str, spec_assignments: list[dict[str, Any]]) -> str:
        """SPEC マーカー注入"""
        lines = content.split("\n")
        spec_assignments = sorted(spec_assignments, key=lambda x: x["lineno"], reverse=True)
        for assignment in spec_assignments:
            func_lineno = assignment["lineno"] - 1
            spec_marker = f"""    @mark.spec("{assignment["spec_id"]}")"""
            insert_line = func_lineno
            while insert_line > 0 and (
                lines[insert_line - 1].strip().startswith("@") or lines[insert_line - 1].strip() == ""
            ):
                insert_line -= 1
            if assignment["is_async"] and "@pytest.mark.asyncio" not in lines[insert_line:func_lineno]:
                lines.insert(insert_line, "    @pytest.mark.asyncio")
                insert_line += 1
            lines.insert(insert_line, spec_marker)
        updated_content = "\n".join(lines)
        if "@mark.spec(" in updated_content and "from pytest import mark" not in updated_content:
            updated_content = self._add_pytest_mark_import(updated_content)
        return updated_content

    def _add_pytest_mark_import(self, content: str) -> str:
        """pytest.mark import 追加"""
        lines = content.split("\n")
        import_section_end = 0
        for i, line in enumerate(lines):
            if line.startswith(("import ", "from ")):
                import_section_end = i
            elif line.strip() == "" and i > 0:
                continue
            elif not line.strip().startswith("#") and line.strip():
                break
        if import_section_end > 0:
            insert_position = import_section_end + 1
            pytest_import_exists = False
            for line in lines[: import_section_end + 1]:
                if "from pytest import" in line:
                    if "mark" not in line:
                        lines[lines.index(line)] = line.replace(
                            "from pytest import", "from pytest import mark,"
                        ).replace(",,", ",")
                    pytest_import_exists = True
                    break
            if not pytest_import_exists:
                lines.insert(insert_position, "from pytest import mark")
        return "\n".join(lines)

    def _create_backup(self, original_file: Path, content: str) -> Path:
        """バックアップファイル作成"""
        timestamp = project_now().datetime.strftime("%Y%m%d_%H%M%S")
        backup_dir = self.project_root / "temp" / "spec_injection_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        relative_path = original_file.relative_to(self.project_root)
        backup_name = f"{relative_path.stem}_{timestamp}{relative_path.suffix}"
        backup_path = backup_dir / backup_name
        # バッチ書き込みを使用
        backup_path.write_text(content, encoding="utf-8")
        return backup_path

    def validate_spec_injection(self, test_file: Path) -> dict[str, Any]:
        """SPEC注入結果検証"""
        try:
            content = test_file.read_text(encoding="utf-8")
            spec_markers = re.findall('@mark\\.spec\\("([^"]+)"\\)', content)
            test_functions = re.findall("def (test_\\w+)", content)
            duplicates = [spec for spec in set(spec_markers) if spec_markers.count(spec) > 1]
            invalid_specs = [spec for spec in spec_markers if not re.match("SPEC-\\w{2,3}-\\d{3}", spec)]
            return {
                "valid": len(duplicates) == 0 and len(invalid_specs) == 0,
                "total_specs": len(spec_markers),
                "total_tests": len(test_functions),
                "coverage_ratio": len(spec_markers) / len(test_functions) if test_functions else 0,
                "duplicates": duplicates,
                "invalid_formats": invalid_specs,
                "missing_specs": len(test_functions) - len(spec_markers),
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def rollback_spec_injection(self, backup_path: Path, target_file: Path) -> bool:
        """SPEC注入ロールバック"""
        try:
            if not backup_path.exists():
                self.logger_service.error(f"バックアップファイルが存在しません: {backup_path}")
                return False
            backup_content = backup_path.read_text(encoding="utf-8")

            # バッチ書き込みを使用
            target_file.write_text(backup_content, encoding="utf-8")
            self.logger_service.info(f"ロールバック完了: {target_file}")
            return True
        except Exception:
            logger.exception("ロールバックエラー")
            return False

    def generate_spec_report(self, result: SpecInjectionResult) -> str:
        """SPEC注入レポート生成"""
        report_lines = [
            "# SPEC準拠マーカー注入レポート",
            f"実行日時: {project_now().datetime.isoformat()}",
            "",
            "## 処理結果",
            f"- 処理ファイル数: {len(result.processed_files)}",
            f"- 更新ファイル数: {len(result.updated_files)}",
            f"- 追加SPEC数: {result.total_specs_added}",
            f"- 実行時間: {result.execution_time_seconds:.2f}秒",
            "",
        ]
        if result.updated_files:
            report_lines.extend(["## 更新されたファイル", ""])
            for file_path in result.updated_files:
                report_lines.append(f"- {file_path}")
            report_lines.append("")
        if result.errors:
            report_lines.extend(["## エラー", ""])
            for error in result.errors:
                report_lines.append(f"- {error}")
            report_lines.append("")
        report_lines.extend(
            [
                "## 推奨事項",
                "1. 生成されたSPECマーカーが適切かレビューする",
                "2. テスト実行してSPECマーカーが正常に動作するか確認する",
                "3. 必要に応じてSPEC IDを調整する",
                "4. バックアップファイルを適切に管理する",
            ]
        )
        return "\n".join(report_lines)


def main():
    """メイン実行"""
    get_console_service()
    parser = argparse.ArgumentParser(description="SPEC準拠マーカー自動注入ツール")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="プロジェクトルートディレクトリ")
    parser.add_argument("--files", nargs="*", type=Path, help="対象テストファイル（指定しない場合は全ファイル）")
    parser.add_argument("--validate", action="store_true", help="注入結果の検証のみ実行")
    parser.add_argument("--rollback", type=Path, help="指定バックアップからロールバック")
    parser.add_argument("--dry-run", action="store_true", help="実際の変更を行わずに確認のみ")
    parser.add_argument("--output-report", type=Path, help="レポート出力パス")
    args = parser.parse_args()
    try:
        injector = SpecMarkerInjector(args.project_root)
        if args.rollback:
            target_file = args.files[0] if args.files else None
            if not target_file:
                console.print("ロールバック対象ファイルを指定してください")
                return 1
            success = injector.rollback_spec_injection(args.rollback, target_file)
            return 0 if success else 1
        if args.validate:
            if not args.files:
                console.print("検証対象ファイルを指定してください")
                return 1
            for test_file in args.files:
                validation_result = injector.validate_spec_injection(test_file)
                console.print(f"\n📋 検証結果: {test_file}")
                for key, value in validation_result.items():
                    console.print(f"   {key}: {value}")
            return 0
        if args.dry_run:
            console.print("🔍 ドライランモード: 実際の変更は行いません")
            return 0
        result = injector.inject_spec_markers_batch(args.files)
        report = injector.generate_spec_report(result)
        if args.output_report:
            with Path(args.output_report).open("w", encoding="utf-8") as f:
                f.write(report)
            console.print(f"📝 レポート出力: {args.output_report}")
        else:
            console.print(report)
        console.print("\n🎉 SPEC注入完了!")
        console.print(f"📁 更新ファイル数: {len(result.updated_files)}")
        console.print(f"🏷️  追加SPEC数: {result.total_specs_added}")
        console.print(f"⏱️  実行時間: {result.execution_time_seconds:.2f}秒")
        if result.errors:
            console.print(f"⚠️  エラー数: {len(result.errors)}")
            return 1
        return 0
    except Exception:
        logger.exception("SPEC注入エラー")
        return 1


if __name__ == "__main__":
    sys.exit(main())
