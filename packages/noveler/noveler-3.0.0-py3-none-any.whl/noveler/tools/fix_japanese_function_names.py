#!/usr/bin/env python3
"""日本語を含む関数名を英語に翻訳するスクリプト"""

import re
import subprocess
from pathlib import Path
from typing import Any

class JapaneseFunctionNameFixer:
    """日本語関数名を英語に修正するクラス"""

    def __init__(self, logger_service: Any | None = None, console_service: Any | None = None):
        # 日本語パターンと英語訳のマッピング
        self.translations = {
            # 基本動詞
            "creation": "creation",
            "できる": "_possible",
            "する": "",
            "される": "_is_done",
            "した": "_done",
            "している": "_is_doing",

            # 基本名詞
            "固有名詞": "proper_noun",
            "コレクション": "collection",
            "マージ": "merge",
            "差分": "diff",
            "重複": "duplicate",
            "用語": "terms",
            "自動": "auto",
            "integration": "integration",
            "ファイル": "file",
            "変更": "change",
            "イベント": "event",
            "configuration": "configuration",
            "ディレクトリ": "directory",
            "監視対象": "watch_target",
            "init状態": "initial_state",
            "記録": "record",
            "判定": "determine",
            "judge": "judge",
            "extract": "extract",
            "必要": "required",
            "状態": "state",

            # 助詞
            "を": "_",
            "が": "_",
            "に": "_",
            "で": "_",
            "と": "_",
            "は": "_",
            "の": "_",
            "から": "_from_",
            "へ": "_to_",
            "まで": "_until_",
            "より": "_than_",
            "かどうか": "_or_not",
            "か": "_",

            # 複合パターン
            "空の": "empty_",
            "コレクションをマージ": "merge_collections",
            "差分をget": "get_diff",
            "重複する": "duplicate_",
            "自動でintegration_": "auto_integrated_",
            "ファイル変更イベント": "file_change_event",
            "configurationファイル": "configuration_file",
            "固有名詞extract": "proper_noun_extraction",
            "監視対象にconfiguration": "configure_as_watch_target",
            "ファイル状態": "file_state",
        }

        self.fixed_count = 0
        self.total_count = 0

        self.logger_service = logger_service
        self.console_service = console_service
    def translate_japanese(self, text: str) -> str:
        """日本語を英語に翻訳"""
        # まず複合パターンを処理
        for jp, en in sorted(self.translations.items(), key=lambda x: len(x[0]), reverse=True):
            text = text.replace(jp, en)

        # 残った日本語文字を削除
        text = re.sub(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+", "", text)

        # 連続するアンダースコアを1つに
        text = re.sub(r"_+", "_", text)

        # 先頭と末尾のアンダースコアを削除
        text = text.strip("_")

        # 空文字列になった場合
        if not text:
            text = "unnamed"

        return text

    def fix_function_name(self, name: str) -> str:
        """関数名を修正"""
        # 既に正しい形式の場合はそのまま返す
        if re.match(r"^[a-z_][a-z0-9_]*$", name):
            return name

        # test_プレフィックスを保持
        if name.startswith("test_"):
            prefix = "test_"
            name_body = name[5:]
        else:
            prefix = ""
            name_body = name

        # 日本語を翻訳
        translated = self.translate_japanese(name_body)

        # CamelCaseをsnake_caseに変換
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", translated)
        s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
        translated = s2.lower()

        # 最終的なクリーンアップ
        translated = re.sub(r"_+", "_", translated)
        translated = translated.strip("_")

        return prefix + translated

    def process_file(self, file_path: Path) -> list[tuple[str, str]]:
        """ファイルを処理して日本語関数名を修正"""
        changes = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines(keepends=True)

            # 関数定義を探して修正
            for i, line in enumerate(lines):
                # 関数定義のパターン
                match = re.match(r"^(\s*)(async\s+)?def\s+([^\s(]+)\s*\(", line)
                if match and re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", match.group(3)):
                    indent = match.group(1)
                    async_keyword = match.group(2) or ""
                    old_name = match.group(3)
                    new_name = self.fix_function_name(old_name)

                    if old_name != new_name:
                        # 関数定義行を置換
                        new_line = line.replace(f"def {old_name}(", f"def {new_name}(")
                        if async_keyword:
                            new_line = new_line.replace(f"async def {old_name}(", f"async def {new_name}(")
                        lines[i] = new_line
                        changes.append((old_name, new_name))

                        # ファイル全体で関数呼び出しも置換
                        for j, other_line in enumerate(lines):
                            if i != j:  # 定義行以外:
                                # 単純な文字列置換
                                lines[j] = lines[j].replace(f"{old_name}(", f"{new_name}(")
                                lines[j] = lines[j].replace(f".{old_name}(", f".{new_name}(")

            if changes:
                # ファイルを書き戻す
                file_path.write_text("".join(lines), encoding="utf-8")
                self.console_service.print(f"  修正済み: {file_path.name}")
                for old, new in changes:
                    self.console_service.print(f"    {old} → {new}")

        except Exception as e:
            self.console_service.print(f"Error processing {file_path}: {e}")

        return changes

    def run(self):
        """メイン処理を実行"""
        scripts_dir = Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/scripts")

        # N802エラーのあるファイルを取得
        self.console_service.print("日本語関数名を含むファイルを検索中...")
        result = subprocess.run(
            ["ruff", "check", str(scripts_dir), "--select", "N802"],
            check=False, capture_output=True,
            text=True)

        # エラーファイルを収集
        error_files = set()
        for line in result.stdout.strip().split("\n"):
            if line and "N802" in line:
                # 日本語を含むエラーのみ対象
                if re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", line):
                    self.total_count += 1
                    file_path = line.split(":")[0]
                    error_files.add(file_path)

        self.console_service.print(f"検出された日本語関数名エラー: {self.total_count}件")
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
        self.console_service.print(f"総エラー数: {self.total_count}")
        self.console_service.print(f"修正済み: {self.fixed_count}")
        self.console_service.print(f"修正率: {self.fixed_count / self.total_count * 100:.1f}%" if self.total_count > 0 else "N/A")

        # 残りのエラーを確認
        self.console_service.print("\n残りのエラーを確認中...")
        result = subprocess.run(
            ["ruff", "check", str(scripts_dir), "--select", "N802", "--statistics"],
            check=False, capture_output=True,
            text=True)

        remaining_count = 0
        for line in result.stdout.strip().split("\n"):
            if line and "N802" in line:
                parts = line.split()
                if parts and parts[0].isdigit():
                    remaining_count = int(parts[0])

        self.console_service.print(f"残りのN802エラー: {remaining_count}件")

if __name__ == "__main__":
    fixer = JapaneseFunctionNameFixer()
    fixer.run()
