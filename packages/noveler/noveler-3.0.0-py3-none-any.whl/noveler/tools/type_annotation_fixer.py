"""Tools.type_annotation_fixer
Where: Tool that fixes type annotations.
What: Updates code to match required type annotation standards.
Why: Keeps the codebase consistent with typing expectations.
"""

import argparse
import ast
import json
import re
import shutil
import sys
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from noveler.presentation.shared.shared_utilities import console

'型アノテーション自動修正ツール\n\nPython ASTを使用してPythonファイルの型アノテーションを自動で追加・修正する。\nmypy エラー 4918件の段階的解決を目標とする。\n\n重要: domain services を最優先対象とする。\n- system_diagnostics.py (missing "details" variable annotation)\n- scene_validator.py (missing return type annotations)\n- dependency_analysis.py (missing "violations" variable annotation)\n'

from noveler.domain.value_objects.project_time import project_now


class FixPriority(Enum):
    """修正優先度"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TypeAnnotationConfig:
    """型アノテーション修正設定"""

    project_root: Path
    source_patterns: list[str] = None
    backup_enabled: bool = True
    backup_suffix: str = ".bak"
    priority_patterns: dict[str, FixPriority] = None
    max_fixes_per_file: int = 50
    include_return_types: bool = True
    include_variable_annotations: bool = True
    include_parameter_annotations: bool = True
    dry_run: bool = False

    def __post_init__(self):
        if self.source_patterns is None:
            self.source_patterns = ["src/noveler/**", "src/noveler/tools/**"]
        if self.priority_patterns is None:
            self.priority_patterns = {
                "noveler/domain/services/**": FixPriority.CRITICAL,
                "noveler/domain/**": FixPriority.HIGH,
                "noveler/application/**": FixPriority.HIGH,
                "noveler/infrastructure/**": FixPriority.MEDIUM,
                "noveler/presentation/**": FixPriority.MEDIUM,
            }


@dataclass
class FileFixInfo:
    """ファイル修正情報"""

    file_path: Path
    priority: FixPriority
    missing_parameter_annotations: list[str]
    missing_return_annotations: list[str]
    missing_variable_annotations: list[str]
    complexity_score: int
    estimated_fix_time: int


@dataclass
class FixResult:
    """修正結果"""

    file_path: Path
    success: bool
    fixes_applied: int
    backup_path: Path | None
    errors: list[str]
    execution_time_seconds: float


@dataclass
class TypeAnnotationFixResult:
    """型アノテーション修正総合結果"""

    processed_files: list[str]
    fixed_files: list[str]
    skipped_files: list[str]
    backup_files: list[str]
    errors: list[str]
    total_fixes_applied: int
    execution_time_seconds: float
    quality_metrics: dict[str, Any]


class TypeInferenceEngine:
    """型推論エンジン

    ASTを解析して適切な型アノテーションを推論する
    """

    def __init__(self) -> None:
        self.common_types = {
            "str": "str",
            "int": "int",
            "float": "float",
            "bool": "bool",
            "None": "None",
            "list": "List[Any]",
            "dict": "Dict[str, Any]",
            "set": "Set[Any]",
            "tuple": "Tuple[Any, ...]",
            "Path": "Path",
            "pathlib.Path": "Path",
            "Episode": "Episode",
            "QualityCheckSession": "QualityCheckSession",
            "Plot": "Plot",
            "Scene": "Scene",
            "Character": "Character",
            "Project": "Project",
        }
        self.pattern_mappings = {
            ".*_id$": "str",
            ".*_count$": "int",
            ".*_size$": "int",
            ".*_path$": "Path",
            ".*_paths$": "List[Path]",
            ".*_config$": "Dict[str, Any]",
            ".*_result$": "Dict[str, Any]",
            ".*_results$": "List[Dict[str, Any]]",
            ".*_data$": "Dict[str, Any]",
            ".*_info$": "Dict[str, Any]",
            ".*_details$": "Dict[str, Any]",
            ".*_violations$": "List[str]",
            ".*_errors$": "List[str]",
            ".*_messages$": "List[str]",
        }

    def infer_variable_type(self, var_name: str, assignment_node: ast.AST) -> str:
        """変数の型を推論"""
        for pattern, type_hint in self.pattern_mappings.items():
            if re.match(pattern, var_name):
                return type_hint
        if isinstance(assignment_node, ast.Constant):
            value_type = type(assignment_node.value).__name__
            return self.common_types.get(value_type, "Any")
        if isinstance(assignment_node, ast.List):
            if assignment_node.elts:
                first_element = assignment_node.elts[0]
                element_type = self.infer_variable_type("temp", first_element)
                if element_type != "Any":
                    return f"List[{element_type}]"
                if "errors" in var_name or "messages" in var_name or "warnings" in var_name:
                    return "List[str]"
                if "results" in var_name or "items" in var_name:
                    return "List[Dict[str, Any]]"
                if "violations" in var_name:
                    return "List[str]"
            return "List[Any]"
        if isinstance(assignment_node, ast.Dict):
            if (
                "config" in var_name
                or "settings" in var_name
                or "options" in var_name
                or ("results" in var_name)
                or ("details" in var_name)
            ):
                return "Dict[str, Any]"
            return "Dict[str, Any]"
        if isinstance(assignment_node, ast.Set):
            return "Set[Any]"
        if isinstance(assignment_node, ast.Call):
            func_name = self._get_function_name(assignment_node.func)
            if func_name in ["list", "dict", "set", "tuple"]:
                base_type = self.common_types.get(func_name, "Any")
                if func_name == "list":
                    if "errors" in var_name or "messages" in var_name:
                        return "List[str]"
                    if "results" in var_name:
                        return "List[Dict[str, Any]]"
                return base_type
            if func_name == "Path":
                return "Path"
        return "Any"

    def infer_parameter_type(self, param_name: str, default_value: ast.AST | None = None) -> str:
        """パラメータの型を推論"""
        for pattern, type_hint in self.pattern_mappings.items():
            if re.match(pattern, param_name):
                return type_hint
        if default_value:
            if isinstance(default_value, ast.Constant):
                if default_value.value is None:
                    return "Optional[Any]"
                value_type = type(default_value.value).__name__
                base_type = self.common_types.get(value_type, "Any")
                return f"Optional[{base_type}]" if base_type != "None" else "Optional[Any]"
        if param_name in ["path", "file_path", "directory", "target_path", "source_path"]:
            return "Path"
        if param_name in ["config", "settings", "options"]:
            return "Dict[str, Any]"
        if param_name.endswith(("_list", "_items")):
            return "List[Any]"
        if param_name.endswith(("_dict", "_map")):
            return "Dict[str, Any]"
        return "Any"

    def infer_return_type(self, function_node: ast.FunctionDef) -> str:
        """関数の戻り値型を推論"""
        if function_node.name == "__init__":
            return "None"
        return_statements = []
        for node in ast.walk(function_node):
            if isinstance(node, ast.Return) and node.value:
                return_statements.append(node.value)
        if not return_statements:
            return "None"
        first_return = return_statements[0]
        if isinstance(first_return, ast.Constant):
            if first_return.value is None:
                return "None"
            value_type = type(first_return.value).__name__
            return self.common_types.get(value_type, "Any")
        if isinstance(first_return, ast.List):
            return "List[Any]"
        if isinstance(first_return, ast.Dict):
            return "Dict[str, Any]"
        if isinstance(first_return, ast.Set):
            return "Set[Any]"
        if isinstance(first_return, ast.Tuple):
            return "Tuple[Any, ...]"
        func_name = function_node.name
        for pattern, type_hint in self.pattern_mappings.items():
            if re.match(pattern, func_name):
                return type_hint
        if func_name.startswith("get_"):
            return "Any"
        if func_name.startswith(("is_", "has_", "validate_", "check_")):
            return "bool"
        if func_name.startswith("create_"):
            return "Any"
        return "Any"

    def _get_function_name(self, node: ast.AST) -> str:
        """関数名を取得"""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return ""


class TypeAnnotationFixer:
    """型アノテーション自動修正器

    責務:
    - Pythonファイルの型アノテーション不足箇所の検出
    - 適切な型アノテーションの自動推論・追加
    - バックアップ・ロールバック機能
    - 進捗レポート生成
    """

    def __init__(self, config: TypeAnnotationConfig) -> None:
        """初期化

        Args:
            config: 型アノテーション修正設定
        """
        self.config = config
        self.project_root = config.project_root
        self.type_engine = TypeInferenceEngine()
        self.fixed_count = 0

    def fix_annotations_batch(self, target_files: list[str] | None = None) -> TypeAnnotationFixResult:
        """一括型アノテーション修正実行

        Args:
            target_files: 対象ファイルリスト（None で全対象）

        Returns:
            TypeAnnotationFixResult: 修正結果
        """
        start_time = project_now().datetime
        self.logger_service.info("一括型アノテーション修正開始")
        try:
            if target_files is None:
                target_file_infos = self._discover_files_needing_fixes()
            else:
                target_file_infos = self._analyze_specified_files(target_files)
            self.logger_service.info(f"対象ファイル数: {len(target_file_infos)}")
            target_file_infos.sort(key=lambda x: (x.priority.value, -x.complexity_score))
            processed_files = []
            fixed_files = []
            skipped_files = []
            backup_files = []
            errors = []
            total_fixes = 0
            for file_info in target_file_infos:
                try:
                    result = self._fix_file_annotations(file_info)
                    processed_files.append(str(file_info.file_path))
                    if result.success:
                        fixed_files.append(str(file_info.file_path))
                        total_fixes += result.fixes_applied
                        if result.backup_path:
                            backup_files.append(str(result.backup_path))
                        self.logger_service.info(f"修正完了: {file_info.file_path} ({result.fixes_applied} fixes)")
                    else:
                        skipped_files.append(str(file_info.file_path))
                        errors.extend(result.errors)
                except Exception as e:
                    errors.append(f"{file_info.file_path}: {e!s}")
                    console.print(f"修正エラー {file_info.file_path}: {e}")
            quality_metrics = self._calculate_quality_metrics(fixed_files, total_fixes)
            end_time = project_now().datetime
            execution_time = (end_time - start_time).total_seconds()
            result = TypeAnnotationFixResult(
                processed_files=processed_files,
                fixed_files=fixed_files,
                skipped_files=skipped_files,
                backup_files=backup_files,
                errors=errors,
                total_fixes_applied=total_fixes,
                execution_time_seconds=execution_time,
                quality_metrics=quality_metrics,
            )
            self.logger_service.info(f"一括型アノテーション修正完了: {len(fixed_files)}ファイル、{total_fixes}箇所修正")
            return result
        except Exception as e:
            console.print(f"一括型アノテーション修正エラー: {e}")
            raise

    def _discover_files_needing_fixes(self) -> list[FileFixInfo]:
        """修正が必要なファイルを発見"""
        file_infos = []
        for pattern in self.config.source_patterns:
            if pattern.startswith("!"):
                continue
            for source_file in self.project_root.rglob(pattern):
                if self._should_skip_file(source_file):
                    continue
                file_info = self._analyze_file_for_fixes(source_file)
                if self._needs_fixing(file_info):
                    file_infos.append(file_info)
        return file_infos

    def _analyze_specified_files(self, file_paths: list[str]) -> list[FileFixInfo]:
        """指定されたファイルを解析"""
        file_infos = []
        for file_path in file_paths:
            path_obj = Path(file_path)
            if path_obj.exists():
                file_info = self._analyze_file_for_fixes(path_obj)
                file_infos.append(file_info)
        return file_infos

    def _analyze_file_for_fixes(self, file_path: Path) -> FileFixInfo:
        """ファイルの修正箇所を解析"""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            missing_parameter_annotations = []
            missing_return_annotations = []
            missing_variable_annotations = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for arg in node.args.args:
                        if not arg.annotation and arg.arg != "self":
                            missing_parameter_annotations.append(f"{node.name}.{arg.arg}")
                    if not node.returns and node.name != "__init__":
                        missing_return_annotations.append(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            if var_name in [
                                "details",
                                "violations",
                                "results",
                                "errors",
                                "messages",
                            ] or var_name.endswith(("_data", "_config")):
                                missing_variable_annotations.append(var_name)
            priority = self._determine_file_priority(file_path)
            complexity_score = self._calculate_file_complexity(tree)
            total_missing = (
                len(missing_parameter_annotations) + len(missing_return_annotations) + len(missing_variable_annotations)
            )
            estimated_time = min(total_missing * 10, 300)
            return FileFixInfo(
                file_path=file_path,
                priority=priority,
                missing_parameter_annotations=missing_parameter_annotations,
                missing_return_annotations=missing_return_annotations,
                missing_variable_annotations=missing_variable_annotations,
                complexity_score=complexity_score,
                estimated_fix_time=estimated_time,
            )
        except Exception as e:
            self.logger_service.warning(f"ファイル解析エラー {file_path}: {e}")
            return FileFixInfo(
                file_path=file_path,
                priority=FixPriority.LOW,
                missing_parameter_annotations=[],
                missing_return_annotations=[],
                missing_variable_annotations=[],
                complexity_score=0,
                estimated_fix_time=0,
            )

    def _fix_file_annotations(self, file_info: FileFixInfo) -> FixResult:
        """ファイルの型アノテーションを修正"""
        start_time = project_now().datetime
        try:
            with file_info.file_path.open(encoding="utf-8") as f:
                original_content = f.read()
            backup_path = None
            if self.config.backup_enabled:
                backup_path = self._create_backup(file_info.file_path, original_content)
            if self.config.dry_run:
                self.logger_service.info(
                    f"DRY RUN: {file_info.file_path} (would fix {len(file_info.missing_parameter_annotations + file_info.missing_return_annotations + file_info.missing_variable_annotations)} annotations)"
                )
                return FixResult(
                    file_path=file_info.file_path,
                    success=True,
                    fixes_applied=0,
                    backup_path=backup_path,
                    errors=[],
                    execution_time_seconds=0,
                )
            ast.parse(original_content)
            modified_content = self._apply_string_based_annotations(original_content, file_info)
            fixes_applied = (
                len(file_info.missing_parameter_annotations)
                + len(file_info.missing_return_annotations)
                + len(file_info.missing_variable_annotations)
            )
            with file_info.file_path.open("w", encoding="utf-8") as f:
                f.write(modified_content)
            end_time = project_now().datetime
            execution_time = (end_time - start_time).total_seconds()
            return FixResult(
                file_path=file_info.file_path,
                success=True,
                fixes_applied=fixes_applied,
                backup_path=backup_path,
                errors=[],
                execution_time_seconds=execution_time,
            )
        except Exception as e:
            end_time = project_now().datetime
            execution_time = (end_time - start_time).total_seconds()
            return FixResult(
                file_path=file_info.file_path,
                success=False,
                fixes_applied=0,
                backup_path=backup_path,
                errors=[str(e)],
                execution_time_seconds=execution_time,
            )

    def _apply_string_based_annotations(self, content: str, file_info: FileFixInfo) -> str:
        """文字列ベースで型アノテーションを適用"""
        lines = content.split("\n")
        modified_lines = lines.copy()
        modified_lines = self._add_typing_imports_to_lines(modified_lines)
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in file_info.missing_return_annotations:
                return_type = self.type_engine.infer_return_type(node)
                line_num = node.lineno - 1
                found_colon = False
                search_line = line_num
                while search_line < len(modified_lines) and (not found_colon):
                    line = modified_lines[search_line]
                    if ":" in line and "->" not in line:
                        if "):" in line:
                            modified_lines[search_line] = line.replace("):", f") -> {return_type}:")
                            found_colon = True
                        elif line.strip().endswith(":"):
                            modified_lines[search_line] = line.replace(":", f" -> {return_type}:")
                            found_colon = True
                    search_line += 1
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in file_info.missing_variable_annotations:
                        var_name = target.id
                        inferred_type = self.type_engine.infer_variable_type(var_name, node.value)
                        line_num = node.lineno - 1
                        if line_num < len(modified_lines):
                            line = modified_lines[line_num]
                            if "=" in line and ":" not in line.split("=")[0]:
                                parts = line.split("=", 1)
                                if len(parts) == 2:
                                    var_part = parts[0].strip()
                                    value_part = parts[1]
                                    if var_part == var_name:
                                        indent = len(line) - len(line.lstrip())
                                        indent_str = " " * indent
                                        modified_lines[line_num] = (
                                            f"{indent_str}{var_name}: {inferred_type} ={value_part}"
                                        )
        return "\n".join(modified_lines)

    def _add_typing_imports_to_lines(self, lines: list[str]) -> list[str]:
        """必要なtyping importを行に追加"""
        has_typing_import = False
        import_line_index = -1
        for i, line in enumerate(lines):
            if "from typing import" in line:
                has_typing_import = True
                current_imports = line.replace("from typing import", "").strip()
                needed_types = {"List", "Dict", "Set", "Tuple", "Optional", "Any"}
                existing_imports = set()
                for imp in current_imports.split(","):
                    existing_imports.add(imp.strip())
                missing_imports = needed_types - existing_imports
                if missing_imports:
                    all_imports = existing_imports | needed_types
                    lines[i] = f"from typing import {', '.join(sorted(all_imports))}"
                break
            if line.startswith(("import ", "from ")):
                if import_line_index == -1:
                    import_line_index = i
        if not has_typing_import:
            insert_position = 0
            for i, line in enumerate(lines):
                if line.startswith("from __future__"):
                    insert_position = i + 1
                    continue
                if line.startswith("#!") or line.strip().startswith('"""') or line.strip().startswith("'''"):
                    continue
                if line.startswith(("import ", "from ")) and (not line.startswith("from __future__")):
                    insert_position = i
                    break
                if line.strip() == "":
                    continue
                insert_position = i
                break
            lines.insert(insert_position, "from typing import List, Dict, Set, Tuple, Optional, Any")
            if insert_position + 1 < len(lines) and lines[insert_position + 1].strip():
                lines.insert(insert_position + 1, "")
        return lines

    def _determine_file_priority(self, file_path: Path) -> FixPriority:
        """ファイルの修正優先度を決定"""
        file_str = str(file_path)
        for pattern, priority in self.config.priority_patterns.items():
            pattern_path = pattern.replace("**", "*")
            if Path(file_str).match(pattern_path):
                return priority
        return FixPriority.LOW

    def _calculate_file_complexity(self, tree: ast.AST) -> int:
        """ファイルの複雑度スコアを計算"""
        score = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                score += 2
            elif isinstance(node, ast.ClassDef):
                score += 3
            elif isinstance(node, ast.If | ast.While | ast.For | ast.Try):
                score += 1
        return score

    def _needs_fixing(self, file_info: FileFixInfo) -> bool:
        """修正が必要かどうか判定"""
        total_missing = (
            len(file_info.missing_parameter_annotations)
            + len(file_info.missing_return_annotations)
            + len(file_info.missing_variable_annotations)
        )
        return total_missing > 0

    def _should_skip_file(self, file_path: Path) -> bool:
        """ファイルスキップ判定"""
        skip_patterns = ["__pycache__", "__init__.py", "test_", ".pyc", "migrations/"]
        for pattern in self.config.source_patterns:
            if pattern.startswith("!") and file_path.match(pattern[1:]):
                return True
        file_str = str(file_path)
        return any(pattern in file_str for pattern in skip_patterns)

    def _create_backup(self, file_path: Path, content: str) -> Path:
        """バックアップファイル作成"""
        timestamp = project_now().datetime.strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f"{self.config.backup_suffix}_{timestamp}")
        # バッチ書き込みを使用
        backup_path.write_text(content, encoding="utf-8")
        return backup_path

    def _calculate_quality_metrics(self, fixed_files: list[str], total_fixes: int) -> dict[str, Any]:
        """品質メトリクス計算"""
        return {
            "files_fixed": len(fixed_files),
            "total_annotations_added": total_fixes,
            "average_fixes_per_file": total_fixes / len(fixed_files) if fixed_files else 0,
            "mypy_compliance_improvement_estimate": total_fixes * 0.2,
            "type_safety_improvement": len(fixed_files) * 10,
        }

    def rollback_changes(self, backup_files: list[str]) -> dict[str, Any]:
        """変更をロールバック"""
        results = {"success_count": 0, "failure_count": 0, "errors": []}
        for backup_path_str in backup_files:
            try:
                backup_path = Path(backup_path_str)
                original_path = Path(str(backup_path).replace(self.config.backup_suffix, "").split("_")[0] + ".py")
                if backup_path.exists():
                    shutil.copy2(backup_path, original_path)
                    results["success_count"] += 1
                    self.logger_service.info(f"ロールバック完了: {original_path}")
                else:
                    results["errors"].append(f"バックアップファイルが見つかりません: {backup_path}")
                    results["failure_count"] += 1
            except Exception as e:
                results["errors"].append(f"ロールバックエラー {backup_path_str}: {e!s}")
                results["failure_count"] += 1
                console.print(f"ロールバックエラー {backup_path_str}: {e}")
        return results

    def export_fix_report(self, result: TypeAnnotationFixResult, output_path: Path | None = None) -> None:
        """修正レポートをエクスポート"""
        if output_path is None:
            output_path = self.project_root / "temp" / "type_annotation_fix_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report_data = {
            "fix_timestamp": project_now().datetime.isoformat(),
            "configuration": asdict(self.config),
            "results": asdict(result),
            "recommendations": self._generate_recommendations(result),
        }
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        self.logger_service.info(f"修正レポートをエクスポート: {output_path}")

    def _generate_recommendations(self, result: TypeAnnotationFixResult) -> list[str]:
        """改善推奨事項生成"""
        recommendations = []
        if result.quality_metrics["average_fixes_per_file"] > 20:
            recommendations.append("多数の型アノテーション不足があったファイルは設計レビューを推奨")
        if len(result.errors) > 0:
            recommendations.append("修正エラーの原因調査と手動修正を実施")
        if result.total_fixes_applied > 100:
            recommendations.append("大量修正後は統合テスト実行を推奨")
        recommendations.append("mypy strict モードでの再チェック実施")
        recommendations.append("修正されたコードの手動レビューと調整")
        recommendations.append("CI/CD パイプラインでの型チェック有効化")
        return recommendations


