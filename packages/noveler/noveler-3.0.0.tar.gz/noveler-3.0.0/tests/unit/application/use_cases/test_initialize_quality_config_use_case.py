"""InitializeQualityConfigUseCaseのテスト

仕様書: SPEC-APPLICATION-USE-CASES
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from noveler.application.use_cases.initialize_quality_config_use_case import (
    InitializeQualityConfigCommand,
    InitializeQualityConfigResult,
    InitializeQualityConfigUseCase,
)


class TestInitializeQualityConfigUseCase:
    """品質設定初期化ユースケースのテスト"""

    @pytest.fixture
    def use_case(self):
        """テスト用ユースケースインスタンス"""
        service = Mock()
        return InitializeQualityConfigUseCase(service)

    @pytest.mark.spec("SPEC-INITIALIZE_QUALITY_CONFIG_USE_CASE-NEW_QUALITY_CONFIGUR")
    def test_new_quality_configurationinit(self, use_case: object) -> None:
        """新規プロジェクトで品質設定が初期化されることを確認"""
        # Arrange
        command = InitializeQualityConfigCommand(project_root=Path("/test/project"), genre="ファンタジー", force=False)

        use_case.service.initialize_for_project.return_value = Mock(
            success=True, message="ファンタジージャンルの品質設定を作成しました"
        )

        # Act
        result = use_case.execute(command)

        # Assert
        assert isinstance(result, InitializeQualityConfigResult)
        assert result.success is True
        assert "ファンタジー" in result.message
        use_case.service.initialize_for_project.assert_called_once_with(Path("/test/project"))

    @pytest.mark.spec("SPEC-INITIALIZE_QUALITY_CONFIG_USE_CASE-CONFIGURATION_OPERAT")
    def test_configuration_operation(self, use_case: object) -> None:
        """既存設定がある場合は上書きしないことを確認"""
        # Arrange
        command = InitializeQualityConfigCommand(project_root=Path("/test/project"), genre="恋愛", force=False)

        use_case.service.initialize_for_project.return_value = Mock(
            success=True, message="品質設定ファイルは既に存在します"
        )

        # Act
        result = use_case.execute(command)

        # Assert
        assert result.success is True
        assert "既に存在" in result.message

    @pytest.mark.spec("SPEC-INITIALIZE_QUALITY_CONFIG_USE_CASE-WRITE")
    def test_write(self, use_case: object) -> None:
        """forceオプションで既存設定を上書きできることを確認"""
        # Arrange
        command = InitializeQualityConfigCommand(project_root=Path("/test/project"), genre="ミステリー", force=True)

        use_case.service.initialize_for_project.return_value = Mock(
            success=True, message="ミステリージャンルの品質設定を作成しました(強制上書き)"
        )

        # Act
        result = use_case.execute(command)

        # Assert
        assert result.success is True
        assert "ミステリー" in result.message
        # force=Trueの場合の特別な処理があれば検証

    @pytest.mark.spec("SPEC-INITIALIZE_QUALITY_CONFIG_USE_CASE-ERROR_HANDLING")
    def test_error_handling(self, use_case: object) -> None:
        """エラーが適切に処理されることを確認"""
        # Arrange
        command = InitializeQualityConfigCommand(project_root=Path("/test/project"), genre="ファンタジー", force=False)

        use_case.service.initialize_for_project.side_effect = Exception("テストエラー")

        # Act
        result = use_case.execute(command)

        # Assert
        assert result.success is False
        assert "エラー" in result.message

    @pytest.mark.spec("SPEC-INITIALIZE_QUALITY_CONFIG_USE_CASE-HANDLING")
    def test_handling(self, use_case: object) -> None:
        """無効なジャンルが指定された場合の処理を確認"""
        # Arrange
        command = InitializeQualityConfigCommand(
            project_root=Path("/test/project"),
            genre="",  # 空のジャンル
            force=False,
        )

        use_case.service.initialize_for_project.side_effect = ValueError("ジャンル名は空にできません")

        # Act
        result = use_case.execute(command)

        # Assert
        assert result.success is False
        assert "ジャンル" in result.message
