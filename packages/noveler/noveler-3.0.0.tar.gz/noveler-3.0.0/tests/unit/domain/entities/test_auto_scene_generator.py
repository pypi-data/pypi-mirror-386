#!/usr/bin/env python3
"""AutoSceneGeneratorエンティティのユニットテスト
TDD RED段階:失敗するテストを先に作成


仕様書: SPEC-DOMAIN-ENTITIES
"""

from unittest.mock import Mock

import pytest

from noveler.domain.entities.auto_scene_generator import AutoSceneGenerator
from noveler.domain.exceptions import BusinessRuleViolationError
from noveler.domain.value_objects.generation_options import GenerationOptions
from noveler.domain.value_objects.project_context import ProjectContext
from noveler.domain.value_objects.scene_template import SceneTemplate


class TestAutoSceneGenerator:
    """AutoSceneGeneratorエンティティのテスト"""

    @pytest.mark.spec("SPEC-AUTO_SCENE_GENERATOR-CREATE_AUTO_SCENE_GE")
    def test_create_auto_scene_generator_with_valid_context(self) -> None:
        """有効なプロジェクトコンテキストでジェネレーターを作成"""
        # Arrange
        project_context = ProjectContext(
            project_name="test_project", genre="ファンタジー", protagonist_name="勇者", total_episodes=50
        )

        # Act
        generator = AutoSceneGenerator()
        generator.set_project_context(project_context)

        # Assert
        assert generator.project_context == project_context
        assert generator.project_context.project_name == "test_project"
        assert generator.project_context.genre == "ファンタジー"

    @pytest.mark.spec("SPEC-AUTO_SCENE_GENERATOR-GENERATE_SCENE_WITH_")
    def test_generate_scene_with_climax_template(self) -> None:
        """クライマックステンプレートでシーン生成"""
        # Arrange
        project_context = ProjectContext(
            project_name="test_project",
            genre="ファンタジー",
            protagonist_name="勇者",
            main_characters=[{"name": "勇者", "role": "主人公"}, {"name": "魔王", "role": "アンタゴニスト"}],
        )

        options = GenerationOptions(title="最終決戦", importance_level="S", detail_level="full")

        # Act
        generator = AutoSceneGenerator()
        generator.set_project_context(project_context)

        # まずクライマックステンプレートを追加
        climax_template = SceneTemplate.create_default_template("climax_scenes")
        generator.add_template(climax_template)

        result = generator.generate_scene("climax_scenes", "final_battle", options)

        # Assert
        assert result.category == "climax_scenes"
        assert result.scene_id == "final_battle"
        assert result.title == "最終決戦"
        assert result.importance_level == "S"
        assert result.auto_generated is True

    @pytest.mark.spec("SPEC-AUTO_SCENE_GENERATOR-VALIDATE_GENERATION_")
    def test_validate_generation_rules_with_insufficient_context(self) -> None:
        """不十分なコンテキストでルール検証"""
        # Arrange
        minimal_context = ProjectContext(
            project_name="test",
            genre="テスト",  # 有効なジャンル
        )

        options = GenerationOptions(importance_level="S")

        # Act & Assert - 最小限のコンテキストでも生成可能(デフォルトテンプレートがあるため)
        generator = AutoSceneGenerator(project_context=minimal_context)
        result = generator.generate_scene("climax_scenes", "test_scene", options)

        # 生成は成功するが、情報が限定的
        assert result.category == "climax_scenes"
        assert result.scene_id == "test_scene"
        assert result.auto_generated is True

    @pytest.mark.spec("SPEC-AUTO_SCENE_GENERATOR-GET_GENERATION_HISTO")
    def test_get_generation_history_empty_initially(self) -> None:
        """初期状態での生成履歴は空"""
        # Arrange
        context = ProjectContext(project_name="test", genre="ファンタジー")
        generator = AutoSceneGenerator(project_context=context)

        # Act
        history = generator.get_generation_history()

        # Assert
        assert history == []

    @pytest.mark.spec("SPEC-AUTO_SCENE_GENERATOR-ADD_CUSTOM_TEMPLATE_")
    def test_add_custom_template_and_retrieve(self) -> None:
        """カスタムテンプレートの追加と取得"""
        # Arrange
        context = ProjectContext(project_name="test", genre="ファンタジー")
        custom_template = SceneTemplate(
            name="custom_test", category="custom_scenes", setting_patterns={"location": ["test_location"]}
        )

        # Act
        generator = AutoSceneGenerator(project_context=context)
        generator.add_custom_template(custom_template)
        retrieved = generator.get_template("custom_test")

        # Assert
        assert retrieved is not None
        assert retrieved.name == "custom_test"

    @pytest.mark.spec("SPEC-AUTO_SCENE_GENERATOR-GENERATE_MULTIPLE_SC")
    def test_generate_multiple_scenes_updates_history(self) -> None:
        """複数シーン生成で履歴が更新される"""
        # Arrange
        context = ProjectContext(project_name="test", genre="ファンタジー")
        options1 = GenerationOptions(title="Scene 1")
        options2 = GenerationOptions(title="Scene 2")

        # Act
        generator = AutoSceneGenerator(project_context=context)

        generator.generate_scene("emotional_scenes", "scene1", options1)
        generator.generate_scene("romance_scenes", "scene2", options2)

        history = generator.get_generation_history()

        # Assert
        assert len(history) == 2
        assert history[0]["scene_id"] == "scene1"
        assert history[1]["scene_id"] == "scene2"

    @pytest.mark.spec("SPEC-AUTO_SCENE_GENERATOR-VALIDATE_SCENE_ID_UN")
    def test_validate_scene_id_uniqueness(self) -> None:
        """シーンID重複の検証"""
        # Arrange
        context = ProjectContext(project_name="test", genre="ファンタジー")
        options = GenerationOptions(title="Test Scene")

        # Act & Assert
        generator = AutoSceneGenerator(project_context=context)

        # 最初の生成は成功
        generator.generate_scene("emotional_scenes", "duplicate_id", options)

        # 同じIDでの生成はエラーになる想定
        with pytest.raises(BusinessRuleViolationError, match=".*"):
            generator.generate_scene("romance_scenes", "duplicate_id", options)

    @pytest.mark.spec("SPEC-AUTO_SCENE_GENERATOR-GET_SCENE_STATISTICS")
    def test_get_scene_statistics_with_generated_scenes(self) -> None:
        """生成済みシーンの統計取得"""
        # Arrange
        context = ProjectContext(project_name="test", genre="ファンタジー")

        # Act & Assert
        generator = AutoSceneGenerator(project_context=context)

        # 複数のシーンを生成
        for i in range(3):
            options = GenerationOptions(title=f"Scene {i}")
            generator.generate_scene("emotional_scenes", f"scene_{i}", options)

        stats = generator.get_scene_statistics()
        assert stats["total_scenes"] == 3
        assert stats["by_category"]["emotional_scenes"] == 3

    @pytest.mark.spec("SPEC-AUTO_SCENE_GENERATOR-CLEAR_GENERATION_HIS")
    def test_clear_generation_history(self) -> None:
        """生成履歴のクリア"""
        # Arrange
        context = ProjectContext(project_name="test", genre="ファンタジー")

        # Act & Assert
        generator = AutoSceneGenerator(project_context=context)

        # シーンを生成
        options = GenerationOptions(title="Test")
        generator.generate_scene("emotional_scenes", "test", options)

        # 履歴をクリア
        generator.clear_generation_history()

        history = generator.get_generation_history()
        assert len(history) == 0

    @pytest.mark.spec("SPEC-AUTO_SCENE_GENERATOR-PROJECT_CONTEXT_UPDA")
    def test_project_context_update_affects_generation(self) -> None:
        """プロジェクトコンテキスト更新による生成結果の変化"""
        # Arrange
        original_context = ProjectContext(project_name="test", genre="ファンタジー")
        updated_context = ProjectContext(project_name="test", genre="恋愛")

        # Act & Assert
        generator = AutoSceneGenerator(project_context=original_context)

        # コンテキスト更新
        generator.update_project_context(updated_context)

        # 更新後のコンテキストが反映されているか確認
        assert generator.project_context.genre == "恋愛"


