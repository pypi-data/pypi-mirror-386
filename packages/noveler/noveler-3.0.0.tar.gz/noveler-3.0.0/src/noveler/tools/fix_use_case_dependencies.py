#!/usr/bin/env python3
"""ユースケース層の依存関係修正スクリプト

プレゼンテーション層への直接依存を削除し、
DIパターンを適用する。
"""


import re
from pathlib import Path

from typing import TYPE_CHECKING

from noveler.presentation.shared.shared_utilities import console

if TYPE_CHECKING:
    pass


def fix_use_case_file(file_path: Path) -> bool:
    """ユースケースファイルの依存関係を修正

    Args:
        file_path: 修正対象ファイルパス

    Returns:
        修正があった場合True
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # 1. インポート部分の修正
        # presentation層からのインポートを検出
        if "from noveler.presentation.shared.shared_utilities import" in content:
            # IPathServiceのインポートを追加（まだない場合）
            if "from noveler.domain.interfaces.path_service import IPathService" not in content:
                # 最後のimport文を見つける
                import_lines = []
                lines = content.split("\n")
                last_import_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith("from noveler.") or line.startswith("import "):
                        last_import_idx = i

                # IPathServiceインポートを追加
                lines.insert(last_import_idx + 1, "from noveler.domain.interfaces.path_service import IPathService")
                content = "\n".join(lines)

        # 2. クラスのコンストラクタ修正
        # __init__メソッドを見つけて、path_serviceパラメータを追加
        init_pattern = r"def __init__\(self([^)]*)\):"
        init_matches = list(re.finditer(init_pattern, content))

        for match in reversed(init_matches):  # 後ろから処理
            params = match.group(1)
            # すでにpath_serviceがある場合はスキップ
            if "path_service" in params:
                continue

            # パラメータリストの最後に追加
            if params.strip():
                new_params = params.rstrip() + ", path_service: IPathService | None = None"
            else:
                new_params = ", path_service: IPathService | None = None"

            content = content[:match.start()] + f"def __init__(self{new_params}):" + content[match.end():]

            # self.path_service = path_serviceの追加
            # __init__の本体を見つける
            init_body_start = content.index(":", match.start()) + 1
            # 次のインデントレベルを見つける
            lines_after = content[init_body_start:].split("\n")
            for i, line in enumerate(lines_after):
                if line.strip() and not line.strip().startswith('"""') and not line.strip().startswith("#"):
                    # 最初の実行文の前に追加
                    indent = len(line) - len(line.lstrip())
                    if "self.path_service = path_service" not in content:
                        insert_pos = init_body_start + sum(len(l) + 1 for l in lines_after[:i])
                        content = content[:insert_pos] + " " * indent + "self.path_service = path_service\n" + content[insert_pos:]
                    break

        # 3. get_common_path_serviceの使用箇所を修正
        pattern = r"from noveler\.presentation\.cli\.shared_utilities import get_common_path_service\s*\n\s*path_service = get_common_path_service\([^)]+\)"

        def replace_path_service(match):
            # フォールバック処理に置き換え
            return """if not self.path_service:
                # Import moved to top-level
                path_service = get_common_path_service(self._project_root)
            else:
                path_service = self.path_service"""

        content = re.sub(pattern, replace_path_service, content)

        # 4. consoleの使用をロガーに置き換え
        if "from noveler.presentation.shared.shared_utilities import self._console" in content:
            # ILoggerServiceのインポートを追加
            if "from noveler.domain.interfaces.logger_service import noveler.domain.interfaces.logger_service_protocol.ILoggerService" not in content:
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "from noveler.presentation.shared.shared_utilities import self._console" in line:
                        # consoleインポートを削除してロガーインポートに置き換え
                        lines[i] = "from noveler.domain.interfaces.logger_service import noveler.domain.interfaces.logger_service_protocol.ILoggerService"
                        break
                content = "\n".join(lines)

            # self._console.printをロガーに置き換え
            content = re.sub(r'self._console\.print\(f?"?\[bold blue\]([^]]+)\[/bold blue\]"?\)',
                            r'if self._logger:\n            self._self.logger_service.info("\1")', content)
            content = re.sub(r'self._console\.print\("?\[yellow\]([^]]+)\[/yellow\]"?\)',
                            r'if self._logger:\n            self._self.logger_service.info("\1")', content)
            content = re.sub(r'self._console\.print\("?\[bold green\]([^]]+)\[/bold green\]"?\)',
                            r'if self._logger:\n            self._self.logger_service.info("\1")', content)
            content = re.sub(r'self._console\.print\(f?"?\[bold red\]([^]]+)\[/bold red\]"?\)',
                            r'if self._logger:\n            self._self.logger_service.error("\1")', content)

        # 変更があったか確認
        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            return True
        return False

    except Exception as e:
        console.print(f"エラー: {file_path}: {e}")
        return False

def main():
    """メイン処理"""
    use_cases_dir = Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/scripts/application/use_cases")

    # プレゼンテーション層に依存しているファイルを検索
    files_to_fix = []
    for file_path in use_cases_dir.glob("*.py"):
        if file_path.name == "__init__.py":
            continue

        content = file_path.read_text(encoding="utf-8")
        if "from noveler.presentation.shared.shared_utilities" in content:
            files_to_fix.append(file_path)

    console.print(f"修正対象ファイル数: {len(files_to_fix)}")

    fixed_count = 0
    for file_path in files_to_fix:
        console.print(f"修正中: {file_path.name}")
        if fix_use_case_file(file_path):
            fixed_count += 1
            console.print("  ✓ 修正完了")
        else:
            console.print("  - 変更なし")

    console.print(f"\n修正完了: {fixed_count}/{len(files_to_fix)} ファイル")

if __name__ == "__main__":
    main()
