"""PlotViewpointRepositoryのエラーハンドリングテスト.

仕様書: SPEC-INFRASTRUCTURE
"""

from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
import yaml

from noveler.domain.exceptions.viewpoint_exceptions import (
    ViewpointDataInvalidError,
    ViewpointFileNotFoundError,
    ViewpointRepositoryError,
    ViewpointYAMLParseError,
)
from noveler.domain.quality.viewpoint_entities import ViewpointInfo
from noveler.infrastructure.persistence.plot_viewpoint_repository import PlotViewpointRepository


class TestPlotViewpointRepositoryErrorHandling:
    """PlotViewpointRepositoryのエラーハンドリングテスト.

    仕様書: SPEC-INFRASTRUCTURE
    """

    def test_init_with_nonexistent_project_path(self) -> None:
        """存在しないプロジェクトパスでの初期化時エラー."""
        with pytest.raises(ViewpointFileNotFoundError) as exc_info:
            PlotViewpointRepository(Path("/nonexistent/project"), enable_backup=False)

        error = exc_info.value
        assert "視点管理ファイルが見つかりません" in str(error)
        assert error.details["project_name"] == "project"

    def test_get_episode_viewpoint_info_invalid_episode_number(self) -> None:
        """無効なエピソード番号でのエラー."""
        with patch("pathlib.Path.exists", return_value=True):
            repo = PlotViewpointRepository(Path("/test/project"), enable_backup=False)

        # 数値以外の文字列
        with pytest.raises(ViewpointDataInvalidError) as exc_info:
            repo.get_episode_viewpoint_info("abc")

        error = exc_info.value
        assert "episode_number" in error.details["field_name"]
        assert "正の整数または数値文字列" in error.details["expected_type"]

        # 負の数
        with pytest.raises(ViewpointDataInvalidError) as exc_info:
            repo.get_episode_viewpoint_info("-1")

        # ゼロ
        with pytest.raises(ViewpointDataInvalidError) as exc_info:
            repo.get_episode_viewpoint_info("0")

    def test_plot_dir_not_exists(self) -> None:
        """プロットディレクトリが存在しない場合."""
        with patch("pathlib.Path.exists") as mock_exists:
            # プロジェクトパスは存在するが、プロットディレクトリは存在しない
            mock_exists.side_effect = lambda: mock_exists.call_count == 1
            repo = PlotViewpointRepository(Path("/test/project"), enable_backup=False)

        # plot_dirのインスタンスをモック
        mock_plot_dir = Mock()
        mock_plot_dir.exists.return_value = False

        with patch.object(repo, "plot_dir", mock_plot_dir):
            result = repo.get_episode_viewpoint_info("001")
            assert result is None

    def test_yaml_parse_error_with_location(self) -> None:
        """YAML構文エラー(位置情報付き)."""
        with patch("pathlib.Path.exists", return_value=True):
            repo = PlotViewpointRepository(Path("/test/project"), enable_backup=False)

        # YAMLエラーをシミュレート
        yaml_error = yaml.YAMLError()
        yaml_error.problem_mark = Mock()
        yaml_error.problem_mark.line = 24
        yaml_error.problem_mark.column = 9

        plot_file = Path("/test/project/20_プロット/章別プロット/chapter01.yaml")

        # plot_dirのインスタンスをモック
        mock_plot_dir = Mock()
        mock_plot_dir.exists.return_value = True
        mock_plot_dir.glob.return_value = [plot_file]

        with (
            patch.object(repo, "plot_dir", mock_plot_dir),
            patch("pathlib.Path.open", mock_open(read_data="invalid: yaml: content")),
            patch("yaml.safe_load", side_effect=yaml_error),
        ):
            with pytest.raises(ViewpointRepositoryError) as exc_info:
                repo.get_episode_viewpoint_info("001")

            error = exc_info.value
            # ViewpointRepositoryErrorでラップされているが、元の原因がViewpointYAMLParseErrorであることを確認
            assert "YAMLファイルの解析に失敗しました" in str(error)
            assert "行: 25" in str(error)
            assert "列: 10" in str(error)
            assert str(plot_file) in str(error)

    def test_yaml_parse_error_without_location(self) -> None:
        """YAML構文エラー(位置情報なし)."""
        with patch("pathlib.Path.exists", return_value=True):
            repo = PlotViewpointRepository(Path("/test/project"), enable_backup=False)

        yaml_error = yaml.YAMLError("Invalid YAML syntax")
        plot_file = Path("/test/project/20_プロット/章別プロット/chapter01.yaml")

        # plot_dirのインスタンスをモック
        mock_plot_dir = Mock()
        mock_plot_dir.exists.return_value = True
        mock_plot_dir.glob.return_value = [plot_file]

        with (
            patch.object(repo, "plot_dir", mock_plot_dir),
            patch("pathlib.Path.open", mock_open(read_data="invalid yaml")),
            patch("yaml.safe_load", side_effect=yaml_error),
        ):
            with pytest.raises(ViewpointRepositoryError) as exc_info:
                repo.get_episode_viewpoint_info("001")

            error = exc_info.value
            # ViewpointRepositoryErrorでラップされているが、元のエラーメッセージが含まれることを確認
            assert "Invalid YAML syntax" in str(error)

    def test_unicode_decode_error(self) -> None:
        """ファイルエンコーディングエラー."""
        with patch("pathlib.Path.exists", return_value=True):
            repo = PlotViewpointRepository(Path("/test/project"), enable_backup=False)

        plot_file = Path("/test/project/20_プロット/章別プロット/chapter01.yaml")

        # plot_dirのインスタンスをモック
        mock_plot_dir = Mock()
        mock_plot_dir.exists.return_value = True
        mock_plot_dir.glob.return_value = [plot_file]

        with (
            patch.object(repo, "plot_dir", mock_plot_dir),
            patch("pathlib.Path.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid byte")),
        ):
            with pytest.raises(ViewpointRepositoryError) as exc_info:
                repo.get_episode_viewpoint_info("001")

            error = exc_info.value
            # エラーメッセージにエンコーディングエラーの情報が含まれることを確認
            assert "エンコーディングエラー" in str(error) or "UnicodeDecodeError" in str(error)

    def test_os_error_reading_file(self) -> None:
        """ファイル読み込み時のOSエラー."""
        with patch("pathlib.Path.exists", return_value=True):
            repo = PlotViewpointRepository(Path("/test/project"), enable_backup=False)

        plot_file = Path("/test/project/20_プロット/章別プロット/chapter01.yaml")

        # plot_dirのインスタンスをモック
        mock_plot_dir = Mock()
        mock_plot_dir.exists.return_value = True
        mock_plot_dir.glob.return_value = [plot_file]

        with (
            patch.object(repo, "plot_dir", mock_plot_dir),
            patch("pathlib.Path.open", side_effect=OSError("Permission denied")),
        ):
            with pytest.raises(ViewpointRepositoryError) as exc_info:
                repo.get_episode_viewpoint_info("001")

            error = exc_info.value
            # エラーメッセージにファイル読み込みエラーの情報が含まれることを確認
            assert "Permission denied" in str(error) or "ファイル読み込みエラー" in str(error)

    def test_invalid_episode_breakdown_type(self) -> None:
        """episode_breakdownが辞書でない場合のエラー."""
        with patch("pathlib.Path.exists", return_value=True):
            repo = PlotViewpointRepository(Path("/test/project"), enable_backup=False)

        plot_file = Path("/test/project/20_プロット/章別プロット/chapter01.yaml")
        invalid_data = {
            "episode_breakdown": "not a dict"  # 辞書でない
        }

        # plot_dirのインスタンスをモック
        mock_plot_dir = Mock()
        mock_plot_dir.exists.return_value = True
        mock_plot_dir.glob.return_value = [plot_file]

        with (
            patch.object(repo, "plot_dir", mock_plot_dir),
            patch("pathlib.Path.open", mock_open(read_data=yaml.dump(invalid_data))),
        ):
            with pytest.raises((ViewpointDataInvalidError, ViewpointRepositoryError)) as exc_info:
                repo.get_episode_viewpoint_info("001")

            error = exc_info.value
            # エラーメッセージにepisode_breakdownの不正に関する情報が含まれることを確認
            assert "episode_breakdown" in str(error) or "エピソード" in str(error)

    def test_convert_to_viewpoint_info_invalid_data(self) -> None:
        """ViewpointInfo変換時の不正データエラー."""
        with patch("pathlib.Path.exists", return_value=True):
            repo = PlotViewpointRepository(Path("/test/project"), enable_backup=False)

        # episode_dataが辞書でない
        with pytest.raises(ViewpointRepositoryError) as exc_info:
            repo._convert_to_viewpoint_info("not a dict", {})

        error = exc_info.value
        # エラーメッセージにepisode_dataの不正に関する情報が含まれることを確認
        assert "episode_data" in str(error) and "dict" in str(error)

        # chapter_dataが辞書でない
        with pytest.raises(ViewpointRepositoryError) as exc_info:
            repo._convert_to_viewpoint_info({}, ["not", "a", "dict"])

        error = exc_info.value
        # エラーメッセージにchapter_dataの問題に関する情報が含まれることを確認
        assert "chapter_data" in str(error) or "章" in str(error) or "不正なデータ" in str(error)

    def test_backup_creation_error(self) -> None:
        """バックアップ作成時のエラー(エラーハンドリングのテスト)."""
        with patch("pathlib.Path.exists", return_value=True):
            repo = PlotViewpointRepository(Path("/test/project"), enable_backup=True)

        plot_file = Path("/test/project/20_プロット/章別プロット/chapter01.yaml")
        valid_data = {
            "episode_breakdown": {"ep1": {"viewpoint_details": {"consciousness": "主人公"}}},
            "chapter_info": {},
        }

        # plot_dirのインスタンスをモック
        mock_plot_dir = Mock()
        mock_plot_dir.exists.return_value = True
        mock_plot_dir.glob.return_value = [plot_file]

        with (
            patch.object(repo, "plot_dir", mock_plot_dir),
            patch("pathlib.Path.open", mock_open(read_data=yaml.dump(valid_data))),
            patch("shutil.copy2", side_effect=Exception("Backup failed")),
        ):
            # バックアップ失敗してもメイン処理は継続する
            result = repo.get_episode_viewpoint_info("001")
            assert isinstance(result, ViewpointInfo)

    def test_repository_error_during_conversion(self) -> None:
        """ViewpointInfo変換中の予期しないエラー."""
        with patch("pathlib.Path.exists", return_value=True):
            repo = PlotViewpointRepository(Path("/test/project"), enable_backup=False)

        episode_data = {"viewpoint_details": {}}
        chapter_data = {}

        # ViewpointInfoコンストラクタでエラーを発生させる
        with patch(
            "noveler.infrastructure.persistence.plot_viewpoint_repository.ViewpointInfo",
            side_effect=Exception("Unexpected error")
        ):
            with pytest.raises(ViewpointRepositoryError) as exc_info:
                repo._convert_to_viewpoint_info(episode_data, chapter_data)

            error = exc_info.value
            # エラーメッセージにViewpointInfo変換エラーの情報が含まれることを確認
            assert "ViewpointInfo" in str(error) or "変換エラー" in str(error)
