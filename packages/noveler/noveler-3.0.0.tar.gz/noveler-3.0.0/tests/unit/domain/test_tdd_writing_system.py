"""TDD Test-First Novel Writing System
テスト駆動開発による小説執筆システム


仕様書: SPEC-UNIT-TEST
"""

import sys
import tempfile
from pathlib import Path

import pytest
import yaml

from noveler.domain.writing.entities import AutoEpisodeCreator, ContentGenerator, EpisodeManager, ProgressTracker

# Add parent directory to path
# PathManager統一パス管理システムを使用(事前にパスを設定)
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/を追加
from noveler.infrastructure.utils.path_manager import ensure_imports
from noveler.presentation.shared.shared_utilities import get_common_path_service

ensure_imports()


class TestEpisodeAutoCreation:
    """TDD: エピソード自動作成機能のテスト"""

    @pytest.mark.spec("SPEC-TDD_WRITING_SYSTEM-SHOULD_FIND_NEXT_UNW")
    def test_should_find_next_unwritten_episode_from_plot(self) -> None:
        """未執筆の次のエピソードをプロットから見つけられるべき"""
        # RED: 失敗するテストを先に書く
        path_service = get_common_path_service()
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            plot_dir = project_root / str(path_service.get_plots_dir()) / "章別プロット"
            plot_dir.mkdir(parents=True)

            # プロットファイル作成
            plot_data = {
                "episodes": [
                    {"episode_number": "001", "title": "第1話 始まり", "status": "未執筆"},
                    {"episode_number": "002", "title": "第2話 出会い", "status": "未執筆"},
                ],
            }
            plot_file = plot_dir / "chapter01.yaml"
            with Path(plot_file).open("w", encoding="utf-8") as f:
                yaml.dump(plot_data, f, allow_unicode=True)

            # この時点では関数が存在しないのでテストは失敗する

            manager = EpisodeManager(project_root)

            next_episode = manager.find_next_unwritten_episode()
            assert next_episode == "001"

    @pytest.mark.spec("SPEC-TDD_WRITING_SYSTEM-SHOULD_EXTRACT_TITLE")
    def test_should_extract_title_from_plot_data(self) -> None:
        """プロットデータからタイトルを抽出できるべき"""
        # RED: 失敗テスト

        plot_info = {
            "title": "第1話 冒険の始まり",
            "summary": "テストサマリー",
        }

        manager = EpisodeManager(Path("/tmp"))  # noqa: S108
        title = manager.extract_title_from_plot(plot_info["title"])
        assert title == "冒険の始まり"

    @pytest.mark.spec("SPEC-TDD_WRITING_SYSTEM-SHOULD_CREATE_EPISOD")
    def test_should_create_episode_with_plot_info(self) -> None:
        """プロット情報を使ってエピソードを作成できるべき"""
        # RED: 失敗テスト
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            plot_info = {
                "episode_number": "001",
                "title": "第1話 始まりの街",
                "summary": "主人公が冒険を始める",
                "plot_points": ["日常描写", "事件発生"],
                "character_focus": ["主人公"],
                "word_count_target": 3000,
            }

            manager = EpisodeManager(project_root)

            result = manager.create_episode_from_plot(plot_info)

            assert result.success is True
            assert result.file_path.exists()
            assert "始まりの街" in result.file_path.name

    @pytest.mark.spec("SPEC-TDD_WRITING_SYSTEM-SHOULD_UPDATE_PLOT_S")
    def test_should_update_plot_status_after_creation(self) -> None:
        """エピソード作成後にプロットステータスを更新すべき"""
        # RED: 失敗テスト
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            path_service = get_common_path_service()
            plot_dir = project_root / str(path_service.get_plots_dir()) / "章別プロット"
            plot_dir.mkdir(parents=True)

            plot_data = {
                "episodes": [
                    {"episode_number": "001", "title": "第1話 始まり", "status": "未執筆"},
                ],
            }
            plot_file = plot_dir / "chapter01.yaml"
            with Path(plot_file).open("w", encoding="utf-8") as f:
                yaml.dump(plot_data, f, allow_unicode=True)

            manager = EpisodeManager(project_root)

            manager.update_plot_status("001", "執筆中")

            # ファイルを再読み込みしてステータス確認
            with Path(plot_file).open(encoding="utf-8") as f:
                updated_data = yaml.safe_load(f)

            assert updated_data["episodes"][0]["status"] == "執筆中"


