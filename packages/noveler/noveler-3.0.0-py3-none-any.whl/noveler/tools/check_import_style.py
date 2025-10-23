"""統合インポート管理システム - インポートスタイルチェッカー

CLAUDE.md記載の統合インポート管理システムの実装
すべてのPythonファイルで絶対インポート(noveler.で始まる)を強制する
"""
import ast
import sys
from pathlib import Path
from typing import Any

from noveler.presentation.shared.shared_utilities import console


class ImportStyleChecker(ast.NodeVisitor):
    """インポートスタイルをチェックするASTビジター"""

    def __init__(self, file_path: Path, logger_service: Any | None=None, console_service: Any | None=None) -> None:
        self.file_path = file_path
        self.violations: list[tuple[int, str, str]] = []
        self.logger_service = logger_service
        self.console_service = console_service

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """from ... import文をチェック"""
        if node.module:
            if node.level > 0:
                self.violations.append((node.lineno, f"from {'.' * node.level}{node.module or ''} import ...", "相対インポートは禁止されています"))
            elif not node.module.startswith(("noveler.", "tests.")):
                if not self._is_standard_or_external_import(node.module):
                    self.violations.append((node.lineno, f"from {node.module} import ...", "ローカルインポートは'noveler.'プレフィックスが必要です"))
        elif node.level > 0:
            self.violations.append((node.lineno, f"from {'.' * node.level} import ...", "相対インポートは禁止されています"))
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """import文をチェック"""
        for alias in node.names:
            name = alias.name
            if not name.startswith(("noveler.", "tests.")):
                if not self._is_standard_or_external_import(name):
                    self.violations.append((node.lineno, f"import {name}", "ローカルインポートは'noveler.'プレフィックスが必要です"))
        self.generic_visit(node)

    def _is_standard_or_external_import(self, module_name: str) -> bool:
        """標準ライブラリまたは外部パッケージかチェック"""
        standard_libs = {"os", "sys", "ast", "json", "yaml", "argparse", "pathlib", "typing", "dataclasses", "enum", "datetime", "time", "uuid", "re", "subprocess", "threading", "unittest", "abc", "functools", "itertools", "collections", "logging", "shutil", "tempfile", "io", "copy", "traceback", "warnings", "inspect", "textwrap", "__future__", "asyncio", "importlib", "decimal", "getpass", "statistics", "math", "concurrent", "glob", "contextlib", "unicodedata", "secrets", "signal", "platform", "random", "string", "hashlib", "hmac", "base64", "binascii", "struct", "array", "queue", "heapq", "bisect", "weakref", "types", "operator", "numbers", "fractions", "cmath", "pickle", "shelve", "sqlite3", "gzip", "zipfile", "tarfile", "csv", "configparser", "xml", "html", "http", "urllib", "email", "mimetypes", "cgi", "wsgiref", "socketserver", "xmlrpc", "ipaddress", "socket", "ssl", "select", "selectors", "asyncore", "asynchat", "mmap", "codecs", "locale", "gettext", "optparse", "getopt", "readline", "rlcompleter", "difflib", "pprint", "reprlib", "stat", "smtplib", "faulthandler", "fileinput", "fnmatch", "linecache", "mailbox", "netrc", "nntplib", "poplib", "py_compile", "pyclbr", "quopri", "sched", "site", "sndhdr", "sunau", "tabnanny", "telnetlib", "trace", "tty", "uu", "wave", "webbrowser", "zipapp", "bz2", "lzma", "zlib"}
        external_packages = {"pytest", "pytest_bdd", "watchdog", "click", "requests", "numpy", "pandas", "matplotlib", "seaborn", "pydantic", "astor", "deal", "sched", "psutil", "MeCab", "ruamel", "flask", "flask_cors", "schedule", "pywin32", "win32com", "aiofiles", "httpx", "janome", "fugashi", "sudachipy", "yamllint", "winreg", "fastapi", "uvicorn", "hypothesis"}
        top_level = module_name.split(".")[0]
        return top_level in standard_libs or top_level in external_packages

def check_file(file_path: Path) -> list[tuple[int, str, str]]:
    """単一ファイルのインポートスタイルをチェック"""
    try:
        content = Path(file_path).read_text(encoding="utf-8")
        tree = ast.parse(content)
        checker = ImportStyleChecker(file_path)
        checker.visit(tree)
        return checker.violations
    except SyntaxError:
        return []
    except Exception as e:
        console.print(f"Error checking {file_path}: {e}")
        return []

def check_directory(directory: Path) -> tuple[int, int]:
    """ディレクトリ内のすべてのPythonファイルをチェック"""
    total_files = 0
    files_with_violations = 0
    exclude_patterns = ["__pycache__", ".git", "backup", "temp", "htmlcov"]
    for py_file in directory.rglob("*.py"):
        if any(pattern in str(py_file) for pattern in exclude_patterns):
            continue
        total_files += 1
        violations = check_file(py_file)
        if violations:
            files_with_violations += 1
            console.print(f"\n❌ {py_file.relative_to(directory)}:")
            for (line_no, import_stmt, reason) in violations:
                console.print(f"  Line {line_no}: {import_stmt}")
                console.print(f"    → {reason}")
    return (total_files, files_with_violations)

def main():
    """メイン処理"""
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if target.is_file():
            violations = check_file(target)
            if violations:
                console.print(f"❌ {target.name}:")
                for (line_no, import_stmt, reason) in violations:
                    console.print(f"  Line {line_no}: {import_stmt}")
                    console.print(f"    → {reason}")
                sys.exit(1)
            else:
                console.print(f"✅ {target.name}: インポートスタイル準拠")
                sys.exit(0)
        else:
            console.print(f"❌ ファイルが見つかりません: {target}")
            sys.exit(1)
    else:
        scripts_dir = Path(__file__).parent.parent
        console.print("🔍 統合インポート管理システム - インポートスタイルチェック")
        console.print("=" * 60)
        (total_files, files_with_violations) = check_directory(scripts_dir)
        console.print("\n" + "=" * 60)
        if files_with_violations == 0:
            console.print(f"✅ すべてのファイル ({total_files}個) がインポートスタイルに準拠しています")
            sys.exit(0)
        else:
            console.print(f"❌ {files_with_violations}/{total_files} ファイルに違反があります")
            console.print("\n💡 修正方法:")
            console.print("  1. 手動修正: 上記の違反箇所を修正してください")
            console.print("  2. 相対インポートを絶対インポートに変更")
            console.print("  3. ローカルインポートに'noveler.'プレフィックスを追加")
            sys.exit(1)
if __name__ == "__main__":
    main()
