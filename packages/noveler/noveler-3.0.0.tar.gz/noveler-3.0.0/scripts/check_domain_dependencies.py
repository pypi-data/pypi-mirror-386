#!/usr/bin/env python3
"""Domain層依存関係チェックツール

B20準拠: Domain層がインフラ層に依存していないことを検証
"""

import ast
import sys
from pathlib import Path


class DomainDependencyChecker:
    """Domain層の依存関係をチェック"""

    FORBIDDEN_IMPORTS = {
        "noveler.infrastructure",
        "scripts.infrastructure",
        "logging",
        "os.environ",
        "os.getenv",
    }

    ALLOWED_INFRASTRUCTURE = {
        # 許可されるインフラ層インターフェース（Domain層で定義されたものに限る）
        "noveler.domain.interfaces",
        "scripts.domain.interfaces",
    }

    def __init__(self) -> None:
        self.violations: list[tuple[Path, int, str, str]] = []

    def check_file(self, file_path: Path) -> bool:
        """ファイルの依存関係をチェック

        Args:
            file_path: チェック対象ファイル

        Returns:
            違反がない場合True
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._check_import(file_path, node.lineno, alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._check_import(file_path, node.lineno, node.module)

            return len(self.violations) == 0

        except Exception as e:
            print(f"エラー: {file_path}の解析中にエラーが発生: {e}")
            return False

    def _check_import(self, file_path: Path, line_no: int, module_name: str) -> None:
        """インポートが許可されているかチェック

        Args:
            file_path: ファイルパス
            line_no: 行番号
            module_name: モジュール名
        """
        # 禁止されたインポートをチェック
        for forbidden in self.FORBIDDEN_IMPORTS:
            if module_name.startswith(forbidden):
                # 許可されたインターフェースは除外
                if not any(module_name.startswith(allowed) for allowed in self.ALLOWED_INFRASTRUCTURE):
                    self.violations.append((
                        file_path,
                        line_no,
                        module_name,
                        f"Domain層で{forbidden}への依存は禁止されています"
                    ))

        # pathlib.Pathの直接使用をチェック（PathServiceを使うべき）
        if module_name == "pathlib" and "interfaces" not in str(file_path):
            self.violations.append((
                file_path,
                line_no,
                module_name,
                "Domain層ではpathlib.Pathの直接使用は推奨されません。IPathServiceを使用してください"
            ))

    def report_violations(self) -> None:
        """違反をレポート"""
        if not self.violations:
            print("✅ Domain層の依存関係チェック: 違反なし")
            return

        print(f"❌ Domain層の依存関係チェック: {len(self.violations)}件の違反を検出")
        for file_path, line_no, module, message in self.violations:
            print(f"  {file_path}:{line_no}")
            print(f"    インポート: {module}")
            print(f"    理由: {message}")


def main() -> int:
    """メインエントリーポイント"""
    if len(sys.argv) < 2:
        print("使用方法: python check_domain_dependencies.py <file1> [file2] ...")
        return 1

    checker = DomainDependencyChecker()

    for file_arg in sys.argv[1:]:
        file_path = Path(file_arg)
        if file_path.exists() and file_path.suffix == ".py":
            # Domain層のファイルのみチェック
            if "domain" in str(file_path):
                checker.check_file(file_path)

    checker.report_violations()
    return 0 if not checker.violations else 1


if __name__ == "__main__":
    sys.exit(main())
