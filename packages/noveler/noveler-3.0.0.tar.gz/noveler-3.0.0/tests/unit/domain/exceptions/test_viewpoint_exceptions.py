"""視点管理システムの例外クラスのテスト.

仕様書: SPEC-UNIT-TEST
"""

import pytest

from noveler.domain.exceptions.viewpoint_exceptions import (
    ViewpointDataInvalidError,
    ViewpointError,
    ViewpointFileNotFoundError,
    ViewpointRepositoryError,
    ViewpointYAMLParseError,
)


class TestViewpointError:
    """ViewpointError基底クラスのテスト."""

    @pytest.mark.spec("SPEC-VIEWPOINT_EXCEPTIONS-SIMPLE_MESSAGE")
    def test_simple_message(self) -> None:
        """シンプルなメッセージのみの例外."""
        error = ViewpointError("エラーが発生しました")
        assert str(error) == "エラーが発生しました"
        assert error.message == "エラーが発生しました"
        assert error.details == {}

    @pytest.mark.spec("SPEC-VIEWPOINT_EXCEPTIONS-MESSAGE_WITH_DETAILS")
    def test_message_with_details(self) -> None:
        """詳細情報付きの例外."""
        details = {"file": "test.yaml", "line": 10}
        error = ViewpointError("解析エラー", details)
        assert str(error) == "解析エラー [file=test.yaml, line=10]"
        assert error.message == "解析エラー"
        assert error.details == details


class TestViewpointFileNotFoundError:
    """ViewpointFileNotFoundErrorのテスト."""

    @pytest.mark.spec("SPEC-VIEWPOINT_EXCEPTIONS-FILE_NOT_FOUND_WITHO")
    def test_file_not_found_without_project(self) -> None:
        """プロジェクト名なしのファイル不在エラー."""
        error = ViewpointFileNotFoundError("/path/to/file.yaml")
        assert "視点管理ファイルが見つかりません: /path/to/file.yaml" in str(error)
        assert error.details["file_path"] == "/path/to/file.yaml"
        assert "project_name" not in error.details

    @pytest.mark.spec("SPEC-VIEWPOINT_EXCEPTIONS-FILE_NOT_FOUND_WITH_")
    def test_file_not_found_with_project(self) -> None:
        """プロジェクト名付きのファイル不在エラー."""
        error = ViewpointFileNotFoundError("/path/to/file.yaml", "MyNovel")
        assert "プロジェクト 'MyNovel' の視点管理ファイルが見つかりません" in str(error)
        assert error.details["file_path"] == "/path/to/file.yaml"
        assert error.details["project_name"] == "MyNovel"


class TestViewpointYAMLParseError:
    """ViewpointYAMLParseErrorのテスト."""

    @pytest.mark.spec("SPEC-VIEWPOINT_EXCEPTIONS-PARSE_ERROR_MINIMAL")
    def test_parse_error_minimal(self) -> None:
        """最小限の情報でのYAML解析エラー."""
        error = ViewpointYAMLParseError("/path/to/plot.yaml")
        assert "YAMLファイルの解析に失敗しました: /path/to/plot.yaml" in str(error)
        assert error.details["file_path"] == "/path/to/plot.yaml"

    @pytest.mark.spec("SPEC-VIEWPOINT_EXCEPTIONS-PARSE_ERROR_WITH_LOC")
    def test_parse_error_with_location(self) -> None:
        """行番号・列番号付きのYAML解析エラー."""
        error = ViewpointYAMLParseError("/path/to/plot.yaml", line_number=25, column_number=10)
        assert "(行: 25, 列: 10)" in str(error)
        assert error.details["line"] == 25
        assert error.details["column"] == 10

    @pytest.mark.spec("SPEC-VIEWPOINT_EXCEPTIONS-PARSE_ERROR_WITH_ORI")
    def test_parse_error_with_original_error(self) -> None:
        """元のエラー情報付きのYAML解析エラー."""
        original = "expected ':', but found '}'"
        error = ViewpointYAMLParseError("/path/to/plot.yaml", original_error=original)
        assert f"詳細: {original}" in str(error)
        assert error.details["original_error"] == original

    @pytest.mark.spec("SPEC-VIEWPOINT_EXCEPTIONS-PARSE_ERROR_FULL_INF")
    def test_parse_error_full_info(self) -> None:
        """全情報付きのYAML解析エラー."""
        error = ViewpointYAMLParseError(
            "/path/to/plot.yaml", line_number=25, column_number=10, original_error="unexpected end of file"
        )

        assert "(行: 25, 列: 10)" in str(error)
        assert "詳細: unexpected end of file" in str(error)


