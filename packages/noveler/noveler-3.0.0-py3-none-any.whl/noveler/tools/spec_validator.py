#!/usr/bin/env python3
"""仕様書検証ツール

仕様書の標準フォーマット準拠と、テストとの紐付けを検証する。
品質ゲートの一部として実行される。
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from noveler.infrastructure.logging.unified_logger import get_logger


@dataclass
class ValidationResult:
    """検証結果"""
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)


@dataclass
class SpecValidation:
    """仕様書検証情報"""
    spec_id: str
    file_path: Path
    has_test_type: bool
    has_e2e_test: bool
    has_metadata: bool
    format_errors: list[str] = field(default_factory=list)


class SpecValidator:
    """仕様書検証クラス"""

    REQUIRED_METADATA_FIELDS = [
        "仕様ID",
        "E2EテストID",
        "test_type",
        "バージョン",
        "作成日",
        "最終更新",
        "ステータス"
    ]

    VALID_TEST_TYPES = ["e2e", "integration", "unit"]

    REQUIRED_SECTIONS = [
        "## 1. 概要",
        "## 2. ビジネス要件",
        "## 3. 機能仕様",
        "## 4. 技術仕様",
        "## 5. 検証仕様"
    ]

    def __init__(self, specs_dir: Path, tests_dir: Path, logger_service: Any | None = None, console_service: Any | None = None) -> None:
        """初期化

        Args:
            specs_dir: 仕様書ディレクトリ
            tests_dir: テストディレクトリ
        """
        self.specs_dir = specs_dir
        self.tests_dir = tests_dir
        self._load_mapping()
        self._scan_tests()

        self.logger_service = logger_service
        self.console_service = console_service
    def _load_mapping(self) -> None:
        """E2Eテストマッピングを読み込み"""
        mapping_file = self.specs_dir / "E2E_TEST_MAPPING.yaml"
        if mapping_file.exists():
            with mapping_file.open(encoding="utf-8") as f:
                self.mapping = yaml.safe_load(f)
        else:
            self.mapping = {"e2e_mappings": {}}

    def _scan_tests(self) -> None:
        """テストファイルをスキャンして@pytest.mark.spec()を収集"""
        self.test_specs: set[str] = set()

        for test_file in self.tests_dir.rglob("*.py"):
            content = test_file.read_text(encoding="utf-8")
            # @pytest.mark.spec('SPEC-XXX-NNN')パターンを探す
            spec_marks = re.findall(r"@pytest\.mark\.spec\(['\"](SPEC-[A-Z]+-\d+)['\"]\)", content)
            self.test_specs.update(spec_marks)

    def validate_all(self) -> ValidationResult:
        """すべての仕様書を検証

        Returns:
            全体の検証結果
        """
        result = ValidationResult(is_valid=True)
        spec_validations: list[SpecValidation] = []

        # SPEC-*.md ファイルを検証
        for spec_file in self.specs_dir.glob("SPEC-*.md"):
            validation = self.validate_spec(spec_file)
            spec_validations.append(validation)

            if validation.format_errors:
                result.errors.extend([
                    f"{spec_file.name}: {error}"
                    for error in validation.format_errors
                ])

        # 未標準化の.spec.mdファイルを検出
        legacy_specs = list(self.specs_dir.glob("*.spec.md"))
        if legacy_specs:
            result.warnings.append(
                f"未標準化の仕様書が {len(legacy_specs)} 個存在します"
            )

        # テストのない仕様書を検出
        orphaned_specs = []
        for validation in spec_validations:
            if not validation.has_e2e_test and validation.spec_id not in self.test_specs:
                orphaned_specs.append(validation.spec_id)

        if orphaned_specs:
            result.warnings.append(
                f"テストのない仕様書: {', '.join(orphaned_specs)}"
            )

        # 仕様書のないテストを検出
        all_spec_ids = {v.spec_id for v in spec_validations}
        orphaned_tests = self.test_specs - all_spec_ids
        if orphaned_tests:
            result.warnings.append(
                f"仕様書のないテスト: {', '.join(orphaned_tests)}"
            )

        # カバレッジ計算
        if spec_validations:
            with_tests = sum(1 for v in spec_validations if v.has_e2e_test or v.spec_id in self.test_specs)
            coverage = (with_tests / len(spec_validations)) * 100
            result.info.append(f"テストカバレッジ: {coverage:.1f}% ({with_tests}/{len(spec_validations)})")

        # 全体の妥当性判定
        if result.errors:
            result.is_valid = False

        return result

    def validate_spec(self, spec_file: Path) -> SpecValidation:
        """個別の仕様書を検証

        Args:
            spec_file: 仕様書ファイル

        Returns:
            検証結果
        """
        content = spec_file.read_text(encoding="utf-8")

        # 仕様IDを抽出
        spec_id_match = re.search(r"^# (SPEC-[A-Z]+-\d+):", content, re.MULTILINE)
        if not spec_id_match:
            return SpecValidation(
                spec_id="UNKNOWN",
                file_path=spec_file,
                has_test_type=False,
                has_e2e_test=False,
                has_metadata=False,
                format_errors=["仕様IDが見つかりません"]
            )

        spec_id = spec_id_match.group(1)

        validation = SpecValidation(
            spec_id=spec_id,
            file_path=spec_file,
            has_test_type=False,
            has_e2e_test=False,
            has_metadata=False
        )

        # メタデータセクションの検証
        if "## メタデータ" in content:
            validation.has_metadata = True
            metadata_section = content.split("## メタデータ")[1].split("##")[0]

            # 必須フィールドの確認
            for field in self.REQUIRED_METADATA_FIELDS:
                if f"| {field}" not in metadata_section:
                    validation.format_errors.append(f"必須メタデータフィールド '{field}' が不足")

            # test_typeの検証
            test_type_match = re.search(r"\| test_type \| ([a-z]+)", metadata_section)
            if test_type_match:
                validation.has_test_type = True
                test_type = test_type_match.group(1)
                if test_type not in self.VALID_TEST_TYPES:
                    validation.format_errors.append(
                        f"無効なtest_type: {test_type} (有効: {', '.join(self.VALID_TEST_TYPES)})"
                    )
            else:
                validation.format_errors.append("test_typeが指定されていません")

        else:
            validation.format_errors.append("メタデータセクションがありません")

        # 必須セクションの確認
        for section in self.REQUIRED_SECTIONS:
            if section not in content:
                validation.format_errors.append(f"必須セクション '{section}' が不足")

        # E2Eテストマッピングの確認
        if spec_id in self.mapping.get("e2e_mappings", {}):
            validation.has_e2e_test = True

        # ファイル名の妥当性チェック
        expected_pattern = re.compile(r"^SPEC-[A-Z]+-\d+(_[a-z_]+)?\.md$")
        if not expected_pattern.match(spec_file.name):
            validation.format_errors.append(
                f"ファイル名が標準形式に従っていません: {spec_file.name}"
            )

        return validation

    def generate_report(self, result: ValidationResult) -> str:
        """検証レポートを生成

        Args:
            result: 検証結果

        Returns:
            マークダウン形式のレポート
        """
        report = """# 仕様書検証レポート

