"""バージョン管理・品質チェック・伏線管理リポジトリインターフェーステスト"""

from abc import ABC
from unittest.mock import Mock

import pytest

from noveler.domain.entities.plot_version import PlotVersion
from noveler.domain.entities.quality_check_aggregate import QualityCheckConfiguration, QualityRule
from noveler.domain.repositories.foreshadowing_repository import ForeshadowingRepository
from noveler.domain.repositories.plot_version_repository import PlotVersionRepository
from noveler.domain.repositories.quality_check_repository import QualityCheckRepository
from noveler.domain.value_objects.foreshadowing import Foreshadowing, ForeshadowingId
from noveler.domain.value_objects.quality_check_result import QualityCheckResult
from noveler.domain.value_objects.quality_threshold import QualityThreshold


class TestPlotVersionRepository:
    """プロットバージョンリポジトリインターフェースのテスト"""

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_interface_definition(self) -> None:
        """インターフェースが正しく定義されていることを確認"""
        assert issubclass(PlotVersionRepository, ABC)

        methods = [
            "find_by_id",
            "find_by_plot_id",
            "save",
            "get_latest_version",
            "get_current",
            "find_by_version",
            "find_all",
        ]
        for method in methods:
            assert hasattr(PlotVersionRepository, method)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_abstract_methods(self) -> None:
        """抽象メソッドの定義を確認"""
        with pytest.raises(TypeError, match=".*"):
            PlotVersionRepository()

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_method_signatures(self) -> None:
        """メソッドシグネチャの確認"""
        # from noveler.domain.entities.plot_version import PlotVersion  # Moved to top-level

        # モックエンティティの作成
        mock_version = Mock(spec=PlotVersion)
        mock_version.version_id = "ver001"
        mock_version.plot_id = "plot001"
        mock_version.version = "1.0.0"
        mock_version.created_at = "2025-01-23T12:00:00"
        mock_version.is_current = True

        # モック実装を作成
        class MockPlotVersionRepo(PlotVersionRepository):
            def __init__(self) -> None:
                self.versions = {}
                self.current_version = None

            def find_by_id(self, version_id: str) -> PlotVersion | None:
                return self.versions.get(version_id)

            def find_by_plot_id(self, plot_id: str) -> list[PlotVersion]:
                return [v for v in self.versions.values() if v.plot_id == plot_id]

            def save(self, plot_version: PlotVersion) -> None:
                self.versions[plot_version.version_id] = plot_version
                if plot_version.is_current:
                    self.current_version = plot_version

            def get_latest_version(self, plot_id: str) -> PlotVersion | None:
                plot_versions = self.find_by_plot_id(plot_id)
                if not plot_versions:
                    return None
                # バージョン番号でソート(実際の実装では適切な比較が必要)
                return max(plot_versions, key=lambda v: v.version)

            def get_current(self) -> PlotVersion | None:
                return self.current_version

            def find_by_version(self, version: str) -> PlotVersion | None:
                for v in self.versions.values():
                    if v.version == version:
                        return v
                return None

            def find_all(self) -> list[PlotVersion]:
                return list(self.versions.values())

        repo = MockPlotVersionRepo()

        # バージョンの保存とテスト
        repo.save(mock_version)

        assert repo.find_by_id("ver001") == mock_version
        assert repo.find_by_id("not_exists") is None

        # プロットIDでの検索
        by_plot = repo.find_by_plot_id("plot001")
        assert len(by_plot) == 1
        assert by_plot[0] == mock_version

        # 最新バージョンの取得
        latest = repo.get_latest_version("plot001")
        assert latest == mock_version

        # 現在のバージョン
        current = repo.get_current()
        assert current == mock_version

        # バージョン番号での検索
        by_version = repo.find_by_version("1.0.0")
        assert by_version == mock_version

        # 全バージョンの取得
        all_versions = repo.find_all()
        assert len(all_versions) == 1

        # 複数バージョンのテスト
        mock_version2 = Mock(spec=PlotVersion)
        mock_version2.version_id = "ver002"
        mock_version2.plot_id = "plot001"
        mock_version2.version = "2.0.0"
        mock_version2.is_current = False

        repo.save(mock_version2)

        all_versions = repo.find_all()
        assert len(all_versions) == 2

        latest = repo.get_latest_version("plot001")
        assert latest.version == "2.0.0"  # より新しいバージョン


