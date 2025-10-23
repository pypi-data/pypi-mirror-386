"""プロット検証サービスのテスト

DDD準拠テスト:
- ビジネスロジックのテスト
- スキーマ検証の動作確認
- 検証ルールのテスト


仕様書: SPEC-DOMAIN-SERVICES
"""

import pytest

from noveler.domain.services.plot_validation_service import PlotValidationService
from noveler.domain.value_objects.plot_schema import (
    CHAPTER_PLOT_SCHEMA,
    MASTER_PLOT_SCHEMA,
)
from noveler.domain.value_objects.validation_result import ValidationLevel
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType


class TestPlotValidationService:
    """PlotValidationServiceのテスト"""

    @pytest.fixture
    def service(self):
        """テスト用サービスインスタンス"""
        return PlotValidationService()

    @pytest.mark.spec("SPEC-PLOT_VALIDATION_SERVICE-VALIDATE_MASTER_PLOT")
    def test_validate_master_plot_with_valid_data(self, service: object) -> None:
        """有効な全体構成データの検証"""
        # Given
        valid_data = {
            "title": "テスト小説",
            "genre": "ファンタジー",
            "target_readers": {
                "age": "10-20代",
                "gender": "男女問わず",
            },
            "story_concept": {
                "theme": "成長と冒険",
                "logline": "普通の高校生が異世界で英雄になる",
            },
            "chapters": [
                {"number": 1, "title": "ch01", "summary": "始まり"},
                {"number": 2, "title": "ch02", "summary": "冒険"},
            ],
        }

        # When
        result = service.validate_plot_file(WorkflowStageType.MASTER_PLOT, valid_data)

        # Then
        assert result.is_valid
        assert all(issue.level != ValidationLevel.ERROR for issue in result.issues)

    @pytest.mark.spec("SPEC-PLOT_VALIDATION_SERVICE-VALIDATE_MASTER_PLOT")
    def test_validate_master_plot_with_missing_required_fields(self, service: object) -> None:
        """必須フィールドが不足している全体構成データの検証"""
        # Given
        invalid_data = {
            "title": "テスト小説",
            # genreが不足
            "target_readers": {
                "age": "10-20代",
            },
            # story_conceptが不足
            "chapters": [],  # 空のchapters
        }

        # When
        result = service.validate_plot_file(WorkflowStageType.MASTER_PLOT, invalid_data)

        # Then
        assert not result.is_valid
        assert any(issue.level == ValidationLevel.ERROR for issue in result.issues)

        # エラーメッセージの確認
        error_messages = [issue.message for issue in result.issues if issue.level == ValidationLevel.ERROR]
        assert any("genre" in msg or "必須フィールド" in msg for msg in error_messages)

    @pytest.mark.spec("SPEC-PLOT_VALIDATION_SERVICE-VALIDATE_CHAPTER_PLO")
    def test_validate_chapter_plot_with_valid_data(self, service: object) -> None:
        """有効な章別プロットデータの検証"""
        # Given
        valid_data = {
            "chapter_number": 1,
            "title": "ch01:始まりの章",
            "summary": "主人公が異世界に転生する",
            "key_events": [
                "転生イベント",
                "能力覚醒",
                "仲間との出会い",
            ],
            "episodes": [
                {"number": 1, "title": "転生"},
                {"number": 2, "title": "覚醒"},
            ],
        }

        # When
        result = service.validate_plot_file(WorkflowStageType.CHAPTER_PLOT, valid_data)

        # Then
        assert result.is_valid
        assert all(issue.level != ValidationLevel.ERROR for issue in result.issues)

    @pytest.mark.spec("SPEC-PLOT_VALIDATION_SERVICE-VALIDATE_EPISODE_PLO")
    def test_validate_episode_plot_with_valid_data(self, service: object) -> None:
        """有効な話数別プロットデータの検証"""
        # Given
        valid_data = {
            "episode_number": 1,
            "title": "転生!異世界での新たな始まり",
            "summary": "トラックに轢かれた主人公が異世界で目覚める",
            "scenes": [
                {
                    "scene_number": 1,
                    "description": "事故シーン",
                },
                {
                    "scene_number": 2,
                    "description": "異世界で目覚める",
                },
            ],
        }

        # When
        result = service.validate_plot_file(WorkflowStageType.EPISODE_PLOT, valid_data)

        # Then
        assert result.is_valid
        assert all(issue.level != ValidationLevel.ERROR for issue in result.issues)

    @pytest.mark.spec("SPEC-PLOT_VALIDATION_SERVICE-VALIDATE_WITH_WRONG_")
    def test_validate_with_wrong_field_type(self, service: object) -> None:
        """フィールドの型が間違っている場合の検証"""
        # Given
        invalid_data = {
            "title": "テスト小説",
            "genre": "ファンタジー",
            "target_readers": "文字列",  # dictであるべき
            "story_concept": {
                "theme": "成長",
            },
            "chapters": "文字列",  # listであるべき
        }

        # When
        result = service.validate_plot_file(WorkflowStageType.MASTER_PLOT, invalid_data)

        # Then
        assert not result.is_valid
        assert any(issue.level == ValidationLevel.ERROR for issue in result.issues)

        # 型エラーの確認
        type_errors = [
            issue
            for issue in result.issues
            if issue.level == ValidationLevel.ERROR and ("型" in issue.message or "type" in issue.message.lower())
        ]
        assert len(type_errors) >= 2

    @pytest.mark.spec("SPEC-PLOT_VALIDATION_SERVICE-VALIDATE_YAML_SYNTAX")
    def test_validate_yaml_syntax(self, service: object) -> None:
        """YAML構文の検証"""
        # Given
        yaml_content = """
title: テスト小説
genre: ファンタジー
target_readers:
  age: 10-20代
  gender: 男女問わず
story_concept:
  theme: 成長と冒険
  logline: 普通の高校生が異世界で英雄になる
chapters:
  - number: 1
    title: ch01
    summary: 始まり
"""

        # When
        result = service.validate_yaml_syntax(yaml_content)

        # Then
        assert result.is_valid
        assert all(issue.level != ValidationLevel.ERROR for issue in result.issues)

    @pytest.mark.spec("SPEC-PLOT_VALIDATION_SERVICE-VALIDATE_INVALID_YAM")
    def test_validate_invalid_yaml_syntax(self, service: object) -> None:
        """無効なYAML構文の検証"""
        # Given
        invalid_yaml = """
title: テスト小説
genre: [ファンタジー
  invalid: syntax
"""

        # When
        result = service.validate_yaml_syntax(invalid_yaml)

        # Then
        assert not result.is_valid
        assert any(issue.level == ValidationLevel.ERROR for issue in result.issues)
        assert any("YAML" in issue.message for issue in result.issues if issue.level == ValidationLevel.ERROR)

    @pytest.mark.spec("SPEC-PLOT_VALIDATION_SERVICE-VALIDATE_WITH_WARNIN")
    def test_validate_with_warnings(self, service: object) -> None:
        """推奨フィールドが不足している場合の警告"""
        # Given
        data_without_optional = {
            "title": "テスト小説",
            "genre": "ファンタジー",
            "target_readers": {"age": "10-20代"},
            "story_concept": {"theme": "成長"},
            "chapters": [{"number": 1, "title": "ch01"}],
            # themes, world_buildingが不足(オプション)
        }

        # When
        result = service.validate_plot_file(WorkflowStageType.MASTER_PLOT, data_without_optional)

        # Then
        assert result.is_valid  # オプションフィールドの不足では無効にならない

        # 警告メッセージの確認
        warnings = [issue for issue in result.issues if issue.level == ValidationLevel.WARNING]
        assert len(warnings) > 0

    @pytest.mark.spec("SPEC-PLOT_VALIDATION_SERVICE-VALIDATE_EMPTY_REQUI")
    def test_validate_empty_required_fields(self, service: object) -> None:
        """必須フィールドが空の場合の検証"""
        # Given
        data_with_empty = {
            "title": "",  # 空文字列
            "genre": "ファンタジー",
            "target_readers": {},  # 空の辞書
            "story_concept": {"theme": "成長"},
            "chapters": [],  # 空のリスト
        }

        # When
        result = service.validate_plot_file(WorkflowStageType.MASTER_PLOT, data_with_empty)

        # Then
        assert not result.is_valid
        assert any(issue.level == ValidationLevel.ERROR for issue in result.issues)

        # 空フィールドのエラー確認
        empty_errors = [
            issue
            for issue in result.issues
            if issue.level == ValidationLevel.ERROR and ("空" in issue.message or "empty" in issue.message.lower())
        ]
        assert len(empty_errors) >= 1  # titleが空

    @pytest.mark.spec("SPEC-PLOT_VALIDATION_SERVICE-GET_SCHEMA_FOR_STAGE")
    def test_get_schema_for_stage(self, service: object) -> None:
        """ステージタイプに応じたスキーマ取得"""
        # When/Then
        assert service.get_schema_for_stage(WorkflowStageType.MASTER_PLOT) == MASTER_PLOT_SCHEMA
        assert service.get_schema_for_stage(WorkflowStageType.CHAPTER_PLOT) == CHAPTER_PLOT_SCHEMA
        assert service.get_schema_for_stage(WorkflowStageType.EPISODE_PLOT) is not None

    @pytest.mark.spec("SPEC-PLOT_VALIDATION_SERVICE-VALIDATE_PROJECT_SPE")
    def test_validate_project_specific_fields(self, service: object) -> None:
        """プロジェクト固有情報の検証"""
        # Given
        plot_data = {
            "title": "${project_title}が残っている",  # テンプレート変数が残っている
            "genre": "ファンタジー",
            "target_readers": {"age": "10-20代"},
            "story_concept": {"theme": "成長"},
            "chapters": [{"number": 1, "title": "ch01"}],
        }

        # When
        result = service.validate_plot_file(WorkflowStageType.MASTER_PLOT, plot_data)

        # Then
        # テンプレート変数の残存は警告
        template_warnings = [
            issue
            for issue in result.issues
            if issue.level == ValidationLevel.WARNING and ("${" in issue.message or "テンプレート" in issue.message)
        ]
        assert len(template_warnings) > 0