class TestViewpointDataInvalidError:
    """ViewpointDataInvalidErrorのテスト."""

    @pytest.mark.spec("SPEC-VIEWPOINT_EXCEPTIONS-INVALID_DATA_WITHOUT")
    def test_invalid_data_without_file(self) -> None:
        """ファイルパスなしのデータ不正エラー."""
        error = ViewpointDataInvalidError(field_name="episode_breakdown", expected_type="dict", actual_value=[1, 2, 3])
        assert "フィールド 'episode_breakdown' は dict 型である必要があります" in str(error)
        assert error.details["field_name"] == "episode_breakdown"
        assert error.details["expected_type"] == "dict"
        assert error.details["actual_type"] == "list"
        assert error.details["actual_value"] == "[1, 2, 3]"

    @pytest.mark.spec("SPEC-VIEWPOINT_EXCEPTIONS-INVALID_DATA_WITH_FI")
    def test_invalid_data_with_file(self) -> None:
        """ファイルパス付きのデータ不正エラー."""
        error = ViewpointDataInvalidError(
            field_name="complexity_level", expected_type="str", actual_value=123, file_path="/path/to/plot.yaml"
        )

        assert "(/path/to/plot.yaml)" in str(error)
        assert error.details["file_path"] == "/path/to/plot.yaml"

    @pytest.mark.spec("SPEC-VIEWPOINT_EXCEPTIONS-LONG_VALUE_TRUNCATIO")
    def test_long_value_truncation(self) -> None:
        """長い値の切り詰めテスト."""
        long_value = "a" * 200
        error = ViewpointDataInvalidError(field_name="content", expected_type="dict", actual_value=long_value)
        # 100文字に切り詰められる
        assert len(error.details["actual_value"]) == 100
        assert error.details["actual_value"] == "a" * 100


class TestViewpointRepositoryError:
    """ViewpointRepositoryErrorのテスト."""

    @pytest.mark.spec("SPEC-VIEWPOINT_EXCEPTIONS-REPOSITORY_ERROR_BAS")
    def test_repository_error_basic(self) -> None:
        """基本的なリポジトリエラー."""
        error = ViewpointRepositoryError(operation="get_episode_viewpoint_info", reason="ファイルが読み込めません")
        assert "視点管理リポジトリ操作 'get_episode_viewpoint_info' に失敗しました" in str(error)
        assert "ファイルが読み込めません" in str(error)
        assert error.details["operation"] == "get_episode_viewpoint_info"
        assert error.details["reason"] == "ファイルが読み込めません"

    @pytest.mark.spec("SPEC-VIEWPOINT_EXCEPTIONS-REPOSITORY_ERROR_WIT")
    def test_repository_error_with_extra_details(self) -> None:
        """追加情報付きのリポジトリエラー."""
        error = ViewpointRepositoryError(
            operation="save_viewpoint_info",
            reason="書き込み権限がありません",
            file_path="/path/to/file.yaml",
            episode_number="001",
        )

        assert error.details["file_path"] == "/path/to/file.yaml"
        assert error.details["episode_number"] == "001"
        assert "file_path=/path/to/file.yaml" in str(error)
        assert "episode_number=001" in str(error)
