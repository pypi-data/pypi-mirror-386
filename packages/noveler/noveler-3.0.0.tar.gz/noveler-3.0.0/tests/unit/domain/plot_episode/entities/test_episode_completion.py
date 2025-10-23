#!/usr/bin/env python3
"""EpisodeCompletion エンティティのユニットテスト

仕様書: specs/episode_completion_entity.spec.md
TDD原則に従い、仕様書に基づいてテストを作成
"""

import pytest
from datetime import datetime
from decimal import Decimal
pytestmark = pytest.mark.plot_episode



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


class TestCharacterGrowthRecord:
    """CharacterGrowthRecordのテストクラス"""

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    @pytest.mark.spec("SPEC-EPISODE-001")
    @pytest.mark.requirement("REQ-1.4.3")
    def test_from_event_creates_record_with_current_time(self) -> None:
        """イベントから記録作成時は現在時刻で記録されることを確認

        仕様書: specs/episode_management.md
        要件: メタデータの更新
        """
        # Given
        event = CharacterGrowthEvent(
            character_name="主人公",
            growth_type=GrowthType.SKILL_ACQUISITION,
            description="剣術レベルアップ",
            importance="high",
            auto_detected=True,
        )

        episode_number = 5
        before_time = project_now().datetime

        # When
        record = CharacterGrowthRecord.from_event(episode_number, event)

        # Then
        after_time = project_now().datetime
        assert record.character_name == "主人公"
        assert record.episode_number == 5
        assert record.growth_type == GrowthType.SKILL_ACQUISITION
        assert record.description == "剣術レベルアップ"
        assert record.importance == "high"
        assert record.auto_detected is True
        assert before_time <= record.recorded_at <= after_time

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_to_persistence_dict_formats_episode_number(self) -> None:
        """永続化時は話数形式で保存されることを確認"""
        # Given
        event = CharacterGrowthEvent(
            character_name="ヒロイン",
            growth_type=GrowthType.RELATIONSHIP_CHANGE,
            description="主人公との関係深化",
            importance="medium",
        )

        record = CharacterGrowthRecord.from_event(10, event)

        # When
        result = record.to_persistence_dict()

        # Then
        assert result["character"] == "ヒロイン"
        assert result["episode"] == "第10話"
        assert result["growth_type"] == "relationship_change"
        assert result["description"] == "主人公との関係深化"
        assert result["importance"] == "medium"
        assert result["auto_detected"] is False
        assert "recorded_at" in result