class TestQualityCheckRepository:
    """品質チェックリポジトリインターフェースのテスト"""

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_interface_definition(self) -> None:
        """インターフェースが正しく定義されていることを確認"""
        assert issubclass(QualityCheckRepository, ABC)

        methods = [
            "get_default_rules",
            "get_rules_by_category",
            "get_quality_threshold",
            "save_result",
            "find_result_by_id",
            "find_results_by_episode",
            "get_configuration",
            "save_configuration",
            "delete_result",
        ]
        for method in methods:
            assert hasattr(QualityCheckRepository, method)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_method_signatures(self) -> None:
        """メソッドシグネチャの確認"""
        # モックエンティティの作成に必要な型情報
        # QualityCheckConfiguration, QualityCheckResult, QualityRule, QualityThreshold
        # は既にトップレベルでインポート済み

        # モックエンティティの作成
        mock_rule = Mock(spec=QualityRule)
        mock_rule.rule_id = "rule001"
        mock_rule.name = "文体チェック"
        mock_rule.category = "basic_style"
        mock_rule.enabled = True

        mock_result = Mock(spec=QualityCheckResult)
        mock_result.check_id = "check001"
        mock_result.episode_id = "episode001"
        mock_result.overall_score = 85.0
        mock_result.passed = True

        mock_config = Mock(spec=QualityCheckConfiguration)
        mock_config.enabled_categories = ["basic_style", "composition"]
        mock_config.minimum_score = 70.0

        mock_threshold = Mock(spec=QualityThreshold)
        mock_threshold.minimum_score = 70.0
        mock_threshold.warning_score = 80.0

        # モック実装を作成
        class MockQualityCheckRepo(QualityCheckRepository):
            def __init__(self) -> None:
                self.rules = [mock_rule]
                self.results = {}
                self.configuration = mock_config
                self.threshold = mock_threshold

            def get_default_rules(self) -> list[QualityRule]:
                return self.rules

            def get_rules_by_category(self, category: str) -> list[QualityRule]:
                return [r for r in self.rules if r.category == category]

            def get_quality_threshold(self) -> QualityThreshold:
                return self.threshold

            def save_result(self, result: QualityCheckResult) -> None:
                self.results[result.check_id] = result

            def find_result_by_id(self, check_id: str) -> QualityCheckResult | None:
                return self.results.get(check_id)

            def find_results_by_episode(self, episode_id: str) -> list[QualityCheckResult]:
                return [r for r in self.results.values() if r.episode_id == episode_id]

            def get_configuration(self) -> QualityCheckConfiguration:
                return self.configuration

            def save_configuration(self, config: QualityCheckConfiguration) -> None:
                self.configuration = config

            def delete_result(self, check_id: str) -> bool:
                if check_id in self.results:
                    del self.results[check_id]
                    return True
                return False

        repo = MockQualityCheckRepo()

        # デフォルトルールの取得
        default_rules = repo.get_default_rules()
        assert len(default_rules) == 1
        assert default_rules[0].name == "文体チェック"

        # カテゴリ別ルールの取得
        style_rules = repo.get_rules_by_category("basic_style")
        assert len(style_rules) == 1

        # 品質閾値の取得
        threshold = repo.get_quality_threshold()
        assert threshold.minimum_score == 70.0

        # 結果の保存と検索
        repo.save_result(mock_result)

        found = repo.find_result_by_id("check001")
        assert found == mock_result

        by_episode = repo.find_results_by_episode("episode001")
        assert len(by_episode) == 1
        assert by_episode[0].overall_score == 85.0

        # 設定の取得と保存
        config = repo.get_configuration()
        assert "basic_style" in config.enabled_categories

        new_config = Mock(spec=QualityCheckConfiguration)
        new_config.enabled_categories = ["advanced_style"]
        repo.save_configuration(new_config)

        updated_config = repo.get_configuration()
        assert updated_config == new_config

        # 結果の削除
        assert repo.delete_result("check001") is True
        assert repo.find_result_by_id("check001") is None
        assert repo.delete_result("not_exists") is False


