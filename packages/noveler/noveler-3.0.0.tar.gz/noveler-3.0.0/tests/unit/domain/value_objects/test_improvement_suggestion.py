#!/usr/bin/env python3
"""改善提案値オブジェクトのユニットテスト

TDD原則に従い、値オブジェクトの不変条件とビジネスロジックをテスト
"""

import pytest

from noveler.domain.exceptions import ValidationError
from noveler.domain.value_objects.improvement_suggestion import ImprovementSuggestion, SuggestionType

pytestmark = pytest.mark.vo_smoke



class TestImprovementSuggestion:
    """ImprovementSuggestion値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_create_valid_high_priority(self) -> None:
        """有効なデータで作成(高優先度)"""
        # When
        suggestion = ImprovementSuggestion(
            content="文章の冗長性を改善: 同じ表現が繰り返されており、読者の集中力を削ぎます。",
            suggestion_type=SuggestionType.STYLE_REFINEMENT,
            confidence=0.85,
            fix_example="「です・ます」調の重複を削減、接続詞の多用を避ける、段落冒頭の言い換えを検討",
            expected_impact="読みやすさが向上し、読者の集中力が維持される",
            implementation_difficulty="medium",
        )

        # Then
        assert suggestion.content == "文章の冗長性を改善: 同じ表現が繰り返されており、読者の集中力を削ぎます。"
        assert suggestion.suggestion_type == SuggestionType.STYLE_REFINEMENT
        assert suggestion.confidence == 0.85
        assert suggestion.fix_example == "「です・ます」調の重複を削減、接続詞の多用を避ける、段落冒頭の言い換えを検討"
        assert suggestion.expected_impact == "読みやすさが向上し、読者の集中力が維持される"
        assert suggestion.implementation_difficulty == "medium"

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_create_valid_medium_priority(self) -> None:
        """有効なデータで作成(中優先度)"""
        # When
        suggestion = ImprovementSuggestion(
            content="伏線の配置を見直し: 重要な伏線が目立ちすぎています。",
            suggestion_type=SuggestionType.CONTENT_ENHANCEMENT,
            confidence=0.75,
            fix_example="伏線を自然な会話に組み込む",
            expected_impact="より自然な物語展開になる",
            implementation_difficulty="medium",
        )

        # Then
        assert suggestion.content == "伏線の配置を見直し: 重要な伏線が目立ちすぎています。"
        assert suggestion.suggestion_type == SuggestionType.CONTENT_ENHANCEMENT
        assert suggestion.confidence == 0.75

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_create_valid_low_priority(self) -> None:
        """有効なデータで作成(低優先度)"""
        # When
        suggestion = ImprovementSuggestion(
            category="readability",
            priority="low",
            title="漢字の使用率調整",
            description="やや漢字が多めです。",
            specific_actions=["一部をひらがなに変更"],
            estimated_impact=2.0,
            confidence=0.6,
        )

        # Then
        assert suggestion.priority == "low"
        assert suggestion.estimated_impact == 2.0

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_priority_validation_invalid(self) -> None:
        """優先度の検証(無効な値)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            ImprovementSuggestion(
                category="test",
                priority="urgent",  # 無効
                title="テスト",
                description="テスト説明",
                specific_actions=["アクション"],
                estimated_impact=5.0,
                confidence=0.5,
            )

        assert "優先度は 'high', 'medium', 'low' のいずれかを指定してください" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_title_validation_empty(self) -> None:
        """タイトルの検証(空文字列)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            ImprovementSuggestion(
                category="test",
                priority="high",
                title="",
                description="テスト説明",
                specific_actions=["アクション"],
                estimated_impact=5.0,
                confidence=0.5,
            )

        assert "タイトルは必須です" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_title_validation_whitespace(self) -> None:
        """タイトルの検証(空白のみ)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            ImprovementSuggestion(
                category="test",
                priority="high",
                title="   ",
                description="テスト説明",
                specific_actions=["アクション"],
                estimated_impact=5.0,
                confidence=0.5,
            )

        assert "タイトルは必須です" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_title_validation_too_long(self) -> None:
        """タイトルの検証(長すぎる)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            ImprovementSuggestion(
                category="test",
                priority="high",
                title="あ" * 101,  # 101文字
                description="テスト説明",
                specific_actions=["アクション"],
                estimated_impact=5.0,
                confidence=0.5,
            )

        assert "タイトルは100文字以内で指定してください" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_description_validation_empty(self) -> None:
        """説明の検証(空文字列)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            ImprovementSuggestion(
                category="test",
                priority="high",
                title="テストタイトル",
                description="",
                specific_actions=["アクション"],
                estimated_impact=5.0,
                confidence=0.5,
            )

        assert "説明は必須です" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_description_validation_too_long(self) -> None:
        """説明の検証(長すぎる)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            ImprovementSuggestion(
                category="test",
                priority="high",
                title="テストタイトル",
                description="あ" * 501,  # 501文字
                specific_actions=["アクション"],
                estimated_impact=5.0,
                confidence=0.5,
            )

        assert "説明は500文字以内で指定してください" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_specific_actions_validation_empty_list(self) -> None:
        """具体的アクションの検証(空リスト)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            ImprovementSuggestion(
                category="test",
                priority="high",
                title="テストタイトル",
                description="テスト説明",
                specific_actions=[],
                estimated_impact=5.0,
                confidence=0.5,
            )

        assert "具体的アクションは最低1つ必要です" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_specific_actions_validation_empty_action(self) -> None:
        """具体的アクションの検証(空アクション)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            ImprovementSuggestion(
                category="test",
                priority="high",
                title="テストタイトル",
                description="テスト説明",
                specific_actions=["有効なアクション", ""],
                estimated_impact=5.0,
                confidence=0.5,
            )

        assert "具体的アクションは空文字にできません" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_specific_actions_validation_whitespace_action(self) -> None:
        """具体的アクションの検証(空白のみのアクション)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            ImprovementSuggestion(
                category="test",
                priority="high",
                title="テストタイトル",
                description="テスト説明",
                specific_actions=["   "],
                estimated_impact=5.0,
                confidence=0.5,
            )

        assert "具体的アクションは空文字にできません" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_specific_actions_validation_too_long(self) -> None:
        """具体的アクションの検証(長すぎる)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            ImprovementSuggestion(
                category="test",
                priority="high",
                title="テストタイトル",
                description="テスト説明",
                specific_actions=["あ" * 201],  # 201文字
                estimated_impact=5.0,
                confidence=0.5,
            )

        assert "具体的アクションは200文字以内で指定してください" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_estimated_impact_validation_too_low(self) -> None:
        """推定インパクトの検証(低すぎる値)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            ImprovementSuggestion(
                category="test",
                priority="high",
                title="テストタイトル",
                description="テスト説明",
                specific_actions=["アクション"],
                estimated_impact=-0.1,
                confidence=0.5,
            )

        assert "推定インパクトは0.0から10.0の範囲で指定してください" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_estimated_impact_validation_too_high(self) -> None:
        """推定インパクトの検証(高すぎる値)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            ImprovementSuggestion(
                category="test",
                priority="high",
                title="テストタイトル",
                description="テスト説明",
                specific_actions=["アクション"],
                estimated_impact=10.1,
                confidence=0.5,
            )

        assert "推定インパクトは0.0から10.0の範囲で指定してください" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_estimated_impact_validation_boundary(self) -> None:
        """推定インパクトの検証(境界値)"""
        # When & Then
        # 0.0はOK
        suggestion1 = ImprovementSuggestion(
            category="test",
            priority="low",
            title="テストタイトル",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=0.0,
            confidence=0.5,
        )

        assert suggestion1.estimated_impact == 0.0

        # 10.0はOK
        suggestion2 = ImprovementSuggestion(
            category="test",
            priority="high",
            title="テストタイトル",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=10.0,
            confidence=0.5,
        )

        assert suggestion2.estimated_impact == 10.0

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_confidence_validation_too_low(self) -> None:
        """信頼度の検証(低すぎる値)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            ImprovementSuggestion(
                category="test",
                priority="high",
                title="テストタイトル",
                description="テスト説明",
                specific_actions=["アクション"],
                estimated_impact=5.0,
                confidence=-0.1,
            )

        assert "信頼度は0.0から1.0の範囲で指定してください" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_confidence_validation_too_high(self) -> None:
        """信頼度の検証(高すぎる値)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            ImprovementSuggestion(
                category="test",
                priority="high",
                title="テストタイトル",
                description="テスト説明",
                specific_actions=["アクション"],
                estimated_impact=5.0,
                confidence=1.1,
            )

        assert "信頼度は0.0から1.0の範囲で指定してください" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_is_high_priority(self) -> None:
        """高優先度判定"""
        # Given
        high = ImprovementSuggestion(
            category="test",
            priority="high",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.5,
        )

        medium = ImprovementSuggestion(
            category="test",
            priority="medium",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.5,
        )

        # When & Then
        assert high.is_high_priority() is True
        assert medium.is_high_priority() is False

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_is_medium_priority(self) -> None:
        """中優先度判定"""
        # Given
        medium = ImprovementSuggestion(
            category="test",
            priority="medium",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.5,
        )

        low = ImprovementSuggestion(
            category="test",
            priority="low",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.5,
        )

        # When & Then
        assert medium.is_medium_priority() is True
        assert low.is_medium_priority() is False

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_is_low_priority(self) -> None:
        """低優先度判定"""
        # Given
        low = ImprovementSuggestion(
            category="test",
            priority="low",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.5,
        )

        high = ImprovementSuggestion(
            category="test",
            priority="high",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.5,
        )

        # When & Then
        assert low.is_low_priority() is True
        assert high.is_low_priority() is False

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_is_high_impact_default_threshold(self) -> None:
        """高インパクト判定(デフォルト閾値)"""
        # Given
        high_impact = ImprovementSuggestion(
            category="test",
            priority="high",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=7.0,
            confidence=0.5,
        )

        low_impact = ImprovementSuggestion(
            category="test",
            priority="low",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=6.9,
            confidence=0.5,
        )

        # When & Then
        assert high_impact.is_high_impact() is True  # 7.0 >= 7.0
        assert low_impact.is_high_impact() is False  # 6.9 < 7.0

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_is_high_impact_custom_threshold(self) -> None:
        """高インパクト判定(カスタム閾値)"""
        # Given
        suggestion = ImprovementSuggestion(
            category="test",
            priority="high",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=8.0,
            confidence=0.5,
        )

        # When & Then
        assert suggestion.is_high_impact(threshold=8.0) is True  # 8.0 >= 8.0
        assert suggestion.is_high_impact(threshold=8.5) is False  # 8.0 < 8.5
        assert suggestion.is_high_impact(threshold=5.0) is True  # 8.0 >= 5.0

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_is_reliable_default_threshold(self) -> None:
        """信頼性判定(デフォルト閾値)"""
        # Given
        reliable = ImprovementSuggestion(
            category="test",
            priority="high",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.7,
        )

        unreliable = ImprovementSuggestion(
            category="test",
            priority="high",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.69,
        )

        # When & Then
        assert reliable.is_reliable() is True  # 0.7 >= 0.7
        assert unreliable.is_reliable() is False  # 0.69 < 0.7

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_is_reliable_custom_threshold(self) -> None:
        """信頼性判定(カスタム閾値)"""
        # Given
        suggestion = ImprovementSuggestion(
            category="test",
            priority="high",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.8,
        )

        # When & Then
        assert suggestion.is_reliable(threshold=0.8) is True  # 0.8 >= 0.8
        assert suggestion.is_reliable(threshold=0.85) is False  # 0.8 < 0.85
        assert suggestion.is_reliable(threshold=0.5) is True  # 0.8 >= 0.5

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_get_priority_score(self) -> None:
        """優先度スコア取得"""
        # Given
        high = ImprovementSuggestion(
            category="test",
            priority="high",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.5,
        )

        medium = ImprovementSuggestion(
            category="test",
            priority="medium",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.5,
        )

        low = ImprovementSuggestion(
            category="test",
            priority="low",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.5,
        )

        # When & Then
        assert high.get_priority_score() == 3
        assert medium.get_priority_score() == 2
        assert low.get_priority_score() == 1

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_get_action_count(self) -> None:
        """アクション数取得"""
        # Given
        suggestion = ImprovementSuggestion(
            category="test",
            priority="high",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション1", "アクション2", "アクション3", "アクション4"],
            estimated_impact=5.0,
            confidence=0.5,
        )

        # When
        count = suggestion.get_action_count()

        # Then
        assert count == 4

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_get_suggestion_summary(self) -> None:
        """提案サマリー取得"""
        # Given
        suggestion = ImprovementSuggestion(
            category="basic_writing_style",
            priority="high",
            title="文章の冗長性を改善",
            description="同じ表現が繰り返されています。",
            specific_actions=["重複表現を削除", "簡潔な表現に置き換え"],
            estimated_impact=8.5,
            confidence=0.85,
        )

        # When
        summary = suggestion.get_suggestion_summary()

        # Then
        assert summary["category"] == "basic_writing_style"
        assert summary["priority"] == "high"
        assert summary["priority_score"] == 3
        assert summary["title"] == "文章の冗長性を改善"
        assert summary["description"] == "同じ表現が繰り返されています。"
        assert summary["action_count"] == 2
        assert summary["estimated_impact"] == 8.5
        assert summary["confidence"] == 0.85
        assert summary["is_high_priority"] is True
        assert summary["is_high_impact"] is True
        assert summary["is_reliable"] is True

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_immutability(self) -> None:
        """値オブジェクトの不変性"""
        # Given
        suggestion = ImprovementSuggestion(
            category="test",
            priority="high",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.5,
        )

        # When & Then
        # frozen=Trueのため、属性の変更はできない
        with pytest.raises(AttributeError, match=".*"):
            suggestion.category = "new_category"

        with pytest.raises(AttributeError, match=".*"):
            suggestion.priority = "low"

        with pytest.raises(AttributeError, match=".*"):
            suggestion.estimated_impact = 10.0

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_equality(self) -> None:
        """値オブジェクトの等価性"""
        # Given
        suggestion1 = ImprovementSuggestion(
            category="test",
            priority="high",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.5,
        )

        suggestion2 = ImprovementSuggestion(
            category="test",
            priority="high",
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.5,
        )

        suggestion3 = ImprovementSuggestion(
            category="test",
            priority="medium",  # 異なる優先度
            title="テスト",
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.5,
        )

        # When & Then
        assert suggestion1 == suggestion2
        assert suggestion1 != suggestion3
        # リストを含むdataclassはhashableではないため、hash比較は行わない

    @pytest.mark.spec("SPEC-QUALITY-009")
    def test_boundary_values_for_lengths(self) -> None:
        """文字列長の境界値テスト"""
        # Given & When
        # タイトル100文字(境界値)
        suggestion1 = ImprovementSuggestion(
            category="test",
            priority="high",
            title="あ" * 100,
            description="テスト説明",
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.5,
        )

        assert len(suggestion1.title) == 100

        # 説明500文字(境界値)
        suggestion2 = ImprovementSuggestion(
            category="test",
            priority="high",
            title="テスト",
            description="あ" * 500,
            specific_actions=["アクション"],
            estimated_impact=5.0,
            confidence=0.5,
        )

        assert len(suggestion2.description) == 500

        # アクション200文字(境界値)
        suggestion3 = ImprovementSuggestion(
            category="test",
            priority="high",
            title="テスト",
            description="テスト説明",
            specific_actions=["あ" * 200],
            estimated_impact=5.0,
            confidence=0.5,
        )

        assert len(suggestion3.specific_actions[0]) == 200
