#!/usr/bin/env python3
"""仕様書標準化ツール

既存の仕様書を標準フォーマットに変換し、E2Eテストとの紐付けを管理する。
SPEC-{CATEGORY}-{NUMBER}形式への統一と test_type の付与を行う。
"""

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.logging.unified_logger import get_logger


@dataclass
class SpecInfo:
    """仕様書情報"""
    file_path: Path
    original_name: str
    spec_id: str | None = None
    category: str | None = None
    test_type: str | None = None
    has_standard_format: bool = False
    needs_migration: bool = True


@dataclass
class SpecCategory:
    """仕様カテゴリ定義"""
    name: str
    prefix: str
    description: str
    patterns: list[str] = field(default_factory=list)


class SpecStandardizer:
    """仕様書標準化クラス"""

    # カテゴリ定義
    CATEGORIES = [
        SpecCategory(
            name="EPISODE",
            prefix="SPEC-EPISODE",
            description="エピソード管理関連",
            patterns=["episode", "エピソード"]
        ),
        SpecCategory(
            name="QUALITY",
            prefix="SPEC-QUALITY",
            description="品質管理・チェック関連",
            patterns=["quality", "品質", "check", "チェック"]
        ),
        SpecCategory(
            name="PLOT",
            prefix="SPEC-PLOT",
            description="プロット生成・管理関連",
            patterns=["plot", "プロット"]
        ),
        SpecCategory(
            name="CLAUDE",
            prefix="SPEC-CLAUDE",
            description="Claude Code連携関連",
            patterns=["claude", "Claude"]
        ),
        SpecCategory(
            name="CONFIG",
            prefix="SPEC-CONFIG",
            description="設定管理関連",
            patterns=["config", "設定", "configuration"]
        ),
        SpecCategory(
            name="WORKFLOW",
            prefix="SPEC-WORKFLOW",
            description="ワークフロー・プロセス関連",
            patterns=["workflow", "process", "ワークフロー"]
        ),
        SpecCategory(
            name="YAML",
            prefix="SPEC-YAML",
            description="YAML処理関連",
            patterns=["yaml", "YAML"]
        ),
        SpecCategory(
            name="CLI",
            prefix="SPEC-CLI",
            description="CLI関連",
            patterns=["cli", "CLI", "command"]
        ),
        SpecCategory(
            name="DOMAIN",
            prefix="SPEC-DOMAIN",
            description="ドメインモデル関連",
            patterns=["entity", "value_object", "domain", "エンティティ"]
        ),
    ]

    def __init__(self, specs_dir: Path, logger_service: Any | None = None, console_service: Any | None = None) -> None:
        """初期化

        Args:
            specs_dir: 仕様書ディレクトリパス
        """
        self.specs_dir = specs_dir
        self.spec_counter: dict[str, int] = {}
        self._load_existing_counters()

        self.logger_service = logger_service
        self.console_service = console_service
    def _load_existing_counters(self) -> None:
        """既存のSPEC番号カウンターを読み込み"""
        counter_file = self.specs_dir / ".spec_counters.json"
        if counter_file.exists():
            with counter_file.open(encoding="utf-8") as f:
                self.spec_counter = json.load(f)
        else:
            # 既存のSPEC-*ファイルから最大番号を取得
            for spec_file in self.specs_dir.glob("SPEC-*.md"):
                match = re.match(r"SPEC-([A-Z]+)-(\d+)", spec_file.stem)
                if match:
                    category = match.group(1)
                    number = int(match.group(2))
                    if category not in self.spec_counter:
                        self.spec_counter[category] = 0
                    self.spec_counter[category] = max(self.spec_counter[category], number)

    def analyze_specs(self) -> list[SpecInfo]:
        """仕様書ディレクトリを分析

        Returns:
            仕様書情報のリスト
        """
        specs = []

        # すべての.mdファイルを検査
        for md_file in self.specs_dir.glob("*.md"):
            if md_file.name == "README.md":
                continue

            spec_info = self._analyze_single_spec(md_file)
            specs.append(spec_info)

        # .spec.md ファイルも検査
        for spec_file in self.specs_dir.glob("*.spec.md"):
            spec_info = self._analyze_single_spec(spec_file)
            specs.append(spec_info)

        return specs

    def _analyze_single_spec(self, file_path: Path) -> SpecInfo:
        """単一の仕様書を分析

        Args:
            file_path: 仕様書ファイルパス

        Returns:
            仕様書情報
        """
        spec_info = SpecInfo(
            file_path=file_path,
            original_name=file_path.name
        )

        # 標準形式かチェック
        if file_path.stem.startswith("SPEC-"):
            match = re.match(r"SPEC-([A-Z]+)-(\d+)", file_path.stem)
            if match:
                spec_info.has_standard_format = True
                spec_info.spec_id = f"SPEC-{match.group(1)}-{match.group(2)}"
                spec_info.category = match.group(1)
                spec_info.needs_migration = False

        # .spec.md形式の場合はカテゴリを推定
        if file_path.suffix == ".md" and file_path.stem.endswith(".spec"):
            spec_info.category = self._infer_category(file_path.stem)
            spec_info.test_type = self._infer_test_type(file_path)

        return spec_info

    def _infer_category(self, filename: str) -> str:
        """ファイル名からカテゴリを推定

        Args:
            filename: ファイル名

        Returns:
            推定されたカテゴリ
        """
        filename_lower = filename.lower()

        for category in self.CATEGORIES:
            for pattern in category.patterns:
                if pattern.lower() in filename_lower:
                    return category.name

        return "GENERAL"  # デフォルトカテゴリ

    def _infer_test_type(self, file_path: Path) -> str:
        """仕様書内容からtest_typeを推定

        Args:
            file_path: ファイルパス

        Returns:
            推定されたtest_type
        """
        content = file_path.read_text(encoding="utf-8")
        content_lower = content.lower()

        # E2Eテストのキーワード
        if any(keyword in content_lower for keyword in
               ["e2e", "end-to-end", "ユーザーシナリオ", "フロー", "workflow"]):
            return "e2e"

        # 統合テストのキーワード
        if any(keyword in content_lower for keyword in
               ["integration", "統合", "連携", "repository", "adapter"]):
            return "integration"

        # デフォルトは単体テスト
        return "unit"

    def generate_spec_id(self, category: str) -> str:
        """新しい仕様IDを生成

        Args:
            category: カテゴリ名

        Returns:
            生成された仕様ID
        """
        if category not in self.spec_counter:
            self.spec_counter[category] = 0

        self.spec_counter[category] += 1
        return f"SPEC-{category}-{self.spec_counter[category]:03d}"

    def standardize_spec(self, spec_info: SpecInfo) -> tuple[str, str]:
        """仕様書を標準化

        Args:
            spec_info: 仕様書情報

        Returns:
            (新しいファイル名, 更新された内容)
        """
        if spec_info.has_standard_format:
            return spec_info.file_path.name, spec_info.file_path.read_text(encoding="utf-8")

        # 新しいSPEC IDを生成
        if not spec_info.spec_id:
            spec_info.spec_id = self.generate_spec_id(spec_info.category)

        # 新しいファイル名を生成
        base_name = spec_info.file_path.stem.replace(".spec", "")
        new_filename = f"{spec_info.spec_id}_{base_name}.md"

        # 内容を更新
        content = spec_info.file_path.read_text(encoding="utf-8")
        updated_content = self._update_spec_content(content, spec_info)

        return new_filename, updated_content

    def _update_spec_content(self, content: str, spec_info: SpecInfo) -> str:
        """仕様書の内容を更新してメタデータを追加

        Args:
            content: 元の内容
            spec_info: 仕様書情報

        Returns:
            更新された内容
        """
        # 既存のタイトルを検索
        lines = content.split("\n")
        title_line = 0
        for i, line in enumerate(lines):
            if line.startswith("# "):
                title_line = i
                break

        # メタデータセクションを作成
        metadata_section = f"""
## メタデータ

| 項目 | 内容 |
|------|------|
| 仕様ID | {spec_info.spec_id} |
| E2EテストID | E2E-{spec_info.category}-{spec_info.spec_id.split('-')[-1]} |
| test_type | {spec_info.test_type or 'unit'} |
| バージョン | v1.0.0 |
| 作成日 | {project_now().datetime.strftime('%Y-%m-%d')} |
| 最終更新 | {project_now().datetime.strftime('%Y-%m-%d')} |
| ステータス | draft |

"""

        # タイトル行の後にメタデータを挿入
        if title_line > 0:
            lines.insert(title_line + 1, metadata_section)

        # タイトルも更新
        if title_line >= 0:
            original_title = lines[title_line].replace("# ", "").strip()
            lines[title_line] = f"# {spec_info.spec_id}: {original_title}"

        return "\n".join(lines)

    def generate_migration_report(self, specs: list[SpecInfo]) -> str:
        """移行レポートを生成

        Args:
            specs: 仕様書情報リスト

        Returns:
            マークダウン形式のレポート
        """
        report = f"""# 仕様書標準化移行レポート

生成日時: {project_now().datetime.strftime('%Y-%m-%d %H:%M:%S')}

## サマリ

- 総ファイル数: {len(specs)}
- 標準形式: {sum(1 for s in specs if s.has_standard_format)}
- 要移行: {sum(1 for s in specs if s.needs_migration)}

## カテゴリ別集計

"""
        # カテゴリ別に集計
        category_counts = {}
        for spec in specs:
            cat = spec.category or "UNKNOWN"
            if cat not in category_counts:
                category_counts[cat] = 0
            category_counts[cat] += 1

        for cat, count in sorted(category_counts.items()):
            report += f"- {cat}: {count}件\n"

        report += "\n## 移行対象ファイル\n\n"
        report += "| 元ファイル名 | 推定カテゴリ | 新SPEC ID | test_type |\n"
        report += "|-------------|-------------|-----------|----------|\n"

        for spec in specs:
            if spec.needs_migration:
                new_id = spec.spec_id or f"SPEC-{spec.category}-XXX"
                report += f"| {spec.original_name} | {spec.category} | {new_id} | {spec.test_type} |\n"

        return report

