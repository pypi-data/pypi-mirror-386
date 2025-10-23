"""品質管理ドメインのリポジトリインターフェーステスト

仕様書: SPEC-UNIT-TEST
"""

from abc import ABC
from unittest.mock import Mock

import pytest
pytestmark = pytest.mark.quality_domain


from noveler.domain.quality.entities import QualityReport
from noveler.domain.quality.repositories import (
    ProperNounRepository,
    QualityReportRepository,
    QualityRuleRepository,
)


class TestProperNounRepository:
    """固有名詞リポジトリインターフェースのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_REPOSITORIES-INTERFACE_DEFINITION")
    def test_interface_definition(self) -> None:
        """インターフェースが正しく定義されていることを確認"""
        assert issubclass(ProperNounRepository, ABC)
        assert hasattr(ProperNounRepository, "get_all_by_project")
        assert hasattr(ProperNounRepository, "exists")

    @pytest.mark.spec("SPEC-QUALITY_REPOSITORIES-ABSTRACT_METHODS")
    def test_abstract_methods(self) -> None:
        """抽象メソッドの定義を確認"""
        # 直接インスタンス化できないことを確認
        with pytest.raises(TypeError, match=".*"):
            ProperNounRepository()

    @pytest.mark.spec("SPEC-QUALITY_REPOSITORIES-METHOD_SIGNATURES")
    def test_method_signatures(self) -> None:
        """メソッドシグネチャの確認"""

        # モック実装を作成
        class MockProperNounRepo(ProperNounRepository):
            def get_all_by_project(self, _project_id: str) -> set[str]:
                return {"キャラ名", "地名", "魔法名"}

            def exists(self, _project_id: str, proper_noun: str) -> bool:
                return proper_noun in ["キャラ名", "地名", "魔法名"]

        repo = MockProperNounRepo()

        # get_all_by_project のテスト
        result = repo.get_all_by_project("test_project")
        assert isinstance(result, set)
        assert "キャラ名" in result

        # exists のテスト
        assert repo.exists("test_project", "キャラ名") is True
        assert repo.exists("test_project", "存在しない名前") is False


class TestQualityRuleRepository:
    """品質ルールリポジトリインターフェースのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_REPOSITORIES-INTERFACE_DEFINITION")
    def test_interface_definition(self) -> None:
        """インターフェースが正しく定義されていることを確認"""
        assert issubclass(QualityRuleRepository, ABC)
        assert hasattr(QualityRuleRepository, "get_active_rules")
        assert hasattr(QualityRuleRepository, "get_rule_config")

    @pytest.mark.spec("SPEC-QUALITY_REPOSITORIES-ABSTRACT_METHODS")
    def test_abstract_methods(self) -> None:
        """抽象メソッドの定義を確認"""
        with pytest.raises(TypeError, match=".*"):
            QualityRuleRepository()

    @pytest.mark.spec("SPEC-QUALITY_REPOSITORIES-METHOD_SIGNATURES")
    def test_method_signatures(self) -> None:
        """メソッドシグネチャの確認"""

        # モック実装を作成
        class MockQualityRuleRepo(QualityRuleRepository):
            def get_active_rules(self, _project_id: str) -> list[str]:
                return ["文体チェック", "構成チェック", "禁則チェック"]

            def get_rule_config(self, _project_id: str, _rule_name: str) -> dict:
                return {"enabled": True, "severity": "warning", "params": {"threshold": 0.8}}

        repo = MockQualityRuleRepo()

        # get_active_rules のテスト
        rules = repo.get_active_rules("test_project")
        assert isinstance(rules, list)
        assert "文体チェック" in rules

        # get_rule_config のテスト
        config = repo.get_rule_config("test_project", "文体チェック")
        assert isinstance(config, dict)
        assert "enabled" in config
        assert config["enabled"] is True


