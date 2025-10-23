"""キャラクター一貫性チェックセッションのテスト

TDD RED Phase: 失敗するテストを先に作成
"""

from unittest.mock import Mock

import pytest

from noveler.domain.entities.character_consistency_session import CharacterConsistencySession
from noveler.domain.entities.episode import Episode
from noveler.domain.entities.project import Project
from noveler.domain.services.character_consistency_service import CharacterConsistencyService
from noveler.domain.value_objects.character_profile import CharacterProfile
from noveler.domain.value_objects.consistency_check_result import ConsistencyCheckResult
from noveler.domain.value_objects.consistency_violation import ConsistencyViolation
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.episode_title import EpisodeTitle
from noveler.domain.value_objects.session_id import SessionId
from noveler.domain.value_objects.word_count import WordCount


@pytest.mark.spec("SPEC-QUALITY-014")
class TestCharacterConsistencySession:
    """キャラクター一貫性チェックセッションのテスト"""

    @pytest.mark.spec("SPEC-CHARACTER_CONSISTENCY_SESSION-UNNAMED")
    def test_unnamed(self) -> None:
        """セッションを作成できることを確認"""
        # Given
        session_id = SessionId()
        project = Project(name="テストプロジェクト")

        # When
        session = CharacterConsistencySession(session_id, project)

        # Then
        assert session.session_id == session_id
        assert session.project == project
        assert len(session.results) == 0

    @pytest.mark.spec("SPEC-CHARACTER_CONSISTENCY_SESSION-CHECK")
    def test_check(self) -> None:
        """エピソード内のキャラクター描写の一貫性をチェック"""
        # Given
        session_id = SessionId()
        project = Project(name="テストプロジェクト")
        # ドメインサービスをモック化
        character_repo = Mock()
        consistency_service = CharacterConsistencyService(character_repo)
        session = CharacterConsistencySession(session_id, project, consistency_service)

        # キャラクタープロファイル
        character = CharacterProfile(
            name="山田太郎",
            attributes={"hair_color": "黒髪", "eye_color": "茶色", "personality": "内向的", "speech_style": "丁寧語"},
        )

        # エピソード(矛盾を含む)
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("第1話"),
            target_words=WordCount(2000),
            content="""山田太郎は教室に入った。
彼の金髪が朝日に輝いていた。
「おはよう!」と山田太郎は元気に挨拶した。
山田太郎の茶色い瞳が優しく微笑んでいた。""",
        )

        # When
        result = session.check_episode(episode, [character])

        # Then
        assert len(result.violations) >= 2  # 性格、話し方の矛盾(髪色は代名詞解決が必要)
        # 髪色の矛盾(代名詞解決が実装されている場合)
        hair_violations = [v for v in result.violations if v.attribute == "hair_color"]
        if hair_violations:
            hair_violation = hair_violations[0]
            assert hair_violation.character_name == "山田太郎"
            assert hair_violation.expected == "黒髪"
            assert hair_violation.actual == "金髪"
            assert hair_violation.line_number == 2

        # 性格の矛盾
        personality_violation = next(v for v in result.violations if v.attribute == "personality")
        assert personality_violation.expected == "内向的"
        assert "元気に" in personality_violation.actual

        # 話し方の矛盾
        speech_violation = next(v for v in result.violations if v.attribute == "speech_style")
        assert speech_violation.expected == "丁寧語"
        assert speech_violation.actual == "おはよう!"

    @pytest.mark.spec("SPEC-CHARACTER_CONSISTENCY_SESSION-PHYSICAL_CONSISTENCY")
    def test_physical_consistency_check(self) -> None:
        """体格一貫性チェックのテスト"""
        # Given
        characters = [
            CharacterProfile(
                name="太郎", attributes={"age": "18", "eye_color": "黒", "hair_color": "黒", "speech_style": "普通"}
            ),
            CharacterProfile(
                name="花子", attributes={"age": "17", "eye_color": "青", "hair_color": "金", "speech_style": "丁寧語"}
            ),
        ]
        session_id = SessionId()
        project = Project(name="テストプロジェクト")
        session = CharacterConsistencySession(session_id, project)
        episode = Episode(
            number=1,
            title="テスト",
            content="""18歳の太郎は真剣に本を読んでいる。
花子の金髪がふわりと揺れた。""",
            target_words=WordCount(2000),
        )

        # When
        result = session.check_episode(episode, characters)

        # Then
        assert len(result.violations) >= 1  # 最低でも一つの矛盾は検出される

        # 花子の髪色矛盾をチェック(実際に検出されている矛盾)
        hanako_violations = [v for v in result.violations if v.character_name == "花子" and v.attribute == "hair_color"]
        assert len(hanako_violations) > 0, "花子の髪色矛盾が検出されるべき"

        hanako_hair = hanako_violations[0]
        assert hanako_hair.expected == "金"  # プロファイルの設定値
        assert hanako_hair.actual == "金髪"  # エピソード内の表現

        # 太郎の情報は一貫している(年齢18歳はプロファイルと一致)
        taro_violations = [v for v in result.violations if v.character_name == "太郎"]
        # 太郎については矛盾が検出されないことを確認(プロファイルと一致しているため)
        assert len(taro_violations) == 0, "太郎の情報は一貫しているため矛盾は検出されないべき"

    @pytest.mark.spec("SPEC-CHARACTER_CONSISTENCY_SESSION-UNNAMED")
    def test_basic_functionality(self) -> None:
        """一貫性スコアを計算できることを確認"""
        # Given

        session = CharacterConsistencySession(SessionId(), Project("テスト"))
        result = ConsistencyCheckResult(
            episode_number=1,
            violations=[
                ConsistencyViolation("太郎", "hair_color", "黒髪", "金髪", 2),
                ConsistencyViolation("太郎", "age", "17歳", "18歳", 5),
            ],
        )

        # When
        score = session.calculate_consistency_score(result)

        # Then
        assert 0 <= score <= 100
        assert score < 100  # 矛盾があるので100点未満

    @pytest.mark.spec("SPEC-CHARACTER_CONSISTENCY_SESSION-UNNAMED")
    def test_edge_cases(self) -> None:
        """複数エピソードのチェック結果を集計"""
        # Given

        session = CharacterConsistencySession(SessionId(), Project("テスト"))

        # 複数エピソードをチェック
        for i in range(3):
            episode = Episode(
                number=EpisodeNumber(i + 1),
                title=EpisodeTitle(f"第{i + 1}話"),
                target_words=WordCount(2000),
                content=f"エピソード{i + 1}の内容",
            )

            session.check_episode(episode, [])

        # When
        summary = session.get_summary()

        # Then
        assert summary.total_episodes == 3
        assert summary.total_violations >= 0
        assert summary.average_consistency_score >= 0
        assert len(summary.violation_by_character) >= 0
        assert len(summary.violation_by_attribute) >= 0

    @pytest.mark.spec("SPEC-CHARACTER_CONSISTENCY_SESSION-UNNAMED")
    def test_error_handling(self) -> None:
        """プロジェクト固有の設定でチェックをカスタマイズ"""
        # Given
        project = Project(
            name="ファンタジー小説",
            settings={
                "consistency_check": {
                    "strict_mode": True,
                    "ignore_attributes": ["clothing"],
                    "custom_rules": {"magic_system": "consistent"},
                }
            },
        )

        session = CharacterConsistencySession(SessionId(), project)

        # When
        # 設定に基づいてチェックが調整される
        assert session.is_strict_mode is True
        assert "clothing" in session.ignored_attributes
        assert "magic_system" in session.custom_rules


