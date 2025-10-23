#!/usr/bin/env python3
"""Scene エンティティのユニットテスト

仕様書: specs/scene_entity.spec.md
TDD原則に従い、仕様書に基づいてテストを作成
"""

from datetime import datetime

import pytest

from noveler.domain.entities.scene_entity import ImportanceLevel, Scene, SceneCategory
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.scene_direction import SceneDirection
from noveler.domain.value_objects.scene_setting import SceneSetting

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestScene:
    """Sceneのテストクラス"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.scene_id = "scene_001"
        self.title = "決戦の時"
        self.category = SceneCategory.CLIMAX
        self.importance_level = ImportanceLevel.S
        self.episode_range = "第10話-第11話"

    # ===== 1. 初期化と検証テスト =====

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_valid_initialization_required_fields_only(self) -> None:
        """TEST-1: 必須フィールドのみでの正常初期化"""
        # Given & When
        before_creation = project_now().datetime
        scene = Scene(
            scene_id=self.scene_id,
            title=self.title,
            category=self.category,
            importance_level=self.importance_level,
            episode_range=self.episode_range,
        )

        after_creation = project_now().datetime

        # Then: 基本フィールド
        assert scene.scene_id == self.scene_id
        assert scene.title == self.title
        assert scene.category == self.category
        assert scene.importance_level == self.importance_level
        assert scene.episode_range == self.episode_range

        # Then: 時刻フィールド
        assert before_creation <= scene.created_at <= after_creation
        assert before_creation <= scene.updated_at <= after_creation

        # Then: オプションフィールドのデフォルト値
        assert scene.setting is None
        assert scene.direction is None
        assert scene.characters == []
        assert scene.key_elements == []
        assert scene.writing_notes == {}
        assert scene.quality_checklist == {}

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_initialization_with_all_fields(self) -> None:
        """TEST-2: 全フィールド指定での初期化"""
        # Given
        custom_created_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=JST)
        custom_updated_at = datetime(2025, 1, 1, 13, 0, 0, tzinfo=JST)
        setting = SceneSetting("学園の屋上", "夕方", "晴れ", "緊張した")
        direction = SceneDirection("fast", "急上昇", "怒り")
        characters = ["主人公", "ヒロイン"]
        key_elements = ["決闘", "真実の告白"]
        writing_notes = {"重要": "読者の心を掴む"}
        quality_checklist = {"感情描写": ["怒りの表現"]}

        # When
        scene = Scene(
            scene_id=self.scene_id,
            title=self.title,
            category=self.category,
            importance_level=self.importance_level,
            episode_range=self.episode_range,
            created_at=custom_created_at,
            updated_at=custom_updated_at,
            setting=setting,
            direction=direction,
            characters=characters,
            key_elements=key_elements,
            writing_notes=writing_notes,
            quality_checklist=quality_checklist,
        )

        # Then
        assert scene.created_at == custom_created_at
        assert scene.updated_at == custom_updated_at
        assert scene.setting == setting
        assert scene.direction == direction
        assert scene.characters == characters
        assert scene.key_elements == key_elements
        assert scene.writing_notes == writing_notes
        assert scene.quality_checklist == quality_checklist

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_empty_scene_id_raises_error(self) -> None:
        """TEST-3: 空のscene_idでValueError"""
        # When & Then
        with pytest.raises(ValueError, match="scene_id は必須です"):
            Scene(
                scene_id="",
                title=self.title,
                category=self.category,
                importance_level=self.importance_level,
                episode_range=self.episode_range,
            )

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_whitespace_scene_id_raises_error(self) -> None:
        """TEST-4: 空白のみのscene_idでValueError"""
        # When & Then
        with pytest.raises(ValueError, match="scene_id は必須です"):
            Scene(
                scene_id="   \t\n  ",
                title=self.title,
                category=self.category,
                importance_level=self.importance_level,
                episode_range=self.episode_range,
            )

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_empty_title_raises_error(self) -> None:
        """TEST-5: 空のtitleでValueError"""
        # When & Then
        with pytest.raises(ValueError, match="title は必須です"):
            Scene(
                scene_id=self.scene_id,
                title="",
                category=self.category,
                importance_level=self.importance_level,
                episode_range=self.episode_range,
            )

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_whitespace_title_raises_error(self) -> None:
        """TEST-6: 空白のみのtitleでValueError"""
        # When & Then
        with pytest.raises(ValueError, match="title は必須です"):
            Scene(
                scene_id=self.scene_id,
                title="   \t\n  ",
                category=self.category,
                importance_level=self.importance_level,
                episode_range=self.episode_range,
            )

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_empty_episode_range_raises_error(self) -> None:
        """TEST-7: 空のepisode_rangeでValueError"""
        # When & Then
        with pytest.raises(ValueError, match="episode_range は必須です"):
            Scene(
                scene_id=self.scene_id,
                title=self.title,
                category=self.category,
                importance_level=self.importance_level,
                episode_range="",
            )

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_whitespace_episode_range_raises_error(self) -> None:
        """TEST-8: 空白のみのepisode_rangeでValueError"""
        # When & Then
        with pytest.raises(ValueError, match="episode_range は必須です"):
            Scene(
                scene_id=self.scene_id,
                title=self.title,
                category=self.category,
                importance_level=self.importance_level,
                episode_range="   \t\n  ",
            )

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_all_scene_categories_accepted(self) -> None:
        """TEST-9: 全SceneCategoryの受け入れ確認"""
        # Given
        categories = [
            SceneCategory.CLIMAX,
            SceneCategory.EMOTIONAL,
            SceneCategory.ROMANCE,
            SceneCategory.ACTION,
            SceneCategory.MYSTERY,
            SceneCategory.COMEDY,
            SceneCategory.DAILY,
        ]

        # When & Then
        for category in categories:
            scene = Scene(
                scene_id=f"scene_{category.value}",
                title="テストシーン",
                category=category,
                importance_level=ImportanceLevel.B,
                episode_range="第1話",
            )

            assert scene.category == category

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_all_importance_levels_accepted(self) -> None:
        """TEST-10: 全ImportanceLevelの受け入れ確認"""
        # Given
        levels = [ImportanceLevel.S, ImportanceLevel.A, ImportanceLevel.B, ImportanceLevel.C]

        # When & Then
        for level in levels:
            scene = Scene(
                scene_id=f"scene_{level.value}",
                title="テストシーン",
                category=SceneCategory.DAILY,
                importance_level=level,
                episode_range="第1話",
            )

            assert scene.importance_level == level

    # ===== 2. 設定情報管理テスト =====

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_set_setting_updates_field_and_time(self) -> None:
        """TEST-11: 設定情報の更新と時刻記録"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        setting = SceneSetting("魔法学園", "昼", "快晴", "活気のある")
        original_updated_at = scene.updated_at

        # When
        before_update = project_now().datetime
        scene.set_setting(setting)
        after_update = project_now().datetime

        # Then
        assert scene.setting == setting
        assert scene.updated_at > original_updated_at
        assert before_update <= scene.updated_at <= after_update

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_set_direction_updates_field_and_time(self) -> None:
        """TEST-12: 演出指示の更新と時刻記録"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        direction = SceneDirection("medium", "徐々に上昇", "期待と不安")
        original_updated_at = scene.updated_at

        # When
        before_update = project_now().datetime
        scene.set_direction(direction)
        after_update = project_now().datetime

        # Then
        assert scene.direction == direction
        assert scene.updated_at > original_updated_at
        assert before_update <= scene.updated_at <= after_update

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_updated_at_changes_on_modifications(self) -> None:
        """TEST-13: 各種更新時のupdated_at変更確認"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        original_updated_at = scene.updated_at

        # When & Then: キャラクター追加
        scene.add_character("新キャラ")
        assert scene.updated_at > original_updated_at

        # When & Then: 重要要素追加
        updated_at_after_char = scene.updated_at
        scene.add_key_element("新要素")
        assert scene.updated_at > updated_at_after_char

        # When & Then: 執筆ノート設定
        updated_at_after_element = scene.updated_at
        scene.set_writing_note("メモ", "内容")
        assert scene.updated_at > updated_at_after_element

        # When & Then: 品質チェック追加
        updated_at_after_note = scene.updated_at
        scene.add_quality_check("カテゴリ", "チェック項目")
        assert scene.updated_at > updated_at_after_note

    # ===== 3. 要素管理テスト =====

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_add_character_normal_case(self) -> None:
        """TEST-14: 通常のキャラクター追加"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        character = "主人公"

        # When
        scene.add_character(character)

        # Then
        assert character in scene.characters
        assert len(scene.characters) == 1

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_add_character_duplicate_prevention(self) -> None:
        """TEST-15: 重複キャラクターの排除"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        character = "主人公"
        scene.add_character(character)

        # When
        scene.add_character(character)  # 同じキャラクターを再度追加

        # Then
        assert scene.characters.count(character) == 1
        assert len(scene.characters) == 1

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_add_character_empty_string_ignored(self) -> None:
        """TEST-16: 空文字列キャラクターの処理"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)

        # When: 空文字列は無視される
        scene.add_character("")

        # When: 空白文字のみは追加される(実装の動作)
        scene.add_character("   ")

        # When: Noneは型エラーになる(型ヒントでstr指定)
        # scene.add_character(None)  # 型エラーのためコメントアウト

        # Then: 空文字列は無視、空白は追加
        assert len(scene.characters) == 1
        assert "   " in scene.characters

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_add_key_element_normal_case(self) -> None:
        """TEST-17: 通常の重要要素追加"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        element = "魔法の剣"

        # When
        scene.add_key_element(element)

        # Then
        assert element in scene.key_elements
        assert len(scene.key_elements) == 1

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_add_key_element_duplicate_prevention(self) -> None:
        """TEST-18: 重複要素の排除"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        element = "魔法の剣"
        scene.add_key_element(element)

        # When
        scene.add_key_element(element)  # 同じ要素を再度追加

        # Then
        assert scene.key_elements.count(element) == 1
        assert len(scene.key_elements) == 1

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_add_key_element_empty_string_ignored(self) -> None:
        """TEST-19: 空文字列要素の処理"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)

        # When: 空文字列は無視される
        scene.add_key_element("")

        # When: 空白文字のみは追加される(実装の動作)
        scene.add_key_element("   ")

        # When: Noneは型エラーになる(型ヒントでstr指定)
        # scene.add_key_element(None)  # 型エラーのためコメントアウト

        # Then: 空文字列は無視、空白は追加
        assert len(scene.key_elements) == 1
        assert "   " in scene.key_elements

    # ===== 4. 執筆ノート管理テスト =====

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_set_writing_note_various_types(self) -> None:
        """TEST-20: 様々な型の値の設定"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)

        # When
        scene.set_writing_note("文字列", "テスト文字列")
        scene.set_writing_note("数値", 123)
        scene.set_writing_note("リスト", ["要素1", "要素2"])
        scene.set_writing_note("辞書", {"内部キー": "内部値"})
        scene.set_writing_note("真偽値", True)

        # Then
        assert scene.writing_notes["文字列"] == "テスト文字列"
        assert scene.writing_notes["数値"] == 123
        assert scene.writing_notes["リスト"] == ["要素1", "要素2"]
        assert scene.writing_notes["辞書"] == {"内部キー": "内部値"}
        assert scene.writing_notes["真偽値"] is True

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_set_writing_note_updates_time(self) -> None:
        """TEST-21: ノート設定時の時刻更新"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        original_updated_at = scene.updated_at

        # When
        scene.set_writing_note("テストキー", "テスト値")

        # Then
        assert scene.updated_at > original_updated_at

    # ===== 5. 品質チェック管理テスト =====

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_add_quality_check_new_category(self) -> None:
        """TEST-22: 新カテゴリでのチェック項目追加"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        category = "感情描写"
        check_item = "主人公の内面描写"

        # When
        scene.add_quality_check(category, check_item)

        # Then
        assert category in scene.quality_checklist
        assert check_item in scene.quality_checklist[category]
        assert len(scene.quality_checklist[category]) == 1

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_add_quality_check_existing_category(self) -> None:
        """TEST-23: 既存カテゴリへのチェック項目追加"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        category = "アクション描写"
        scene.add_quality_check(category, "戦闘シーンの迫力")

        # When
        scene.add_quality_check(category, "動きの具体性")

        # Then
        assert len(scene.quality_checklist[category]) == 2
        assert "戦闘シーンの迫力" in scene.quality_checklist[category]
        assert "動きの具体性" in scene.quality_checklist[category]

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_add_quality_check_duplicate_prevention(self) -> None:
        """TEST-24: 重複チェック項目の排除"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        category = "対話"
        check_item = "自然な会話"
        scene.add_quality_check(category, check_item)

        # When
        scene.add_quality_check(category, check_item)  # 同じ項目を再度追加

        # Then
        assert len(scene.quality_checklist[category]) == 1
        assert scene.quality_checklist[category].count(check_item) == 1

    # ===== 6. 完成度評価テスト =====

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_completion_score_minimum_fields(self) -> None:
        """TEST-25: 最小フィールドでのスコア(2/8 = 0.25)"""
        # Given: 必須フィールドのみ(title、episode_range)
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)

        # When
        score = scene.get_completion_score()

        # Then: title(1) + episode_range(1) = 2/8 = 0.25
        assert score == 0.25

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_completion_score_all_fields(self) -> None:
        """TEST-26: 全フィールドでのスコア(8/8 = 1.0)"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        scene.set_setting(SceneSetting("場所", "時間", "天気", "雰囲気"))
        scene.set_direction(SceneDirection("fast", "緊張", "感情"))
        scene.add_character("キャラクター")
        scene.add_key_element("重要要素")
        scene.set_writing_note("ノート", "内容")
        scene.add_quality_check("カテゴリ", "チェック項目")

        # When
        score = scene.get_completion_score()

        # Then: 8項目すべて存在するため 8/8 = 1.0
        assert score == 1.0

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_completion_score_partial_fields(self) -> None:
        """TEST-27: 部分フィールドでのスコア計算"""
        # Given: 5項目を満たすシーン
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        scene.set_setting(SceneSetting("場所", "時間", "天気", "雰囲気"))
        scene.add_character("キャラクター")
        scene.add_key_element("重要要素")
        # setting(1) + characters(1) + key_elements(1) + title(1) + episode_range(1) = 5

        # When
        score = scene.get_completion_score()

        # Then: 5/8 = 0.625
        assert score == 0.625

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_is_critical_s_level(self) -> None:
        """TEST-28: Sレベルでのクリティカル判定"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, ImportanceLevel.S, self.episode_range)

        # When & Then
        assert scene.is_critical() is True

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_is_critical_a_level(self) -> None:
        """TEST-29: Aレベルでのクリティカル判定"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, ImportanceLevel.A, self.episode_range)

        # When & Then
        assert scene.is_critical() is True

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_is_critical_b_c_levels(self) -> None:
        """TEST-30: B/Cレベルでの非クリティカル判定"""
        # Given
        scene_b = Scene(self.scene_id + "_B", self.title, self.category, ImportanceLevel.B, self.episode_range)
        scene_c = Scene(self.scene_id + "_C", self.title, self.category, ImportanceLevel.C, self.episode_range)

        # When & Then
        assert scene_b.is_critical() is False
        assert scene_c.is_critical() is False

    # ===== 7. データ変換テスト =====

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_to_dict_minimal_scene(self) -> None:
        """TEST-31: 最小シーンの辞書変換"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)

        # When
        data = scene.to_dict()

        # Then
        assert data["scene_id"] == self.scene_id
        assert data["title"] == self.title
        assert data["category"] == self.category.value
        assert data["importance_level"] == self.importance_level.value
        assert data["episode_range"] == self.episode_range
        assert "created_at" in data
        assert "updated_at" in data
        assert data["characters"] == []
        assert data["key_elements"] == []
        assert data["writing_notes"] == {}
        assert data["quality_checklist"] == {}
        # setting と direction は含まれない
        assert "setting" not in data
        assert "direction" not in data

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_to_dict_full_scene(self) -> None:
        """TEST-32: 完全シーンの辞書変換"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        setting = SceneSetting("学校", "朝", "曇り", "静か")
        direction = SceneDirection("slow", "平坦", "穏やか")
        scene.set_setting(setting)
        scene.set_direction(direction)
        scene.add_character("主人公")
        scene.add_key_element("重要アイテム")
        scene.set_writing_note("メモ", "内容")
        scene.add_quality_check("チェック", "項目")

        # When
        data = scene.to_dict()

        # Then
        assert "setting" in data
        assert "direction" in data
        assert data["characters"] == ["主人公"]
        assert data["key_elements"] == ["重要アイテム"]
        assert data["writing_notes"] == {"メモ": "内容"}
        assert data["quality_checklist"] == {"チェック": ["項目"]}

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_to_dict_includes_value_objects(self) -> None:
        """TEST-33: 値オブジェクトの変換確認"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        setting = SceneSetting("場所", "時間", "天気", "雰囲気")
        direction = SceneDirection("medium", "上昇", "緊張")
        scene.set_setting(setting)
        scene.set_direction(direction)

        # When
        data = scene.to_dict()

        # Then
        assert isinstance(data["setting"], dict)
        assert isinstance(data["direction"], dict)
        assert data["setting"]["location"] == "場所"
        assert data["direction"]["pacing"] == "medium"

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_from_dict_minimal_data(self) -> None:
        """TEST-34: 最小データからの復元"""
        # Given
        data = {
            "scene_id": self.scene_id,
            "title": self.title,
            "category": self.category.value,
            "importance_level": self.importance_level.value,
            "episode_range": self.episode_range,
            "created_at": "2025-01-22T10:00:00",
            "updated_at": "2025-01-22T11:00:00",
        }

        # When
        scene = Scene.from_dict(data)

        # Then
        assert scene.scene_id == self.scene_id
        assert scene.title == self.title
        assert scene.category == self.category
        assert scene.importance_level == self.importance_level
        assert scene.episode_range == self.episode_range
        assert scene.created_at == datetime(2025, 1, 22, 10, 0, 0, tzinfo=JST)
        assert scene.updated_at == datetime(2025, 1, 22, 11, 0, 0, tzinfo=JST)

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_from_dict_full_data(self) -> None:
        """TEST-35: 完全データからの復元"""
        # Given
        data = {
            "scene_id": self.scene_id,
            "title": self.title,
            "category": self.category.value,
            "importance_level": self.importance_level.value,
            "episode_range": self.episode_range,
            "created_at": "2025-01-22T10:00:00",
            "updated_at": "2025-01-22T11:00:00",
            "characters": ["主人公", "敵"],
            "key_elements": ["剣", "魔法"],
            "writing_notes": {"重要": "クライマックス"},
            "quality_checklist": {"アクション": ["迫力", "スピード"]},
            "setting": {"location": "戦場", "time": "夕方", "weather": "嵐", "atmosphere": "緊迫した"},
            "direction": {"pacing": "fast", "tension_curve": "急上昇", "emotional_flow": "怒りと決意"},
        }

        # When
        scene = Scene.from_dict(data)

        # Then
        assert scene.characters == ["主人公", "敵"]
        assert scene.key_elements == ["剣", "魔法"]
        assert scene.writing_notes == {"重要": "クライマックス"}
        assert scene.quality_checklist == {"アクション": ["迫力", "スピード"]}
        assert scene.setting is not None
        assert scene.setting.location == "戦場"
        assert scene.direction is not None
        assert scene.direction.pacing == "fast"

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_from_dict_with_value_objects(self) -> None:
        """TEST-36: 値オブジェクト付きデータの復元"""
        # Given
        data = {
            "scene_id": self.scene_id,
            "title": self.title,
            "category": self.category.value,
            "importance_level": self.importance_level.value,
            "episode_range": self.episode_range,
            "setting": {"location": "図書館", "time": "深夜", "weather": "雨", "atmosphere": "神秘的"},
            "direction": {"pacing": "slow", "tension_curve": "徐々に上昇", "emotional_flow": "不安から希望へ"},
        }

        # When
        scene = Scene.from_dict(data)

        # Then
        assert isinstance(scene.setting, SceneSetting)
        assert isinstance(scene.direction, SceneDirection)
        assert scene.setting.location == "図書館"
        assert scene.direction.emotional_flow == "不安から希望へ"

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_roundtrip_conversion(self) -> None:
        """TEST-37: to_dict → from_dict の往復変換確認"""
        # Given
        original_scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        original_scene.set_setting(SceneSetting("元の場所", "昼", "晴れ", "明るい"))
        original_scene.set_direction(SceneDirection("medium", "安定", "穏やか"))
        original_scene.add_character("テストキャラ")
        original_scene.add_key_element("テスト要素")
        original_scene.set_writing_note("テストノート", "テスト内容")
        original_scene.add_quality_check("テストカテゴリ", "テストチェック")

        # When
        data = original_scene.to_dict()
        restored_scene = Scene.from_dict(data)

        # Then
        assert restored_scene.scene_id == original_scene.scene_id
        assert restored_scene.title == original_scene.title
        assert restored_scene.category == original_scene.category
        assert restored_scene.importance_level == original_scene.importance_level
        assert restored_scene.episode_range == original_scene.episode_range
        assert restored_scene.characters == original_scene.characters
        assert restored_scene.key_elements == original_scene.key_elements
        assert restored_scene.writing_notes == original_scene.writing_notes
        assert restored_scene.quality_checklist == original_scene.quality_checklist
        assert restored_scene.setting.location == original_scene.setting.location
        assert restored_scene.direction.pacing == original_scene.direction.pacing

    # ===== 8. エッジケーステスト =====

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_unicode_fields(self) -> None:
        """TEST-38: Unicode文字のフィールド処理"""
        # Given
        unicode_scene_id = "シーン_001_🎭"
        unicode_title = "感動の再会 ✨"
        unicode_episode_range = "第１０話〜第１１話"

        # When
        scene = Scene(
            scene_id=unicode_scene_id,
            title=unicode_title,
            category=SceneCategory.EMOTIONAL,
            importance_level=ImportanceLevel.A,
            episode_range=unicode_episode_range,
        )

        scene.add_character("主人公🦸")
        scene.add_key_element("魔法の杖🪄")
        scene.set_writing_note("感情描写", "涙😭")

        # Then
        assert scene.scene_id == unicode_scene_id
        assert scene.title == unicode_title
        assert scene.episode_range == unicode_episode_range
        assert "主人公🦸" in scene.characters
        assert "魔法の杖🪄" in scene.key_elements
        assert scene.writing_notes["感情描写"] == "涙😭"

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_large_data_handling(self) -> None:
        """TEST-39: 大量データの処理"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)

        # When: 大量のキャラクターと要素を追加
        for i in range(100):
            scene.add_character(f"キャラクター{i:03d}")
            scene.add_key_element(f"要素{i:03d}")
            scene.set_writing_note(f"ノート{i:03d}", f"内容{i:03d}")
            scene.add_quality_check(f"カテゴリ{i:03d}", f"チェック{i:03d}")

        # Then
        assert len(scene.characters) == 100
        assert len(scene.key_elements) == 100
        assert len(scene.writing_notes) == 100
        assert len(scene.quality_checklist) == 100

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_special_characters_in_fields(self) -> None:
        """TEST-40: 特殊文字のフィールド処理"""
        # Given
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"

        # When
        scene = Scene(
            scene_id=f"scene_{special_chars}",
            title=f"タイトル_{special_chars}",
            category=SceneCategory.MYSTERY,
            importance_level=ImportanceLevel.B,
            episode_range=f"第1話_{special_chars}",
        )

        scene.add_character(f"キャラ_{special_chars}")
        scene.add_key_element(f"要素_{special_chars}")

        # Then
        assert special_chars in scene.scene_id
        assert special_chars in scene.title
        assert special_chars in scene.episode_range
        assert f"キャラ_{special_chars}" in scene.characters
        assert f"要素_{special_chars}" in scene.key_elements

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_timestamp_precision(self) -> None:
        """TEST-41: タイムスタンプ精度の確認"""
        # Given & When
        scene1 = Scene(self.scene_id + "_1", self.title, self.category, self.importance_level, self.episode_range)
        scene2 = Scene(self.scene_id + "_2", self.title, self.category, self.importance_level, self.episode_range)

        # Then: 作成時刻が異なることを確認
        # 注意:非常に高速に作成された場合は同じ時刻になる可能性もある
        assert scene1.created_at <= scene2.created_at

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_created_updated_time_difference(self) -> None:
        """TEST-42: 作成時刻と更新時刻の差異確認"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        original_created_at = scene.created_at
        original_updated_at = scene.updated_at

        # When: 変更を加える
        scene.add_character("新キャラ")

        # Then
        assert scene.created_at == original_created_at  # 作成時刻は変わらない
        assert scene.updated_at > original_updated_at  # 更新時刻は変わる

    # ===== 9. 統合テスト =====

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_integration_with_scene_setting(self) -> None:
        """TEST-43: SceneSetting統合動作"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        setting = SceneSetting("統合テスト場所", "統合テスト時間", "統合テスト天気", "統合テスト雰囲気")

        # When
        scene.set_setting(setting)

        # Then: 値オブジェクトのメソッドが正常に動作
        description = scene.setting.get_description()
        assert "統合テスト場所" in description
        assert "統合テスト雰囲気" in description

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_integration_with_scene_direction(self) -> None:
        """TEST-44: SceneDirection統合動作"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        direction = SceneDirection(
            "fast", "統合テスト緊張カーブ", "統合テスト感情フロー", special_effects=["エフェクト1", "エフェクト2"]
        )

        # When
        scene.set_direction(direction)

        # Then: 値オブジェクトのメソッドが正常に動作
        summary = scene.direction.get_summary()
        assert "fast" in summary
        assert "統合テスト緊張カーブ" in summary
        assert "エフェクト1" in summary

    @pytest.mark.spec("SPEC-SCENE-001")
    def test_multiple_modifications_timeline(self) -> None:
        """TEST-45: 複数変更操作のタイムライン確認"""
        # Given
        scene = Scene(self.scene_id, self.title, self.category, self.importance_level, self.episode_range)
        timestamps = []

        # When: 連続的な変更を記録
        timestamps.append(scene.updated_at)

        scene.add_character("キャラ1")
        timestamps.append(scene.updated_at)

        scene.add_key_element("要素1")
        timestamps.append(scene.updated_at)

        scene.set_writing_note("ノート1", "内容1")
        timestamps.append(scene.updated_at)

        scene.add_quality_check("品質1", "チェック1")
        timestamps.append(scene.updated_at)

        # Then: タイムスタンプが単調増加
        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i - 1]