## サマリ

"""
        status = "✅ 合格" if result.is_valid else "❌ 不合格"
        report += f"- **ステータス**: {status}\n"
        report += f"- **エラー数**: {len(result.errors)}\n"
        report += f"- **警告数**: {len(result.warnings)}\n"

        if result.info:
            report += "\n### 情報\n\n"
            for info in result.info:
                report += f"- {info}\n"

        if result.errors:
            report += "\n## ❌ エラー\n\n"
            for error in result.errors:
                report += f"- {error}\n"

        if result.warnings:
            report += "\n## ⚠️ 警告\n\n"
            for warning in result.warnings:
                report += f"- {warning}\n"

        report += "\n## 推奨アクション\n\n"

        if result.errors:
            report += """
1. **エラーの修正**
   ```bash
   python src/noveler/tools/spec_standardizer.py --execute --batch-size 10
   ```

"""

        if result.warnings:
            report += """
2. **テストの生成**
   ```bash
   python src/noveler/tools/e2e_test_generator.py specs/SPEC-XXX-NNN.md
   ```

"""

        report += """
3. **検証の再実行**
   ```bash
   python src/noveler/tools/spec_validator.py
   ```
"""

        return report


def main():
    """メイン処理"""

    parser = argparse.ArgumentParser(description="仕様書検証ツール")
    parser.add_argument(
        "--specs-dir",
        type=Path,
        default=Path("specs"),
        help="仕様書ディレクトリ"
    )
    parser.add_argument(
        "--tests-dir",
        type=Path,
        default=Path("tests"),
        help="テストディレクトリ"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="レポート出力先"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="警告もエラーとして扱う（CI/CD用）"
    )

    args = parser.parse_args()

    # 検証実行
    validator = SpecValidator(args.specs_dir, args.tests_dir)
    result = validator.validate_all()

    # strictモードでは警告もエラーとする
    if args.strict and result.warnings:
        result.is_valid = False

    # レポート生成
    report = validator.generate_report(result)

    logger = get_logger(__name__)
    if args.output:
        args.output.write_text(report, encoding="utf-8")
        logger.info(f"検証レポートを生成しました: {args.output}")
    else:
        logger.info(report)

    # 終了コード
    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
