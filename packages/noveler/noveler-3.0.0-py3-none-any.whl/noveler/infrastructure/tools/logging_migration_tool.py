#!/usr/bin/env python3
"""統一ロギング自動移行ツール

既存のlogging使用箇所を統一ロガーに自動移行するツール
"""

import argparse
import re
from pathlib import Path

from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)


class LoggingMigrationTool:
    """ロギング移行ツール"""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.scripts_dir = project_root / "scripts"

        # 移行パターン定義
        self.import_patterns = [
            # Standard logging import
            (r"^import logging$", "from noveler.infrastructure.logging.unified_logger import get_logger"),
            # From logging import
            (r"^from logging import.*$", "from noveler.infrastructure.logging.unified_logger import get_logger"),
        ]

        self.logger_patterns = [
            # get_logger(__name__)
            (r"logging\.getLogger\(__name__\)", "get_logger(__name__)"),
            # get_logger("name")
            (r'logging\.getLogger\("([^"]+)"\)', r'get_logger("\1")'),
            # get_logger('name')
            (r"logging\.getLogger\('([^']+)'\)", r"get_logger('\1')"),
            # self.logger = get_logger(...)
            (r"self\.logger = logging\.getLogger\(([^)]+)\)", r"self.logger = get_logger(\1)"),
            # logger = get_logger(...)
            (r"logger = logging\.getLogger\(([^)]+)\)", r"logger = get_logger(\1)"),
        ]

        # 除外ファイル
        self.excluded_files = {
            "noveler/infrastructure/logging/logger.py",
            "noveler/infrastructure/logging/unified_logger.py",
            "noveler/conftest.py",  # テスト設定は除外
        }

    def scan_files(self) -> list[Path]:
        """Python ファイルをスキャン"""
        python_files = []

        for py_file in self.scripts_dir.rglob("*.py"):
            relative_path = py_file.relative_to(self.project_root)
            if str(relative_path) not in self.excluded_files:
                python_files.append(py_file)

        return python_files

    def analyze_file(self, file_path: Path) -> dict[str, list[tuple[int, str]]]:
        """ファイルの移行箇所を分析"""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()
        except Exception as e:
            logger.exception("ファイル読み取りエラー: %s - %s", file_path, e)
            return {}

        issues = {"imports": [], "loggers": [], "direct_logging": []}

        for line_num, line in enumerate(lines, 1):
            # Import文チェック
            for pattern, _ in self.import_patterns:
                if re.search(pattern, line.strip()):
                    issues["imports"].append((line_num, line.strip()))

            # ロガー使用チェック
            for pattern, _ in self.logger_patterns:
                if re.search(pattern, line):
                    issues["loggers"].append((line_num, line.strip()))

            # 直接ロギング使用チェック
            if re.search(r"logging\.(debug|info|warning|error|critical)", line):
                issues["direct_logging"].append((line_num, line.strip()))

        return issues

    def migrate_file(self, file_path: Path, dry_run: bool = True) -> bool:
        """ファイルを移行"""
        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # Import文の置換
            for pattern, replacement in self.import_patterns:
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

            # ロガー使用の置換
            for pattern, replacement in self.logger_patterns:
                content = re.sub(pattern, replacement, content)

            # 変更があるかチェック
            if content == original_content:
                return False

            if not dry_run:
                file_path.write_text(content, encoding="utf-8")
                self.logger_service.info("移行完了: %s", (file_path.relative_to(self.project_root)))
            else:
                self.logger_service.info("移行対象: %s", (file_path.relative_to(self.project_root)))

            return True

        except Exception as e:
            logger.exception("ファイル移行エラー: %s - %s", file_path, e)
            return False

    def generate_report(self, files: list[Path]) -> dict[str, int]:
        """移行レポート生成"""
        report = {
            "total_files": len(files),
            "files_with_imports": 0,
            "files_with_loggers": 0,
            "files_with_direct_logging": 0,
            "total_import_issues": 0,
            "total_logger_issues": 0,
            "total_direct_issues": 0,
        }

        for file_path in files:
            issues = self.analyze_file(file_path)

            if issues["imports"]:
                report["files_with_imports"] += 1
                report["total_import_issues"] += len(issues["imports"])

            if issues["loggers"]:
                report["files_with_loggers"] += 1
                report["total_logger_issues"] += len(issues["loggers"])

            if issues["direct_logging"]:
                report["files_with_direct_logging"] += 1
                report["total_direct_issues"] += len(issues["direct_logging"])

        return report

    def run_migration(self, dry_run: bool = True, layer_filter: str | None = None) -> int:
        """移行実行"""
        files = self.scan_files()

        # レイヤーフィルタリング
        if layer_filter:
            layer_path = f"noveler/{layer_filter}"
            files = [f for f in files if layer_path in str(f)]

        self.logger_service.info("スキャン対象ファイル数: %s", (len(files)))

        # レポート生成
        report = self.generate_report(files)
        self._print_report(report)

        if dry_run:
            self.logger_service.info("DRY RUN: 実際の変更は行いません")

        # 移行実行
        migrated_count = 0
        for file_path in files:
            if self.migrate_file(file_path, dry_run):
                migrated_count += 1

        self.logger_service.info("移行完了ファイル数: %s", migrated_count)
        return migrated_count

    def _print_report(self, report: dict[str, int]) -> None:
        """レポート出力"""
        self.logger_service.info("=== 移行レポート ===")
        self.logger_service.info(f"総ファイル数: {report['total_files']}")
        self.logger_service.info(
            f"Import修正対象: {report['files_with_imports']} ファイル ({report['total_import_issues']} 箇所)"
        )
        self.logger_service.info(
            f"Logger修正対象: {report['files_with_loggers']} ファイル ({report['total_logger_issues']} 箇所)"
        )
        self.logger_service.info(
            f"直接ロギング対象: {report['files_with_direct_logging']} ファイル ({report['total_direct_issues']} 箇所)"
        )


