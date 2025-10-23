"""
from noveler.domain.services.path_service_factory import IPathServiceFactory
from noveler.presentation.shared.shared_utilities import get_common_path_service
DDD準拠度検証テスト

SPEC-DDD-COMPLIANCE-005: DDD原則準拠の自動検証


仕様書: SPEC-UNIT-TEST
"""

import ast

from pathlib import Path

import pytest


class DDDComplianceChecker:
    """DDD準拠度チェッカー"""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.scripts_dir = project_root / "scripts"

    def check_domain_layer_dependencies(self) -> dict[str, list[str]]:
        """ドメイン層の依存関係違反をチェック"""
        domain_dir = self.scripts_dir / "domain"
        violations = {}

        for py_file in domain_dir.rglob("*.py"):
            violations_in_file = self._check_file_dependencies(py_file)
            if violations_in_file:
                relative_path = str(py_file.relative_to(self.project_root))
                violations[relative_path] = violations_in_file

        return violations

    def _check_file_dependencies(self, file_path: Path) -> list[str]:
        """単一ファイルの依存関係違反をチェック"""
        violations = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        # プレゼンテーション層への依存チェック
                        if "noveler.presentation" in node.module:
                            violations.append(f"Presentation layer dependency: {node.module}")

                        # インフラ層直接依存チェック（アダプタ経由以外）
                        if (
                            "noveler.infrastructure" in node.module
                            and "noveler.infrastructure.adapters" not in node.module
                        ):
                            violations.append(f"Direct infrastructure dependency: {node.module}")

        except (FileNotFoundError, SyntaxError, UnicodeDecodeError):
            # ファイル読み込みエラーは無視
            pass

        return violations

    def check_interface_abstractions(self) -> dict[str, bool]:
        """インターフェース抽象化の存在確認"""
        interfaces_dir = self.scripts_dir / "domain" / "interfaces"

        return {
            "path_service_protocol_exists": (interfaces_dir / "path_service_protocol.py").exists(),
            "event_publisher_protocol_exists": (interfaces_dir / "event_publisher_protocol.py").exists(),
            "interfaces_init_exists": (interfaces_dir / "__init__.py").exists(),
        }

    def check_adapter_implementations(self) -> dict[str, bool]:
        """アダプター実装の存在確認"""
        adapters_dir = self.scripts_dir / "infrastructure" / "adapters"

        return {
            "path_service_adapter_exists": (adapters_dir / "path_service_adapter.py").exists(),
            "domain_event_publisher_adapter_exists": (adapters_dir / "domain_event_publisher_adapter.py").exists(),
        }


@pytest.fixture
def ddd_checker():
    """DDDチェッカーのフィクスチャ"""
    project_root = Path(__file__).parent.parent.parent.parent
    return DDDComplianceChecker(project_root)


