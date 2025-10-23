"""Tools.fix_f821_errors
Where: Tool that fixes F821 (undefined name) lint errors.
What: Parses lint outputs and applies targeted fixes automatically.
Why: Speeds up code quality remediation.
"""

# 循環インポート防止のためのTYPE_CHECKINGブロック
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # TODO: Move circular import prone imports here
    pass

#!/usr/bin/env python3
"""F821: undefined-name エラーを修正

未定義の名前参照を適切なインポートまたは定義で修正します。
"""

import ast
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger


class UndefinedNameFixer:
    """未定義名エラー修正クラス"""

    def __init__(self, logger_service: Any | None = None, console_service: Any | None = None):
        """初期化"""
        self.scripts_dir = Path("scripts")
        self.common_imports = {
            # よく使われる型
            "ExecutionResult": "from noveler.domain.value_objects.execution_result import ExecutionResult",
            "ChapterNumber": "from noveler.domain.value_objects.chapter_number import ChapterNumber",
            "SessionAnalysisResult": "from noveler.domain.value_objects.session_analysis_result import SessionAnalysisResult",
            "SessionAnalysisResponse": "from noveler.domain.value_objects.session_analysis_response import SessionAnalysisResponse",
            "PromptSaveResult": "from noveler.domain.value_objects.prompt_save_result import PromptSaveResult",

            # インターフェース・抽象クラス
            "IRepositoryFactory": "from noveler.domain.interfaces.repository_factory import IRepositoryFactory",
            "ClaudePlotInterface": "from noveler.domain.interfaces.claude_plot_interface import ClaudePlotInterface",

            # サービス・アナライザー
            "InSessionClaudeAnalyzer": "from noveler.domain.services.in_session_claude_analyzer import InSessionClaudeAnalyzer",
            "A31ResultIntegrator": "from noveler.domain.services.a31_result_integrator import A31ResultIntegrator",

            # ファクトリー
            "UnifiedRepositoryFactory": "from noveler.infrastructure.factories.unified_repository_factory import UnifiedRepositoryFactory",

            # ユースケース
            "UniversalClaudeCodeUseCase": "from noveler.application.use_cases.universal_claude_code_use_case import UniversalClaudeCodeUseCase",
            "UniversalPromptRequest": "from noveler.application.use_cases.universal_prompt_request import UniversalPromptRequest",
            "UniversalPromptResponse": "from noveler.application.use_cases.universal_prompt_response import UniversalPromptResponse",

            # 設定クラス
            "ClaudeCodeIntegrationConfig": "from noveler.infrastructure.config.claude_code_integration_config import ClaudeCodeIntegrationConfig",

            # リポジトリ
            "EpisodePromptRepository": "from noveler.domain.repositories.episode_prompt_repository import EpisodePromptRepository",
        }

        self.logger_service = logger_service
        self.console_service = console_service
    def find_undefined_names(self, file_path: Path) -> list[tuple[str, int]]:
        """ファイルから未定義の名前を検出

        Args:
            file_path: 対象ファイル

        Returns:
            (未定義名, 行番号)のリスト
        """
        undefined_names = []

        try:
            content = Path(file_path).read_text(encoding="utf-8")

            tree = ast.parse(content)
            defined_names = self._get_defined_names(tree)
            imported_names = self._get_imported_names(tree)

            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    name = node.id
                    if name not in defined_names and name not in imported_names:
                        # Python組み込み名でないかチェック
                        if not self._is_builtin(name):
                            undefined_names.append((name, getattr(node, "lineno", 0)))

        except Exception:
            pass

        return undefined_names

    def _get_defined_names(self, tree: ast.AST) -> set[str]:
        """定義された名前を取得"""
        defined = set()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined.add(target.id)

        return defined

    def _get_imported_names(self, tree: ast.AST) -> set[str]:
        """インポートされた名前を取得"""
        imported = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported.add(name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported.add(name)

        return imported

    def _is_builtin(self, name: str) -> bool:
        """組み込み名かどうかを判定"""
        builtins = {
            "True", "False", "None", "self", "cls",
            "int", "str", "float", "bool", "list", "dict", "set", "tuple",
            "any", "all", "len", "range", "enumerate", "zip",
            "print", "input", "open", "file",
            "Exception", "ValueError", "TypeError", "KeyError",
            "__name__", "__file__", "__doc__",
        }
        return name in builtins

    def fix_undefined_names(self, file_path: Path) -> bool:
        """未定義名エラーを修正

        Args:
            file_path: 対象ファイル

        Returns:
            修正が行われたかどうか
        """
        undefined_names = self.find_undefined_names(file_path)
        if not undefined_names:
            return False

        # 一意な未定義名を取得
        unique_names = set(name for name, _ in undefined_names)

        # 修正が必要なインポートを特定
        imports_to_add = []
        for name in unique_names:
            if name in self.common_imports:
                imports_to_add.append(self.common_imports[name])

        if not imports_to_add:
            return False

        # ファイルを読み込み
        with Path(file_path).open("r", encoding="utf-8") as f:
            lines = f.readlines()

        # インポート文を追加
        modified = self._add_imports(lines, imports_to_add)

        if modified:
            # ファイルを書き戻し
            with Path(file_path).open("w", encoding="utf-8") as f:
                f.writelines(lines)
            return True

        return False

    def _add_imports(self, lines: list[str], imports: list[str]) -> bool:
        """インポート文を追加

        Args:
            lines: ファイルの行リスト
            imports: 追加するインポート文

        Returns:
            修正が行われたかどうか
        """
        if not imports:
            return False

        # 既存のインポート位置を探す
        last_import_idx = -1
        for i, line in enumerate(lines):
            if line.strip().startswith(("import ", "from ")):
                last_import_idx = i

        # インポート文を追加
        if last_import_idx >= 0:
            # 既存のインポートの後に追加
            for import_stmt in sorted(imports):
                # 既に存在するかチェック
                if not any(import_stmt in line for line in lines):
                    lines.insert(last_import_idx + 1, import_stmt + "\n")
                    last_import_idx += 1
        else:
            # docstringの後に追加
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith("#"):
                    if '"""' in line or "'''" in line:
                        # docstringをスキップ
                        in_docstring = True
                        quote = '"""' if '"""' in line else "'''"
                        if line.count(quote) == 2:
                            insert_idx = i + 1
                            break
                        for j in range(i + 1, len(lines)):
                            if quote in lines[j]:
                                insert_idx = j + 1
                                break
                        break
                    insert_idx = i
                    break

            # インポート文を挿入
            for import_stmt in sorted(imports):
                if not any(import_stmt in line for line in lines):
                    lines.insert(insert_idx, import_stmt + "\n")
                    insert_idx += 1

            # 空行を追加
            if insert_idx < len(lines) and lines[insert_idx].strip():
                lines.insert(insert_idx, "\n")

        return True

def main():
    """メイン処理"""
    logger = get_logger(__name__)
    fixer = UndefinedNameFixer()
    fixed_count = 0

    logger.info("=== Fixing F821: undefined-name errors ===")

    # 重要なファイルから修正
    important_files = [
        "noveler/application/orchestrators/error_handling_orchestrator.py",
        "noveler/application/orchestrators/plot_generation_orchestrator.py",
        "noveler/application/use_cases/a31_complete_check_use_case.py",
        "noveler/application/use_cases/enhanced_plot_generation_use_case.py",
        "noveler/application/use_cases/enhanced_plot_generation_use_case_factory.py",
        "noveler/application/use_cases/episode_prompt_save_use_case.py",
    ]

    for file_path in important_files:
        py_file = Path(file_path)
        if py_file.exists():
            undefined = fixer.find_undefined_names(py_file)
            if undefined:
                logger.info(f"Found {len(undefined)} undefined names in {py_file}")
                if fixer.fix_undefined_names(py_file):
                    logger.info(f"✅ Fixed: {py_file}")
                    fixed_count += 1
                else:
                    logger.warning(f"⚠️ Could not auto-fix: {py_file}")
                    # 未定義名を表示
                    unique_names = set(name for name, _ in undefined)
                    logger.info(f"   Undefined: {', '.join(unique_names)}")

    logger.info(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    main()