def main() -> None:
    """メイン実行関数"""
    # B30品質基準準拠: 依存性注入パターンでlogger_serviceを注入
    from noveler.infrastructure.di.container import resolve_service

    try:
        logger_service = resolve_service("ILoggerService")
    except ValueError:
        # DIコンテナが初期化されていない場合のフォールバック
        from noveler.infrastructure.adapters.logger_service_adapter import LoggerServiceAdapter

        logger_service = LoggerServiceAdapter("noveler.logging_migration")
    parser = argparse.ArgumentParser(description="統一ロギング自動移行ツール")
    parser.add_argument(
        "--project-root", type=Path, default=Path.cwd(), help="プロジェクトルートパス (default: 現在のディレクトリ)"
    )
    parser.add_argument("--dry-run", action="store_true", default=True, help="ドライラン実行 (実際の変更なし)")
    parser.add_argument("--execute", action="store_true", help="実際に変更を実行")
    parser.add_argument("--layer", choices=["infrastructure", "application", "domain"], help="特定レイヤーのみ移行")
    parser.add_argument("--report-only", action="store_true", help="レポートのみ生成")

    args = parser.parse_args()

    # dry-runのデフォルトを調整
    dry_run = not args.execute

    tool = LoggingMigrationTool(args.project_root)

    if args.report_only:
        files = tool.scan_files()
        if args.layer:
            layer_path = f"noveler/{args.layer}"
            files = [f for f in files if layer_path in str(f)]

        report = tool.generate_report(files)
        tool._print_report(report)
        return

    migrated_count = tool.run_migration(dry_run=dry_run, layer_filter=args.layer)

    if migrated_count > 0 and not dry_run:
        logger_service.info("移行が完了しました。テスト実行を推奨します:")
        logger_service.info("python -m pytest noveler/tests/")


if __name__ == "__main__":
    main()