class TestDDDCompliance:
    """DDD準拠度テスト"""

    @pytest.mark.spec("SPEC-UNIT-TEST")
    def test_domain_layer_has_no_presentation_dependencies(self, ddd_checker):
        """ドメイン層がプレゼンテーション層に依存していないことを検証"""
        violations = ddd_checker.check_domain_layer_dependencies()

        # プレゼンテーション層依存の違反をフィルタ
        presentation_violations = {}
        for file_path, file_violations in violations.items():
            presentation_deps = [v for v in file_violations if "Presentation layer dependency" in v]
            if presentation_deps:
                presentation_violations[file_path] = presentation_deps

        # 修正後は違反が0になることを期待
        assert len(presentation_violations) == 0, (
            f"Domain layer still has presentation dependencies: {presentation_violations}"
        )

    @pytest.mark.spec("SPEC-UNIT-TEST")
    def test_domain_interfaces_exist(self, ddd_checker):
        """ドメインインターフェースが存在することを検証"""
        interface_status = ddd_checker.check_interface_abstractions()

        assert interface_status["path_service_protocol_exists"], "IPathService protocol should exist"
        assert interface_status["event_publisher_protocol_exists"], "IDomainEventPublisher protocol should exist"
        assert interface_status["interfaces_init_exists"], "Domain interfaces __init__.py should exist"

    @pytest.mark.spec("SPEC-UNIT-TEST")
    def test_infrastructure_adapters_exist(self, ddd_checker):
        """インフラストラクチャアダプターが存在することを検証"""
        adapter_status = ddd_checker.check_adapter_implementations()

        assert adapter_status["path_service_adapter_exists"], "PathServiceAdapter should exist"
        assert adapter_status["domain_event_publisher_adapter_exists"], "DomainEventPublisherAdapter should exist"

    @pytest.mark.spec("SPEC-UNIT-TEST")
    def test_domain_interfaces_can_be_imported(self):
        """ドメインインターフェースがインポート可能であることを検証"""
        try:
            from noveler.domain.interfaces import IDomainEventPublisher, IPathService
            from noveler.domain.services.path_service_factory import IPathServiceFactory

            # インターフェースが適切に定義されていることを確認
            assert hasattr(IPathService, "project_root"), "IPathService should have project_root property"
            assert hasattr(IDomainEventPublisher, "publish"), "IDomainEventPublisher should have publish method"
            assert hasattr(IPathServiceFactory, "create_path_service"), (
                "IPathServiceFactory should have create_path_service method"
            )

        except ImportError as e:
            pytest.fail(f"Failed to import domain interfaces: {e}")

    @pytest.mark.spec("SPEC-UNIT-TEST")
    def test_infrastructure_adapters_can_be_imported(self):
        """インフラストラクチャアダプターがインポート可能であることを検証"""
        try:
            from noveler.infrastructure.adapters.domain_event_publisher_adapter import (
                ConsoleEventPublisherAdapter,
                get_domain_event_publisher,
            )
            from noveler.infrastructure.adapters.path_service_adapter import (
                PathServiceAdapter,
                PathServiceAdapterFactory,
                create_path_service,
            )

            # アダプターが適切に定義されていることを確認
            assert PathServiceAdapter is not None
            assert PathServiceAdapterFactory is not None
            assert create_path_service is not None
            assert ConsoleEventPublisherAdapter is not None
            assert get_domain_event_publisher is not None

        except ImportError as e:
            pytest.fail(f"Failed to import infrastructure adapters: {e}")

    @pytest.mark.spec("SPEC-UNIT-TEST")
    def test_adapter_factory_works(self):
        """アダプターファクトリーが動作することを検証"""
        try:
            from noveler.infrastructure.adapters.domain_event_publisher_adapter import get_domain_event_publisher
            from noveler.infrastructure.adapters.path_service_adapter import create_path_service

            # パスサービス作成テスト
            path_service = create_path_service()
            assert path_service is not None
            assert hasattr(path_service, "project_root")
            assert hasattr(path_service, "get_manuscript_dir")

            # イベントパブリッシャー取得テスト
            event_publisher = get_domain_event_publisher()
            assert event_publisher is not None
            assert hasattr(event_publisher, "publish")
            assert hasattr(event_publisher, "publish_info")

        except Exception as e:
            pytest.fail(f"Adapter factory test failed: {e}")


class TestDDDArchitecture:
    """DDDアーキテクチャテスト"""

    @pytest.mark.spec("SPEC-UNIT-TEST")
    def test_episode_entity_is_ddd_compliant(self):
        """Episodeエンティティ がDDD準拠であることを検証"""
        from noveler.domain.entities.episode import Episode
        from noveler.domain.value_objects.episode_number import EpisodeNumber
        from noveler.domain.value_objects.episode_title import EpisodeTitle
        from noveler.domain.value_objects.word_count import WordCount

        # エンティティが適切なビジネスロジックを持つことを確認
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("テスト"),
            content="テスト内容" * 500,  # 十分な文字数
            target_words=WordCount(3000),
        )

        # ビジネスルール検証
        assert episode.can_publish() is False, "Episode without completed status and quality score should not be publishable"

        # エピソードを完成させる
        episode.complete()
        assert episode.can_publish() is False, "Episode without quality score should not be publishable"

        episode.set_quality_score(80.0)
        assert episode.can_publish() is True, "Episode with completed status and good quality score should be publishable"

        # 不変条件検証
        with pytest.raises(Exception):
            Episode(
                number=EpisodeNumber(0),  # 無効な番号
                title=EpisodeTitle("テスト"),
                content="内容",
                target_words=WordCount(3000),
            )


@pytest.mark.integration
class TestDDDIntegration:
    """DDD統合テスト"""

    @pytest.mark.spec("SPEC-UNIT-TEST")
    def test_path_service_adapter_integration(self):
        """PathServiceAdapterの統合テスト"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service()

        # 基本機能テスト
        path_service = get_common_path_service()
        project_root = path_service.project_root
        assert project_root is not None
        assert project_root.exists()

        # ディレクトリ取得テスト
        manuscript_dir = path_service.get_manuscript_dir()
        assert manuscript_dir is not None
        assert "原稿" in str(manuscript_dir)

    @pytest.mark.spec("SPEC-UNIT-TEST")
    def test_event_publisher_adapter_integration(self):
        """EventPublisherAdapterの統合テスト"""
        from noveler.domain.interfaces.event_publisher_protocol import DomainEvent, EventLevel
        from noveler.infrastructure.adapters.domain_event_publisher_adapter import get_domain_event_publisher

        event_publisher = get_domain_event_publisher()

        # 基本機能テスト（例外が発生しないことを確認）
        try:
            event = DomainEvent(message="テストメッセージ", level=EventLevel.INFO)
            event_publisher.publish(event)

            event_publisher.publish_info("情報メッセージ")
            event_publisher.publish_warning("警告メッセージ")
            event_publisher.publish_progress("進捗", 1, 10)

        except Exception as e:
            pytest.fail(f"Event publisher integration test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
