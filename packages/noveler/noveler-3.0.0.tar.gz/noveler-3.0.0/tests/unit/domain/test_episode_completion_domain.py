#!/usr/bin/env python3
"""執筆完了ドメインエンティティのテスト
TDD原則:失敗するテストを先に書く(RED段階)
"""

from decimal import Decimal

import pytest

from noveler.domain.entities.episode_completion import (
    CharacterGrowthRecord,
    CompletedEpisode,
    ForeshadowingRecord,
    ImportantSceneRecord,
)
from noveler.domain.exceptions import EpisodeCompletionError
from noveler.domain.value_objects.episode_completion import (
    CharacterGrowthEvent,
    EpisodeCompletionEvent,
    ForeshadowingStatus,
    GrowthType,
    ImportantScene,
    SceneType,
)
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestEpisodeCompletionEvent:
    """執筆完了イベント値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_valid_completion_event(self) -> None:
        """有効な完了イベント作成"""
        event = EpisodeCompletionEvent(
            episode_number=1,
            completed_at=project_now().datetime,
            quality_score=Decimal("85.5"),
            word_count=5234,
            plot_data={"title": "テストエピソード"},
        )

        assert event.episode_number == 1
        assert event.quality_score == Decimal("85.5")
        assert event.word_count == 5234
        assert event.plot_data["title"] == "テストエピソード"

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_invalid_episode_number(self) -> None:
        """無効なエピソード番号は拒否"""
        with pytest.raises(ValueError, match="Episode number must be positive"):
            EpisodeCompletionEvent(
                episode_number=-1, completed_at=project_now().datetime, quality_score=Decimal("80"), word_count=5000
            )

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_invalid_quality_score(self) -> None:
        """無効な品質スコアは拒否"""
        with pytest.raises(ValueError, match="Quality score must be between 0 and 100"):
            EpisodeCompletionEvent(
                episode_number=1, completed_at=project_now().datetime, quality_score=Decimal("101"), word_count=5000
            )

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_invalid_word_count(self) -> None:
        """負の文字数は拒否"""
        with pytest.raises(ValueError, match="Word count must be non-negative"):
            EpisodeCompletionEvent(
                episode_number=1, completed_at=project_now().datetime, quality_score=Decimal("80"), word_count=-100
            )


class TestCharacterGrowthEvent:
    """キャラクター成長イベントのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_valid_growth_event(self) -> None:
        """有効な成長イベント作成"""
        event = CharacterGrowthEvent(
            character_name="綾瀬カノン",
            growth_type=GrowthType.REALIZATION,
            description="表面的な関係の限界を自覚",
            importance="high",
            auto_detected=False,
        )

        assert event.character_name == "綾瀬カノン"
        assert event.growth_type == GrowthType.REALIZATION
        assert event.importance == "high"
        assert not event.auto_detected

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_empty_character_name(self) -> None:
        """空のキャラクター名は拒否"""
        with pytest.raises(ValueError, match="Character name cannot be empty"):
            CharacterGrowthEvent(character_name="", growth_type=GrowthType.SKILL_ACQUISITION, description="テスト")

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_invalid_importance(self) -> None:
        """無効な重要度は拒否"""
        with pytest.raises(ValueError, match="Invalid importance level"):
            CharacterGrowthEvent(
                character_name="テスト",
                growth_type=GrowthType.EMOTIONAL_CHANGE,
                description="テスト",
                importance="very-high",
            )


class TestImportantScene:
    """重要シーン値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_valid_important_scene(self) -> None:
        """有効な重要シーン作成"""
        scene = ImportantScene(
            scene_id="first_glitch",
            scene_type=SceneType.TURNING_POINT,
            description="初めてのグリッチ体験",
            emotion_level="high",
            tags=["感覚共有", "記憶混線"],
        )

        assert scene.scene_id == "first_glitch"
        assert scene.scene_type == SceneType.TURNING_POINT
        assert scene.emotion_level == "high"
        assert "感覚共有" in scene.tags

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_immutable_tags(self) -> None:
        """タグリストの不変性"""
        tags = ["タグ1", "タグ2"]
        scene = ImportantScene(scene_id="test", scene_type=SceneType.EMOTIONAL_PEAK, description="テスト", tags=tags)

        # タグはタプルとして保存される
        assert isinstance(scene.tags, tuple)
        assert len(scene.tags) == 2


class TestForeshadowingStatus:
    """伏線ステータスのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_foreshadowing_status_values(self) -> None:
        """伏線ステータスの値確認"""
        assert ForeshadowingStatus.PLANNED.value == "planned"
        assert ForeshadowingStatus.PLANTED.value == "planted"
        assert ForeshadowingStatus.RESOLVED.value == "resolved"
        assert ForeshadowingStatus.ABANDONED.value == "abandoned"


