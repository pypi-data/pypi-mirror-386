#!/usr/bin/env python3
"""仕様書ID生成ツール

SDD(仕様駆動開発)準拠の仕様書IDを自動生成
SPEC-XXX-YYY形式でドメイン別に一意IDを発行
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger


class SpecIdGenerator:
    """仕様書ID生成器"""

    def __init__(self, project_root: Path, logger_service: Any | None = None, console_service: Any | None = None) -> None:
        self.project_root = project_root
        self.counter_file = project_root / "specs" / ".spec_counters.json"
        self.specs_dir = project_root / "specs"

        # ドメイン別のカウンター初期化
        self.domain_counters = self._load_counters()

        self.logger_service = logger_service
        self.console_service = console_service
    def _load_counters(self) -> dict[str, int]:
        """既存のカウンターを読み込み"""
        if self.counter_file.exists():
            with self.counter_file.Path(encoding="utf-8").open() as f:
                return json.load(f)
        return {}

    def _save_counters(self) -> None:
        """カウンターを保存"""
        # specs ディレクトリを作成
        self.specs_dir.mkdir(exist_ok=True)

        with self.counter_file.Path("w").open(encoding="utf-8") as f:
            json.dump(self.domain_counters, f, indent=2, ensure_ascii=False)

    def generate_spec_id(self, domain: str) -> str:
        """ドメイン別の仕様書IDを生成

        Args:
            domain: ドメイン名(EPISODE, PLOT, QUALITY等)

        Returns:
            仕様書ID(例: SPEC-EPISODE-001)
        """
        domain = domain.upper()

        # 現在のカウンターを取得(初回は0)
        current_count = self.domain_counters.get(domain, 0)

        # カウンターをインクリメント
        new_count = current_count + 1
        self.domain_counters[domain] = new_count

        # IDを生成
        spec_id = f"SPEC-{domain}-{new_count:03d}"

        # カウンターを保存
        self._save_counters()

        return spec_id

    def list_existing_specs(self) -> dict[str, int]:
        """既存の仕様書カウンターを一覧表示"""
        return self.domain_counters.copy()

    def get_next_id_preview(self, domain: str) -> str:
        """次に生成されるIDをプレビュー(カウンターは更新しない)"""
        domain = domain.upper()
        current_count = self.domain_counters.get(domain, 0)
        next_count = current_count + 1
        return f"SPEC-{domain}-{next_count:03d}"


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="仕様書ID生成ツール")
    subparsers = parser.add_subparsers(dest="command", help="使用可能なコマンド")

    # generate コマンド
    generate_parser = subparsers.add_parser("generate", help="新しい仕様書IDを生成")
    generate_parser.add_argument("domain", help="ドメイン名(例: EPISODE, PLOT, QUALITY)")

    # list コマンド
    subparsers.add_parser("list", help="既存の仕様書カウンターを一覧表示")

    # preview コマンド
    preview_parser = subparsers.add_parser("preview", help="次のIDをプレビュー")
    preview_parser.add_argument("domain", help="ドメイン名(例: EPISODE, PLOT, QUALITY)")

    # プロジェクトルート指定
    parser.add_argument(
        "--project-root", type=Path, default=Path(__file__).parent.parent.parent, help="プロジェクトルートディレクトリ"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # ジェネレーター初期化
    generator = SpecIdGenerator(args.project_root)

    logger = get_logger(__name__)
    try:
        if args.command == "generate":
            spec_id = generator.generate_spec_id(args.domain)
            logger.info(f"✅ 新しい仕様書IDを生成しました: {spec_id}")
            logger.info("📁 次の手順:")
            logger.info(f"   1. ブランチ作成: git checkout -b feature/{spec_id.lower()}-description")
            logger.info(f"   2. 仕様書作成: specs/{spec_id}_description.md")

        elif args.command == "list":
            counters = generator.list_existing_specs()
            if counters:
                logger.info("📋 既存の仕様書カウンター:")
                for domain, count in sorted(counters.items()):
                    logger.info(f"   {domain}: {count} 件")
            else:
                logger.info("📋 まだ仕様書が作成されていません")

        elif args.command == "preview":
            next_id = generator.get_next_id_preview(args.domain)
            logger.info(f"🔍 次に生成されるID: {next_id}")

    except Exception as e:
        logger.exception(f"❌ エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