class TestImportantSceneRecord:
    """ImportantSceneRecordのテストクラス"""

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_from_scene_creates_record_with_current_time(self) -> None:
        """シーンから記録作成時は現在時刻で記録されることを確認"""
        # Given
        scene = ImportantScene(
            scene_id="scene_001",
            scene_type=SceneType.CLIMAX,
            description="最終決戦",
            emotion_level="high",
            tags=["戦闘", "感動"],
        )

        episode_number = 12
        before_time = project_now().datetime

        # When
        record = ImportantSceneRecord.from_scene(episode_number, scene)

        # Then
        after_time = project_now().datetime
        assert record.episode_number == 12
        assert record.scene_id == "scene_001"
        assert record.scene_type == SceneType.CLIMAX
        assert record.description == "最終決戦"
        assert record.emotion_level == "high"
        assert record.tags == ["戦闘", "感動"]
        assert before_time <= record.recorded_at <= after_time

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_calculate_importance_critical_level(self) -> None:
        """重要度がcriticalと計算されることを確認"""
        # Given: high感情レベル(3) + CLIMAX(3) = 6 → critical (score >= 6 のため)
        record = ImportantSceneRecord(
            episode_number=1,
            scene_id="test",
            scene_type=SceneType.CLIMAX,
            description="test",
            emotion_level="high",
            tags=[],
            recorded_at=project_now().datetime,
        )

        # When
        importance = record.calculate_importance()

        # Then
        assert importance == "critical"  # high(3) + CLIMAX(3) = 6, score >= 6

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_calculate_importance_high_level(self) -> None:
        """重要度がhighと計算されることを確認"""
        # Given: medium感情レベル(2) + TURNING_POINT(3) = 5 → high (score < 6)
        # Given: medium感情レベル(2) + REVELATION(2) = 4 → high
        record = ImportantSceneRecord(
            episode_number=1,
            scene_id="test",
            scene_type=SceneType.REVELATION,
            description="test",
            emotion_level="medium",
            tags=[],
            recorded_at=project_now().datetime,
        )

        # When
        importance = record.calculate_importance()

        # Then
        assert importance == "high"

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_calculate_importance_medium_level(self) -> None:
        """重要度がmediumと計算されることを確認"""
        # Given: low感情レベル(1) + その他シーン(1) = 2 → medium
        record = ImportantSceneRecord(
            episode_number=1,
            scene_id="test",
            scene_type=SceneType.EMOTIONAL_PEAK,
            description="test",
            emotion_level="low",
            tags=[],
            recorded_at=project_now().datetime,
        )

        # When
        importance = record.calculate_importance()

        # Then
        assert importance == "medium"

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_to_persistence_dict_includes_calculated_importance(self) -> None:
        """永続化辞書に計算された重要度が含まれることを確認"""
        # Given
        record = ImportantSceneRecord(
            episode_number=5,
            scene_id="scene_test",
            scene_type=SceneType.TURNING_POINT,
            description="転換点",
            emotion_level="high",
            tags=["重要", "転機"],
            recorded_at=datetime(2025, 1, 1, 12, 0, 0, tzinfo=JST),
        )

        # When
        result = record.to_persistence_dict()

        # Then
        assert result["episode"] == "第5話"
        assert result["scene_id"] == "scene_test"
        assert result["scene_type"] == "turning_point"
        assert result["description"] == "転換点"
        assert result["emotion_level"] == "high"
        assert result["importance"] == "critical"  # high(3) + TURNING_POINT(3) = 6, score >= 6
        assert result["tags"] == ["重要", "転機"]
        assert result["recorded_at"] == "2025-01-01T12:00:00"


class TestForeshadowingRecord:
    """ForeshadowingRecordのテストクラス"""

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_plant_from_planned_status(self) -> None:
        """計画済み状態から仕込み成功することを確認"""
        # Given
        record = ForeshadowingRecord(
            foreshadowing_id="F001", description="主人公の秘密", status=ForeshadowingStatus.PLANNED
        )

        before_time = project_now().datetime

        # When
        record.plant(5)

        # Then
        after_time = project_now().datetime
        assert record.status == ForeshadowingStatus.PLANTED
        assert record.planted_episode == 5
        assert before_time <= record.updated_at <= after_time

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_plant_from_invalid_status_raises_error(self) -> None:
        """既に仕込み済みの伏線を再度仕込もうとするとエラーが発生することを確認"""
        # Given
        record = ForeshadowingRecord(foreshadowing_id="F001", description="test", status=ForeshadowingStatus.PLANTED)

        # When & Then
        with pytest.raises(EpisodeCompletionError) as exc_info:
            record.plant(5)
        assert "F001 is already planted" in str(exc_info.value)

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_resolve_from_planted_status(self) -> None:
        """仕込み済み状態から回収成功することを確認"""
        # Given
        record = ForeshadowingRecord(foreshadowing_id="F001", description="test", status=ForeshadowingStatus.PLANTED)
        before_time = project_now().datetime

        # When
        record.resolve(10)

        # Then
        after_time = project_now().datetime
        assert record.status == ForeshadowingStatus.RESOLVED
        assert record.resolved_episode == 10
        assert before_time <= record.updated_at <= after_time

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_resolve_from_invalid_status_raises_error(self) -> None:
        """未仕込みの伏線を回収しようとするとエラーが発生することを確認"""
        # Given
        record = ForeshadowingRecord(foreshadowing_id="F001", description="test", status=ForeshadowingStatus.PLANNED)

        # When & Then
        with pytest.raises(EpisodeCompletionError) as exc_info:
            record.resolve(10)
        assert "Cannot resolve unplanted foreshadowing F001" in str(exc_info.value)

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_abandon_updates_status_and_time(self) -> None:
        """放棄時にステータスと更新時刻が更新されることを確認"""
        # Given
        record = ForeshadowingRecord(foreshadowing_id="F001", description="test", status=ForeshadowingStatus.PLANNED)
        before_time = project_now().datetime

        # When
        record.abandon()

        # Then
        after_time = project_now().datetime
        assert record.status == ForeshadowingStatus.ABANDONED
        assert before_time <= record.updated_at <= after_time

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_to_persistence_dict_includes_episodes(self) -> None:
        """永続化辞書にエピソード情報が含まれることを確認"""
        # Given
        record = ForeshadowingRecord(
            foreshadowing_id="F001",
            description="test foreshadowing",
            status=ForeshadowingStatus.RESOLVED,
            planted_episode=3,
            resolved_episode=8,
        )

        # When
        result = record.to_persistence_dict()

        # Then
        assert result["id"] == "F001"
        assert result["description"] == "test foreshadowing"
        assert result["status"] == "resolved"
        assert result["planted_episode"] == 3
        assert result["resolved_episode"] == 8
        assert result["episodes"] == [3, 8]
        assert "updated_at" in result