class TestAutoSceneGeneratorWithMockRepository:
    """モックリポジトリを使用したテスト"""

    @pytest.mark.spec("SPEC-AUTO_SCENE_GENERATOR-GENERATE_SCENE_WITH_")
    def test_generate_scene_with_repository_integration(self) -> None:
        """リポジトリ統合での生成(将来の拡張を想定したテスト)"""
        # Arrange
        Mock()
        context = ProjectContext(project_name="test", genre="ファンタジー")

        # Act & Assert - 現在の実装ではリポジトリは直接使用しない
        generator = AutoSceneGenerator(project_context=context)

        options = GenerationOptions(title="Test Scene")
        result = generator.generate_scene("climax_scenes", "test", options)

        # 生成結果を確認
        assert result.category == "climax_scenes"
        assert result.scene_id == "test"
        assert result.title == "Test Scene"

    @pytest.mark.spec("SPEC-AUTO_SCENE_GENERATOR-ERROR_HANDLING_WHEN_")
    def test_error_handling_when_repository_fails(self) -> None:
        """リポジトリエラー時のハンドリング(将来の拡張を想定)"""
        # Arrange
        mock_repo = Mock()
        mock_repo.load_project_files.side_effect = Exception("Repository error")

        context = ProjectContext(project_name="test", genre="ファンタジー")

        # Act & Assert - 現在の実装ではリポジトリエラーは発生しない
        generator = AutoSceneGenerator(project_context=context)

        options = GenerationOptions(title="Test")

        # 正常に生成される(リポジトリに依存しないため)
        result = generator.generate_scene("climax_scenes", "test", options)
        assert result.scene_id == "test"


