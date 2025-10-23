#!/usr/bin/env python3
"""統一ロギング品質ゲート

レガシーロギングの使用を検出し、統一ロガーの使用を強制する品質チェック
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)


class UnifiedLoggingGate:
    """統一ロギング品質ゲート"""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.scripts_dir = project_root / "scripts"
        self.src_dir = project_root / "src"
        # デフォルトのロガーサービス（DI未初期化時のフォールバック）
        self.logger_service = logger

        # レガシーパターン（禁止）
        self.legacy_patterns = [
            # Standard logging import
            (r"^\s*import logging\s*$", "レガシーloggingインポート"),
            # From logging import
            (r"^\s*from logging import", "レガシーloggingインポート"),
            # legacy logger getter usage
            (r"logging\.getLogger\(", "レガシーlogging.getLogger使用"),
            # Direct logging calls
            (r"logging\.(debug|info|warning|error|critical)\(", "レガシー直接ロギング使用"),
        ]

        # 除外ファイル（完全一致）: src/ 有無の両形式を許容
        self.excluded_files = {
            # logging 基盤
            "noveler/infrastructure/logging/logger.py",
            "noveler/infrastructure/logging/unified_logger.py",
            "noveler/infrastructure/logging/error_logger.py",
            "src/noveler/infrastructure/logging/logger.py",
            "src/noveler/infrastructure/logging/unified_logger.py",
            "src/noveler/infrastructure/logging/error_logger.py",
            # テスト設定/補助
            "noveler/conftest.py",
            "noveler/infrastructure/shared/test_cleanup_manager.py",
            "src/noveler/conftest.py",
            "src/noveler/infrastructure/shared/test_cleanup_manager.py",
        }

        # 除外ディレクトリ（前方一致）
        self.excluded_dirs = {
            "scripts/",           # 運用スクリプト群
            "tests/",             # テストコード
            "src/noveler/tools/", # ツール群（ドキュメント・補助）
            "src/noveler/infrastructure/logging/", # ロギング基盤
        }

    def scan_files(self) -> list[Path]:
        """Python ファイルをスキャン"""
        python_files: list[Path] = []

        for base_dir in (self.scripts_dir, self.src_dir):
            if not base_dir.exists():
                continue
            for py_file in base_dir.rglob("*.py"):
                relative_path = py_file.relative_to(self.project_root)
                rel = str(relative_path)
                # ディレクトリ除外
                if any(rel.startswith(prefix) for prefix in self.excluded_dirs):
                    continue
                # ファイル完全一致除外
                if rel in self.excluded_files:
                    continue
                python_files.append(py_file)

        return python_files

    def check_file(self, file_path: Path) -> list[tuple[int, str, str]]:
        """ファイルのレガシーロギング使用をチェック"""
        violations: list[Any] = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()
        except Exception as e:
            logger.exception("ファイル読み取りエラー: %s - %s", file_path, e)
            return violations

        for line_num, line in enumerate(lines, 1):
            for pattern, description in self.legacy_patterns:
                if re.search(pattern, line):
                    violations.append((line_num, line.strip(), description))

        return violations

    def run_check(self, fail_on_error: bool = True) -> bool:
        """品質チェック実行"""
        files = self.scan_files()
        total_violations = 0
        failed_files = []

        self.logger_service.info("統一ロギング品質チェック開始: %s ファイルを検査", (len(files)))

        for file_path in files:
            violations: Any = self.check_file(file_path)

            if violations:
                relative_path = file_path.relative_to(self.project_root)
                failed_files.append(str(relative_path))
                total_violations += len(violations)

                self.logger_service.error("❌ レガシーロギング検出: %s", relative_path)
                for line_num, line, description in violations:
                    self.logger_service.error("  L%s: %s", line_num, description)
                    self.logger_service.error("    %s", line)

        # 結果報告
        if total_violations == 0:
            self.logger_service.info("✅ 統一ロギング品質チェック: 全てパス")
            return True
        self.logger_service.error("❌ 統一ロギング品質チェック: %s 件の違反", total_violations)
        self.logger_service.error("対象ファイル: %s / %s", (len(failed_files)), (len(files)))

        if fail_on_error:
            self.logger_service.error("品質ゲート: 失敗")
            return False
        self.logger_service.warning("品質ゲート: 警告のみ")
        return True

    def generate_fix_suggestions(self) -> dict[str, list[str]]:
        """修正提案を生成"""
        return {
            "import_fixes": [
                "❌ import logging",
                "✅ from noveler.infrastructure.logging.unified_logger import get_logger",
            ],
            "logger_fixes": ["❌ # logger_service経由で注入", "✅ logger = get_logger(__name__)"],
            "migration_command": [
                "自動修正コマンド:",
                "python scripts/infrastructure/tools/logging_migration_tool.py --execute",
            ],
        }



def main() -> None:
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="統一ログ品質ゲート")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="プロジェクトルートパス")
    parser.add_argument("--fail-on-error", action="store_true", default=True, help="エラー時に失敗終了")
    parser.add_argument("--warn-only", action="store_true", help="警告のみ（失敗しない）")
    parser.add_argument("--suggest-fixes", action="store_true", help="修正提案を表示")

    args = parser.parse_args()

    # B30品質基準準拠: 依存性注入パターンでlogger_serviceを注入
    from noveler.infrastructure.di.container import resolve_service

    try:
        logger_service = resolve_service("ILogger")
    except ValueError:
        # DIコンテナが初期化されていない場合のフォールバック
        from noveler.infrastructure.adapters.domain_logger_adapter import DomainLoggerAdapter
        logger_service = DomainLoggerAdapter()

    gate = UnifiedLoggingGate(args.project_root)

    # 修正提案表示
    if args.suggest_fixes:
        suggestions = gate.generate_fix_suggestions()
        logger_service.info("=== 修正提案 ===")
        for category, items in suggestions.items():
            logger_service.info("\n%s:", category)
            for item in items:
                logger_service.info("  %s", item)
        return

    # 品質チェック実行
    fail_on_error = not args.warn_only
    success = gate.run_check(fail_on_error=fail_on_error)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
