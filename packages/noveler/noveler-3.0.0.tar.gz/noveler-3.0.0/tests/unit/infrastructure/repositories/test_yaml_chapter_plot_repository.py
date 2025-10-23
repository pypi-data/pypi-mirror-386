"""YAML章別プロットリポジトリのテスト

SPEC-PLOT-001: Claude Code連携プロット生成システム
"""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

from noveler.domain.entities.chapter_plot import ChapterPlot
from noveler.domain.repositories.chapter_plot_repository import ChapterPlotNotFoundError
from noveler.domain.value_objects.chapter_number import ChapterNumber
from noveler.infrastructure.repositories.yaml_chapter_plot_repository import YamlChapterPlotRepository
from noveler.presentation.shared.shared_utilities import get_common_path_service


class TestYamlChapterPlotRepository:
    """YAML章別プロットリポジトリのテストクラス"""

    @pytest.fixture
    def project_root(self) -> Path:
        """プロジェクトルートのフィクスチャ"""
        return Path("/test/project")

    @pytest.fixture
    def repository(self, project_root: Path) -> YamlChapterPlotRepository:
        """リポジトリのフィクスチャ"""
        return YamlChapterPlotRepository(project_root)

    @pytest.fixture
    def sample_chapter_yaml_data(self) -> dict:
        """サンプル章別プロットYAMLデータのフィクスチャ"""
        return {
            "chapter_number": 1,
            "title": "ch01 出会いと冒険の始まり",
            "summary": "主人公が新しい世界に踏み出す章",
            "key_events": ["転生", "能力発覚", "仲間との出会い"],
            "episodes": [
                {"episode_number": 1, "title": "第1話", "summary": "転生シーン"},
                {"episode_number": 2, "title": "第2話", "summary": "能力発覚"},
            ],
            "chapter_info": {
                "central_theme": "新しい世界への適応と成長",
                "viewpoint_management": {
                    "primary_pov_character": "主人公",
                    "complexity_level": "低",
                },
            },
        }

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_find_by_chapter_number_success(
        self,
        repository: YamlChapterPlotRepository,
        sample_chapter_yaml_data: dict,
    ) -> None:
        """章番号による章別プロット取得成功テスト"""
        # Given: YAMLファイル読み込みのモック
        yaml_content = yaml.dump(sample_chapter_yaml_data, allow_unicode=True)

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.open", mock_open(read_data=yaml_content)),
        ):
            # When: 章番号で章別プロットを取得
            chapter_number = ChapterNumber(1)
            result = repository.find_by_chapter_number(chapter_number)

            # Then: 正しい章別プロットが返される
            assert isinstance(result, ChapterPlot)
            assert result.chapter_number == chapter_number
            assert result.title == "ch01 出会いと冒険の始まり"
            assert result.summary == "主人公が新しい世界に踏み出す章"
            assert result.key_events == ["転生", "能力発覚", "仲間との出会い"]
            assert len(result.episodes) == 2
            assert result.central_theme == "新しい世界への適応と成長"

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_find_by_chapter_number_file_not_found(
        self,
        repository: YamlChapterPlotRepository,
    ) -> None:
        """章別プロットファイルが見つからない場合のテスト"""
        # Given: ファイルが存在しない設定
        with patch("pathlib.Path.exists", return_value=False):
            # When & Then: 例外が発生
            chapter_number = ChapterNumber(99)
            with pytest.raises(ChapterPlotNotFoundError, match="章別プロットファイルが見つかりません"):
                repository.find_by_chapter_number(chapter_number)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_find_by_chapter_number_yaml_parse_error(
        self,
        repository: YamlChapterPlotRepository,
    ) -> None:
        """YAMLパースエラーの場合のテスト"""
        # Given: 無効なYAMLファイル
        invalid_yaml = "invalid: yaml: content: ["

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.open", mock_open(read_data=invalid_yaml)),
        ):
            # When & Then: 例外が発生
            chapter_number = ChapterNumber(1)
            with pytest.raises(ChapterPlotNotFoundError, match="章別プロットファイルの読み込みに失敗しました"):
                repository.find_by_chapter_number(chapter_number)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_find_by_episode_number_success(
        self,
        repository: YamlChapterPlotRepository,
        sample_chapter_yaml_data: dict,
    ) -> None:
        """エピソード番号による章別プロット取得成功テスト"""
        # Given: YAMLファイル読み込みのモック(ch01: エピソード1-10)
        yaml_content = yaml.dump(sample_chapter_yaml_data, allow_unicode=True)

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.open", mock_open(read_data=yaml_content)),
        ):
            # When: エピソード番号で章別プロットを取得
            result = repository.find_by_episode_number(1)

            # Then: 正しい章別プロットが返される
            assert isinstance(result, ChapterPlot)
            assert result.chapter_number == ChapterNumber(1)
            assert result.title == "ch01 出会いと冒険の始まり"

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_find_by_episode_number_chapter_not_found(
        self,
        repository: YamlChapterPlotRepository,
    ) -> None:
        """エピソード番号による章別プロット取得(章が見つからない)テスト"""
        # Given: 推定される章ファイルが存在しない設定
        with patch("pathlib.Path.exists", return_value=False):
            # When & Then: 例外が発生
            with pytest.raises(ChapterPlotNotFoundError, match="エピソード99を含む章別プロットが見つかりません"):
                repository.find_by_episode_number(99)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_exists_true(
        self,
        repository: YamlChapterPlotRepository,
    ) -> None:
        """章別プロット存在確認成功テスト"""
        # Given: ファイルが存在する設定
        with patch("pathlib.Path.exists", return_value=True):
            # When: 存在確認
            result = repository.exists(ChapterNumber(1))

            # Then: Trueが返される
            assert result is True

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_exists_false(
        self,
        repository: YamlChapterPlotRepository,
    ) -> None:
        """章別プロット存在確認失敗テスト"""
        # Given: ファイルが存在しない設定
        with patch("pathlib.Path.exists", return_value=False):
            # When: 存在確認
            result = repository.exists(ChapterNumber(99))

            # Then: Falseが返される
            assert result is False

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_list_all_success(
        self,
        repository: YamlChapterPlotRepository,
        sample_chapter_yaml_data: dict,
    ) -> None:
        """全章別プロット一覧取得成功テスト"""
        # Given: 複数の章ファイルが存在する設定
        yaml_content = yaml.dump(sample_chapter_yaml_data, allow_unicode=True)

        with (
            patch("pathlib.Path.glob") as mock_glob,
            patch("pathlib.Path.open", mock_open(read_data=yaml_content)),
        ):
            # モックで2つの章ファイルを返す
            mock_files = [Path("/test/project/20_プロット/章別プロット/chapter01.yaml")]
            mock_glob.return_value = mock_files

            # When: 全章別プロット取得
            result = repository.list_all()

            # Then: 正しいリストが返される
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], ChapterPlot)
            assert result[0].chapter_number == ChapterNumber(1)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_list_all_empty(
        self,
        repository: YamlChapterPlotRepository,
    ) -> None:
        """全章別プロット一覧取得(空)テスト"""
        # Given: 章ファイルが存在しない設定
        with patch("pathlib.Path.glob", return_value=[]):
            # When: 全章別プロット取得
            result = repository.list_all()

            # Then: 空のリストが返される
            assert result == []

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_get_chapter_plot_file_path(
        self,
        repository: YamlChapterPlotRepository,
        project_root: Path,
    ) -> None:
        """章別プロットファイルパス取得テスト"""
        # Given: 章番号
        chapter_number = ChapterNumber(1)

        # When: ファイルパスを取得
        result = repository.get_chapter_plot_file_path(chapter_number)

        # Then: 正しいパスが返される
        path_service = get_common_path_service()
        expected_path = project_root / str(path_service.get_plots_dir()) / "章別プロット" / "chapter01.yaml"
        assert result == expected_path

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_parse_yaml_to_chapter_plot_success(
        self,
        repository: YamlChapterPlotRepository,
        sample_chapter_yaml_data: dict,
    ) -> None:
        """YAMLから章別プロット変換成功テスト"""
        # When: YAMLデータから章別プロットを作成
        result = repository._parse_yaml_to_chapter_plot(sample_chapter_yaml_data)

        # Then: 正しい章別プロットが返される
        assert isinstance(result, ChapterPlot)
        assert result.chapter_number == ChapterNumber(1)
        assert result.title == "ch01 出会いと冒険の始まり"
        assert result.summary == "主人公が新しい世界に踏み出す章"
        assert result.central_theme == "新しい世界への適応と成長"
        assert result.viewpoint_management["primary_pov_character"] == "主人公"

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_parse_yaml_to_chapter_plot_missing_fields(
        self,
        repository: YamlChapterPlotRepository,
    ) -> None:
        """YAMLから章別プロット変換(必須フィールド不足)テスト"""
        # Given: 必須フィールドが不足したYAMLデータ
        incomplete_data = {
            "chapter_number": 1,
            "title": "ch01テスト",
            # summary が不足
        }

        # When & Then: 例外が発生
        with pytest.raises(ChapterPlotNotFoundError, match="必須フィールドが不足しています"):
            repository._parse_yaml_to_chapter_plot(incomplete_data)
