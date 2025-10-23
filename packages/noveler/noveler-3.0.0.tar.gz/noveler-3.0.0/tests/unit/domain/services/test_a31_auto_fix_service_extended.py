"""小説原稿自動修正サービス拡張機能のテスト（旧A31AutoFixService）

新規追加される3つの修正器のテストケース:
    - A31-032: 文章のリズムと読みやすさ(readability_check)
- A31-033: キャラクター口調一貫性(character_consistency)
- A31-034: 伏線と描写の過不足調整(content_balance)
"""

from unittest.mock import Mock

import pytest

from noveler.domain.entities.a31_checklist_item import A31ChecklistItem, ChecklistItemType
from noveler.domain.services.manuscript_auto_correct_service import ManuscriptAutoCorrectService
# 後方互換性のためのエイリアス
A31AutoFixService = ManuscriptAutoCorrectService
from noveler.domain.value_objects.a31_fix_level import FixLevel


@pytest.mark.spec("SPEC-A31-001")
class TestA31AutoFixServiceExtended:
    """小説原稿自動修正サービス拡張機能テスト（旧A31AutoFixService）"""

    def setup_method(self) -> None:
        """テストメソッド前の初期化"""
        self.auto_fix_service = A31AutoFixService()
        self.sample_content = """第001話 魔法学院の落ちこぼれ

 俺の名前は田中太郎、この世界では「Fランク魔法使い」として有名だった。
「おい太郎、また失敗したのか?」クラスメイトの声が響く。
 また だ...。今日も魔法の実習で失敗してしまった。
 でも、諦めるわけにはいかない。
「必ず強くなってみせる」俺は拳を握りしめた。
 その時、奇妙なメッセージが脳裏に浮かんだ。
「DEBUG: スキル習得可能」
"""

    @pytest.mark.spec("SPEC-A31-031")
    def test_fix_basic_proofreading_corrects_common_typos(self) -> None:
        """基本的な誤字脱字修正が正しく動作することを確認"""
        # Arrange
        content_with_typos = """ 俺の名前は田中太郎だつた。
 「こんにちわ」と彼は云った。
 モンスタが現れた!!
 数字は１２３で、英字はＡＢＣだった。
 括弧は(これ)と{これ}がある。。"""

        checklist_item = A31ChecklistItem(
            item_id="A31-031",
            title="誤字脱字の基本チェック",
            required=True,
            item_type=ChecklistItemType.BASIC_PROOFREAD,
            auto_fix_strategy=Mock(),
        )

        checklist_item.auto_fix_strategy.fix_level = "standard"

        evaluation_result = Mock()
        evaluation_result.passed = False
        evaluation_result.current_score = 45.0
        evaluation_result.details = {
            "typo_patterns": ["だつた", "こんにちわ", "云った"],
            "punctuation_issues": ["!!", "。。"],
            "character_type_issues": ["１２３", "ＡＢＣ"],
        }

        # Act
        fixed_content, changes = self.auto_fix_service._fix_basic_proofreading(
            content_with_typos, checklist_item, evaluation_result
        )

        # Assert
        assert fixed_content != content_with_typos
        assert len(changes) > 0
        assert "だった" in fixed_content
        assert "こんにちは" in fixed_content
        assert "言った" in fixed_content
        assert "123" in fixed_content
        assert "ABC" in fixed_content
        assert any("誤字修正" in change for change in changes)

    @pytest.mark.spec("SPEC-A31-031")
    def test_fix_basic_proofreading_handles_punctuation_normalization(self) -> None:
        """句読点・記号の正規化が正しく動作することを確認"""
        # Arrange
        content_with_punctuation = """ これは文章だ。。
 本当ですか??
 素晴らしい!!!
 (注意)と{警告}がある。"""

        checklist_item = A31ChecklistItem(
            item_id="A31-031",
            title="誤字脱字の基本チェック",
            required=True,
            item_type=ChecklistItemType.BASIC_PROOFREAD,
            auto_fix_strategy=Mock(),
        )

        checklist_item.auto_fix_strategy.fix_level = "safe"

        evaluation_result = Mock()
        evaluation_result.passed = False
        evaluation_result.current_score = 60.0
        evaluation_result.details = {"punctuation_issues": ["。。", "??", "!!!"]}

        # Act
        fixed_content, changes = self.auto_fix_service._fix_basic_proofreading(
            content_with_punctuation, checklist_item, evaluation_result
        )

        # Assert
        assert "。。" not in fixed_content
        assert "??" not in fixed_content
        assert "!!!" not in fixed_content
        assert any("句読点修正" in change for change in changes)

    @pytest.mark.spec("SPEC-A31-044")
    def test_fix_terminology_issues_standardizes_character_names(self) -> None:
        """キャラクター名の表記統一が正しく動作することを確認"""
        # Arrange
        content_with_variants = """ 太郎は学院に向かった。
 「タロウ、どこにいるんだ?」
 たろうは魔法の練習をしていた。
 田中太郎が主人公だ。"""

        checklist_item = A31ChecklistItem(
            item_id="A31-044",
            title="固有名詞の表記統一を確認",
            required=True,
            item_type=ChecklistItemType.TERMINOLOGY_CHECK,
            auto_fix_strategy=Mock(),
        )

        checklist_item.auto_fix_strategy.fix_level = "standard"

        evaluation_result = Mock()
        evaluation_result.passed = False
        evaluation_result.current_score = 55.0
        evaluation_result.details = {
            "terminology_inconsistencies": [
                {"canonical": "太郎", "variants": ["タロウ", "たろう"]},
                {"canonical": "魔法学院", "variants": ["魔法学園", "魔導学院"]},
            ]
        }

        # Act
        fixed_content, changes = self.auto_fix_service._fix_terminology_issues(
            content_with_variants, checklist_item, evaluation_result
        )

        # Assert
        assert fixed_content != content_with_variants
        assert len(changes) > 0
        assert content_with_variants.count("太郎") < fixed_content.count("太郎")
        assert "タロウ" not in fixed_content
        assert "たろう" not in fixed_content
        assert any("用語統一" in change for change in changes)

    @pytest.mark.spec("SPEC-A31-044")
    def test_fix_terminology_issues_handles_location_names(self) -> None:
        """地名・組織名の統一が正しく動作することを確認"""
        # Arrange
        content_with_location_variants = """ 魔法学院は立派な建物だった。
 魔法学園の生徒たちが集まっている。
 魔導学院の入学試験は難しい。
 冒険者ギルドに行こう。
 冒険者組合で依頼を受けた。"""

        checklist_item = A31ChecklistItem(
            item_id="A31-044",
            title="固有名詞の表記統一を確認",
            required=True,
            item_type=ChecklistItemType.TERMINOLOGY_CHECK,
            auto_fix_strategy=Mock(),
        )

        checklist_item.auto_fix_strategy.fix_level = "standard"

        evaluation_result = Mock()
        evaluation_result.passed = False
        evaluation_result.current_score = 48.0
        evaluation_result.details = {
            "terminology_inconsistencies": [
                {"canonical": "魔法学院", "variants": ["魔法学園", "魔導学院"]},
                {"canonical": "冒険者ギルド", "variants": ["冒険者組合"]},
            ]
        }

        # Act
        fixed_content, changes = self.auto_fix_service._fix_terminology_issues(
            content_with_location_variants, checklist_item, evaluation_result
        )

        # Assert
        assert "魔法学園" not in fixed_content
        assert "魔導学院" not in fixed_content
        assert "冒険者組合" not in fixed_content
        assert fixed_content.count("魔法学院") >= 3
        assert fixed_content.count("冒険者ギルド") >= 2
        assert any("地名統一" in change or "組織名統一" in change for change in changes)

    @pytest.mark.spec("SPEC-A31-044")
    def test_fix_terminology_issues_handles_spell_names(self) -> None:
        """魔法・技名の統一が正しく動作することを確認"""
        # Arrange
        content_with_spell_variants = """ ファイアボールを唱えた。
 火球の威力は凄まじい。
 炎球が敵を襲う。
 ファイヤーボールは初級魔法だ。"""

        checklist_item = A31ChecklistItem(
            item_id="A31-044",
            title="固有名詞の表記統一を確認",
            required=True,
            item_type=ChecklistItemType.TERMINOLOGY_CHECK,
            auto_fix_strategy=Mock(),
        )

        checklist_item.auto_fix_strategy.fix_level = "standard"

        evaluation_result = Mock()
        evaluation_result.passed = False
        evaluation_result.current_score = 52.0
        evaluation_result.details = {
            "terminology_inconsistencies": [
                {"canonical": "ファイアボール", "variants": ["火球", "炎球", "ファイヤーボール"]}
            ]
        }

        # Act
        fixed_content, changes = self.auto_fix_service._fix_terminology_issues(
            content_with_spell_variants, checklist_item, evaluation_result
        )

        # Assert
        assert "火球" not in fixed_content
        assert "炎球" not in fixed_content
        assert "ファイヤーボール" not in fixed_content
        assert fixed_content.count("ファイアボール") >= 4
        assert any("魔法名統一" in change or "技名統一" in change for change in changes)

    @pytest.mark.spec("SPEC-A31-001")
    def test_basic_proofread_and_terminology_integration(self) -> None:
        """誤字脱字修正と用語統一の統合動作を確認"""
        # Arrange
        content_with_both_issues = """ 太郎は魔法学園でファイヤーボールを練習していた。。
 「タロウ、もっと集中しろ!!」先生が云った。
 でも、火球の威力はまだ弱かつた。"""

        basic_item = A31ChecklistItem(
            item_id="A31-031",
            title="誤字脱字の基本チェック",
            required=True,
            item_type=ChecklistItemType.BASIC_PROOFREAD,
            auto_fix_strategy=Mock(),
        )

        basic_item.auto_fix_strategy.fix_level = "standard"

        terminology_item = A31ChecklistItem(
            item_id="A31-044",
            title="固有名詞の表記統一を確認",
            required=True,
            item_type=ChecklistItemType.TERMINOLOGY_CHECK,
            auto_fix_strategy=Mock(),
        )

        terminology_item.auto_fix_strategy.fix_level = "standard"

        basic_evaluation = Mock()
        basic_evaluation.passed = False
        basic_evaluation.current_score = 40.0
        basic_evaluation.details = {"typo_patterns": ["云った", "弱かつた"]}

        terminology_evaluation = Mock()
        terminology_evaluation.passed = False
        terminology_evaluation.current_score = 45.0
        terminology_evaluation.details = {
            "terminology_inconsistencies": [
                {"canonical": "太郎", "variants": ["タロウ"]},
                {"canonical": "魔法学院", "variants": ["魔法学園"]},
                {"canonical": "ファイアボール", "variants": ["ファイヤーボール", "火球"]},
            ]
        }

        # Act - Apply both fixes
        intermediate_content, basic_changes = self.auto_fix_service._fix_basic_proofreading(
            content_with_both_issues, basic_item, basic_evaluation
        )

        final_content, terminology_changes = self.auto_fix_service._fix_terminology_issues(
            intermediate_content, terminology_item, terminology_evaluation
        )

        # Assert
        assert final_content != content_with_both_issues
        assert len(basic_changes) > 0
        assert len(terminology_changes) > 0
        assert "。。" not in final_content
        assert "!!" not in final_content
        assert "云った" not in final_content
        assert "弱かつた" not in final_content
        assert "タロウ" not in final_content
        assert "魔法学園" not in final_content
        assert "ファイヤーボール" not in final_content
        assert "火球" not in final_content

    @pytest.mark.spec("SPEC-A31-032")
    def test_fix_readability_issues_improves_text_flow(self) -> None:
        """文章リズム修正により読みやすさが向上することを確認"""
        # Arrange
        checklist_item = A31ChecklistItem(
            item_id="A31-032",
            title="文章のリズムと読みやすさ",
            required=True,
            item_type=ChecklistItemType.READABILITY_CHECK,
            auto_fix_strategy=Mock(),
        )

        checklist_item.auto_fix_strategy.fix_level = "interactive"

        evaluation_result = Mock()
        evaluation_result.passed = False
        evaluation_result.current_score = 65.0
        evaluation_result.details = {
            "repetitive_patterns": ["だった", "した"],
            "sentence_length_variance": 12.5,
            "rhythm_issues": ["短文の連続", "語尾の単調性"],
        }

        # Act
        fixed_content, changes = self.auto_fix_service._fix_readability_issues(
            self.sample_content, checklist_item, evaluation_result
        )

        # Assert
        assert fixed_content != self.sample_content
        assert len(changes) > 0
        assert any("語尾修正" in change for change in changes)
        assert any("文長調整" in change for change in changes)

    @pytest.mark.spec("SPEC-A31-033")
    def test_fix_character_consistency_maintains_character_voice(self) -> None:
        """キャラクター口調一貫性修正がキャラクター設定を維持することを確認"""
        # Arrange
        content_with_inconsistency = """「俺は絶対に負けない!」太郎は叫んだ。
「あの、すみません...」太郎は小声で言った。
「おい、お前ら!」太郎が大声で呼びかけた。"""

        checklist_item = A31ChecklistItem(
            item_id="A31-033",
            title="キャラクター口調一貫性",
            required=True,
            item_type=ChecklistItemType.CHARACTER_CONSISTENCY,
            auto_fix_strategy=Mock(),
        )

        checklist_item.auto_fix_strategy.fix_level = "interactive"

        evaluation_result = Mock()
        evaluation_result.passed = False
        evaluation_result.current_score = 58.0
        evaluation_result.details = {
            "character_inconsistencies": [{"character": "太郎", "expected_tone": "confident", "found_tone": "timid"}]
        }

        # Act
        fixed_content, changes = self.auto_fix_service._fix_character_consistency(
            content_with_inconsistency, checklist_item, evaluation_result
        )

        # Assert
        assert fixed_content != content_with_inconsistency
        assert len(changes) > 0
        assert any("口調修正" in change for change in changes)

    @pytest.mark.spec("SPEC-A31-034")
    def test_fix_content_balance_adjusts_description_ratio(self) -> None:
        """内容バランス修正が描写比率を適切に調整することを確認"""
        # Arrange
        dialogue_heavy_content = """「こんにちは」
「元気ですか?」
「はい、元気です」
「良かった」
「ありがとう」"""

        checklist_item = A31ChecklistItem(
            item_id="A31-034",
            title="伏線と描写の過不足調整",
            required=True,
            item_type=ChecklistItemType.CONTENT_BALANCE,
            auto_fix_strategy=Mock(),
        )

        checklist_item.auto_fix_strategy.fix_level = "standard"

        evaluation_result = Mock()
        evaluation_result.passed = False
        evaluation_result.current_score = 45.0
        evaluation_result.details = {
            "dialogue_ratio": 95.0,
            "description_ratio": 5.0,
            "balance_issues": ["描写不足", "会話過多"],
        }

        # Act
        fixed_content, changes = self.auto_fix_service._fix_content_balance(
            dialogue_heavy_content, checklist_item, evaluation_result
        )

        # Assert
        assert fixed_content != dialogue_heavy_content
        assert len(changes) > 0
        assert any("描写追加" in change for change in changes)

    @pytest.mark.spec("SPEC-A31-001")
    def test_new_fixers_are_properly_registered(self) -> None:
        """新しい修正器が適切に登録されていることを確認"""
        # Act & Assert
        assert ChecklistItemType.BASIC_PROOFREAD in self.auto_fix_service._standard_fixers
        assert ChecklistItemType.TERMINOLOGY_CHECK in self.auto_fix_service._standard_fixers
        assert ChecklistItemType.READABILITY_CHECK in self.auto_fix_service._interactive_fixers
        assert ChecklistItemType.CHARACTER_CONSISTENCY in self.auto_fix_service._interactive_fixers
        assert ChecklistItemType.CONTENT_BALANCE in self.auto_fix_service._standard_fixers

    @pytest.mark.spec("SPEC-A31-001")
    def test_fix_level_compatibility_for_new_fixers(self) -> None:
        """新しい修正器のレベル互換性を確認"""
        # Arrange
        basic_item = Mock()
        basic_item.auto_fix_strategy.fix_level = "standard"

        terminology_item = Mock()
        terminology_item.auto_fix_strategy.fix_level = "standard"

        readability_item = Mock()
        readability_item.auto_fix_strategy.fix_level = "interactive"

        character_item = Mock()
        character_item.auto_fix_strategy.fix_level = "interactive"

        content_item = Mock()
        content_item.auto_fix_strategy.fix_level = "standard"

        # Act & Assert
        assert self.auto_fix_service._can_apply_fix_level(basic_item, FixLevel.STANDARD)
        assert self.auto_fix_service._can_apply_fix_level(basic_item, FixLevel.INTERACTIVE)
        assert not self.auto_fix_service._can_apply_fix_level(basic_item, FixLevel.SAFE)

        assert self.auto_fix_service._can_apply_fix_level(terminology_item, FixLevel.STANDARD)
        assert self.auto_fix_service._can_apply_fix_level(terminology_item, FixLevel.INTERACTIVE)
        assert not self.auto_fix_service._can_apply_fix_level(terminology_item, FixLevel.SAFE)

        assert self.auto_fix_service._can_apply_fix_level(readability_item, FixLevel.INTERACTIVE)
        assert not self.auto_fix_service._can_apply_fix_level(readability_item, FixLevel.STANDARD)

        assert self.auto_fix_service._can_apply_fix_level(character_item, FixLevel.INTERACTIVE)
        assert not self.auto_fix_service._can_apply_fix_level(character_item, FixLevel.STANDARD)

        assert self.auto_fix_service._can_apply_fix_level(content_item, FixLevel.STANDARD)
        assert self.auto_fix_service._can_apply_fix_level(content_item, FixLevel.INTERACTIVE)
        assert not self.auto_fix_service._can_apply_fix_level(content_item, FixLevel.SAFE)

    @pytest.mark.spec("SPEC-A31-001")
    def test_integration_with_existing_apply_fixes_method(self) -> None:
        """既存のapply_fixesメソッドとの統合動作を確認"""
        # Arrange
        items = [
            A31ChecklistItem(
                item_id="A31-031",
                title="誤字脱字の基本チェック",
                required=True,
                item_type=ChecklistItemType.BASIC_PROOFREAD,
                auto_fix_strategy=Mock(),
            ),
            A31ChecklistItem(
                item_id="A31-044",
                title="固有名詞の表記統一を確認",
                required=True,
                item_type=ChecklistItemType.TERMINOLOGY_CHECK,
                auto_fix_strategy=Mock(),
            ),
        ]
        items[0].auto_fix_strategy.fix_level = "standard"
        items[1].auto_fix_strategy.fix_level = "standard"

        evaluation_results = {
            "A31-031": Mock(passed=False, current_score=50.0, details={}),
            "A31-044": Mock(passed=False, current_score=55.0, details={}),
        }

        # Act
        fixed_content, fix_results = self.auto_fix_service.apply_fixes(
            self.sample_content, evaluation_results, items, FixLevel.STANDARD
        )

        # Assert
        assert len(fix_results) == 2
        assert fix_results[0].item_id == "A31-031"
        assert fix_results[1].item_id == "A31-044"