def main():
    """メイン実行関数"""

    parser = argparse.ArgumentParser(description="型アノテーション自動修正ツール")
    parser.add_argument(
        "--project-root", type=Path, default=Path(), help="プロジェクトルート (デフォルト: 現在のディレクトリ)"
    )
    parser.add_argument("--target-files", nargs="*", help="対象ファイル指定 (未指定で全対象)")
    parser.add_argument("--dry-run", action="store_true", help="実際に修正せずに検出のみ実行")
    parser.add_argument("--no-backup", action="store_true", help="バックアップを作成しない")
    parser.add_argument("--priority", choices=["critical", "high", "medium", "low"], help="処理優先度フィルター")
    parser.add_argument("--report-output", type=Path, help="レポート出力パス")
    parser.add_argument("--rollback", nargs="*", help="指定したバックアップファイルをロールバック")
    args = parser.parse_args()
    if args.rollback is not None:
        config = TypeAnnotationConfig(project_root=args.project_root)
        fixer = TypeAnnotationFixer(config)
        backup_files = args.rollback if args.rollback else []
        if not backup_files:
            backup_files = list(args.project_root.rglob("*.bak_*"))
            backup_files = [str(f) for f in backup_files]
        result = fixer.rollback_changes(backup_files)
        console.print(f"ロールバック結果: 成功={result['success_count']}, 失敗={result['failure_count']}")
        if result["errors"]:
            console.print("エラー:")
            for error in result["errors"]:
                console.print(f"  - {error}")
        return 0
    config = TypeAnnotationConfig(
        project_root=args.project_root, backup_enabled=not args.no_backup, dry_run=args.dry_run
    )
    fixer = TypeAnnotationFixer(config)
    try:
        result = fixer.fix_annotations_batch(args.target_files)
        if args.report_output:
            fixer.export_fix_report(result, args.report_output)
        console.print("\n=== 型アノテーション修正結果 ===")
        console.print(f"処理ファイル数: {len(result.processed_files)}")
        console.print(f"修正ファイル数: {len(result.fixed_files)}")
        console.print(f"スキップファイル数: {len(result.skipped_files)}")
        console.print(f"総修正箇所数: {result.total_fixes_applied}")
        console.print(f"実行時間: {result.execution_time_seconds:.2f}秒")
        if result.errors:
            console.print(f"\nエラー発生数: {len(result.errors)}")
            for error in result.errors[:5]:
                console.print(f"  - {error}")
        console.print("\n品質メトリクス:")
        for key, value in result.quality_metrics.items():
            console.print(f"  {key}: {value}")
        if result.backup_files:
            console.print(f"\nバックアップファイル数: {len(result.backup_files)}")
            console.print("ロールバックが必要な場合は --rollback オプションを使用してください")
    except Exception as e:
        console.print(f"実行エラー: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
