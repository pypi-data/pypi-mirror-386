#!/usr/bin/env python3
"""GeneratedSceneの値オブジェクトテスト
TDD RED段階:生成されたシーンデータの検証とビジネスルール


仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

from datetime import datetime

import pytest

from noveler.domain.value_objects.generated_scene import GeneratedScene

pytestmark = pytest.mark.vo_smoke



class TestGeneratedSceneCreation:
    """GeneratedScene作成時のテスト"""

    def test_create_with_minimal_required_fields(self) -> None:
        """最小限必須フィールドでの作成"""
        # Act
        scene = GeneratedScene(category="emotional_scenes", scene_id="test_scene", title="テストシーン")

        # Assert
        assert scene.category == "emotional_scenes"
        assert scene.scene_id == "test_scene"
        assert scene.title == "テストシーン"
        assert scene.importance_level == "A"  # デフォルト値
        assert scene.auto_generated is True

    def test_create_with_all_fields(self) -> None:
        """全フィールド指定での作成"""
        # Arrange
        setting = {"location": "魔王城", "time": "夜", "atmosphere": "緊迫"}
        direction = {"pacing": "急速", "tension_curve": "上昇"}
        characters = ["勇者", "魔王"]
        key_elements = ["最終決戦", "友情の証明"]
        writing_notes = {"must_include": ["仲間との絆"], "avoid": ["都合の良い展開"]}

        # Act
        scene = GeneratedScene(
            category="climax_scenes",
            scene_id="final_battle",
            title="最終決戦",
            importance_level="S",
            episode_range="第48-50話",
            setting=setting,
            direction=direction,
            characters=characters,
            key_elements=key_elements,
            writing_notes=writing_notes,
        )

        # Assert
        assert scene.importance_level == "S"
        assert scene.episode_range == "第48-50話"
        assert len(scene.characters) == 2
        assert len(scene.key_elements) == 2
        assert "must_include" in scene.writing_notes

    def test_validation_empty_category_raises_error(self) -> None:
        """空のカテゴリでエラー"""
        # Act & Assert
        with pytest.raises(ValueError, match="カテゴリは必須です"):
            GeneratedScene(category="", scene_id="test", title="テスト")

    def test_validation_empty_scene_id_raises_error(self) -> None:
        """空のシーンIDでエラー"""
        # Act & Assert
        with pytest.raises(ValueError, match="シーンIDは必須です"):
            GeneratedScene(category="test", scene_id="", title="テスト")

    def test_validation_empty_title_raises_error(self) -> None:
        """空のタイトルでエラー"""
        # Act & Assert
        with pytest.raises(ValueError, match="タイトルは必須です"):
            GeneratedScene(category="test", scene_id="test", title="")

    def test_validation_invalid_importance_level_raises_error(self) -> None:
        """無効な重要度レベルでエラー"""
        # Act & Assert
        with pytest.raises(ValueError, match="重要度レベルは"):
            GeneratedScene(
                category="test",
                scene_id="test",
                title="テスト",
                importance_level="X",  # 無効なレベル
            )


class TestGeneratedSceneCompletion:
    """GeneratedSceneの完成度関連テスト"""

    def test_get_completion_score_minimal_scene(self) -> None:
        """最小限シーンの完成度スコア"""
        # Arrange
        scene = GeneratedScene(category="test", scene_id="minimal", title="最小限シーン")

        # Act
        score = scene.get_completion_score()

        # Assert
        assert score == 0.15  # タイトルのみ(15%)

    def test_get_completion_score_complete_scene(self) -> None:
        """完成シーンの完成度スコア"""
        # Arrange
        scene = GeneratedScene(
            category="climax_scenes",
            scene_id="complete",
            title="完成シーン",
            setting={"location": "魔王城", "time": "夜", "weather": "嵐", "atmosphere": "緊迫"},
            direction={"pacing": "急速", "tension_curve": "上昇", "emotional_flow": "緊張→爆発"},
            characters=["勇者", "魔王"],
            key_elements=["最終決戦", "成長の証明"],
            writing_notes={"must_include": ["仲間との絆"], "avoid": ["都合の良い展開"]},
        )

        # Act
        score = scene.get_completion_score()

        # Assert
        assert score >= 0.95  # ほぼ完成(95%以上)

    def test_is_complete_with_high_score(self) -> None:
        """高スコアシーンの完成判定"""
        # Arrange
        scene = GeneratedScene(
            category="test",
            scene_id="high_score",
            title="高スコアシーン",
            setting={"location": "場所", "time": "時間", "weather": "天候", "atmosphere": "雰囲気"},
            direction={"pacing": "ペース", "tension_curve": "緊張", "emotional_flow": "感情"},
            characters=["キャラクター"],
            key_elements=["要素"],
            writing_notes={"must_include": ["必須"], "avoid": ["回避"]},
        )

        # Act & Assert
        assert scene.is_complete() is True

    def test_is_complete_with_low_score(self) -> None:
        """低スコアシーンの完成判定"""
        # Arrange
        scene = GeneratedScene(category="test", scene_id="low_score", title="低スコアシーン")

        # Act & Assert
        assert scene.is_complete() is False

    def test_get_missing_elements_minimal_scene(self) -> None:
        """最小限シーンの不足要素"""
        # Arrange
        scene = GeneratedScene(category="test", scene_id="minimal", title="最小限")

        # Act
        missing = scene.get_missing_elements()

        # Assert
        assert len(missing) > 0
        assert any("シーン設定" in element for element in missing)
        assert any("登場キャラクター" in element for element in missing)

    def test_get_missing_elements_partial_scene(self) -> None:
        """部分的完成シーンの不足要素"""
        # Arrange
        scene = GeneratedScene(
            category="test",
            scene_id="partial",
            title="部分的完成",
            setting={"location": "場所"},  # 部分的な設定
            characters=["キャラクター"],
        )

        # Act
        missing = scene.get_missing_elements()

        # Assert
        assert len(missing) >= 2  # 演出指示、重要要素、執筆ノートが不足
        assert any("演出指示" in element for element in missing)


class TestGeneratedSceneSerialization:
    """GeneratedSceneのシリアライゼーション"""

    def test_to_yaml_dict_basic_conversion(self) -> None:
        """基本的なYAML辞書変換"""
        # Arrange
        scene = GeneratedScene(category="test", scene_id="yaml_test", title="YAMLテスト", importance_level="A")

        # Act
        yaml_dict = scene.to_yaml_dict()

        # Assert
        assert yaml_dict["title"] == "YAMLテスト"
        assert yaml_dict["importance_level"] == "A"
        assert yaml_dict["completion_score"] == 0.0  # 初期状態
        assert yaml_dict["is_critical"] is False  # A級はcriticalではない
        assert "created_at" in yaml_dict
        assert "updated_at" in yaml_dict

    def test_to_yaml_dict_with_all_data(self) -> None:
        """全データを含むYAML変換"""
        # Arrange
        scene = GeneratedScene(
            category="climax_scenes",
            scene_id="full_data",
            title="フルデータテスト",
            importance_level="S",
            setting={"location": "場所"},
            direction={"pacing": "ペース"},
            characters=["キャラ1"],
            key_elements=["要素1"],
            writing_notes={"must_include": ["必須要素"]},
        )

        # Act
        yaml_dict = scene.to_yaml_dict()

        # Assert
        assert yaml_dict["is_critical"] is True  # S級はcritical
        assert "setting" in yaml_dict
        assert "direction" in yaml_dict
        assert "characters" in yaml_dict
        assert "key_elements" in yaml_dict
        assert "writing_notes" in yaml_dict
        assert yaml_dict["auto_generated"] is True

    def test_enhance_with_manual_edits_no_edits(self) -> None:
        """手動編集なしでの拡張"""
        # Arrange
        scene = GeneratedScene(category="test", scene_id="edit_test", title="編集テスト")

        # Act
        enhanced = scene.enhance_with_manual_edits({})

        # Assert
        assert "_editing_guide" in enhanced
        assert "recommendations" in enhanced["_editing_guide"]
        assert "completion_score" in enhanced["_editing_guide"]
        assert "missing_elements" in enhanced["_editing_guide"]
        assert enhanced["auto_generated"] is True

    def test_enhance_with_manual_edits_with_edits(self) -> None:
        """手動編集ありでの拡張"""
        # Arrange
        scene = GeneratedScene(category="test", scene_id="edit_test", title="編集テスト")

        edits = {"title": "手動編集後タイトル", "setting": {"location": "手動設定場所"}}

        # Act
        enhanced = scene.enhance_with_manual_edits(edits)

        # Assert
        assert enhanced["title"] == "手動編集後タイトル"
        assert enhanced["setting"]["location"] == "手動設定場所"
        assert enhanced["auto_generated"] is False
        assert enhanced["manually_edited"] is True
        assert "updated_at" in enhanced


class TestGeneratedSceneBusinessRules:
    """GeneratedSceneのビジネスルール"""

    def test_importance_s_is_critical(self) -> None:
        """重要度Sがクリティカル判定"""
        # Arrange
        scene = GeneratedScene(category="test", scene_id="critical", title="クリティカル", importance_level="S")

        # Act
        yaml_dict = scene.to_yaml_dict()

        # Assert
        assert yaml_dict["is_critical"] is True

    def test_importance_abc_not_critical(self) -> None:
        """重要度A,B,Cがクリティカルでない"""
        for level in ["A", "B", "C"]:
            # Arrange
            scene = GeneratedScene(
                category="test",
                scene_id=f"not_critical_{level}",
                title=f"非クリティカル{level}",
                importance_level=level,
            )

            # Act
            yaml_dict = scene.to_yaml_dict()

            # Assert
            assert yaml_dict["is_critical"] is False

    def test_created_at_and_updated_at_defaults(self) -> None:
        """作成日時と更新日時のデフォルト値"""
        # Act
        scene = GeneratedScene(category="test", scene_id="time_test", title="時間テスト")

        # Assert
        assert isinstance(scene.created_at, datetime)
        assert isinstance(scene.updated_at, datetime)
        assert scene.created_at <= scene.updated_at

    def test_auto_generated_default_true(self) -> None:
        """自動生成フラグのデフォルト値"""
        # Act
        scene = GeneratedScene(category="test", scene_id="auto_test", title="自動生成テスト")

        # Assert
        assert scene.auto_generated is True

    def test_generation_source_tracking(self) -> None:
        """生成ソースの追跡"""
        # Arrange
        sources = ["project_settings", "character_info", "template"]

        # Act
        scene = GeneratedScene(category="test", scene_id="source_test", title="ソーステスト", generation_source=sources)

        # Assert
        assert scene.generation_source == sources

        yaml_dict = scene.to_yaml_dict()
        assert yaml_dict["generation_source"] == sources
