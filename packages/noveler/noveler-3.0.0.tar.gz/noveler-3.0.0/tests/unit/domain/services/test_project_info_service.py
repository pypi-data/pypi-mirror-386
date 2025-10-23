#!/usr/bin/env python3
"""ProjectInfoServiceのユニットテスト

ドメインサービスのビジネスロジックをテスト


仕様書: SPEC-DOMAIN-SERVICES
"""

from unittest.mock import Mock, patch

import pytest

from noveler.domain.exceptions import BusinessRuleViolationError
from noveler.domain.services.project_info_service import ProjectInfoService
from noveler.domain.value_objects.project_context import ProjectContext


class TestProjectInfoService:
    """ProjectInfoServiceのテスト"""

    @pytest.fixture
    def mock_repository(self):
        """モックリポジトリの作成"""
        return Mock()

    @pytest.fixture
    def service(self, mock_repository: object):
        """テスト用サービスインスタンス"""
        return ProjectInfoService(mock_repository)

    @pytest.fixture
    def valid_project_files(self):
        """有効なプロジェクトファイルデータ"""
        return {
            "project_settings": {
                "title": "テスト小説",
                "author": "テスト作者",
                "genre": "ファンタジー",
                "target_readers": ["10代", "20代"],
            },
            "character_settings": {
                "main_character": {
                    "name": "主人公",
                    "age": 17,
                    "description": "普通の高校生",
                }
            },
            "plot_settings": {
                "total_episodes": 100,
                "current_arc": "序章",
            },
            "episode_management": {
                "episodes": [
                    {"number": 1, "title": "第1話", "status": "published"},
                    {"number": 2, "title": "第2話", "status": "draft"},
                ]
            },
        }

    @pytest.mark.spec("SPEC-PROJECT_INFO_SERVICE-LOAD_PROJECT_CONTEXT")
    def test_load_project_context_success(
        self, service: object, mock_repository: object, valid_project_files: object
    ) -> None:
        """正常なプロジェクトコンテキストの読み込み"""
        # Given
        mock_repository.load_project_files.return_value = valid_project_files

        # When
        context = service.load_project_context("/test/project")

        # Then
        mock_repository.load_project_files.assert_called_once_with("/test/project")
        assert isinstance(context, ProjectContext)

    @pytest.mark.spec("SPEC-PROJECT_INFO_SERVICE-LOAD_PROJECT_CONTEXT")
    def test_load_project_context_missing_required_files(self, service: object, mock_repository: object) -> None:
        """必須ファイルが不足している場合"""
        # Given
        incomplete_files = {
            "character_settings": {"main_character": {"name": "主人公"}},
            # project_settings が不足
        }
        mock_repository.load_project_files.return_value = incomplete_files

        # When/Then
        with pytest.raises(BusinessRuleViolationError, match="プロジェクト設定.yaml"):
            service.load_project_context()

    @pytest.mark.spec("SPEC-PROJECT_INFO_SERVICE-LOAD_PROJECT_CONTEXT")
    def test_load_project_context_empty_required_file(self, service: object, mock_repository: object) -> None:
        """必須ファイルが空の場合"""
        # Given
        files_with_empty = {
            "project_settings": {},  # 空のdict
            "character_settings": {"main_character": {"name": "主人公"}},
        }
        mock_repository.load_project_files.return_value = files_with_empty

        # When/Then
        with pytest.raises(BusinessRuleViolationError, match="プロジェクト設定.yaml"):
            service.load_project_context()

    @pytest.mark.spec("SPEC-PROJECT_INFO_SERVICE-VALIDATE_REQUIRED_FI")
    def test_validate_required_files_all_present(self, service: object, valid_project_files: object) -> None:
        """全ての必須ファイルが存在する場合"""
        # When/Then - エラーが発生しないことを確認
        service._validate_required_files(valid_project_files)

    @pytest.mark.spec("SPEC-PROJECT_INFO_SERVICE-VALIDATE_REQUIRED_FI")
    def test_validate_required_files_missing_single(self, service: object) -> None:
        """単一の必須ファイルが不足"""
        # Given
        files = {"character_settings": {"data": "test"}}

        # When/Then
        with pytest.raises(BusinessRuleViolationError) as exc_info:
            service._validate_required_files(files)

        assert "プロジェクト設定.yaml" in str(exc_info.value)

    @pytest.mark.spec("SPEC-PROJECT_INFO_SERVICE-GET_FILE_DISPLAY_NAM")
    def test_get_file_display_name(self, service: object) -> None:
        """ファイル表示名の取得"""
        # When/Then
        assert service._get_file_display_name("project_settings") == "プロジェクト設定.yaml"
        assert service._get_file_display_name("character_settings") == "30_設定集/キャラクター.yaml"
        assert service._get_file_display_name("plot_settings") == "20_プロット/全体構成.yaml"
        assert service._get_file_display_name("episode_management") == "50_管理資料/話数管理.yaml"
        assert service._get_file_display_name("unknown_key") == "unknown_key"

    @pytest.mark.spec("SPEC-PROJECT_INFO_SERVICE-GET_AVAILABLE_PROJEC")
    def test_get_available_project_info_all_available(
        self, service: object, mock_repository: object, valid_project_files: object
    ) -> None:
        """全てのプロジェクト情報が利用可能な場合"""
        # Given
        mock_repository.load_project_files.return_value = valid_project_files

        # When
        availability = service.get_available_project_info()

        # Then
        assert availability["project_settings"] is True
        assert availability["character_settings"] is True
        assert availability["plot_settings"] is True
        assert availability["episode_management"] is True

    @pytest.mark.spec("SPEC-PROJECT_INFO_SERVICE-GET_AVAILABLE_PROJEC")
    def test_get_available_project_info_partial(self, service: object, mock_repository: object) -> None:
        """一部のプロジェクト情報のみ利用可能な場合"""
        # Given
        partial_files = {
            "project_settings": {"title": "テスト"},
            "character_settings": None,
            "plot_settings": {},
            # episode_management は存在しない
        }
        mock_repository.load_project_files.return_value = partial_files

        # When
        availability = service.get_available_project_info()

        # Then
        assert availability["project_settings"] is True
        assert availability["character_settings"] is False
        assert availability["plot_settings"] is False  # 空のdictはFalse
        assert availability["episode_management"] is False

    @pytest.mark.spec("SPEC-PROJECT_INFO_SERVICE-GET_AVAILABLE_PROJEC")
    def test_get_available_project_info_exception(self, service: object, mock_repository: object) -> None:
        """例外が発生した場合は全てFalse"""
        # Given
        mock_repository.load_project_files.side_effect = Exception("読み込みエラー")

        # When
        availability = service.get_available_project_info()

        # Then
        assert all(not available for available in availability.values())

    @pytest.mark.spec("SPEC-PROJECT_INFO_SERVICE-VALIDATE_PROJECT_STR")
    def test_validate_project_structure_valid(
        self, service: object, mock_repository: object, valid_project_files: object
    ) -> None:
        """有効なプロジェクト構造の検証"""
        # Given
        mock_repository.load_project_files.return_value = valid_project_files
        # モックのProjectContextを作成
        mock_context = Mock(spec=ProjectContext)
        mock_context.is_valid.return_value = True

        # ProjectContext.from_project_filesをモック
        with patch.object(ProjectContext, "from_project_files", return_value=mock_context):
            # When
            result = service.validate_project_structure("/test/project")

            # Then
            assert result["is_valid"] is True
            assert len(result["errors"]) == 0
            assert len(result["warnings"]) == 0

    @pytest.mark.spec("SPEC-PROJECT_INFO_SERVICE-VALIDATE_PROJECT_STR")
    def test_validate_project_structure_missing_optional(self, service: object, mock_repository: object) -> None:
        """オプションファイルが不足している場合"""
        # Given
        minimal_files = {
            "project_settings": {"title": "テスト"},
            # その他は不足
        }
        mock_repository.load_project_files.return_value = minimal_files

        # モックのProjectContextを作成
        mock_context = Mock(spec=ProjectContext)
        mock_context.is_valid.return_value = True

        # ProjectContext.from_project_filesをモック
        with patch.object(ProjectContext, "from_project_files", return_value=mock_context):
            # When
            result = service.validate_project_structure()

            # Then
            assert result["is_valid"] is True  # 必須ファイルがあればvalid
            assert len(result["warnings"]) > 0  # オプションファイル不足の警告

    @pytest.mark.spec("SPEC-PROJECT_INFO_SERVICE-VALIDATE_PROJECT_STR")
    def test_validate_project_structure_invalid(self, service: object, mock_repository: object) -> None:
        """無効なプロジェクト構造"""
        # Given
        mock_repository.load_project_files.return_value = {}

        # When
        result = service.validate_project_structure()

        # Then
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
        assert "必須ファイルが見つかりません" in str(result["errors"])

    @pytest.mark.spec("SPEC-PROJECT_INFO_SERVICE-VALIDATE_PROJECT_STR")
    def test_validate_project_structure_exception(self, service: object, mock_repository: object) -> None:
        """検証中の例外処理"""
        # Given
        mock_repository.load_project_files.side_effect = Exception("検証エラー")

        # When
        result = service.validate_project_structure()

        # Then
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
        assert any("検証エラー" in error for error in result["errors"])

    @pytest.mark.spec("SPEC-PROJECT_INFO_SERVICE-VALIDATE_PROJECT_STR")
    def test_validate_project_structure_context_invalid(
        self, service: object, mock_repository: object, valid_project_files: object
    ) -> None:
        """コンテキストが無効な場合の検証結果"""
        # Given
        mock_repository.load_project_files.return_value = valid_project_files

        # モックのProjectContextを作成
        mock_context = Mock(spec=ProjectContext)
        mock_context.is_valid.return_value = False  # コンテキストが無効

        # ProjectContext.from_project_filesをモック
        with patch.object(ProjectContext, "from_project_files", return_value=mock_context):
            # When
            result = service.validate_project_structure()

            # Then
            assert result["is_valid"] is False
            assert "プロジェクトコンテキストが無効です" in result["errors"]

    @pytest.mark.spec("SPEC-PROJECT_INFO_SERVICE-GET_PROJECT_SUMMARY_")
    def test_get_project_summary_success(
        self, service: object, mock_repository: object, valid_project_files: object
    ) -> None:
        """プロジェクトサマリーの取得成功"""
        # Given
        mock_repository.load_project_files.return_value = valid_project_files

        # モックのProjectContextを作成
        mock_context = Mock(spec=ProjectContext)
        mock_context.project_name = "テスト小説"
        mock_context.genre = "ファンタジー"
        mock_context.protagonist_name = "主人公"
        mock_context.total_episodes = 100
        mock_context.structure_type = "起承転結"
        mock_context.has_character_info.return_value = True
        mock_context.has_plot_info.return_value = True
        mock_context.main_characters = ["主人公", "ヒロイン"]
        mock_context.quality_threshold = 80

        with patch.object(ProjectContext, "from_project_files", return_value=mock_context):
            # When
            summary = service.get_project_summary()

            # Then
            assert summary["project_name"] == "テスト小説"
            assert summary["genre"] == "ファンタジー"
            assert summary["protagonist"] == "主人公"
            assert summary["total_episodes"] == 100
            assert summary["structure_type"] == "起承転結"
            assert summary["has_character_info"] is True
            assert summary["has_plot_info"] is True
            assert summary["character_count"] == 2
            assert summary["quality_threshold"] == 80

    @pytest.mark.spec("SPEC-PROJECT_INFO_SERVICE-GET_PROJECT_SUMMARY_")
    def test_get_project_summary_exception(self, service: object, mock_repository: object) -> None:
        """プロジェクトサマリー取得時の例外処理"""
        # Given
        mock_repository.load_project_files.side_effect = Exception("サマリー取得エラー")

        # When
        summary = service.get_project_summary()

        # Then
        assert "error" in summary
        assert "サマリー取得エラー" in summary["error"]
        assert summary["project_name"] is None
        assert summary["genre"] is None