def main():
    """メイン処理"""

    parser = argparse.ArgumentParser(description="仕様書標準化ツール")
    parser.add_argument(
        "--specs-dir",
        type=Path,
        default=Path("specs"),
        help="仕様書ディレクトリ"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際の変更を行わず、レポートのみ生成"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="実際の移行を実行（ファイル名変更と内容更新）"
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=Path("specs/MIGRATION_REPORT.md"),
        help="移行レポート出力先"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="一度に処理するファイル数（デフォルト: 10）"
    )

    args = parser.parse_args()

    # 標準化処理実行
    standardizer = SpecStandardizer(args.specs_dir)
    specs = standardizer.analyze_specs()

    # レポート生成
    report = standardizer.generate_migration_report(specs)

    logger = get_logger(__name__)
    if args.dry_run:
        logger.info("=== DRY RUN MODE ===")
        logger.info(report)
    elif args.execute:
        # レポート保存
        args.output_report.write_text(report, encoding="utf-8")
        logger.info(f"移行レポートを生成しました: {args.output_report}")

        # 実際の移行処理
        migrate_count = 0
        batch_count = 0

        for spec in specs:
            if spec.needs_migration:
                if batch_count >= args.batch_size:
                    logger.info(f"\nバッチサイズ {args.batch_size} に到達しました。")
                    user_input = input("続行しますか？ (y/n): ")
                    if user_input.lower() != "y":
                        break
                    batch_count = 0

                new_name, new_content = standardizer.standardize_spec(spec)
                new_path = spec.file_path.parent / new_name

                # ファイル内容を更新
                new_path.write_text(new_content, encoding="utf-8")

                # 元のファイルが異なる名前の場合は削除
                if spec.file_path != new_path:
                    spec.file_path.unlink()
                    logger.info(f"✅ 移行: {spec.original_name} → {new_name}")
                else:
                    logger.info(f"✅ 更新: {spec.original_name}")

                migrate_count += 1
                batch_count += 1

        logger.info(f"\n✨ 合計 {migrate_count} ファイルを移行しました。")
    else:
        # レポート保存
        args.output_report.write_text(report, encoding="utf-8")
        logger.info(f"移行レポートを生成しました: {args.output_report}")

        # 移行が必要なファイル数を表示
        migrate_count = sum(1 for spec in specs if spec.needs_migration)
        logger.info(f"\n合計 {migrate_count} ファイルの移行が必要です。")
        logger.info("実際に移行を実行するには、--execute フラグを使用してください。")

    # カウンター保存
    counter_file = args.specs_dir / ".spec_counters.json"
    with counter_file.open("w", encoding="utf-8") as f:
        json.dump(standardizer.spec_counter, f, indent=2)

if __name__ == "__main__":
    main()
