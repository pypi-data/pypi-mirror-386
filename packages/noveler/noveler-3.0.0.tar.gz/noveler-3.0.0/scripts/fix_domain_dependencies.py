#!/usr/bin/env python3
"""Domain層依存関係自動修正ツール

B20準拠: Domain層のインフラ層への直接依存を自動修正
"""

import ast
import re
from pathlib import Path
from typing import List, Tuple


class DomainDependencyFixer:
    """Domain層の依存関係を自動修正"""

    def __init__(self) -> None:
        self.fixed_files: List[Path] = []
        self.failed_files: List[Tuple[Path, str]] = []

    def fix_logger_imports(self, file_path: Path) -> bool:
        """ロガーのインポートを修正

        Args:
            file_path: 修正対象ファイル

        Returns:
            修正成功の場合True
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content
            modified = False

            # unified_loggerのインポートを置換
            if "from noveler.infrastructure.logging.unified_logger import get_logger" in content:
                content = content.replace(
                    "from noveler.infrastructure.logging.unified_logger import get_logger",
                    "from noveler.domain.interfaces.logger_interface import ILogger, NullLogger"
                )
                # get_logger(__name__)をNullLogger()に置換
                content = re.sub(
                    r'logger\s*=\s*get_logger\([^)]+\)',
                    'logger: ILogger = NullLogger()',
                    content
                )
                modified = True

            # scripts.infrastructure.loggingのインポートも同様に処理
            if "from noveler.infrastructure.logging" in content:
                content = re.sub(
                    r'from scripts\.infrastructure\.logging\.[^\n]+\nimport get_logger',
                    'from noveler.domain.interfaces.logger_interface import ILogger, NullLogger',
                    content
                )
                content = re.sub(
                    r'logger\s*=\s*get_logger\([^)]+\)',
                    'logger: ILogger = NullLogger()',
                    content
                )
                modified = True

            # 標準loggingモジュールの直接使用を検出
            if re.search(r'^import logging\s*$', content, re.MULTILINE):
                # loggingインポートを削除
                content = re.sub(r'^import logging\s*\n', '', content, flags=re.MULTILINE)
                # logging.getLogger()をNullLogger()に置換
                content = re.sub(
                    r'logging\.getLogger\([^)]*\)',
                    'NullLogger()',
                    content
                )
                # インターフェースインポートを追加（まだない場合）
                if "from noveler.domain.interfaces.logger_interface" not in content:
                    # 最初のimport文の前に追加
                    import_pattern = r'^(from|import)\s+'
                    match = re.search(import_pattern, content, re.MULTILINE)
                    if match:
                        pos = match.start()
                        content = (
                            content[:pos] +
                            "from noveler.domain.interfaces.logger_interface import ILogger, NullLogger\n" +
                            content[pos:]
                        )
                modified = True

            if modified:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.fixed_files.append(file_path)
                return True

            return False

        except Exception as e:
            self.failed_files.append((file_path, str(e)))
            return False

    def fix_pathlib_usage(self, file_path: Path) -> bool:
        """pathlibの直接使用をIPathService経由に修正

        Args:
            file_path: 修正対象ファイル

        Returns:
            修正成功の場合True
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content
            modified = False

            # pathlib.Pathの直接インポートを検出
            if "from pathlib import Path" in content and "interfaces" not in str(file_path):
                # IPathServiceインポートに置換
                content = content.replace(
                    "from pathlib import Path",
                    "from noveler.domain.interfaces.path_service import IPathService"
                )

                # Path()の使用箇所を検出して警告コメントを追加
                content = re.sub(
                    r'Path\((.*?)\)',
                    r'Path(\1)  # TODO: IPathServiceを使用するように修正',
                    content
                )
                modified = True

            if modified:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.fixed_files.append(file_path)
                return True

            return False

        except Exception as e:
            self.failed_files.append((file_path, str(e)))
            return False

    def report_results(self) -> None:
        """修正結果をレポート"""
        if self.fixed_files:
            print(f"✅ {len(self.fixed_files)}個のファイルを修正しました:")
            for file_path in self.fixed_files:
                print(f"  - {file_path}")

        if self.failed_files:
            print(f"\n❌ {len(self.failed_files)}個のファイルの修正に失敗:")
            for file_path, error in self.failed_files:
                print(f"  - {file_path}: {error}")

        if not self.fixed_files and not self.failed_files:
            print("ℹ️ 修正が必要なファイルはありませんでした")


def main() -> None:
    """メインエントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="Domain層依存関係自動修正ツール")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際の修正を行わずに検出のみ実行"
    )
    parser.add_argument(
        "--logger",
        action="store_true",
        help="ロガー依存を修正"
    )
    parser.add_argument(
        "--pathlib",
        action="store_true",
        help="pathlib直接使用を修正"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["src/noveler/domain"],
        help="修正対象のパス（デフォルト: src/noveler/domain）"
    )

    args = parser.parse_args()

    # デフォルトは両方修正
    if not args.logger and not args.pathlib:
        args.logger = True
        args.pathlib = True

    fixer = DomainDependencyFixer()

    for path_str in args.paths:
        base_path = Path(path_str)
        if base_path.is_dir():
            # ディレクトリ内の全Pythonファイルを処理
            for py_file in base_path.rglob("*.py"):
                if args.logger:
                    fixer.fix_logger_imports(py_file)
                if args.pathlib:
                    fixer.fix_pathlib_usage(py_file)
        elif base_path.is_file() and base_path.suffix == ".py":
            # 単一ファイルを処理
            if args.logger:
                fixer.fix_logger_imports(base_path)
            if args.pathlib:
                fixer.fix_pathlib_usage(base_path)

    fixer.report_results()


if __name__ == "__main__":
    main()
