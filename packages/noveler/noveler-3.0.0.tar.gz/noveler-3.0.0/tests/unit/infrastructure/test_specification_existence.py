#!/usr/bin/env python3
"""仕様書の存在を確認するテスト

TDD原則に基づき、まず失敗するテストを作成


仕様書: SPEC-INFRASTRUCTURE
"""

from pathlib import Path


class TestSpecificationExistence:
    """ドメイン層の仕様書存在確認テスト"""

    def test_core_value_objects_have_specifications(self) -> None:
        """コア値オブジェクトの仕様書が存在すること"""
        specs_dir = Path("specs")

        # 必須の値オブジェクト仕様書
        required_specs = [
            "SPEC-EPISODE-027_episode_number.md",
            "SPEC-EPISODE-029_episode_title.md",
            "SPEC-ENTITY-009_word_count.md",
            "SPEC-QUALITY-031_quality_score.md",
        ]

        missing_specs = []
        for spec in required_specs:
            spec_path = specs_dir / spec
            if not spec_path.exists():
                missing_specs.append(spec)

        assert not missing_specs, f"Missing specifications: {missing_specs}"

    def test_core_entities_have_specifications(self) -> None:
        """コアエンティティの仕様書が存在すること"""
        specs_dir = Path("specs")

        # 必須のエンティティ仕様書
        required_specs = [
            "SPEC-EPISODE-022_episode.md",
        ]

        missing_specs = []
        for spec in required_specs:
            spec_path = specs_dir / spec
            if not spec_path.exists():
                missing_specs.append(spec)

        assert not missing_specs, f"Missing specifications: {missing_specs}"

    def test_specification_template_compliance(self) -> None:
        """仕様書がテンプレートに準拠していること"""
        specs_dir = Path("specs")
        existing_spec = specs_dir / "SPEC-QUALITY-031_quality_score.md"

        if existing_spec.exists():
            content = existing_spec.read_text(encoding="utf-8")

            # 必須セクションの確認
            required_sections = [
                "## 1. 目的",
                "## 2. 前提条件",
                "## 3. 主要な振る舞い",
                "## 4. インターフェース仕様",
                "## 5. エラーハンドリング",
            ]

            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)

            assert not missing_sections, f"Missing sections in SPEC-QUALITY-031_quality_score.md: {missing_sections}"
