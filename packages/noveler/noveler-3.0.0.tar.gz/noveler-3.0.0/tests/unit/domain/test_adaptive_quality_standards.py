"""適応的品質基準システムのテストケース

TDD原則に従い、各ドメインエンティティとサービスをテスト


仕様書: SPEC-UNIT-TEST
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

# プロジェクトルートへのパスを追加
# PathManager統一パス管理システムを使用(事前にパスを設定)
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/を追加
from noveler.infrastructure.utils.path_manager import ensure_imports

ensure_imports()

import pytest

from noveler.application.use_cases.adaptive_quality_evaluation_use_case import AdaptiveQualityEvaluator
from noveler.domain.services.quality_standard_factory import QualityStandardFactory
from noveler.domain.services.writer_level_service import WriterLevelService
from noveler.domain.value_objects.quality_standards import Genre, QualityThreshold, WriterLevel
from noveler.infrastructure.yaml_project_settings_repository import YamlProjectSettingsRepository
from noveler.infrastructure.yaml_writer_progress_repository import YamlWriterProgressRepository
from noveler.presentation.shared.shared_utilities import get_common_path_service

# B30準拠: テストでは直接Pathを使用


class TestQualityThreshold(unittest.TestCase):
    """品質閾値のテスト"""

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-VALID_THRESHOLD")
    def test_valid_threshold(self) -> None:
        """有効な閾値の作成"""
        get_common_path_service()
        threshold = QualityThreshold(60, 70, 80)
        assert threshold.minimum_score == 60
        assert threshold.target_score == 70
        assert threshold.excellent_score == 80

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-INVALID_THRESHOLD_OR")
    def test_invalid_threshold_order(self) -> None:
        """無効な閾値順序でエラー"""
        with pytest.raises(
            ValueError, match="スコアは0-100の範囲で、minimum <= target <= excellentである必要があります"
        ):
            QualityThreshold(80, 70, 60)  # 逆順

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-INVALID_THRESHOLD_RA")
    def test_invalid_threshold_range(self) -> None:
        """無効な範囲でエラー"""
        with pytest.raises(
            ValueError, match="スコアは0-100の範囲で、minimum <= target <= excellentである必要があります"
        ):
            QualityThreshold(-10, 50, 110)  # 範囲外


class TestWriterLevelService(unittest.TestCase):
    """執筆レベル判定サービスのテスト"""

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-BEGINNER_LEVEL_BY_EP")
    def test_beginner_level_by_episode_count(self) -> None:
        """初心者レベル判定(エピソード数基準)"""
        level = WriterLevelService.determine_level(3, 70.0)
        assert level == WriterLevel.BEGINNER

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-INTERMEDIATE_LEVEL_B")
    def test_intermediate_level_by_episode_count(self) -> None:
        """中級者レベル判定(エピソード数基準)"""
        level = WriterLevelService.determine_level(15, 70.0)
        assert level == WriterLevel.INTERMEDIATE

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-ADVANCED_LEVEL_BY_EP")
    def test_advanced_level_by_episode_count(self) -> None:
        """上級者レベル判定(エピソード数基準)"""
        level = WriterLevelService.determine_level(35, 70.0)
        assert level == WriterLevel.ADVANCED

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-EXPERT_LEVEL_BY_EPIS")
    def test_expert_level_by_episode_count(self) -> None:
        """エキスパートレベル判定(エピソード数基準)"""
        level = WriterLevelService.determine_level(60, 70.0)
        assert level == WriterLevel.EXPERT

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-LEVEL_UPGRADE_BY_HIG")
    def test_level_upgrade_by_high_score(self) -> None:
        """高スコアによるレベルアップ"""
        # 初心者だが高スコア → 中級者扱い
        level = WriterLevelService.determine_level(3, 90.0)
        assert level == WriterLevel.INTERMEDIATE

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-LEVEL_DOWNGRADE_BY_L")
    def test_level_downgrade_by_low_score(self) -> None:
        """低スコアによるレベルダウン"""
        # 中級者だが低スコア → 初心者扱い
        level = WriterLevelService.determine_level(15, 55.0)
        assert level == WriterLevel.BEGINNER

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-LEVEL_DESCRIPTIONS")
    def test_level_descriptions(self) -> None:
        """レベル説明の取得"""
        desc = WriterLevelService.get_level_description(WriterLevel.BEGINNER)
        assert "初心者" in desc

        desc = WriterLevelService.get_level_description(WriterLevel.EXPERT)
        assert "エキスパート" in desc

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-ENCOURAGEMENT_MESSAG")
    def test_encouragement_messages(self) -> None:
        """励ましメッセージの生成"""
        msg = WriterLevelService.get_encouragement_message(WriterLevel.BEGINNER, 65.0)
        assert "素晴らしい進歩" in msg

        msg = WriterLevelService.get_encouragement_message(WriterLevel.BEGINNER, 50.0)
        assert "少しずつ改善" in msg

        msg = WriterLevelService.get_encouragement_message(WriterLevel.EXPERT, 90.0)
        assert "最高水準" in msg


class TestQualityStandardFactory(unittest.TestCase):
    """品質基準ファクトリーのテスト"""

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-CREATE_BEGINNER_STAN")
    def test_create_beginner_standard(self) -> None:
        """初心者向け基準の生成"""
        standard = QualityStandardFactory.create_standard(
            WriterLevel.BEGINNER,
            Genre.LIGHT_NOVEL,
        )

        assert standard.writer_level == WriterLevel.BEGINNER
        assert standard.genre == Genre.LIGHT_NOVEL

        # 初心者向けの基準値確認
        overall_threshold = standard.get_threshold("overall")
        assert overall_threshold.minimum_score == 50
        assert overall_threshold.target_score == 60
        assert overall_threshold.excellent_score == 70

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-CREATE_EXPERT_STANDA")
    def test_create_expert_standard(self) -> None:
        """エキスパート向け基準の生成"""
        standard = QualityStandardFactory.create_standard(
            WriterLevel.EXPERT,
            Genre.LITERARY,
        )

        # エキスパート向けの高い基準値
        overall_threshold = standard.get_threshold("overall")
        assert overall_threshold.minimum_score == 75
        assert overall_threshold.target_score == 85
        assert overall_threshold.excellent_score == 95

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-GENRE_ADJUSTMENTS_LI")
    def test_genre_adjustments_light_novel(self) -> None:
        """ライトノベル向けの調整"""
        standard = QualityStandardFactory.create_standard(
            WriterLevel.INTERMEDIATE,
            Genre.LIGHT_NOVEL,
        )

        # ライトノベルは読みやすさ重視
        weight = standard.get_weight("readability")
        assert weight > 1.0

        # 会話も重視
        weight = standard.get_weight("dialogue")
        assert weight > 1.0

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-GENRE_ADJUSTMENTS_LI")
    def test_genre_adjustments_literary(self) -> None:
        """純文学向けの調整"""
        standard = QualityStandardFactory.create_standard(
            WriterLevel.INTERMEDIATE,
            Genre.LITERARY,
        )

        # 純文学は文体重視
        weight = standard.get_weight("style")
        assert weight > 1.0

        # 内面描写も重視
        weight = standard.get_weight("narrative_depth")
        assert weight > 1.0


class TestAdaptiveQualityEvaluator(unittest.TestCase):
    """適応的品質評価システムの統合テスト"""

    def setUp(self) -> None:
        """テスト用プロジェクトの準備"""
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir) / "test_project"
        self.project_root.mkdir(parents=True)

        # 必要なディレクトリ構造を作成
        path_service = get_common_path_service()
        (self.project_root / str(path_service.get_manuscript_dir())).mkdir(parents=True, exist_ok=True)
        (self.project_root / str(path_service.get_management_dir())).mkdir(parents=True, exist_ok=True)
        (self.project_root / str(path_service.get_plots_dir())).mkdir(parents=True)

        # テスト用データを配置
        self._setup_test_data()

    def tearDown(self) -> None:
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.test_dir)

    def _setup_test_data(self) -> None:
        """テスト用データのセットアップ"""
        # プロジェクト設定
        settings = {
            "title": "テスト小説",
            "genre": "ファンタジー",
        }
        with Path(self.project_root / "プロジェクト設定.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(settings, f, allow_unicode=True)

        # 話数管理(5話完了)
        episode_data = {
            "episodes": [
                {"episode": 1, "status": "completed"},
                {"episode": 2, "status": "completed"},
                {"episode": 3, "status": "completed"},
                {"episode": 4, "status": "completed"},
                {"episode": 5, "status": "completed"},
            ],
        }
        path_service = get_common_path_service()
        management_dir = self.project_root / str(path_service.get_management_dir())
        with Path(management_dir / "話数管理.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(episode_data, f, allow_unicode=True)

        # 品質記録(平均スコア75)
        quality_data = {
            "quality_records": [
                {"episode": "第001話", "overall_score": 72},
                {"episode": "第002話", "overall_score": 75},
                {"episode": "第003話", "overall_score": 78},
                {"episode": "第004話", "overall_score": 74},
                {"episode": "第005話", "overall_score": 76},
            ],
        }
        with Path(management_dir / "品質記録.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(quality_data, f, allow_unicode=True)

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-ADAPTIVE_EVALUATION_")
    def test_adaptive_evaluation_beginner(self) -> None:
        """初心者の適応的評価"""
        evaluator = AdaptiveQualityEvaluator(str(self.project_root))

        # 品質スコアのサンプル
        scores = {
            "style": 55,
            "composition": 60,
            "readability": 58,
            "dialogue": 65,
            "narrative_depth": 50,
        }

        result = evaluator.evaluate_with_adaptive_standards(scores)

        # 初心者として判定されるはず(5話完了)
        assert result["writer_level"] == "beginner"
        assert result["genre"] == "fantasy"

        # 励ましメッセージが含まれる
        assert "encouragement" in result
        assert result["encouragement"] is not None

        # 改善提案が含まれる
        assert "improvement_suggestions" in result
        assert len(result["improvement_suggestions"]) > 0

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-SCORE_ADJUSTMENT")
    def test_score_adjustment(self) -> None:
        """スコア調整のテスト"""
        evaluator = AdaptiveQualityEvaluator(str(self.project_root))

        scores = {
            "readability": 60,
            "dialogue": 50,
        }

        result = evaluator.evaluate_with_adaptive_standards(scores)

        # 調整後スコアが存在
        assert "adjusted_scores" in result
        assert "readability" in result["adjusted_scores"]

        # ファンタジージャンルの重み調整が適用されているか
        # (詳細な値は実装に依存)
        assert result["overall_score"] is not None


class TestYamlRepositories(unittest.TestCase):
    """YAMLリポジトリのテスト"""

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        path_service = get_common_path_service()
        (self.project_root / str(path_service.get_management_dir())).mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir)

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-WRITER_PROGRESS_REPO")
    def test_writer_progress_repository(self) -> None:
        """執筆進捗リポジトリのテスト"""
        repo = YamlWriterProgressRepository(str(self.project_root))

        # ファイルが存在しない場合
        count = repo.get_completed_episodes_count("test")
        assert count == 0

        score = repo.get_average_quality_score("test")
        assert score == 70.0  # デフォルト値

    @pytest.mark.spec("SPEC-ADAPTIVE_QUALITY_STANDARDS-PROJECT_SETTINGS_REP")
    def test_project_settings_repository(self) -> None:
        """プロジェクト設定リポジトリのテスト"""
        repo = YamlProjectSettingsRepository()

        # プロジェクト設定作成
        settings = {"genre": "ミステリー"}
        with Path(self.project_root / "プロジェクト設定.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(settings, f, allow_unicode=True)

        genre = repo.get_genre(str(self.project_root))
        assert genre == "ミステリー"


if __name__ == "__main__":
    unittest.main()
