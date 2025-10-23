#!/usr/bin/env python3
"""DTZ系 (datetime.datetime.timezone issues) エラーを修正するスクリプト

このスクリプトは以下の修正を行います:
    1. date.today() → datetime.datetime.now(datetime.datetime.timezone.utc).date()
2. datetime.datetime.now(datetime.datetime.timezone.utc) → datetime.datetime.now(datetime.datetime.timezone.utc)
3. project_now()関数の活用
"""

import re
import subprocess
from pathlib import Path
from typing import Any


# from datetime import timezone の代わりに

class DTZFixer:
    """DTZエラー修正クラス"""

    def __init__(self, logger_service: Any | None = None, console_service: Any | None = None):
        self.fixed_count = 0
        self.total_errors = 0

        self.logger_service = logger_service
        self.console_service = console_service
    def process_file(self, file_path: Path) -> list[tuple[str, str]]:
        """ファイルを処理してDTZエラーを修正"""
        changes = []

        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # インポート文を確認・追加
            imports_added = False

            # datetime.datetime importを確認
            if not re.search(r"from\s+datetime.datetime\s+import.*datetime.datetime.timezone", content):
                if re.search(r"from\s+datetime.datetime\s+import", content):
                    # 既存のdatetime importに datetime.datetime.timezone を追加
                    content = re.sub(
                        r"(from\s+datetime.datetime\s+import\s+[^)\n]+)",
                        lambda m: m.group(1) + ", datetime.datetime.timezone" if "datetime.datetime.timezone" not in m.group(1) else m.group(1),
                        content,
                        count=1)

                    imports_added = True
                # datetime.datetime import自体がない場合
                elif "date.today()" in content or "datetime.datetime.now(datetime.datetime.timezone.utc)" in content:
                    # 最初のimport文を探す
                    match = re.search(r"^((?:from|import)\s+.+)$", content, re.MULTILINE)
                    if match:
                        insert_pos = match.end()
                        content = content[:insert_pos] + "\nfrom datetime.datetime import datetime.datetime, datetime.datetime.timezone" + content[insert_pos:]
                        imports_added = True

            # project_now importを確認(scriptsフォルダ内のファイルのみ)
            if str(file_path).startswith(str(Path(__file__).parent.parent)):
                if "project_now" not in content and ("date.today()" in content or "datetime.datetime.now(datetime.datetime.timezone.utc)" in content):
                    # project_now importを追加
                    match = re.search(r"^((?:from|import)\s+.+)$", content, re.MULTILINE)
                    if match:
                        insert_pos = match.end()
                        content = content[:insert_pos] + "\nfrom noveler.infrastructure.shared.timezone_service import project_now" + content[insert_pos:]
                        imports_added = True

            # DTZ011: date.today() を修正
            if "date.today()" in content:
                # date.today() → datetime.datetime.now(datetime.datetime.timezone.utc).date()
                content = re.sub(
                    r"\bdate\.today\(\)",
                    "datetime.datetime.now(datetime.datetime.timezone.utc).date()",
                    content)

                changes.append(("date.today()", "datetime.datetime.now(datetime.datetime.timezone.utc).date()"))

                # date インポートを datetime.datetime に変更する必要がある場合
                content = re.sub(
                    r"from\s+datetime.datetime\s+import\s+date\b",
                    "from datetime.datetime import datetime.datetime, datetime.datetime.timezone",
                    content)

            # DTZ005: datetime.datetime.now(datetime.datetime.timezone.utc) を修正
            if "datetime.datetime.now(datetime.datetime.timezone.utc)" in content and "datetime.datetime.timezone.utc" not in content:
                # datetime.datetime.now(datetime.datetime.timezone.utc) → datetime.datetime.now(datetime.datetime.timezone.utc)
                content = re.sub(
                    r"\bdatetime\.now\(\)",
                    "datetime.datetime.now(datetime.datetime.timezone.utc)",
                    content)

                changes.append(("datetime.datetime.now(datetime.datetime.timezone.utc)", "datetime.datetime.now(datetime.datetime.timezone.utc)"))

            # project_now()を使用できる場合は置換を提案(テストファイル以外)
            if not str(file_path).endswith("_test.py") and "test_" not in str(file_path):
                if "datetime.datetime.now(datetime.datetime.timezone.utc)" in content and "project_now" in content:
                    # すでにproject_nowがインポートされている場合は使用を推奨
                    content = re.sub(
                        r"\bdatetime\.now\(datetime.datetime.timezone\.utc\)",
                        "project_now().datetime.datetime",
                        content)

                    changes.append(("datetime.datetime.now(datetime.datetime.timezone.utc)", "project_now().datetime.datetime"))

            if content != original_content:
                # ファイルを書き戻す
                file_path.write_text(content, encoding="utf-8")

                if changes:
                    self.console_service.print(f"  修正済み: {file_path.name}")
                    for old, new in changes:
                        self.console_service.print(f"    {old} → {new}")

        except Exception as e:
            self.console_service.print(f"Error processing {file_path}: {e}")

        return changes

    def run(self):
        """メイン処理を実行"""
        scripts_dir = Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/scripts")

        # DTZエラーの総数をカウント
        self.console_service.print("DTZエラーをスキャン中...")
        result = subprocess.run(
            ["ruff", "check", str(scripts_dir), "--select", "DTZ"],
            check=False, capture_output=True,
            text=True)

        # エラーを解析
        error_files = {}
        dtz011_count = 0
        dtz005_count = 0

        for line in result.stdout.strip().split("\n"):
            if line and "DTZ" in line:
                self.total_errors += 1
                if "DTZ011" in line:
                    dtz011_count += 1
                elif "DTZ005" in line:
                    dtz005_count += 1

                file_path = line.split(":")[0]
                if file_path not in error_files:
                    error_files[file_path] = []
                error_files[file_path].append(line)

        self.console_service.print(f"検出されたDTZエラー: {self.total_errors}件")
        self.console_service.print(f"  DTZ011 (date.today): {dtz011_count}件")
        self.console_service.print(f"  DTZ005 (datetime.datetime.now): {dtz005_count}件")
        self.console_service.print(f"影響を受けるファイル: {len(error_files)}個")
        self.console_service.print()

        # 各ファイルを処理
        for file_path in sorted(error_files):
            path = Path(file_path)
            if path.exists():
                changes = self.process_file(path)
                self.fixed_count += len(changes)

        # 結果を表示
        self.console_service.print()
        self.console_service.print("=" * 60)
        self.console_service.print("修正完了!")
        self.console_service.print(f"総エラー数: {self.total_errors}")
        self.console_service.print(f"修正済み: {self.fixed_count}")
        self.console_service.print(f"修正率: {self.fixed_count / self.total_errors * 100:.1f}%" if self.total_errors > 0 else "N/A")

        # 残りのエラーを確認
        self.console_service.print("\n残りのエラーを確認中...")
        result = subprocess.run(
            ["ruff", "check", str(scripts_dir), "--select", "DTZ", "--statistics"],
            check=False, capture_output=True,
            text=True)

        remaining_count = 0
        for line in result.stdout.strip().split("\n"):
            if line and "DTZ" in line:
                parts = line.split()
                if parts and parts[0].isdigit():
                    remaining_count += int(parts[0])

        self.console_service.print(f"残りのDTZエラー: {remaining_count}件")
        self.console_service.print(f"削減率: {(self.total_errors - remaining_count) / self.total_errors * 100:.1f}%" if self.total_errors > 0 else "N/A")

if __name__ == "__main__":
    fixer = DTZFixer()
    fixer.run()