class TestQualityReportRepository:
    """品質レポートリポジトリインターフェースのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_REPOSITORIES-INTERFACE_DEFINITION")
    def test_interface_definition(self) -> None:
        """インターフェースが正しく定義されていることを確認"""
        assert issubclass(QualityReportRepository, ABC)
        assert hasattr(QualityReportRepository, "save")
        assert hasattr(QualityReportRepository, "find_by_episode_id")
        assert hasattr(QualityReportRepository, "find_latest_by_episode_id")
        assert hasattr(QualityReportRepository, "find_all_by_project")

    @pytest.mark.spec("SPEC-QUALITY_REPOSITORIES-ABSTRACT_METHODS")
    def test_abstract_methods(self) -> None:
        """抽象メソッドの定義を確認"""
        with pytest.raises(TypeError, match=".*"):
            QualityReportRepository()

    @pytest.mark.spec("SPEC-QUALITY_REPOSITORIES-METHOD_SIGNATURES")
    def test_method_signatures(self) -> None:
        """メソッドシグネチャの確認"""
        # QualityReportのモックを作成
        mock_report = Mock(spec=QualityReport)
        mock_report.episode_id = "episode001"
        mock_report.project_id = "test_project"
        mock_report.overall_score = 85.0

        # モック実装を作成
        class MockQualityReportRepo(QualityReportRepository):
            def __init__(self) -> None:
                self.reports = {}

            def save(self, report: QualityReport) -> None:
                self.reports[report.episode_id] = report

            def find_by_episode_id(self, episode_id: str) -> QualityReport | None:
                return self.reports.get(episode_id)

            def find_latest_by_episode_id(self, episode_id: str) -> QualityReport | None:
                # 実際の実装では最新のものを返す
                return self.reports.get(episode_id)

            def find_all_by_project(self, project_id: str) -> list[QualityReport]:
                return [r for r in self.reports.values() if r.project_id == project_id]

        repo = MockQualityReportRepo()

        # save のテスト
        repo.save(mock_report)

        # find_by_episode_id のテスト
        found = repo.find_by_episode_id("episode001")
        assert found is not None
        assert found.episode_id == "episode001"

        # find_latest_by_episode_id のテスト
        latest = repo.find_latest_by_episode_id("episode001")
        assert latest is not None
        assert latest.episode_id == "episode001"

        # find_all_by_project のテスト
        all_reports = repo.find_all_by_project("test_project")
        assert isinstance(all_reports, list)
        assert len(all_reports) == 1
        assert all_reports[0].project_id == "test_project"

        # 存在しないエピソードの検索
        not_found = repo.find_by_episode_id("not_exists")
        assert not_found is None


class TestRepositoryIntegration:
    """リポジトリインターフェースの統合テスト"""

    @pytest.mark.spec("SPEC-QUALITY_REPOSITORIES-REPOSITORIES_FOLLOW_")
    def test_repositories_follow_ddd_principles(self) -> None:
        """リポジトリがDDD原則に従っていることを確認"""
        # すべてのリポジトリがABCを継承
        repositories = [
            ProperNounRepository,
            QualityRuleRepository,
            QualityReportRepository,
        ]

        for repo in repositories:
            assert issubclass(repo, ABC)

    @pytest.mark.spec("SPEC-QUALITY_REPOSITORIES-REPOSITORY_METHOD_NA")
    def test_repository_method_naming_convention(self) -> None:
        """メソッド命名規則の確認"""
        # 検索メソッドは find_ または get_ で始まる
        repo_methods = {
            ProperNounRepository: ["get_all_by_project", "exists"],
            QualityRuleRepository: ["get_active_rules", "get_rule_config"],
            QualityReportRepository: ["save", "find_by_episode_id", "find_latest_by_episode_id", "find_all_by_project"],
        }

        for repo, methods in repo_methods.items():
            for method in methods:
                assert hasattr(repo, method)
                # 検索系メソッドの命名規則確認
                if method not in ["save", "exists", "delete"]:
                    assert method.startswith(("find_", "get_"))