class TestCompletedEpisode:
    """完了エピソードエンティティのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_create_completed_episode(self) -> None:
        """完了エピソードの作成"""
        event = EpisodeCompletionEvent(
            episode_number=1, completed_at=project_now().datetime, quality_score=Decimal("85.5"), word_count=5234
        )

        episode = CompletedEpisode.create_from_event(event)

        assert episode.episode_number == 1
        assert episode.status == "completed"
        assert episode.quality_score == Decimal("85.5")
        assert episode.word_count == 5234
        assert episode.completed_at is not None

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_add_character_growth(self) -> None:
        """キャラクター成長記録の追加"""
        event = EpisodeCompletionEvent(
            episode_number=1, completed_at=project_now().datetime, quality_score=Decimal("85"), word_count=5000
        )

        episode = CompletedEpisode.create_from_event(event)

        growth_event = CharacterGrowthEvent(
            character_name="主人公", growth_type=GrowthType.SKILL_ACQUISITION, description="新しい能力を獲得"
        )

        episode.add_character_growth(growth_event)

        assert len(episode.character_growth_records) == 1
        assert episode.character_growth_records[0].character_name == "主人公"

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_add_important_scene(self) -> None:
        """重要シーンの追加"""
        event = EpisodeCompletionEvent(
            episode_number=1, completed_at=project_now().datetime, quality_score=Decimal("85"), word_count=5000
        )

        episode = CompletedEpisode.create_from_event(event)

        scene = ImportantScene(scene_id="climax", scene_type=SceneType.CLIMAX, description="クライマックスシーン")

        episode.add_important_scene(scene)

        assert len(episode.important_scenes) == 1
        assert episode.important_scenes[0].scene_id == "climax"

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_update_foreshadowing(self) -> None:
        """伏線ステータスの更新"""
        event = EpisodeCompletionEvent(
            episode_number=1, completed_at=project_now().datetime, quality_score=Decimal("85"), word_count=5000
        )

        episode = CompletedEpisode.create_from_event(event)

        # 伏線を仕込む
        episode.plant_foreshadowing("F001", "重要な伏線")

        assert len(episode.foreshadowing_records) == 1
        assert episode.foreshadowing_records[0].status == ForeshadowingStatus.PLANTED

        # 伏線を回収
        episode.resolve_foreshadowing("F001")

        # ステータスが更新される
        record = next(f for f in episode.foreshadowing_records if f.foreshadowing_id == "F001")
        assert record.status == ForeshadowingStatus.RESOLVED

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_domain_events(self) -> None:
        """ドメインイベントの記録"""
        event = EpisodeCompletionEvent(
            episode_number=1, completed_at=project_now().datetime, quality_score=Decimal("85"), word_count=5000
        )

        episode = CompletedEpisode.create_from_event(event)

        # イベントが記録されている
        events = episode.get_domain_events()
        assert len(events) == 1
        assert events[0]["type"] == "EpisodeCompleted"
        assert events[0]["episode_number"] == 1

        # クリア後は空
        episode.clear_domain_events()
        assert len(episode.get_domain_events()) == 0

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_validation_low_quality_warning(self) -> None:
        """低品質スコアの警告"""
        event = EpisodeCompletionEvent(
            episode_number=1,
            completed_at=project_now().datetime,
            quality_score=Decimal("70"),  # 閾値以下
            word_count=5000,
        )

        episode = CompletedEpisode.create_from_event(event)

        # 低品質警告が発生
        assert episode.has_quality_warning()
        assert "low_quality" in episode.get_warnings()

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_extract_from_plot_data(self) -> None:
        """プロットデータからの情報抽出"""
        plot_data = {
            "character_growth": [{"character": "主人公", "type": "realization", "description": "真実に気づく"}],
            "important_scenes": [{"scene_id": "revelation", "type": "turning_point", "description": "真実の開示"}],
            "foreshadowing": {"planted": ["F001", "F002"], "resolved": ["F003"]},
        }

        event = EpisodeCompletionEvent(
            episode_number=1,
            completed_at=project_now().datetime,
            quality_score=Decimal("85"),
            word_count=5000,
            plot_data=plot_data,
        )

        episode = CompletedEpisode.create_from_event(event)
        episode.extract_from_plot_data()

        # プロットデータから情報が抽出される
        assert len(episode.character_growth_records) == 1
        assert len(episode.important_scenes) == 1
        assert len(episode.foreshadowing_records) == 3  # 2 planted + 1 resolved


class TestCharacterGrowthRecord:
    """キャラクター成長記録エンティティのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_create_growth_record(self) -> None:
        """成長記録の作成"""
        event = CharacterGrowthEvent(
            character_name="主人公",
            growth_type=GrowthType.EMOTIONAL_CHANGE,
            description="感情の変化",
            importance="high",
        )

        record = CharacterGrowthRecord.from_event(episode_number=1, event=event)

        assert record.character_name == "主人公"
        assert record.episode_number == 1
        assert record.growth_type == GrowthType.EMOTIONAL_CHANGE
        assert record.importance == "high"
        assert record.recorded_at is not None

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_to_persistence_dict(self) -> None:
        """永続化用辞書への変換"""
        event = CharacterGrowthEvent(
            character_name="主人公", growth_type=GrowthType.SKILL_ACQUISITION, description="新技能習得"
        )

        record = CharacterGrowthRecord.from_event(1, event)
        persistence_dict = record.to_persistence_dict()

        assert persistence_dict["character"] == "主人公"
        assert persistence_dict["episode"] == "第1話"
        assert persistence_dict["growth_type"] == "skill_acquisition"
        assert persistence_dict["description"] == "新技能習得"
        assert "recorded_at" in persistence_dict


