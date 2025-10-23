#!/usr/bin/env python3
"""Adapter that analyzes Python source files for import usage.

Specification: SPEC-CIRCULAR-IMPORT-DETECTION-001
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import ast
import sys
from dataclasses import dataclass

from noveler.domain.value_objects.import_statement import ImportScope, ImportStatement, ImportType
from noveler.infrastructure.logging.unified_logger import get_logger

if TYPE_CHECKING:
    from pathlib import Path

logger = get_logger(__name__)


@dataclass
class ASTAnalysisResult:
    """Analysis metrics captured for a single AST traversal.

    Attributes:
        imports: Collected import statements resolved into value objects.
        syntax_errors: Detected syntax error messages.
        analysis_warnings: High level warnings about risky import behaviour.
        total_lines: Number of lines parsed in the source file.
        import_density: Ratio of imports to total lines.
"""

    imports: list[ImportStatement]
    syntax_errors: list[str]
    analysis_warnings: list[str]
    total_lines: int
    import_density: float  # インポート密度 (imports/total_lines)


class ASTAnalysisAdapter:
    """Perform import-focused AST analysis for Python modules."""

    def __init__(self, project_root: Path) -> None:
        """Initialize the adapter.

        Args:
            project_root: Root directory used to resolve local modules.
        """
        self.project_root = project_root
        self.builtin_modules = set(sys.builtin_module_names)
        self.stdlib_modules = self._load_stdlib_modules()

    def analyze_file(self, file_path: Path) -> ASTAnalysisResult:
        """Analyze a single Python file for import usage.

        Args:
            file_path: Path to the Python file to inspect.

        Returns:
            ASTAnalysisResult: Structured analysis outcome for the file.
        """
        self.logger_service.info("AST分析開始: %s", file_path)

        try:
            source_code = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source_code, filename=str(file_path))

            imports = self._extract_imports(tree, file_path, source_code)
            warnings = self._analyze_import_patterns(imports)

            total_lines = len(source_code.splitlines())
            import_density = len(imports) / max(1, total_lines)

            return ASTAnalysisResult(
                imports=imports,
                syntax_errors=[],
                analysis_warnings=warnings,
                total_lines=total_lines,
                import_density=import_density,
            )

        except SyntaxError as e:
            self.logger_service.warning("構文エラー: %s:%s - %s", file_path, (e.lineno), (e.msg))
            return ASTAnalysisResult(
                imports=[],
                syntax_errors=[f"Line {e.lineno}: {e.msg}"],
                analysis_warnings=[],
                total_lines=0,
                import_density=0.0,
            )

        except Exception as e:
            logger.exception("AST分析エラー: %s - %s", file_path, e)
            return ASTAnalysisResult(
                imports=[],
                syntax_errors=[f"Analysis error: {e!s}"],
                analysis_warnings=[],
                total_lines=0,
                import_density=0.0,
            )

    def analyze_project(self, include_patterns: list[str] | None = None) -> dict[Path, ASTAnalysisResult]:
        """Analyze all files that match the provided patterns.

        Args:
            include_patterns: Glob patterns that identify candidate Python files.

        Returns:
            dict[Path, ASTAnalysisResult]: Map of file paths to analysis results.
        """
        self.logger_service.info("プロジェクト全体のAST分析開始")

        if include_patterns is None:
            include_patterns = ["**/*.py"]

        results: dict[str, Any] = {}

        for pattern in include_patterns:
            for file_path in self.project_root.glob(pattern):
                if self._should_analyze_file(file_path):
                    results[file_path] = self.analyze_file(file_path)

        self.logger_service.info("AST分析完了: %sファイル", (len(results)))
        return results

    def _extract_imports(self, tree: ast.AST, file_path: Path, source_code: str) -> list[ImportStatement]:
        """Build import statements discovered during AST traversal.

        Args:
            tree: Parsed AST for the current Python module.
            file_path: Path to the analyzed source file.
            source_code: Raw source code of the analyzed file.

        Returns:
            list[ImportStatement]: Normalized import statements.
        """
        imports = []
        source_lines = source_code.splitlines()

        class ImportVisitor(ast.NodeVisitor):
            """Traverse AST nodes and delegate import handling to the adapter."""

            def __init__(self, extractor: ASTAnalysisAdapter) -> None:
                self.extractor = extractor

            def visit_Import(self, node: ast.Import) -> None:
                for alias in node.names:
                    import_stmt = self.extractor._create_import_statement(
                        module_name=alias.name,
                        imported_names=[alias.asname or alias.name],
                        import_type=ImportType.STANDARD,
                        file_path=file_path,
                        line_number=node.lineno,
                        source_lines=source_lines,
                    )

                    imports.append(import_stmt)
                self.generic_visit(node)

            def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
                if node.module is None:
                    return

                imported_names = []
                for alias in node.names:
                    imported_names.append(alias.asname or alias.name)

                import_type = ImportType.RELATIVE if node.level > 0 else ImportType.FROM

                import_stmt = self.extractor._create_import_statement(
                    module_name=node.module,
                    imported_names=imported_names,
                    import_type=import_type,
                    file_path=file_path,
                    line_number=node.lineno,
                    source_lines=source_lines,
                    relative_level=node.level,
                )

                imports.append(import_stmt)

                self.generic_visit(node)

            def visit_Call(self, node: ast.Call) -> None:
                # __import__ や importlib の検出
                if isinstance(node.func, ast.Name):
                    if node.func.id == "__import__":
                        self._handle_dynamic_import(node, "__import__")
                elif isinstance(node.func, ast.Attribute):
                    if (
                        isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "importlib"
                        and node.func.attr == "import_module"
                    ):
                        self._handle_dynamic_import(node, "importlib.import_module")

                self.generic_visit(node)

            def _handle_dynamic_import(self, node: ast.Call, import_func: str) -> None:
                """Record import usage triggered via dynamic calls."""

                if node.args and isinstance(node.args[0], ast.Str):
                    module_name = node.args[0].s
                    import_stmt = self.extractor._create_import_statement(
                        module_name=module_name,
                        imported_names=[module_name.split(".")[-1]],
                        import_type=ImportType.DYNAMIC,
                        file_path=file_path,
                        line_number=node.lineno,
                        source_lines=source_lines,
                    )

                    imports.append(import_stmt)

        visitor = ImportVisitor(self)
        visitor.visit(tree)

        return imports

    def _create_import_statement(
        self,
        module_name: str,
        imported_names: list[str],
        import_type: ImportType,
        file_path: Path,
        line_number: int,
        source_lines: list[str],
        relative_level: int = 0,
    ) -> ImportStatement:
        """Create an ImportStatement value object.

        Args:
            module_name: Module referenced by the import.
            imported_names: Names imported from the module.
            import_type: Classification for the import style.
            file_path: Source file that defines the import.
            line_number: 1-based line number for the import statement.
            source_lines: Source file split into individual lines.
            relative_level: Relative import depth for `from` statements.

        Returns:
            ImportStatement: Structured representation of the import.
        """

        # ソース行の取得
        statement_text = ""
        if 1 <= line_number <= len(source_lines):
            statement_text = source_lines[line_number - 1].strip()

        # インポート範囲の判定
        import_scope = self._determine_import_scope(module_name)

        # 解決されたモジュールパスの計算
        resolved_path = self._resolve_module_path(module_name, file_path, relative_level)

        return ImportStatement(
            module_name=module_name,
            imported_names=imported_names,
            import_type=import_type,
            import_scope=import_scope,
            source_file=file_path,
            line_number=line_number,
            statement_text=statement_text,
            relative_level=relative_level,
            resolved_module_path=resolved_path,
            is_circular_risk=False,  # 後で循環分析で設定
        )

    def _determine_import_scope(self, module_name: str) -> ImportScope:
        """Determine the scope classification for an import.

        Args:
            module_name: Fully qualified module name from the import.

        Returns:
            ImportScope: Categorization for the module.
        """
        if module_name in self.builtin_modules:
            return ImportScope.BUILTIN

        if module_name in self.stdlib_modules:
            return ImportScope.STANDARD_LIB

        # プロジェクト内モジュールかチェック
        if module_name.startswith("noveler."):
            return ImportScope.LOCAL

        # 相対インポートの検出
        if module_name.startswith("."):
            return ImportScope.RELATIVE

        # その他はサードパーティとして扱う
        return ImportScope.THIRD_PARTY

    def _resolve_module_path(self, module_name: str, source_file: Path, relative_level: int) -> Path | None:
        """Resolve an import to an absolute filesystem path.

        Args:
            module_name: Target module identified in the import.
            source_file: File that issues the import statement.
            relative_level: Relative import depth.

        Returns:
            Path | None: Resolved path when it can be inferred.
        """
        try:
            if relative_level > 0:
                # 相対インポートの解決
                current_dir = source_file.parent
                for _ in range(relative_level - 1):
                    current_dir = current_dir.parent

                module_path = current_dir / module_name.replace(".", "/") if module_name else current_dir

                # .py ファイルまたは __init__.py を探す
                if (module_path.with_suffix(".py")).exists():
                    return module_path.with_suffix(".py")
                if (module_path / "__init__.py").exists():
                    return module_path / "__init__.py"

            # 絶対インポートの解決
            elif module_name.startswith("noveler."):
                relative_module_path = module_name[8:].replace(".", "/")  # "noveler." を除去
                module_path = self.project_root / "scripts" / relative_module_path

                if (module_path.with_suffix(".py")).exists():
                    return module_path.with_suffix(".py")
                if (module_path / "__init__.py").exists():
                    return module_path / "__init__.py"

        except Exception:
            pass

        return None

    def _load_stdlib_modules(self) -> set[str]:
        """Return a curated set of standard library module names.

        Returns:
            set[str]: Module names used to classify imports.
        """
        # Python標準ライブラリの主要モジュール
        # 実際の実装ではより包括的なリストまたは動的検出を使用
        return {
            "os",
            "sys",
            "pathlib",
            "json",
            "yaml",
            "csv",
            "xml",
            "re",
            "datetime",
            "time",
            "collections",
            "itertools",
            "functools",
            "operator",
            "math",
            "statistics",
            "random",
            "hashlib",
            "uuid",
            "subprocess",
            "threading",
            "asyncio",
            "concurrent",
            "multiprocessing",
            "logging",
            "unittest",
            "pytest",
            "dataclasses",
            "typing",
            "enum",
            "abc",
            "contextlib",
            "tempfile",
            "shutil",
            "glob",
            "fnmatch",
            "argparse",
            "configparser",
            "http",
            "urllib",
            "socket",
            "ssl",
            "email",
            "mimetypes",
            "base64",
            "binascii",
            "struct",
            "codecs",
            "locale",
            "gettext",
            "sqlite3",
            "pickle",
            "shelve",
            "dbm",
            "zlib",
            "gzip",
            "bz2",
            "lzma",
            "tarfile",
            "zipfile",
            "importlib",
            "pkgutil",
            "modulefinder",
            "runpy",
            "ast",
            "dis",
            "inspect",
            "types",
            "copy",
            "pprint",
            "repr",
            "numbers",
            "fractions",
            "decimal",
            "textwrap",
            "string",
            "io",
            "stringprep",
        }


    def _should_analyze_file(self, file_path: Path) -> bool:
        """Determine whether the file should be analyzed.

        Args:
            file_path: Candidate file path.

        Returns:
            bool: ``True`` if the file needs to be analyzed.
        """
        # 除外対象
        exclude_patterns = [
            "__pycache__",
            ".pyc",
            ".pyo",
            ".git",
            ".tox",
            ".pytest_cache",
            "venv",
            ".venv",
            "node_modules",
            "temp",
        ]

        path_str = str(file_path)
        return not any(pattern in path_str for pattern in exclude_patterns)

    def _analyze_import_patterns(self, imports: list[ImportStatement]) -> list[str]:
        """Evaluate collected imports and derive warnings.

        Args:
            imports: Import statements gathered from the AST.

        Returns:
            list[str]: Warning messages describing risky patterns.
        """
        warnings = []

        # 相対インポートの警告
        relative_imports = [imp for imp in imports if imp.import_type == ImportType.RELATIVE]
        if relative_imports:
            warnings.append(f"相対インポート{len(relative_imports)}件検出 - 絶対インポートを推奨")

        # scriptsプレフィックス不足の警告
        missing_prefix = [
            imp
            for imp in imports
            if imp.import_scope == ImportScope.LOCAL and not imp.module_name.startswith("noveler.")
        ]
        if missing_prefix:
            warnings.append(f"scriptsプレフィックス不足{len(missing_prefix)}件検出")

        # 動的インポートの警告
        dynamic_imports = [imp for imp in imports if imp.import_type == ImportType.DYNAMIC]
        if dynamic_imports:
            warnings.append(f"動的インポート{len(dynamic_imports)}件検出 - 静的分析困難")

        return warnings
