"""キャラクター一貫性チェックドメインサービスのテスト

TDD RED Phase: ドメインサービスの失敗するテスト
"""

import time
from unittest.mock import Mock

import pytest

from noveler.domain.entities.episode import Episode
from noveler.domain.services.character_consistency_service import CharacterConsistencyService
from noveler.domain.value_objects.character_profile import CharacterProfile
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.episode_title import EpisodeTitle
from noveler.domain.value_objects.word_count import WordCount


@pytest.mark.spec("SPEC-QUALITY-014")
class TestCharacterConsistencyService:
    """キャラクター一貫性チェックサービスのテスト"""

    @pytest.fixture
    def service(self):
        """テスト用サービスインスタンス"""
        character_repo = Mock()
        return CharacterConsistencyService(character_repo)

    @pytest.mark.spec("SPEC-QUALITY-015")
    def test_basic_consistency_analysis(self, service: object) -> None:
        """基本的な一貫性分析ができる"""
        # Given

        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("第1話"),
            target_words=WordCount(2000),
            content="""山田太郎が教室に入ってきた。
彼の金髪が朝日でキラキラと輝いている。
「おはようございます」と太郎は言った。""",
        )

        characters = [CharacterProfile(name="山田太郎", attributes={"hair_color": "黒髪", "personality": "真面目"})]

        # When
        violations = service.analyze_consistency(episode, characters)

        # Then
        assert len(violations) == 1
        assert violations[0].character_name == "山田太郎"
        assert violations[0].attribute == "hair_color"
        assert violations[0].expected == "黒髪"
        assert violations[0].actual == "金髪"
        assert violations[0].line_number == 2

    @pytest.mark.spec("SPEC-CHARACTER_CONSISTENCY_SERVICE-MULTIPLE_CHARACTER_C")
    def test_multiple_character_consistency_check(self, service: object) -> None:
        """複数キャラクターの一貫性チェックのテスト"""
        # Given
        episode = Episode(
            number=1,
            title="テスト話",
            content="""彼の茶色い瞳が激しく燃えていた。
普段は物静かな太郎だが、今日は違った。""",
        )

        characters = [
            CharacterProfile(
                name="太郎", attributes={"eye_color": "黒", "personality": "物静か", "speech_style": "丁寧語"}
            )
        ]

        # When
        violations = service.analyze_consistency(episode, characters)

        # Then
        assert len(violations) >= 2

        # 瞳の色の矛盾
        eye_violation = next(v for v in violations if v.attribute == "eye_color")
        assert eye_violation.expected == "黒"
        assert eye_violation.actual == "茶色い"

        # 話し方の矛盾
        speech_violation = next(v for v in violations if v.attribute == "speech_style")
        assert speech_violation.expected == "丁寧語"
        assert "俺" in speech_violation.actual or "負けねぇ" in speech_violation.actual

    @pytest.mark.spec("SPEC-QUALITY-016")
    def test_context_aware_analysis_avoids_false_positives(self, service: object) -> None:
        """文脈を考慮して誤検出を避ける"""
        # Given

        episode = Episode(
            number=EpisodeNumber(3),
            title=EpisodeTitle("第3話"),
            target_words=WordCount(2000),
            content="""太郎は髪を染めることにした。
「今日から金髪にしてみようかな」
数日後、太郎の金髪姿が学校で話題になった。""",
        )

        characters = [CharacterProfile(name="太郎", attributes={"hair_color": "黒髪"})]

        # When
        violations = service.analyze_consistency(episode, characters)

        # Then
        # 髪を染めたという文脈があるので、3行目の金髪は違反としない
        assert len(violations) == 0 or all(v.line_number != 3 for v in violations)

    @pytest.mark.spec("SPEC-QUALITY-017")
    def test_pronoun_resolution_for_character_checking(self, service: object) -> None:
        """代名詞を正しく解決してチェック"""
        # Given

        episode = Episode(
            number=EpisodeNumber(4),
            title=EpisodeTitle("第4話"),
            target_words=WordCount(2000),
            content="""太郎と花子が話していた。
彼の青い瞳が優しく微笑んだ。
彼女の長い黒髪が風に揺れた。""",
        )

        characters = [
            CharacterProfile("太郎", {"eye_color": "茶色", "gender": "男性"}),
            CharacterProfile("花子", {"hair_color": "金髪", "gender": "女性"}),
        ]

        # When
        violations = service.analyze_consistency(episode, characters)

        # Then
        assert len(violations) == 2

        # 太郎の瞳の色(彼=太郎)
        taro_violation = next(v for v in violations if v.character_name == "太郎")
        assert taro_violation.expected == "茶色"
        assert taro_violation.actual == "青い"

        # 花子の髪色(彼女=花子)
        hanako_violation = next(v for v in violations if v.character_name == "花子")
        assert hanako_violation.expected == "金髪"
        assert hanako_violation.actual == "黒髪"

    @pytest.mark.spec("SPEC-QUALITY-018")
    def test_custom_project_rules_application(self, service: object) -> None:
        """プロジェクト固有のカスタムルールを適用"""
        # Given
        custom_rules = {"magic_color_consistency": {"fire_magic": "赤", "water_magic": "青", "earth_magic": "茶"}}

        episode = Episode(
            number=EpisodeNumber(5),
            title=EpisodeTitle("第5話"),
            target_words=WordCount(2000),
            content="""太郎は火の魔法を唱えた。
青い光が彼の手から放たれた。""",
        )

        characters = [CharacterProfile("太郎", {"magic_type": "fire_magic"})]

        # When
        violations = service.analyze_consistency(episode, characters, custom_rules=custom_rules)

        # Then
        assert len(violations) == 1
        assert violations[0].attribute == "magic_color"
        assert violations[0].expected == "赤"
        assert violations[0].actual == "青い"

    @pytest.mark.spec("SPEC-QUALITY-014")
    def test_ambiguous_description_handling(self, service: object) -> None:
        """曖昧な記述に対する適切な処理"""
        # Given

        episode = Episode(
            number=EpisodeNumber(6),
            title=EpisodeTitle("第6話"),
            target_words=WordCount(2000),
            content="""太郎は背が高い方だった。
クラスでは平均的な身長だ。""",
        )

        characters = [CharacterProfile("太郎", {"height": "180cm"})]

        # When
        violations = service.analyze_consistency(episode, characters)

        # Then
        # 「高い方」と「平均的」は矛盾の可能性があるが、
        # 確実でない場合は警告レベルとする
        if violations:
            assert any(v.severity == "warning" for v in violations)

    @pytest.mark.spec("SPEC-QUALITY-014")
    def test_timeline_aware_character_analysis(self, service: object) -> None:
        """時系列の変化を考慮した分析"""
        # Given

        episode = Episode(
            number=EpisodeNumber(10),  # 後半のエピソード
            title=EpisodeTitle("第10話"),
            target_words=WordCount(2000),
            content="""成長した太郎は、もう子供ではなかった。
18歳になった彼は、大人びた表情を見せる。""",
        )

        characters = [CharacterProfile("太郎", {"age": "15歳", "initial_age": "15歳"})]

        # When
        # エピソード番号から経過時間を推定
        violations = service.analyze_consistency(episode, characters, consider_timeline=True)

        # Then
        # 時間経過を考慮すれば18歳は妥当
        assert len(violations) == 0

    @pytest.mark.spec("SPEC-QUALITY-014")
    def test_efficient_processing_for_large_text(self, service: object) -> None:
        """大量のテキストでも効率的に処理"""
        # Given

        # 1万文字の長文エピソード
        long_content = "太郎は歩いていた。\n" * 1000
        episode = Episode(
            number=EpisodeNumber(100),
            title=EpisodeTitle("第100話"),
            target_words=WordCount(10000),
            content=long_content,
        )

        characters = [CharacterProfile("太郎", {"hair_color": "黒髪"})]

        # When
        start_time = time.time()
        service.analyze_consistency(episode, characters)
        elapsed_time = time.time() - start_time

        # Then
        assert elapsed_time < 1.0  # 1秒以内に完了


