#!/usr/bin/env python3
"""
CODEMAP自動更新フック

共通基盤コンポーネントの変更を検出し、CODEMAP.yamlを自動更新するスクリプト。
コミット前フックとして実行され、コンポーネント定義の一貫性を保つ。

Usage:
    python scripts/tools/update_codemap_foundation.py
    python scripts/tools/update_codemap_foundation.py --dry-run
    python scripts/tools/update_codemap_foundation.py --verbose

Version: 1.0.0
Author: Claude Code
Date: 2025-09-09
"""

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# プロジェクトルートを取得
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.tools.codemap_reader import create_codemap_reader

logger = get_logger(__name__)

@dataclass
class ComponentChange:
    """コンポーネント変更情報"""
    component_name: str
    change_type: str  # "added", "removed", "modified"
    old_value: str | None = None
    new_value: str | None = None
    file_path: str | None = None

class CODEMAPFoundationUpdater:
    """CODEMAP共通基盤自動更新システム"""

    def __init__(self, project_root: Path, dry_run: bool = False):
        self.project_root = project_root
        self.dry_run = dry_run
        self.logger = logger
        self.codemap_path = project_root / "CODEMAP.yaml"
        self.changes_detected = []

    def scan_foundation_components(self) -> dict[str, dict[str, Any]]:
        """共通基盤コンポーネントをスキャンして現状を取得"""
        components = {}

        # 既知の共通基盤ファイルをスキャン
        foundation_files = [
            "src/noveler/presentation/shared/shared_utilities.py",
            "src/noveler/infrastructure/logging/unified_logger.py",
            "src/noveler/infrastructure/factories/path_service_factory.py",
            "src/noveler/presentation/cli/shared_utilities.py",
            "scripts/presentation/cli/shared_utilities/__init__.py",
            "scripts/presentation/cli/shared_utilities/console.py",
            "scripts/presentation/cli/shared_utilities/logger.py",
            "scripts/presentation/cli/shared_utilities/path_service.py"
        ]

        for file_path in foundation_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    detected_components = self._analyze_file_for_components(full_path)
                    for comp_name, comp_info in detected_components.items():
                        if comp_name not in components:
                            components[comp_name] = []
                        components[comp_name].append({
                            "file_path": file_path,
                            "module": self._file_path_to_module(file_path),
                            **comp_info
                        })
                except Exception as e:
                    self.logger.warning(f"Error analyzing {file_path}: {e}")

        return components

    def _analyze_file_for_components(self, file_path: Path) -> dict[str, dict[str, str]]:
        """ファイルを解析して共通基盤コンポーネントを検出"""
        components = {}

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            for node in ast.walk(tree):
                # 関数定義の検出
                if isinstance(node, ast.FunctionDef):
                    func_name = node.name

                    # Console関連
                    if "console" in func_name.lower() or func_name in ["_get_console", "get_console"]:
                        components["console"] = {
                            "function": func_name,
                            "type": "function",
                            "description": self._extract_docstring(node)
                        }

                    # Logger関連
                    elif "logger" in func_name.lower() or func_name in ["get_logger", "get_unified_logger"]:
                        components["logger"] = {
                            "function": func_name,
                            "type": "function",
                            "description": self._extract_docstring(node)
                        }

                    # PathService関連
                    elif "path" in func_name.lower() and ("service" in func_name.lower() or "create" in func_name.lower()):
                        components["path_service"] = {
                            "function": func_name,
                            "type": "function",
                            "description": self._extract_docstring(node)
                        }

                    # ErrorHandler関連
                    elif "error" in func_name.lower() and "handle" in func_name.lower():
                        components["error_handler"] = {
                            "function": func_name,
                            "type": "function",
                            "description": self._extract_docstring(node)
                        }

                # 変数代入の検出（グローバルインスタンス）
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            if var_name == "console":
                                components["console"] = {
                                    "variable": var_name,
                                    "type": "global_instance",
                                    "description": "グローバルConsoleインスタンス"
                                }

        except Exception as e:
            self.logger.warning(f"AST parsing failed for {file_path}: {e}")

        return components

    def _extract_docstring(self, node: ast.FunctionDef) -> str:
        """関数のdocstringを抽出"""
        if (node.body and isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            return node.body[0].value.value.strip().split("\n")[0]
        return ""

    def _file_path_to_module(self, file_path: str) -> str:
        """ファイルパスをモジュール名に変換"""
        # src/noveler/... -> noveler...
        # scripts/... -> scripts...
        path_parts = Path(file_path).with_suffix("").parts

        if path_parts[0] == "src":
            return ".".join(path_parts[1:])
        return ".".join(path_parts)

    def compare_with_current_codemap(self, detected_components: dict[str, list[dict]]) -> list[ComponentChange]:
        """検出されたコンポーネントと現在のCODEMAPを比較"""
        changes = []

        try:
            codemap_reader = create_codemap_reader(self.codemap_path)
            current_components = codemap_reader.get_all_component_definitions()

            # 新しく検出されたコンポーネント
            for comp_name, comp_instances in detected_components.items():
                if comp_name not in current_components:
                    # 完全に新しいコンポーネント
                    primary_instance = comp_instances[0]  # 最初のものを主要として使用
                    changes.append(ComponentChange(
                        component_name=comp_name,
                        change_type="added",
                        new_value=f"{primary_instance['module']}.{primary_instance.get('function', 'unknown')}",
                        file_path=primary_instance["file_path"]
                    ))
                else:
                    # 既存コンポーネントの変更チェック
                    current_comp = current_components[comp_name]
                    for instance in comp_instances:
                        detected_module = instance["module"]
                        detected_function = instance.get("function", "")

                        # 主要モジュールの変更
                        if (detected_module == current_comp.primary_module and
                            detected_function != current_comp.primary_function):
                            changes.append(ComponentChange(
                                component_name=comp_name,
                                change_type="modified",
                                old_value=f"{current_comp.primary_module}.{current_comp.primary_function}",
                                new_value=f"{detected_module}.{detected_function}",
                                file_path=instance["file_path"]
                            ))

                        # 新しい代替モジュールの検出
                        is_known_alternative = any(
                            alt["module"] == detected_module
                            for alt in current_comp.alternatives
                        )
                        if not is_known_alternative and detected_module != current_comp.primary_module:
                            changes.append(ComponentChange(
                                component_name=comp_name,
                                change_type="added_alternative",
                                new_value=f"{detected_module}.{detected_function}",
                                file_path=instance["file_path"]
                            ))

        except Exception as e:
            self.logger.error(f"Error comparing with CODEMAP: {e}")

        return changes

    def update_codemap(self, changes: list[ComponentChange]) -> bool:
        """CODEMAPを更新"""
        if not changes:
            self.logger.info("No changes detected in foundation components")
            return True

        try:
            # 現在のCODEMAPを読み込み
            with open(self.codemap_path, encoding="utf-8") as f:
                codemap_data = yaml.safe_load(f)

            # 変更の適用
            for change in changes:
                self._apply_change_to_codemap(codemap_data, change)

            # 更新日時の記録
            if "common_foundation" in codemap_data:
                codemap_data["common_foundation"]["last_updated"] = "2025-09-09"
                codemap_data["common_foundation"]["auto_updated"] = True

            if not self.dry_run:
                # CODEMAPを保存
                with open(self.codemap_path, "w", encoding="utf-8") as f:
                    yaml.dump(codemap_data, f, default_flow_style=False, allow_unicode=True)
                self.logger.info(f"CODEMAP updated with {len(changes)} changes")
            else:
                self.logger.info(f"DRY RUN: Would update CODEMAP with {len(changes)} changes")

            return True

        except Exception as e:
            self.logger.error(f"Error updating CODEMAP: {e}")
            return False

    def _apply_change_to_codemap(self, codemap_data: dict[str, Any], change: ComponentChange):
        """個別の変更をCODEMAPデータに適用"""
        common_foundation = codemap_data.setdefault("common_foundation", {})
        components = common_foundation.setdefault("components", {})

        if change.change_type == "added":
            # 新しいコンポーネントの追加
            module, function = change.new_value.rsplit(".", 1)
            components[change.component_name] = {
                "primary_module": module,
                "primary_function": function,
                "description": f"自動検出: {change.file_path}",
                "usage_pattern": f"{function}()",
                "alternatives": []
            }

        elif change.change_type == "modified":
            # 既存コンポーネントの変更
            if change.component_name in components:
                module, function = change.new_value.rsplit(".", 1)
                components[change.component_name]["primary_module"] = module
                components[change.component_name]["primary_function"] = function

        elif change.change_type == "added_alternative":
            # 代替モジュールの追加
            if change.component_name in components:
                module, function = change.new_value.rsplit(".", 1)
                alternatives = components[change.component_name].setdefault("alternatives", [])
                alternatives.append({
                    "module": module,
                    "function": function,
                    "description": f"自動検出: {change.file_path}"
                })

    def run(self) -> bool:
        """メイン実行処理"""
        self.logger.info("Starting CODEMAP foundation update scan...")

        # 1. 現在の共通基盤コンポーネントをスキャン
        detected_components = self.scan_foundation_components()
        self.logger.info(f"Detected {len(detected_components)} component types")

        # 2. 現在のCODEMAPと比較
        changes = self.compare_with_current_codemap(detected_components)
        self.logger.info(f"Found {len(changes)} changes")

        # 3. 変更の詳細をログ出力
        for change in changes:
            self.logger.info(f"Change: {change.change_type} - {change.component_name}")
            if change.old_value:
                self.logger.info(f"  Old: {change.old_value}")
            if change.new_value:
                self.logger.info(f"  New: {change.new_value}")

        # 4. CODEMAPを更新
        if changes:
            return self.update_codemap(changes)

        return True


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="CODEMAP共通基盤自動更新")
    parser.add_argument("--dry-run", action="store_true",
                       help="実際の更新を行わず、変更内容のみ表示")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="詳細ログを出力")

    args = parser.parse_args()

    # ログレベル設定
    if args.verbose:
        logger.setLevel("DEBUG")

    # 更新処理実行
    updater = CODEMAPFoundationUpdater(PROJECT_ROOT, dry_run=args.dry_run)

    try:
        success = updater.run()
        if success:
            logger.info("CODEMAP foundation update completed successfully")
            sys.exit(0)
        else:
            logger.error("CODEMAP foundation update failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error during CODEMAP update: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