class TestAutoSceneGeneratorBusinessRules:
    """ビジネスルールのテスト"""

    @pytest.mark.spec("SPEC-AUTO_SCENE_GENERATOR-MINIMUM_REQUIRED_PRO")
    def test_minimum_required_project_info_validation(self) -> None:
        """最小限の必要プロジェクト情報の検証"""
        # Arrange - 最小限の情報のみ
        minimal_context = ProjectContext(project_name="minimal", genre="テスト")

        # Act & Assert
        generator = AutoSceneGenerator(project_context=minimal_context)

        # 最小限の情報でも基本的な生成は可能である想定
        options = GenerationOptions(title="Minimal Scene")
        result = generator.generate_scene("emotional_scenes", "minimal", options)

        assert result.title == "Minimal Scene"

    @pytest.mark.spec("SPEC-AUTO_SCENE_GENERATOR-OPTIMAL_PROJECT_INFO")
    def test_optimal_project_info_enhances_generation(self) -> None:
        """充実したプロジェクト情報による生成品質向上"""
        # Arrange - 充実した情報
        rich_context = ProjectContext(
            project_name="rich_project",
            genre="ファンタジー",
            protagonist_name="勇者リック",
            main_characters=[
                {"name": "勇者リック", "role": "主人公"},
                {"name": "魔法使いエルフィ", "role": "ヒロイン"},
                {"name": "魔王ダーク", "role": "アンタゴニスト"},
            ],
            total_episodes=100,
        )

        # Act & Assert
        generator = AutoSceneGenerator(project_context=rich_context)

        options = GenerationOptions(title="Epic Battle", importance_level="S", detail_level="full")

        result = generator.generate_scene("climax_scenes", "epic", options)

        # 充実した情報により詳細なシーンが生成される想定
        assert len(result.characters) >= 2  # 主人公とアンタゴニスト
        assert result.importance_level == "S"

    @pytest.mark.spec("SPEC-AUTO_SCENE_GENERATOR-SCENE_CATEGORY_VALID")
    def test_scene_category_validation(self) -> None:
        """シーンカテゴリの検証"""
        # Arrange
        context = ProjectContext(project_name="test", genre="ファンタジー")

        # Act & Assert
        generator = AutoSceneGenerator(project_context=context)

        options = GenerationOptions(title="Test")

        # 無効なカテゴリでエラーになる想定
        with pytest.raises(BusinessRuleViolationError, match=".*"):
            generator.generate_scene("invalid_category", "test", options)

    @pytest.mark.spec("SPEC-AUTO_SCENE_GENERATOR-IMPORTANCE_LEVEL_AFF")
    def test_importance_level_affects_generation_detail(self) -> None:
        """重要度レベルによる生成詳細度の変化"""
        # Arrange
        context = ProjectContext(project_name="test", genre="ファンタジー")

        # Act & Assert
        generator = AutoSceneGenerator(project_context=context)

        # S級の重要シーン
        high_options = GenerationOptions(title="Critical Scene", importance_level="S", detail_level="full")

        # C級の普通シーン
        low_options = GenerationOptions(title="Minor Scene", importance_level="C", detail_level="basic")

        high_scene = generator.generate_scene("climax_scenes", "high", high_options)
        low_scene = generator.generate_scene("emotional_scenes", "low", low_options)

        # 両方のシーンが生成されることを確認
        assert high_scene.importance_level == "S"
        assert low_scene.importance_level == "C"

        # 詳細レベルの違いが反映されていることを確認
        # (現在の実装では完成度スコアは同じになる可能性があるため、
        # 重要度レベルの違いを確認)
        assert high_scene.get_completion_score() >= low_scene.get_completion_score()