class TestCompletedEpisode:
    """CompletedEpisodeのテストクラス"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.completion_event = EpisodeCompletionEvent(
            episode_number=1,
            completed_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=JST),
            quality_score=Decimal("85.5"),
            word_count=4500,
            plot_data={},
        )

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_create_from_event_initializes_properly(self) -> None:
        """イベントから正しく初期化されることを確認"""
        # When
        episode = CompletedEpisode.create_from_event(self.completion_event)

        # Then
        assert episode.episode_number == 1
        assert episode.status == "completed"
        assert episode.completed_at == datetime(2025, 1, 1, 10, 0, 0, tzinfo=JST)
        assert episode.quality_score == Decimal("85.5")
        assert episode.word_count == 4500
        assert episode.plot_data == {}
        assert len(episode.character_growth_records) == 0
        assert len(episode.important_scenes) == 0
        assert len(episode.foreshadowing_records) == 0

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_constructor_emits_domain_event(self) -> None:
        """コンストラクタでドメインイベントが発行されることを確認"""
        # When
        episode = CompletedEpisode(1, self.completion_event)

        # Then
        events = episode.get_domain_events()
        assert len(events) == 1
        assert events[0]["type"] == "EpisodeCompleted"
        assert events[0]["episode_number"] == 1
        assert events[0]["quality_score"] == 85.5
        assert events[0]["word_count"] == 4500

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_add_character_growth_appends_record_and_emits_event(self) -> None:
        """キャラクター成長追加時に記録追加とイベント発行されることを確認"""
        # Given
        episode = CompletedEpisode(1, self.completion_event)
        growth_event = CharacterGrowthEvent(
            character_name="主人公",
            growth_type=GrowthType.SKILL_ACQUISITION,
            description="戦闘スキル向上",
            importance="high",
        )

        initial_events = len(episode.get_domain_events())

        # When
        episode.add_character_growth(growth_event)

        # Then
        assert len(episode.character_growth_records) == 1
        record = episode.character_growth_records[0]
        assert record.character_name == "主人公"
        assert record.growth_type == GrowthType.SKILL_ACQUISITION
        assert record.description == "戦闘スキル向上"

        events = episode.get_domain_events()
        assert len(events) == initial_events + 1
        new_event = events[-1]
        assert new_event["type"] == "CharacterGrowthAdded"
        assert new_event["character"] == "主人公"
        assert new_event["growth_type"] == "skill_acquisition"

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_add_important_scene_appends_record_and_emits_event(self) -> None:
        """重要シーン追加時に記録追加とイベント発行されることを確認"""
        # Given
        episode = CompletedEpisode(1, self.completion_event)
        scene = ImportantScene(
            scene_id="scene_001",
            scene_type=SceneType.CLIMAX,
            description="決戦シーン",
            emotion_level="high",
            tags=["戦闘"],
        )

        initial_events = len(episode.get_domain_events())

        # When
        episode.add_important_scene(scene)

        # Then
        assert len(episode.important_scenes) == 1
        record = episode.important_scenes[0]
        assert record.scene_id == "scene_001"
        assert record.scene_type == SceneType.CLIMAX
        assert record.description == "決戦シーン"

        events = episode.get_domain_events()
        assert len(events) == initial_events + 1
        new_event = events[-1]
        assert new_event["type"] == "ImportantSceneAdded"
        assert new_event["scene_id"] == "scene_001"
        assert new_event["scene_type"] == "climax"

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_plant_foreshadowing_creates_new_record(self) -> None:
        """新規伏線仕込み時に記録作成とイベント発行されることを確認"""
        # Given
        episode = CompletedEpisode(1, self.completion_event)
        initial_events = len(episode.get_domain_events())

        # When
        episode.plant_foreshadowing("F001", "主人公の秘密")

        # Then
        assert len(episode.foreshadowing_records) == 1
        record = episode.foreshadowing_records[0]
        assert record.foreshadowing_id == "F001"
        assert record.description == "主人公の秘密"
        assert record.status == ForeshadowingStatus.PLANTED
        assert record.planted_episode == 1

        events = episode.get_domain_events()
        assert len(events) == initial_events + 1
        new_event = events[-1]
        assert new_event["type"] == "ForeshadowingPlanted"
        assert new_event["foreshadowing_id"] == "F001"

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_plant_foreshadowing_updates_existing_record(self) -> None:
        """既存伏線レコードの仕込み更新を確認"""
        # Given
        episode = CompletedEpisode(1, self.completion_event)
        existing_record = ForeshadowingRecord(
            foreshadowing_id="F001", description="existing", status=ForeshadowingStatus.PLANNED
        )

        episode.foreshadowing_records.append(existing_record)

        # When
        episode.plant_foreshadowing("F001", "updated description")

        # Then
        assert len(episode.foreshadowing_records) == 1
        record = episode.foreshadowing_records[0]
        assert record.status == ForeshadowingStatus.PLANTED
        assert record.planted_episode == 1

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_resolve_foreshadowing_creates_record_if_not_exists(self) -> None:
        """存在しない伏線の回収時に新しい記録を作成することを確認"""
        # Given
        episode = CompletedEpisode(1, self.completion_event)

        # When
        episode.resolve_foreshadowing("F001")

        # Then
        assert len(episode.foreshadowing_records) == 1
        record = episode.foreshadowing_records[0]
        assert record.foreshadowing_id == "F001"
        assert record.status == ForeshadowingStatus.RESOLVED
        assert record.resolved_episode == 1

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_extract_from_plot_data_processes_character_growth(self) -> None:
        """プロットデータからキャラクター成長を抽出することを確認"""
        # Given
        plot_data = {
            "character_growth": [
                {
                    "character": "主人公",
                    "type": "skill_acquisition",
                    "description": "魔法スキル習得",
                    "importance": "high",
                }
            ]
        }
        event = EpisodeCompletionEvent(
            episode_number=1,
            completed_at=project_now().datetime,
            quality_score=Decimal("85"),
            word_count=4000,
            plot_data=plot_data,
        )

        episode = CompletedEpisode(1, event)

        # When
        episode.extract_from_plot_data()

        # Then
        assert len(episode.character_growth_records) == 1
        record = episode.character_growth_records[0]
        assert record.character_name == "主人公"
        assert record.growth_type == GrowthType.SKILL_ACQUISITION
        assert record.description == "魔法スキル習得"

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_extract_from_plot_data_processes_important_scenes(self) -> None:
        """プロットデータから重要シーンを抽出することを確認"""
        # Given
        plot_data = {
            "important_scenes": [
                {
                    "scene_id": "scene_001",
                    "type": "climax",
                    "description": "最終決戦",
                    "emotion_level": "high",
                    "tags": ["戦闘", "感動"],
                }
            ]
        }
        event = EpisodeCompletionEvent(
            episode_number=1,
            completed_at=project_now().datetime,
            quality_score=Decimal("85"),
            word_count=4000,
            plot_data=plot_data,
        )

        episode = CompletedEpisode(1, event)

        # When
        episode.extract_from_plot_data()

        # Then
        assert len(episode.important_scenes) == 1
        record = episode.important_scenes[0]
        assert record.scene_id == "scene_001"
        assert record.scene_type == SceneType.CLIMAX
        assert record.description == "最終決戦"

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_extract_from_plot_data_processes_foreshadowing(self) -> None:
        """プロットデータから伏線を抽出することを確認"""
        # Given
        plot_data = {"foreshadowing": {"planted": ["F001", "F002"], "resolved": ["F003"]}}
        event = EpisodeCompletionEvent(
            episode_number=1,
            completed_at=project_now().datetime,
            quality_score=Decimal("85"),
            word_count=4000,
            plot_data=plot_data,
        )

        episode = CompletedEpisode(1, event)

        # When
        episode.extract_from_plot_data()

        # Then
        assert len(episode.foreshadowing_records) == 3
        planted_records = [r for r in episode.foreshadowing_records if r.status == ForeshadowingStatus.PLANTED]
        resolved_records = [r for r in episode.foreshadowing_records if r.status == ForeshadowingStatus.RESOLVED]
        assert len(planted_records) == 2
        assert len(resolved_records) == 1

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_quality_check_low_quality_warning(self) -> None:
        """低品質時に警告が発生することを確認"""
        # Given
        low_quality_event = EpisodeCompletionEvent(
            episode_number=1,
            completed_at=project_now().datetime,
            quality_score=Decimal("75"),  # < 80
            word_count=4000,
            plot_data={},
        )

        # When
        episode = CompletedEpisode(1, low_quality_event)

        # Then
        assert episode.has_quality_warning() is True
        warnings = episode.get_warnings()
        assert "low_quality" in warnings

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_quality_check_low_word_count_warning(self) -> None:
        """文字数不足時に警告が発生することを確認"""
        # Given
        low_word_event = EpisodeCompletionEvent(
            episode_number=1,
            completed_at=project_now().datetime,
            quality_score=Decimal("85"),
            word_count=2500,  # < 3000
            plot_data={},
        )

        # When
        episode = CompletedEpisode(1, low_word_event)

        # Then
        assert episode.has_quality_warning() is True
        warnings = episode.get_warnings()
        assert "low_word_count" in warnings

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_quality_check_high_word_count_warning(self) -> None:
        """文字数過多時に警告が発生することを確認"""
        # Given
        high_word_event = EpisodeCompletionEvent(
            episode_number=1,
            completed_at=project_now().datetime,
            quality_score=Decimal("85"),
            word_count=8500,  # > 8000
            plot_data={},
        )

        # When
        episode = CompletedEpisode(1, high_word_event)

        # Then
        assert episode.has_quality_warning() is True
        warnings = episode.get_warnings()
        assert "high_word_count" in warnings

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_clear_domain_events(self) -> None:
        """ドメインイベントクリアが正しく動作することを確認"""
        # Given
        episode = CompletedEpisode(1, self.completion_event)
        initial_count = len(episode.get_domain_events())
        assert initial_count > 0

        # When
        episode.clear_domain_events()

        # Then
        assert len(episode.get_domain_events()) == 0

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_to_persistence_dict_includes_all_data(self) -> None:
        """永続化辞書に全データが含まれることを確認"""
        # Given
        episode = CompletedEpisode(1, self.completion_event)
        growth_event = CharacterGrowthEvent(
            character_name="主人公", growth_type=GrowthType.SKILL_ACQUISITION, description="成長", importance="high"
        )

        episode.add_character_growth(growth_event)

        # When
        result = episode.to_persistence_dict()

        # Then
        assert result["episode_number"] == 1
        assert result["status"] == "completed"
        assert result["completed_at"] == "2025-01-01T10:00:00"
        assert result["quality_score"] == 85.5
        assert result["word_count"] == 4500
        assert len(result["character_growth"]) == 1
        assert len(result["important_scenes"]) == 0
        assert len(result["foreshadowing"]) == 0
        assert isinstance(result["warnings"], list)