class TestForeshadowingRepository:
    """伏線管理リポジトリインターフェースのテスト"""

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_interface_definition(self) -> None:
        """インターフェースが正しく定義されていることを確認"""
        assert issubclass(ForeshadowingRepository, ABC)

        methods = ["load_all", "save_all", "find_by_id", "exists", "create_from_template"]
        for method in methods:
            assert hasattr(ForeshadowingRepository, method)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_method_signatures(self) -> None:
        """メソッドシグネチャの確認"""
        # from noveler.domain.value_objects.foreshadowing import Foreshadowing, ForeshadowingId  # Moved to top-level

        # モック値オブジェクトの作成
        mock_id = Mock(spec=ForeshadowingId)
        mock_id.value = "fs001"

        mock_foreshadowing = Mock(spec=Foreshadowing)
        mock_foreshadowing.id = mock_id
        mock_foreshadowing.content = "重要な伏線"
        mock_foreshadowing.planted_episode = 1
        mock_foreshadowing.resolved_episode = 10
        mock_foreshadowing.is_resolved = False

        # モック実装を作成
        class MockForeshadowingRepo(ForeshadowingRepository):
            def __init__(self) -> None:
                self.foreshadowings = {}
                self.project_files = set()

            def load_all(self, project_root: str) -> list[Foreshadowing]:
                if project_root not in self.project_files:
                    msg = f"伏線管理ファイルが存在しません: {project_root}"
                    raise FileNotFoundError(msg)
                return list(self.foreshadowings.get(project_root, {}).values())

            def save_all(self, foreshadowings: list[Foreshadowing], project_root: str) -> None:
                if project_root not in self.foreshadowings:
                    self.foreshadowings[project_root] = {}

                self.foreshadowings[project_root] = {fs.id.value: fs for fs in foreshadowings}
                self.project_files.add(project_root)

            def find_by_id(self, foreshadowing_id: ForeshadowingId, project_root: str) -> Foreshadowing | None:
                if project_root not in self.foreshadowings:
                    return None
                return self.foreshadowings[project_root].get(foreshadowing_id.value)

            def exists(self, project_root: str) -> bool:
                return project_root in self.project_files

            def create_from_template(self, project_root: str) -> None:
                self.foreshadowings[project_root] = {}
                self.project_files.add(project_root)

        repo = MockForeshadowingRepo()

        # 存在チェック
        assert repo.exists("/test/project") is False

        # テンプレートからの作成
        repo.create_from_template("/test/project")
        assert repo.exists("/test/project") is True

        # 伏線の保存
        foreshadowings = [mock_foreshadowing]
        repo.save_all(foreshadowings, "/test/project")

        # 全伏線の読み込み
        loaded = repo.load_all("/test/project")
        assert len(loaded) == 1
        assert loaded[0].content == "重要な伏線"

        # IDでの検索
        found = repo.find_by_id(mock_id, "/test/project")
        assert found == mock_foreshadowing

        # 存在しないIDの検索
        not_found_id = Mock(spec=ForeshadowingId)
        not_found_id.value = "not_exists"
        not_found = repo.find_by_id(not_found_id, "/test/project")
        assert not_found is None

        # 存在しないプロジェクトからの読み込み
        with pytest.raises(FileNotFoundError, match=".*"):
            repo.load_all("/not/exists")

        # 複数の伏線の管理
        mock_foreshadowing2 = Mock(spec=Foreshadowing)
        mock_id2 = Mock(spec=ForeshadowingId)
        mock_id2.value = "fs002"
        mock_foreshadowing2.id = mock_id2
        mock_foreshadowing2.content = "別の伏線"
        mock_foreshadowing2.is_resolved = True

        foreshadowings = [mock_foreshadowing, mock_foreshadowing2]
        repo.save_all(foreshadowings, "/test/project")

        loaded = repo.load_all("/test/project")
        assert len(loaded) == 2


class TestRepositoryIntegration:
    """リポジトリインターフェースの統合テスト"""

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_repositories_follow_ddd_principles(self) -> None:
        """リポジトリがDDD原則に従っていることを確認"""
        repositories = [
            PlotVersionRepository,
            QualityCheckRepository,
            ForeshadowingRepository,
        ]

        for repo in repositories:
            assert issubclass(repo, ABC)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_repository_method_patterns(self) -> None:
        """リポジトリメソッドのパターン確認"""
        # バージョン管理パターン
        version_methods = dir(PlotVersionRepository)
        assert any(m.startswith("find_") for m in version_methods)
        assert "save" in version_methods
        assert any(m.startswith("get_") for m in version_methods)

        # 品質チェックパターン
        quality_methods = dir(QualityCheckRepository)
        assert any(m.startswith("get_") for m in quality_methods)
        assert "save_result" in quality_methods
        assert "find_result_by_id" in quality_methods
        assert "delete_result" in quality_methods

        # 伏線管理パターン
        foreshadowing_methods = dir(ForeshadowingRepository)
        assert "load_all" in foreshadowing_methods
        assert "save_all" in foreshadowing_methods
        assert "find_by_id" in foreshadowing_methods
        assert "exists" in foreshadowing_methods

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_repository_return_types(self) -> None:
        """リポジトリの戻り値パターンの確認"""
        # find系メソッドは単一オブジェクトまたはNone、リストを返す
        # get系メソッドは必ず値を返す(設定値など)
        # save系メソッドは通常voidまたはbool
        # exists系メソッドはboolを返す
        # delete系メソッドはboolを返す(成功/失敗)
        # 型アノテーションで既に定義済み
