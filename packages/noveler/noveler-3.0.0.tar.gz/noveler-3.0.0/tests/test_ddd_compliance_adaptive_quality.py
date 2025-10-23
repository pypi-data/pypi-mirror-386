"""DDD準拠テスト: 適応的品質評価システム

SPEC-YAML-001: DDD準拠統合基盤拡張
AdaptiveQualityEvaluationUseCaseのDDD準拠性テスト
"""

from unittest.mock import Mock

import pytest

from noveler.application.use_cases.adaptive_quality_evaluation_use_case import AdaptiveQualityEvaluator
from noveler.domain.interfaces.settings_repository import ISettingsRepositoryFactory
from noveler.domain.value_objects.quality_standards import Genre


@pytest.mark.spec("SPEC-YAML-001")
class TestAdaptiveQualityDDDCompliance:
    """適応的品質評価システムのDDD準拠性テスト"""

    @pytest.mark.spec("SPEC-DDD_COMPLIANCE_ADAPTIVE_QUALITY-DDD_COMPLIANT_INITIA")
    def test_ddd_compliant_initialization(self):
        """DDD準拠のコンストラクタ初期化テスト"""
        # モックファクトリーの作成
        mock_factory = Mock(spec=ISettingsRepositoryFactory)
        mock_progress_repo = Mock()
        mock_settings_repo = Mock()

        mock_factory.create_writer_progress_repository.return_value = mock_progress_repo
        mock_factory.create_project_settings_repository.return_value = mock_settings_repo

        # DDD準拠初期化
        evaluator = AdaptiveQualityEvaluator(project_root="/test/project", settings_factory=mock_factory)

        # 依存性注入確認
        assert evaluator.progress_repo == mock_progress_repo
        assert evaluator.settings_repo == mock_settings_repo
        mock_factory.create_writer_progress_repository.assert_called_once()
        mock_factory.create_project_settings_repository.assert_called_once()

    @pytest.mark.spec("SPEC-DDD_COMPLIANCE_ADAPTIVE_QUALITY-NO_DIRECT_INFRASTRUC")
    def test_no_direct_infrastructure_imports(self):
        """インフラ層直接インポートの排除テスト"""
        # ソースコードの検査
        import inspect

        import noveler.application.use_cases.adaptive_quality_evaluation_use_case as module

        source = inspect.getsource(module)

        # インフラ層直接インポートがないことを確認
        forbidden_imports = [
            "from noveler.infrastructure.yaml_project_settings_repository",
            "from noveler.infrastructure.yaml_writer_progress_repository",
        ]

        for forbidden in forbidden_imports:
            assert forbidden not in source, f"DDD違反: {forbidden} が見つかりました"

    @pytest.mark.spec("SPEC-DDD_COMPLIANCE_ADAPTIVE_QUALITY-INTERFACE_ONLY_DEPEN")
    def test_interface_only_dependencies(self):
        """インターフェースのみに依存していることのテスト"""
        # モジュールのインポート確認
        import inspect

        import noveler.application.use_cases.adaptive_quality_evaluation_use_case as module

        source = inspect.getsource(module)

        # インターフェースインポートの確認（ISettingsRepositoryFactoryのみ直接インポート）
        required_interface_imports = [
            "ISettingsRepositoryFactory",
        ]

        for interface in required_interface_imports:
            assert interface in source, f"必要インターフェース未インポート: {interface}"

    @pytest.mark.spec("SPEC-DDD_COMPLIANCE_ADAPTIVE_QUALITY-DEPENDENCY_INJECTION")
    def test_dependency_injection_pattern(self):
        """依存性注入パターンの実装テスト"""
        # モックリポジトリの作成
        mock_factory = Mock(spec=ISettingsRepositoryFactory)
        mock_progress_repo = Mock()
        mock_settings_repo = Mock()

        # モック設定
        mock_factory.create_writer_progress_repository.return_value = mock_progress_repo
        mock_factory.create_project_settings_repository.return_value = mock_settings_repo

        mock_progress_repo.get_writer_progress.return_value = {
            "completed_episodes": 5,
            "quality_history": [{"quality_score": 85.0}],
            "recent_average_quality": 85.0,
        }
        mock_settings_repo.get_project_genre.return_value = Genre.FANTASY

        # 依存性注入での実行
        evaluator = AdaptiveQualityEvaluator(project_root="/test/project", settings_factory=mock_factory)

        # メソッド実行テスト
        quality_scores = {"overall": 80.0, "readability": 75.0, "composition": 85.0}

        result = evaluator.evaluate_with_adaptive_standards(quality_scores)

        # DDD準拠の動作確認 - 返される結果構造をチェック
        assert "writer_level" in result  # 基本的な結果が含まれることを確認
        assert "genre" in result
        assert "overall_score" in result
        mock_progress_repo.get_writer_progress.assert_called_once()
        mock_settings_repo.get_project_genre.assert_called_once()

    @pytest.mark.spec("SPEC-DDD_COMPLIANCE_ADAPTIVE_QUALITY-BACKWARDS_COMPATIBIL")
    def test_backwards_compatibility_fallback(self):
        """後方互換性フォールバック機能テスト"""
        # ファクトリー無しでの初期化テスト
        try:
            evaluator = AdaptiveQualityEvaluator(project_root="/test/project")
            # エラーなく初期化できることを確認（内部でファクトリー自動作成）
            assert evaluator.project_root == "/test/project"
        except ImportError:
            # インフラ層が利用できない環境での適切なエラー処理
            pass


if __name__ == "__main__":
    pytest.main([__file__])
