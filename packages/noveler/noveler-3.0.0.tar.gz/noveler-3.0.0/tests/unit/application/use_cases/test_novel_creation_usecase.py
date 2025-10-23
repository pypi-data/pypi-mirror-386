#!/usr/bin/env python3
"""小説作成ユースケースのテスト

NovelCreationUsecaseの動作を検証するユニットテスト
DDD準拠・パフォーマンス最適化対応版
"""

import pytest
from unittest.mock import Mock

from pathlib import Path


from noveler.application.use_cases.novel_creation_usecase import NovelCreationUsecase


class TestNovelCreationUsecase:
    """NovelCreationUsecase テストクラス"""

    @pytest.fixture
    def mock_project_repository(self):
        """プロジェクトリポジトリのモック"""
        mock_repo = Mock()
        # get_project_path メソッドを追加
        mock_repo.get_project_path.return_value = Path("/test/project/path")
        mock_repo.create_project.return_value = True
        mock_repo.exists.return_value = False
        return mock_repo

    @pytest.fixture
    def mock_project_service(self):
        """プロジェクトサービスのモック"""
        mock_service = Mock()
        mock_service.validate_project_name.return_value = True
        mock_service.initialize_project_structure.return_value = True
        return mock_service

    @pytest.fixture
    def novel_creation_usecase(self, mock_project_repository, mock_project_service):
        """NovelCreationUsecase インスタンス"""
        return NovelCreationUsecase(
            project_repository=mock_project_repository,
            project_service=mock_project_service
        )

    @pytest.mark.spec("SPEC-NOVEL_CREATION_USECASE-CREATE_NOVEL_SUCCESS")
    def test_create_novel_success(self, novel_creation_usecase, mock_project_repository, mock_project_service):
        """小説プロジェクト作成成功テスト"""
        # テストデータ
        project_name = "test_novel"
        author_name = "Test Author"

        # 実行
        result = novel_creation_usecase.create_novel(project_name, author_name)

        # 検証
        assert result is True
        mock_project_service.validate_project_name.assert_called_once_with(project_name)
        mock_project_repository.create_project.assert_called_once()

    @pytest.mark.spec("SPEC-NOVEL_CREATION_USECASE-CREATE_NOVEL_WITH_EX")
    def test_create_novel_with_existing_project(self, novel_creation_usecase, mock_project_repository):
        """既存プロジェクトが存在する場合のテスト"""
        # 既存プロジェクトを模擬
        mock_project_repository.exists.return_value = True

        # テストデータ
        project_name = "existing_novel"
        author_name = "Test Author"

        # 実行と検証
        with pytest.raises(ValueError, match="プロジェクトが既に存在します"):
            novel_creation_usecase.create_novel(project_name, author_name)

    @pytest.mark.spec("SPEC-NOVEL_CREATION_USECASE-CREATE_NOVEL_VALIDAT")
    def test_create_novel_validation_error(self, novel_creation_usecase, mock_project_service):
        """プロジェクト名検証エラーテスト"""
        # 検証失敗を模擬
        mock_project_service.validate_project_name.return_value = False

        # テストデータ
        project_name = "invalid_name"
        author_name = "Test Author"

        # 実行と検証
        with pytest.raises(ValueError, match="不正なプロジェクト名です"):
            novel_creation_usecase.create_novel(project_name, author_name)