class TestImportantSceneRecord:
    """重要シーン記録エンティティのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_create_scene_record(self) -> None:
        """シーン記録の作成"""
        scene = ImportantScene(
            scene_id="battle_start",
            scene_type=SceneType.ACTION_SEQUENCE,
            description="戦闘開始",
            emotion_level="medium",
            tags=["アクション", "転換点"],
        )

        record = ImportantSceneRecord.from_scene(episode_number=5, scene=scene)

        assert record.episode_number == 5
        assert record.scene_id == "battle_start"
        assert record.scene_type == SceneType.ACTION_SEQUENCE
        assert "アクション" in record.tags

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_scene_importance_calculation(self) -> None:
        """シーン重要度の計算"""
        # 高感情レベル + ターニングポイント = 最高重要度
        scene = ImportantScene(
            scene_id="climax", scene_type=SceneType.TURNING_POINT, description="クライマックス", emotion_level="high"
        )

        record = ImportantSceneRecord.from_scene(1, scene)

        assert record.calculate_importance() == "critical"


class TestForeshadowingRecord:
    """伏線記録エンティティのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_create_foreshadowing_record(self) -> None:
        """伏線記録の作成"""
        record = ForeshadowingRecord(
            foreshadowing_id="F001",
            description="重要アイテムの存在を示唆",
            status=ForeshadowingStatus.PLANTED,
            planted_episode=3,
        )

        assert record.foreshadowing_id == "F001"
        assert record.status == ForeshadowingStatus.PLANTED
        assert record.planted_episode == 3
        assert record.resolved_episode is None

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_resolve_foreshadowing(self) -> None:
        """伏線の回収"""
        record = ForeshadowingRecord(
            foreshadowing_id="F001", description="重要アイテム", status=ForeshadowingStatus.PLANTED, planted_episode=3
        )

        record.resolve(episode_number=10)

        assert record.status == ForeshadowingStatus.RESOLVED
        assert record.resolved_episode == 10

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_cannot_resolve_unplanted(self) -> None:
        """未設置の伏線は回収できない"""
        record = ForeshadowingRecord(foreshadowing_id="F001", description="テスト", status=ForeshadowingStatus.PLANNED)

        with pytest.raises(EpisodeCompletionError, match="Cannot resolve unplanted foreshadowing"):
            record.resolve(episode_number=5)

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_to_persistence_dict(self) -> None:
        """永続化用辞書への変換"""
        record = ForeshadowingRecord(
            foreshadowing_id="F001",
            description="伏線の説明",
            status=ForeshadowingStatus.RESOLVED,
            planted_episode=3,
            resolved_episode=8,
        )

        persistence_dict = record.to_persistence_dict()

        assert persistence_dict["id"] == "F001"
        assert persistence_dict["status"] == "resolved"
        assert persistence_dict["planted_episode"] == 3
        assert persistence_dict["resolved_episode"] == 8
        assert "episodes" in persistence_dict
        assert persistence_dict["episodes"] == [3, 8]