class TestEpisodeContentGeneration:
    """TDD: エピソード内容生成のテスト"""

    @pytest.mark.spec("SPEC-TDD_WRITING_SYSTEM-SHOULD_GENERATE_CONT")
    def test_should_generate_content_with_plot_structure(self) -> None:
        """プロット構造に基づいてコンテンツを生成すべき"""
        # RED: 失敗テスト

        plot_info = {
            "title": "冒険の始まり",
            "episode_number": "001",
            "summary": "主人公が旅立つ",
            "plot_points": ["平穏な日常", "事件の発生", "決意の瞬間"],
            "character_focus": ["主人公", "村長"],
            "word_count_target": 3000,
        }

        generator = ContentGenerator()
        content = generator.generate_from_plot(plot_info)

        assert "# 第001話 冒険の始まり" in content
        assert "**目標文字数:** 3000文字" in content
        assert "平穏な日常" in content
        assert "主人公" in content

    @pytest.mark.spec("SPEC-TDD_WRITING_SYSTEM-SHOULD_CALCULATE_SEC")
    def test_should_calculate_section_word_targets(self) -> None:
        """セクション別の目標文字数を計算すべき"""
        # RED: 失敗テスト

        generator = ContentGenerator()
        targets = generator.calculate_section_targets(3000)

        assert targets["introduction"] == 750  # 25%
        assert targets["development"] == 1500  # 50%
        assert targets["climax"] == 600  # 20%
        assert targets["conclusion"] == 150  # 5%

    @pytest.mark.spec("SPEC-TDD_WRITING_SYSTEM-SHOULD_INCLUDE_CHARA")
    def test_should_include_character_focus_hints(self) -> None:
        """フォーカスキャラクターの描写ヒントを含むべき"""
        # RED: 失敗テスト

        plot_info = {
            "character_focus": ["主人公", "魔法使いエルフ", "ドラゴン"],
        }

        generator = ContentGenerator()
        content = generator.generate_character_hints(plot_info)

        assert "主人公の描写を重視" in content
        assert "魔法使いエルフの描写を重視" in content
        assert "ドラゴンの描写を重視" in content


class TestWritingProgressTracking:
    """TDD: 執筆進捗追跡のテスト"""

    @pytest.mark.spec("SPEC-TDD_WRITING_SYSTEM-SHOULD_CALCULATE_WRI")
    def test_should_calculate_writing_progress(self) -> None:
        """執筆進捗を正確に計算すべき"""
        # RED: 失敗テスト

        plot_episodes = [
            {"episode_number": "001", "status": "未執筆"},
            {"episode_number": "002", "status": "執筆中"},
            {"episode_number": "003", "status": "完了"},
        ]

        written_files = ["001", "003"]  # 001は執筆中、003は完了

        tracker = ProgressTracker()
        progress = tracker.calculate_progress(plot_episodes, written_files)

        assert progress.total_episodes == 3
        assert progress.written_episodes == 2
        assert progress.completion_rate == 66.7

    @pytest.mark.spec("SPEC-TDD_WRITING_SYSTEM-SHOULD_IDENTIFY_NEXT")
    def test_should_identify_next_episode_to_write(self) -> None:
        """次に執筆すべきエピソードを特定すべき"""
        # RED: 失敗テスト

        plot_episodes = [
            {"episode_number": "001", "status": "完了"},
            {"episode_number": "002", "status": "未執筆"},
            {"episode_number": "003", "status": "未執筆"},
        ]

        written_files = ["001"]

        tracker = ProgressTracker()
        next_episode = tracker.find_next_episode(plot_episodes, written_files)

        assert next_episode == "002"

    @pytest.mark.spec("SPEC-TDD_WRITING_SYSTEM-SHOULD_ESTIMATE_WORD")
    def test_should_estimate_word_count_accurately(self) -> None:
        """文字数を正確に推定すべき"""
        # RED: 失敗テスト

        sample_content = """
        # 第001話 テスト

        これはテスト用の小説本文です。

        ## 導入部
        主人公が登場します。

        **執筆メモ:**
        - これはメタ情報
        """

        tracker = ProgressTracker()
        word_count = tracker.estimate_word_count(sample_content)

        # メタ情報を除外した実際の小説部分のみカウント
        expected_count = len("これはテスト用の小説本文です。主人公が登場します。")
        assert word_count == expected_count


class TestIntegrationWritingWorkflow:
    """TDD: 統合執筆ワークフローのテスト"""

    @pytest.mark.spec("SPEC-TDD_WRITING_SYSTEM-COMPLETE_AUTO_EPISOD")
    def test_complete_auto_episode_creation_workflow(self) -> None:
        """完全自動エピソード作成ワークフローのテスト"""
        # RED: 失敗テスト(統合テスト)
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # プロット設定
            self._setup_plot_data(project_root)

            creator = AutoEpisodeCreator(project_root)

            # 自動作成実行
            result = creator.create_next_episode()

            assert result.success is True
            assert result.episode_number == "001"
            assert result.title == "冒険の始まり"
            assert result.file_path.exists()

            # プロットステータスが更新されているか確認
            plot_status = creator.get_plot_status("001")
            assert plot_status == "執筆中"

            # 執筆記録が作成されているか確認
            assert result.writing_record_created is True

    def _setup_plot_data(self, project_root: object) -> None:
        """テスト用プロットデータ設定"""
        path_service = get_common_path_service()
        plot_dir = project_root / str(path_service.get_plots_dir()) / "章別プロット"
        plot_dir.mkdir(parents=True)

        plot_data = {
            "chapter_info": {
                "chapter_number": 1,
                "chapter_title": "ch01 序章",
            },
            "episodes": [
                {
                    "episode_number": "001",
                    "title": "第1話 冒険の始まり",
                    "summary": "主人公が旅立つ決意を固める",
                    "plot_points": ["平和な村", "不穏な兆し", "旅立ちの決意"],
                    "character_focus": ["主人公", "村長"],
                    "word_count_target": 3000,
                    "status": "未執筆",
                },
            ],
        }

        with Path(plot_dir / "chapter01.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(plot_data, f, allow_unicode=True)


# 次はGREEN段階:最小実装を行う
# テストが通る最小限のコードを実装する
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
