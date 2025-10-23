#!/usr/bin/env python3
"""ProjectInfo値オブジェクトのユニットテスト

仕様書: specs/project_info.spec.md
TDD原則に従い、仕様書に基づいてテストを作成
"""

from pathlib import Path

import pytest

from noveler.domain.value_objects.project_info import ProjectInfo
from noveler.presentation.shared.shared_utilities import get_common_path_service

pytestmark = pytest.mark.vo_smoke



class TestProjectInfo:
    """ProjectInfoのテストクラス"""

    def test_init(self) -> None:
        """正常なパラメータで初期化できることを確認"""
        # Arrange
        get_common_path_service()
        name = "転生魔法学園"
        root_path = Path("/novels/転生魔法学園")
        config_path = Path("/novels/転生魔法学園/プロジェクト設定.yaml")

        # Act
        project_info = ProjectInfo(name=name, root_path=root_path, config_path=config_path)

        # Assert
        assert project_info.name == name
        assert project_info.root_path == root_path
        assert project_info.config_path == config_path

    def test_value_error(self) -> None:
        """空のプロジェクト名でValueErrorが発生することを確認"""
        # Arrange
        root_path = Path("/novels/test")
        config_path = Path("/novels/test/config.yaml")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ProjectInfo(name="", root_path=root_path, config_path=config_path)

        assert str(exc_info.value) == "プロジェクト名は必須です"

    def test_root_path_type_error(self) -> None:
        """root_pathが文字列の場合にTypeErrorが発生することを確認"""
        # Arrange & Act & Assert
        with pytest.raises(TypeError) as exc_info:
            ProjectInfo(
                name="test",
                root_path="/novels/test",  # type: ignore
                config_path=Path("/novels/test/config.yaml"),
            )

        assert str(exc_info.value) == "root_pathはPathオブジェクトである必要があります"

    def test_config_path_type_error(self) -> None:
        """config_pathが文字列の場合にTypeErrorが発生することを確認"""
        # Arrange & Act & Assert
        with pytest.raises(TypeError) as exc_info:
            ProjectInfo(
                name="test",
                root_path=Path("/novels/test"),
                config_path="/novels/test/config.yaml",  # type: ignore
            )

        assert str(exc_info.value) == "config_pathはPathオブジェクトである必要があります"

    def test_manuscript_path(self) -> None:
        """原稿フォルダパスが正しく取得できることを確認"""
        # Arrange
        project_info = ProjectInfo(
            name="テスト小説",
            root_path=Path("/home/user/novels/テスト小説"),
            config_path=Path("/home/user/novels/テスト小説/プロジェクト設定.yaml"),
        )

        # Act
        manuscript_path = project_info.manuscript_path

        # Assert
        assert manuscript_path == Path("/home/user/novels/テスト小説/40_原稿")
        path_service = get_common_path_service()
        assert str(manuscript_path).endswith(str(path_service.get_manuscript_dir()))

    def test_management_path(self) -> None:
        """管理資料フォルダパスが正しく取得できることを確認"""
        # Arrange
        project_info = ProjectInfo(
            name="テスト小説",
            root_path=Path("/home/user/novels/テスト小説"),
            config_path=Path("/home/user/novels/テスト小説/プロジェクト設定.yaml"),
        )

        # Act
        management_path = project_info.management_path

        # Assert
        assert management_path == Path("/home/user/novels/テスト小説/50_管理資料")
        path_service = get_common_path_service()
        assert str(management_path).endswith(str(path_service.get_management_dir()))

    def test_verification(self) -> None:
        """frozen=Trueにより値の変更ができないことを確認"""
        # Arrange
        project_info = ProjectInfo(name="test", root_path=Path("/test"), config_path=Path("/test/config.yaml"))

        # Act & Assert
        with pytest.raises(AttributeError, match=".*"):
            project_info.name = "変更"  # type: ignore

        with pytest.raises(AttributeError, match=".*"):
            project_info.root_path = Path("/changed")  # type: ignore

    def test_operation_verification(self) -> None:
        """相対パスでも正しく動作することを確認"""
        # Arrange
        project_info = ProjectInfo(
            name="test", root_path=Path("./novels/test"), config_path=Path("./novels/test/config.yaml")
        )

        # Act & Assert
        assert project_info.manuscript_path == Path("./novels/test/40_原稿")
        assert project_info.management_path == Path("./novels/test/50_管理資料")

    def test_windowspath_operation_verification(self) -> None:
        """Windowsスタイルのパスでも正しく動作することを確認"""
        # Arrange
        project_info = ProjectInfo(
            name="test",
            root_path=Path("C:/Users/user/novels/test"),
            config_path=Path("C:/Users/user/novels/test/config.yaml"),
        )

        # Act & Assert
        # Pathオブジェクトは自動的にOSに適したパス区切り文字を使用
        assert project_info.manuscript_path == Path("C:/Users/user/novels/test/40_原稿")
        assert project_info.management_path == Path("C:/Users/user/novels/test/50_管理資料")

    def test_unnamed(self) -> None:
        """同じ内容のインスタンスが等価と判定されることを確認"""
        # Arrange
        project_info1 = ProjectInfo(name="test", root_path=Path("/test"), config_path=Path("/test/config.yaml"))
        project_info2 = ProjectInfo(name="test", root_path=Path("/test"), config_path=Path("/test/config.yaml"))
        project_info3 = ProjectInfo(name="different", root_path=Path("/test"), config_path=Path("/test/config.yaml"))

        # Act & Assert
        assert project_info1 == project_info2
        assert project_info1 != project_info3