@pytest.mark.spec("SPEC-QUALITY-014")
class TestCharacterConsistencyPatterns:
    """キャラクター一貫性パターンのテスト"""

    @pytest.mark.spec("SPEC-QUALITY-014")
    def test_appearance_pattern_matching(self) -> None:
        """外見描写のパターンマッチング"""
        # Given
        service = CharacterConsistencyService(Mock())
        patterns = service.get_appearance_patterns()

        # Then
        assert "髪" in patterns["hair_color"]["keywords"]
        assert "瞳" in patterns["eye_color"]["keywords"]
        assert "肌" in patterns["skin_color"]["keywords"]

    @pytest.mark.spec("SPEC-QUALITY-014")
    def test_personality_pattern_matching(self) -> None:
        """性格描写のパターンマッチング"""
        # Given
        service = CharacterConsistencyService(Mock())
        patterns = service.get_personality_patterns()

        # Then
        assert "明るい" in patterns["cheerful"]["indicators"]
        assert "物静か" in patterns["quiet"]["indicators"]
        assert "熱血" in patterns["passionate"]["indicators"]

    @pytest.mark.spec("SPEC-QUALITY-014")
    def test_speech_pattern_matching(self) -> None:
        """話し方のパターンマッチング"""
        # Given
        service = CharacterConsistencyService(Mock())
        patterns = service.get_speech_patterns()

        # Then
        assert "です・ます" in patterns["polite"]["markers"]
        assert "俺" in patterns["masculine_casual"]["markers"]
        assert "わたくし" in patterns["formal"]["markers"]