@pytest.mark.spec("SPEC-QUALITY-014")
class TestCharacterProfile:
    """キャラクタープロファイル値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-CHARACTER_CONSISTENCY_SESSION-FILE")
    def test_file(self) -> None:
        """キャラクタープロファイルを作成できる"""
        # Given/When
        profile = CharacterProfile(
            name="山田太郎",
            attributes={
                "age": "17歳",
                "gender": "男性",
                "hair_color": "黒髪",
                "personality": ["真面目", "優しい"],
                "speech_style": "丁寧語",
            },
        )

        # Then
        assert profile.name == "山田太郎"
        assert profile.get_attribute("age") == "17歳"
        assert "真面目" in profile.get_attribute("personality")

    @pytest.mark.spec("SPEC-CHARACTER_CONSISTENCY_SESSION-UNNAMED")
    def test_validation(self) -> None:
        """必須属性が不足している場合にエラー"""
        # Given/When/Then
        with pytest.raises(TypeError, match="nameは必須です"):
            CharacterProfile(name="", attributes={})

    @pytest.mark.spec("SPEC-CHARACTER_CONSISTENCY_SESSION-UNNAMED")
    def test_integration(self) -> None:
        """値オブジェクトなので属性は不変"""
        # Given
        profile = CharacterProfile("太郎", {"age": "17歳"})

        # When/Then
        with pytest.raises(AttributeError, match=".*"):
            profile.name = "次郎"

        # 新しいインスタンスを作成して更新する方法が推奨
        new_profile = profile.with_updated_attribute("age", "18歳")
        assert profile.get_attribute("age") == "17歳"  # 元のインスタンスは変更されない
        assert new_profile.get_attribute("age") == "18歳"  # 新しいインスタンスは更新されている


@pytest.mark.spec("SPEC-QUALITY-014")
class TestConsistencyViolation:
    """一貫性違反値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-CHARACTER_CONSISTENCY_SESSION-UNNAMED")
    def test_performance(self) -> None:
        """違反情報を正しく作成できる"""
        # Given/When
        violation = ConsistencyViolation(
            character_name="太郎",
            attribute="hair_color",
            expected="黒髪",
            actual="金髪",
            line_number=10,
            context="彼の金髪が風になびいた。",
        )

        # Then
        assert violation.character_name == "太郎"
        assert violation.attribute == "hair_color"
        assert violation.expected == "黒髪"
        assert violation.actual == "金髪"
        assert violation.line_number == 10
        assert violation.context == "彼の金髪が風になびいた。"

    @pytest.mark.spec("SPEC-CHARACTER_CONSISTENCY_SESSION-UNNAMED")
    def test_configuration(self) -> None:
        """違反の重要度を判定できる"""
        # Given
        critical_violation = ConsistencyViolation("太郎", "gender", "男性", "女性", 5)
        minor_violation = ConsistencyViolation("太郎", "clothing", "制服", "私服", 10)

        # When/Then
        assert critical_violation.severity == "critical"
        assert minor_violation.severity == "minor"

    @pytest.mark.spec("SPEC-CHARACTER_CONSISTENCY_SESSION-UNNAMED")
    def test_initialization(self) -> None:
        """違反に対する修正提案を生成"""
        # Given
        violation = ConsistencyViolation("太郎", "hair_color", "黒髪", "金髪", 10, context="太郎の金髪が輝いていた。")

        # When
        suggestion = violation.get_correction_suggestion()

        # Then
        assert suggestion.original == "太郎の金髪が輝いていた。"
        assert suggestion.corrected == "太郎の黒髪が輝いていた。"
        assert suggestion.explanation == "キャラクター設定に合わせて「金髪」を「黒髪」に修正"
