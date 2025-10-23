#!/usr/bin/env python3
"""視点情報連動型品質チェックのアプリケーション層テスト

TDD: アプリケーション層の失敗するテストを作成


仕様書: SPEC-UNIT-TEST
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from noveler.application.use_cases.viewpoint_aware_quality_check import ViewpointAwareQualityCheckUseCase
from noveler.infrastructure.persistence.plot_viewpoint_repository import PlotViewpointRepository

# Add parent directory to path
# PathManager統一パス管理システムを使用(事前にパスを設定)
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/を追加
from noveler.infrastructure.utils.path_manager import ensure_imports

ensure_imports()

from noveler.domain.quality.value_objects import QualityScore
from noveler.domain.quality.viewpoint_entities import ComplexityLevel, ViewpointInfo, ViewpointType
class TestViewpointAwareQualityCheckUseCase:
    """視点情報連動型品質チェックユースケースのテスト"""

    @pytest.fixture
    def mock_plot_data(self):
        """テスト用プロットデータ"""
        return {
            "chapter_info": {
                "viewpoint_management": {
                    "complexity_level": "中",
                    "primary_pov_character": "カノン",
                },
            },
            "episode_breakdown": {
                "001": {
                    "viewpoint": "カノン",
                    "viewpoint_label": "カノン",
                    "viewpoint_details": {
                        "consciousness": "カノン",
                        "narrative_focus": "inner_thoughts",
                    },
                },
                "002": {
                    "viewpoint": "律→カノンBody",
                    "viewpoint_label": "律→カノンBody",
                    "viewpoint_details": {
                        "consciousness": "律",
                        "body": "カノン",
                        "narrative_focus": "body_adaptation",
                    },
                },
            },
        }

    @pytest.fixture
    def mock_base_quality_scores(self):
        """テスト用基本品質スコア"""
        return {
            "dialogue_ratio": QualityScore(30.0),
            "narrative_depth": QualityScore(80.0),
            "basic_style": QualityScore(85.0),
            "composition": QualityScore(75.0),
        }

    @pytest.mark.spec("SPEC-APPLICATION_VIEWPOINT_QUALITY-CHECK_QUALITY_WITH_I")
    def test_check_quality_with_introspective_viewpoint(
        self, mock_plot_data: object, mock_base_quality_scores: object
    ) -> None:
        """内省型視点での品質チェック"""

        # モックリポジトリの設定
        plot_repo = Mock()
        plot_repo.get_episode_viewpoint_info.return_value = ViewpointInfo(
            character="カノン",
            viewpoint_type=ViewpointType.SINGLE_INTROSPECTIVE,
            complexity_level=ComplexityLevel.MEDIUM,
            special_conditions=[],
            narrative_focus="inner_thoughts",
        )

        quality_checker = Mock()
        quality_checker.check_quality.return_value = mock_base_quality_scores

        use_case = ViewpointAwareQualityCheckUseCase(
            episode_repository=plot_repo,
            quality_repository=quality_checker,
        )

        # テスト実行
        result = use_case.check_episode_quality(
            project_path=Path("/test"),
            episode_number="001",
            text="これはテスト文章です。",
        )

        # 検証
        assert result is not None
        assert "adjusted_scores" in result
        assert "viewpoint_context" in result
        assert "viewpoint_info" in result

        # 内省型なので会話比率が緩和されているはず
        adjusted_dialogue_score = result["adjusted_scores"]["dialogue_ratio"]
        original_dialogue_score = mock_base_quality_scores["dialogue_ratio"]
        assert adjusted_dialogue_score.value > original_dialogue_score.value

        # 視点コンテキストメッセージが含まれている
        context = result["viewpoint_context"]
        assert "単一視点・内省型" in context
        assert "会話比率は参考値" in context

    @pytest.mark.spec("SPEC-APPLICATION_VIEWPOINT_QUALITY-CHECK_QUALITY_WITH_B")
    def test_check_quality_with_body_swap_viewpoint(
        self, mock_plot_data: object, mock_base_quality_scores: object
    ) -> None:
        """身体交換時の品質チェック"""

        # モックリポジトリの設定
        plot_repo = Mock()
        plot_repo.get_episode_viewpoint_info.return_value = ViewpointInfo(
            character="律→カノンBody",
            viewpoint_type=ViewpointType.BODY_SWAP,
            complexity_level=ComplexityLevel.HIGH,
            special_conditions=["body_swap"],
            narrative_focus="body_adaptation",
        )

        quality_checker = Mock()
        quality_checker.check_quality.return_value = mock_base_quality_scores

        use_case = ViewpointAwareQualityCheckUseCase(
            episode_repository=plot_repo,
            quality_repository=quality_checker,
        )

        # テスト実行
        result = use_case.check_episode_quality(
            project_path=Path("/test"),
            episode_number="002",
            text="これはテスト文章です。",
        )

        # 検証
        assert result is not None

        # 身体交換時なので内面描写が重視され、視点明確さがチェックされる
        context = result["viewpoint_context"]
        assert "身体交換" in context
        assert "内面描写深度を重視" in context
        assert "視点の明確さを特に重視" in context

    @pytest.mark.spec("SPEC-APPLICATION_VIEWPOINT_QUALITY-CHECK_QUALITY_WITHOU")
    def test_check_quality_without_plot_data(self, mock_base_quality_scores: object) -> None:
        """プロットデータがない場合のフォールバック"""

        # プロットデータが見つからない場合
        plot_repo = Mock()
        plot_repo.get_episode_viewpoint_info.return_value = None

        quality_checker = Mock()
        quality_checker.check_quality.return_value = mock_base_quality_scores

        use_case = ViewpointAwareQualityCheckUseCase(
            episode_repository=plot_repo,
            quality_repository=quality_checker,
        )

        # テスト実行
        result = use_case.check_episode_quality(
            project_path=Path("/test"),
            episode_number="999",
            text="これはテスト文章です。",
        )

        # 検証:標準的な品質チェックが実行される
        assert result is not None
        assert result["adjusted_scores"] == mock_base_quality_scores
        assert result["viewpoint_context"] == "📍 視点情報なし - 標準的な品質評価を実行"


class TestPlotViewpointRepository:
    """プロット視点リポジトリのテスト"""

    @pytest.mark.spec("SPEC-APPLICATION_VIEWPOINT_QUALITY-GET_EPISODE_VIEWPOIN")
    def test_get_episode_viewpoint_info_introspective(self) -> None:
        """内省型エピソードの視点情報取得"""

        with tempfile.TemporaryDirectory() as tmpdir, patch(
            "noveler.infrastructure.persistence.plot_viewpoint_repository.create_path_service"
        ) as mock_create_path:
            project_path = Path(tmpdir)

            plots_root = project_path / "20_プロット"
            plot_dir = plots_root / "章別プロット"
            plot_dir.mkdir(parents=True)

            mock_path_service = Mock()
            mock_path_service.get_plots_dir.return_value = plots_root
            mock_create_path.return_value = mock_path_service

            plot_file = plot_dir / "chapter01.yaml"
            plot_data = {
                "episode_breakdown": {
                    "episode001": {
                        "viewpoint": "カノン - 内省重視",
                        "viewpoint_label": "カノン",
                        "viewpoint_details": {
                            "consciousness": "カノン",
                            "narrative_focus": "inner_thoughts",
                        },
                    },
                },
                "chapter_info": {
                    "viewpoint_management": {
                        "complexity_level": "中",
                    },
                },
            }

            with plot_file.open("w", encoding="utf-8") as f:
                yaml.dump(plot_data, f, allow_unicode=True)

            # リポジトリテスト
            repo = PlotViewpointRepository(project_path, enable_backup=False)
            viewpoint_info = repo.get_episode_viewpoint_info("episode001")

            assert viewpoint_info is not None
            assert viewpoint_info.character == "カノン"
            assert viewpoint_info.viewpoint_type == ViewpointType.SINGLE_INTROSPECTIVE
            assert viewpoint_info.complexity_level == ComplexityLevel.MEDIUM
            assert viewpoint_info.narrative_focus == "inner_thoughts"

    @pytest.mark.spec("SPEC-APPLICATION_VIEWPOINT_QUALITY-GET_EPISODE_VIEWPOIN")
    def test_get_episode_viewpoint_info_body_swap(self) -> None:
        """身体交換エピソードの視点情報取得"""

        with tempfile.TemporaryDirectory() as tmpdir, patch(
            "noveler.infrastructure.persistence.plot_viewpoint_repository.create_path_service"
        ) as mock_create_path:
            project_path = Path(tmpdir)

            plots_root = project_path / "20_プロット"
            plot_dir = plots_root / "章別プロット"
            plot_dir.mkdir(parents=True)

            mock_path_service = Mock()
            mock_path_service.get_plots_dir.return_value = plots_root
            mock_create_path.return_value = mock_path_service

            plot_file = plot_dir / "chapter02.yaml"
            plot_data = {
                "episode_breakdown": {
                    "episode010": {
                        "viewpoint": "律→カノンBody - 身体交換",
                        "viewpoint_label": "律→カノンBody",
                        "viewpoint_details": {
                            "consciousness": "律",
                            "body": "カノン",
                            "narrative_focus": "body_adaptation",
                            "body_swap_details": {
                                "swap_type": "完全",
                            },
                        },
                    },
                },
                "chapter_info": {
                    "viewpoint_management": {
                        "complexity_level": "高",
                        "special_conditions": ["body_swap"],
                    },
                },
            }

            with plot_file.open("w", encoding="utf-8") as f:
                yaml.dump(plot_data, f, allow_unicode=True)

            # リポジトリテスト
            repo = PlotViewpointRepository(project_path, enable_backup=False)
            viewpoint_info = repo.get_episode_viewpoint_info("episode010")

            assert viewpoint_info is not None
            assert viewpoint_info.character == "律→カノンBody"
            assert viewpoint_info.viewpoint_type == ViewpointType.BODY_SWAP
            assert viewpoint_info.complexity_level == ComplexityLevel.HIGH
            assert "body_swap" in viewpoint_info.special_conditions
            assert viewpoint_info.narrative_focus == "body_adaptation"

    @pytest.mark.spec("SPEC-APPLICATION_VIEWPOINT_QUALITY-GET_EPISODE_VIEWPOIN")
    def test_get_episode_viewpoint_info_not_found(self) -> None:
        """存在しないエピソードの視点情報取得"""

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            repo = PlotViewpointRepository(project_path, enable_backup=False)
            viewpoint_info = repo.get_episode_viewpoint_info("episode999")

            assert viewpoint_info is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
