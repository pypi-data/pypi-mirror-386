#!/usr/bin/env python3
"""シンプル品質チェッカー

レガシーintegrated_quality_checker.pyの代替として、
基本的な品質チェック機能を提供します。
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any


class SimpleQualityChecker:
    """シンプルな品質チェッカー"""

    def __init__(self, logger_service: Any | None = None, console_service: Any | None = None) -> None:
        self.issues = []
        self.score = 0.0

        self.logger_service = logger_service
        self.console_service = console_service
    def check_file(self, filepath: Path, auto_fix: bool = False) -> bool:
        """ファイルの品質チェック"""
        if not filepath.exists():
            self.console_service.print(f"❌ ファイルが見つかりません: {filepath}")
            return False

        try:
            content = filepath.read_text(encoding="utf-8")
            self.console_service.print(f"🔍 品質チェック実行中: {filepath.name}")

            # 基本的なチェック
            self._check_basic_issues(content)
            self._check_composition(content)
            self._calculate_score()

            # 結果表示
            self._display_results(auto_fix)

            return len(self.issues) == 0

        except Exception as e:
            self.console_service.print(f"❌ エラー: {e}")
            return False

    def _check_basic_issues(self, content: str) -> None:
        """基本的な問題をチェック"""
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # 連続する句読点
            if re.search(r"[。、]{2,}", line):
                self.issues.append(f"行 {i}: 連続する句読点")

            # 行頭スペース
            if line.startswith((" ", " ")):
                self.issues.append(f"行 {i}: 行頭に不要なスペース")

            # 長すぎる行
            if len(line) > 100:
                self.issues.append(f"行 {i}: 行が長すぎます ({len(line)}文字)")

    def _check_composition(self, content: str) -> None:
        """文章構成をチェック"""
        # 段落数チェック
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if len(paragraphs) < 3:
            self.issues.append("段落数が少なすぎます(3段落以上推奨)")

        # 文字数チェック
        char_count = len(content.replace("\n", "").replace(" ", ""))
        if char_count < 500:
            self.issues.append(f"文字数が不足しています ({char_count}文字、500文字以上推奨)")

    def _calculate_score(self) -> None:
        """スコア計算"""
        base_score = 100.0
        penalty = len(self.issues) * 5
        self.score = max(0, base_score - penalty)

    def _display_results(self, auto_fix: bool) -> None:
        """結果表示"""
        self.console_service.print("\n📊 品質チェック結果")
        self.console_service.print(f"総合スコア: {self.score:.1f}")

        if self.score >= 90:
            grade = "A"
        elif self.score >= 80:
            grade = "B"
        elif self.score >= 70:
            grade = "C"
        else:
            grade = "D"

        self.console_service.print(f"評価: {grade}")

        if self.issues:
            self.console_service.print(f"\n📋 発見された問題 ({len(self.issues)}件):")
            for issue in self.issues[:10]:  # 最初の10件のみ表示
                self.console_service.print(f"  • {issue}")

            if len(self.issues) > 10:
                self.console_service.print(f"  ... 他 {len(self.issues) - 10} 件")

            if auto_fix:
                self.console_service.print("\n🔧 自動修正機能は実装中です")
        else:
            self.console_service.print("\n✅ 問題は見つかりませんでした")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="シンプル品質チェッカー")
    parser.add_argument("target", help="チェック対象ファイル")
    parser.add_argument("--auto-fix", action="store_true", help="自動修正(実装中)")

    args = parser.parse_args()

    checker = SimpleQualityChecker()
    success = checker.check_file(Path(args.target), args.auto_fix)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
