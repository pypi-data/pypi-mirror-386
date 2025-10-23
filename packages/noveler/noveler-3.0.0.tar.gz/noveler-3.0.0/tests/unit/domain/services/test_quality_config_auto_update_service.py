"""QualityConfigAutoUpdateServiceのテスト

仕様書: SPEC-DOMAIN-SERVICES
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noveler.domain.services.quality_config_auto_update_service import (
    QualityConfigAutoUpdateService,
    UpdateTrigger,
)
from noveler.domain.value_objects.genre_type import GenreType


class TestQualityConfigAutoUpdateService:
    """品質設定自動更新サービスのテスト"""

    @pytest.fixture
    def service(self):
        """テスト用サービスインスタンス"""
        quality_repo = Mock()
        project_repo = Mock()
        return QualityConfigAutoUpdateService(quality_repo, project_repo)

    @pytest.mark.spec("SPEC-QUALITY_CONFIG_AUTO_UPDATE_SERVICE-INITCONFIGURATION")
    def test_initconfiguration(self, service: object) -> None:
        """プロジェクト開始時に適切な初期設定が生成されることを確認"""
        # Arrange
        project_root = Path("/test/project")
        genre = GenreType("ファンタジー")
        service.project_repo.get_genre.return_value = genre
        service.quality_repo.exists.return_value = False

        # Act
        result = service.initialize_for_project(project_root)

        # Assert
        assert result.success is True
        assert result.trigger == UpdateTrigger.PROJECT_START
        assert "ファンタジー" in result.message
        service.quality_repo.save.assert_called_once()

        # 保存されたデータの検証
        saved_config = service.quality_repo.save.call_args[0][1]
        assert saved_config["basic_style"]["max_hiragana_ratio"] == 0.45

    @pytest.mark.spec("SPEC-QUALITY_CONFIG_AUTO_UPDATE_SERVICE-CONFIGURATION")
    def test_configuration(self, service: object) -> None:
        """既存の設定ファイルがある場合は上書きしないことを確認"""
        # Arrange
        project_root = Path("/test/project")
        service.quality_repo.exists.return_value = True

        # Act
        result = service.initialize_for_project(project_root)

        # Assert
        assert result.success is True
        assert "既に存在" in result.message
        service.quality_repo.save.assert_not_called()

    @pytest.mark.spec("SPEC-QUALITY_CONFIG_AUTO_UPDATE_SERVICE-UNNAMED")
    def test_unnamed(self, service: object) -> None:
        """マスタープロット完成時に設定が調整されることを確認"""
        # Arrange
        project_root = Path("/test/project")
        plot_data = {
            "title": "異世界転生ファンタジー",
            "themes": ["成長", "冒険", "友情"],
            "keywords": ["魔法", "バトル", "ダンジョン"],
        }
        current_config = {
            "basic_style": {"max_hiragana_ratio": 0.40},
            "composition": {"dialog_ratio_range": [0.30, 0.50]},
        }
        service.quality_repo.load.return_value = current_config

        # Act
        result = service.adjust_by_master_plot(project_root, plot_data)

        # Assert
        assert result.success is True
        assert result.trigger == UpdateTrigger.MASTER_PLOT_COMPLETED
        assert "バトル要素" in result.message

        # バトル要素による調整の確認
        saved_config = service.quality_repo.save.call_args[0][1]
        assert saved_config["composition"]["short_sentence_ratio"] == 0.45

    @pytest.mark.spec("SPEC-QUALITY_CONFIG_AUTO_UPDATE_SERVICE-10EPISODES")
    def test_10episodes(self, service: object) -> None:
        """10話ごとに品質設定の見直し提案が生成されることを確認"""
        # Arrange
        project_root = Path("/test/project")
        episode_number = 10
        quality_results = []
        for i in range(1, 11):
            quality_results.append(
                {
                    "episode": i,
                    "scores": {"basic_style": 85 if i % 2 == 0 else 75, "composition": 80 if i % 2 == 0 else 85},
                }
            )

        service.quality_repo.get_recent_results.return_value = quality_results

        # Act
        result = service.suggest_optimization(project_root, episode_number)

        # Assert
        assert result.success is True
        assert result.trigger == UpdateTrigger.PERIODIC_REVIEW
        assert "第10話到達" in result.message
        # スコアが良い場合は提案がない
        assert result.suggestions is None

    @pytest.mark.spec("SPEC-QUALITY_CONFIG_AUTO_UPDATE_SERVICE-QUALITY")
    def test_quality(self, service: object) -> None:
        """品質チェック結果から適切な調整が提案されることを確認"""
        # Arrange
        project_root = Path("/test/project")
        episode_number = 20

        # 文体スコアが低い傾向のデータ
        quality_results = []
        for i in range(1, 21):
            quality_results.append(
                {
                    "episode": i,
                    "scores": {
                        "basic_style": 65,  # 低いスコア
                        "composition": 85,
                        "readability": 80,
                    },
                }
            )

        service.quality_repo.get_recent_results.return_value = quality_results
        current_config = {"basic_style": {"max_hiragana_ratio": 0.40}}
        service.quality_repo.load.return_value = current_config

        # Act
        result = service.suggest_optimization(project_root, episode_number)

        # Assert
        assert result.success is True
        assert result.suggestions is not None
        assert any("ひらがな比率" in s for s in result.suggestions)

    @pytest.mark.spec("SPEC-QUALITY_CONFIG_AUTO_UPDATE_SERVICE-CONFIGURATION")
    def test_configuration_1(self, service: object) -> None:
        """恋愛ジャンルで適切なデフォルト設定が適用されることを確認"""
        # Arrange
        project_root = Path("/test/project")
        genre = GenreType("恋愛")
        service.project_repo.get_genre.return_value = genre
        service.quality_repo.exists.return_value = False

        # Act
        service.initialize_for_project(project_root)

        # Assert
        saved_config = service.quality_repo.save.call_args[0][1]
        assert saved_config["basic_style"]["max_hiragana_ratio"] == 0.40
        assert saved_config["composition"]["dialog_ratio_range"] == [0.35, 0.65]

    @pytest.mark.spec("SPEC-QUALITY_CONFIG_AUTO_UPDATE_SERVICE-ERROR_FILEREADERROR")
    def test_error_filereaderror(self, service: object) -> None:
        """ファイル読み込みエラーが適切に処理されることを確認"""
        # Arrange
        project_root = Path("/test/project")
        service.quality_repo.load.side_effect = Exception("ファイル読み込みエラー")

        # Act
        result = service.adjust_by_master_plot(project_root, {})

        # Assert
        assert result.success is False
        assert "エラー" in result.message

    @pytest.mark.spec("SPEC-QUALITY_CONFIG_AUTO_UPDATE_SERVICE-CREATION")
    def test_creation(self, service: object) -> None:
        """設定更新時にバックアップが作成されることを確認"""
        # Arrange
        project_root = Path("/test/project")
        plot_data = {"title": "テスト"}
        current_config = {"basic_style": {"max_hiragana_ratio": 0.40}}
        service.quality_repo.load.return_value = current_config
        service.quality_repo.exists.return_value = True

        # Act
        with patch("domain.services.quality_config_auto_update_service.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            service.adjust_by_master_plot(project_root, plot_data)

        # Assert
        service.quality_repo.backup.assert_called_once()
        backup_suffix = service.quality_repo.backup.call_args[0][1]
        assert "20240101" in backup_suffix
