#!/usr/bin/env python3
"""Port & Adapter分離統合テスト

SPEC-901-DDD-REFACTORING: Port & Adapter分離実装の統合テスト
Golden Sampleに基づくヘキサゴナルアーキテクチャパターンのテスト

このテストは新しいPort & Adapter構造が正常に動作することを確認します。
"""

import asyncio
import pytest
from datetime import datetime
from pathlib import Path

# テスト対象のimport
from noveler.infrastructure.factories.hexagonal_di_container import (
    create_test_hexagonal_container,
    create_production_hexagonal_container,
    HexagonalDIContainer,
)
from noveler.infrastructure.ports.repositories.episode_repository import (
    EpisodeRepositoryPort,
    AdvancedEpisodeRepositoryPort,
    EpisodeQuery,
)
from noveler.infrastructure.adapters.repositories.memory_episode_repository import (
    MemoryEpisodeRepositoryAdapter
)
from noveler.infrastructure.factories.repository_factory import (
    create_test_repository_factory,
    RepositoryFactory,
)
from noveler.domain.entities.episode import Episode, EpisodeStatus
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.episode_title import EpisodeTitle
from noveler.domain.value_objects.quality_score import QualityScore
from noveler.domain.value_objects.word_count import WordCount


class TestPortAdapterIntegration:
    """Port & Adapter分離統合テストクラス"""

    @pytest.mark.spec("SPEC-901-DDD-REFACTORING")
    @pytest.mark.asyncio
    async def test_memory_repository_adapter_basic_operations(self):
        """メモリリポジトリアダプターの基本操作テスト"""
        # Given: メモリリポジトリアダプター
        repository = MemoryEpisodeRepositoryAdapter()
        project_id = "test-project-001"

        # テストエピソードを作成
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("テストエピソード1"),
            content="これはテスト用のエピソード内容です。",
            target_words=WordCount(200),
            status=EpisodeStatus.DRAFT,
        )

        # When: エピソードを保存
        await repository.save(episode, project_id)

        # Then: エピソードが正常に保存されることを確認
        found_episode = await repository.find_by_project_and_number(project_id, 1)
        assert found_episode is not None
        assert found_episode.number.value == 1
        assert found_episode.title.value == "テストエピソード1"
        assert found_episode.content == "これはテスト用のエピソード内容です。"
        assert found_episode.status == EpisodeStatus.DRAFT

    @pytest.mark.spec("SPEC-901-DDD-REFACTORING")
    @pytest.mark.asyncio
    async def test_repository_factory_creates_correct_adapters(self):
        """リポジトリファクトリーが正しいアダプターを作成することをテスト"""
        # Given: テスト用リポジトリファクトリー
        factory = create_test_repository_factory()

        # When: エピソードリポジトリを作成
        repository = factory.create_episode_repository()
        advanced_repository = factory.create_advanced_episode_repository()

        # Then: 適切な型のリポジトリが作成されることを確認
        assert isinstance(repository, EpisodeRepositoryPort)
        assert isinstance(advanced_repository, AdvancedEpisodeRepositoryPort)
        # メモリリポジトリが作成されることを確認
        assert isinstance(repository, MemoryEpisodeRepositoryAdapter)
        assert isinstance(advanced_repository, MemoryEpisodeRepositoryAdapter)

    @pytest.mark.spec("SPEC-901-DDD-REFACTORING")
    @pytest.mark.asyncio
    async def test_hexagonal_di_container_test_mode(self):
        """ヘキサゴナルDIコンテナのテストモードをテスト"""
        # Given: テスト用ヘキサゴナルDIコンテナ
        container = create_test_hexagonal_container()

        # When: リポジトリを解決
        episode_repository = container.get_episode_repository()
        advanced_repository = container.get_advanced_episode_repository()
        factory = container.get_repository_factory()

        # Then: 適切な型のサービスが解決されることを確認
        assert isinstance(episode_repository, EpisodeRepositoryPort)
        assert isinstance(advanced_repository, AdvancedEpisodeRepositoryPort)
        assert isinstance(factory, RepositoryFactory)

        # メモリリポジトリが使用されることを確認
        assert isinstance(episode_repository, MemoryEpisodeRepositoryAdapter)
        assert isinstance(advanced_repository, MemoryEpisodeRepositoryAdapter)

    @pytest.mark.spec("SPEC-901-DDD-REFACTORING")
    @pytest.mark.asyncio
    async def test_advanced_repository_query_functionality(self):
        """高度なリポジトリのクエリ機能をテスト"""
        # Given: テスト用DIコンテナからリポジトリを取得
        container = create_test_hexagonal_container()
        repository = container.get_advanced_episode_repository()
        project_id = "test-project-query"

        # テスト用エピソードを複数作成
        episodes = [
            Episode(
                number=EpisodeNumber(i),
                title=EpisodeTitle(f"エピソード{i}"),
                content=f"エピソード{i}の内容です。" * 10,  # 文字数を変える
                status=EpisodeStatus("published" if i % 2 == 0 else "draft"),
                word_count=WordCount(100 + i * 10),
                quality_score=QualityScore(int(50 + i * 10)),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(1, 6)
        ]

        # When: エピソードを保存
        for episode in episodes:
            await repository.save(episode, project_id)

        # Then: クエリでの検索が正常に動作することを確認

        # ステータスでの検索
        published_episodes = await repository.find_by_status(project_id, "published")
        assert len(published_episodes) == 2  # エピソード2, 4

        draft_episodes = await repository.find_by_status(project_id, "draft")
        assert len(draft_episodes) == 3  # エピソード1, 3, 5

        # クエリオブジェクトを使った検索
        query = (EpisodeQuery()
                .with_project(project_id)
                .with_statuses(["published"])
                .with_word_count_range(115, 150)
                .order_by_field("episode_number", desc=False))

        result = await repository.find_by_query(query)
        assert len(result) == 2  # 条件にマッチするエピソード
        assert result[0].number.value < result[1].number.value  # ソート確認

    @pytest.mark.spec("SPEC-901-DDD-REFACTORING")
    @pytest.mark.asyncio
    async def test_repository_statistics_functionality(self):
        """リポジトリの統計機能をテスト"""
        # Given: テスト用リポジトリ
        container = create_test_hexagonal_container()
        repository = container.get_advanced_episode_repository()
        project_id = "test-project-stats"

        # テスト用エピソード作成
        episodes = [
            Episode(
                number=EpisodeNumber(i),
                title=EpisodeTitle(f"統計テスト{i}"),
                content=f"内容{i}",
                status=EpisodeStatus("published" if i <= 2 else "draft"),
                word_count=WordCount(100 * i),
                quality_score=QualityScore(50),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(1, 4)
        ]

        # When: エピソードを保存
        for episode in episodes:
            await repository.save(episode, project_id)

        # Then: 統計情報が正しく計算されることを確認
        stats = await repository.get_statistics(project_id)

        assert stats["total_episodes"] == 3
        assert stats["total_word_count"] == 600  # 100 + 200 + 300
        assert stats["published_episodes"] == 2
        assert stats["draft_episodes"] == 1
        assert stats["average_word_count"] == 200.0

    @pytest.mark.spec("SPEC-901-DDD-REFACTORING")
    def test_di_container_adapter_mode_switching(self):
        """DIコンテナのアダプターモード切り替えをテスト"""
        # Given: ヘキサゴナルDIコンテナ
        container = HexagonalDIContainer()

        # When & Then: モード切り替えが正常に動作することを確認

        # テストモードに設定
        container.switch_to_test_mode()
        repository1 = container.get_episode_repository()
        assert isinstance(repository1, MemoryEpisodeRepositoryAdapter)

        # カスタムアダプターを登録
        container.set_adapter_mode("custom")
        custom_adapter = MemoryEpisodeRepositoryAdapter()
        container.register_custom_adapter(EpisodeRepositoryPort, custom_adapter)

        repository2 = container.get_episode_repository()
        assert repository2 is custom_adapter  # 同じインスタンスであることを確認

    @pytest.mark.spec("SPEC-901-DDD-REFACTORING")
    @pytest.mark.asyncio
    async def test_backup_and_restore_functionality(self):
        """バックアップ・復元機能をテスト"""
        # Given: テスト用リポジトリ
        container = create_test_hexagonal_container()
        repository = container.get_advanced_episode_repository()
        project_id = "test-project-backup"

        # 初期エピソード
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("バックアップテスト"),
            content="元の内容",
            status=EpisodeStatus("draft"),
            word_count=WordCount(10),
            quality_score=QualityScore(50),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        await repository.save(episode, project_id)
        episode_id = "episode_1"

        # When: バックアップ作成
        backup_success = await repository.backup_episode(episode_id, project_id)
        assert backup_success is True

        # エピソード内容を変更
        episode.content = "変更後の内容"
        await repository.save(episode, project_id)

        # バックアップから復元
        restore_success = await repository.restore_episode(episode_id, project_id, "latest")
        assert restore_success is True

        # Then: 元の内容に戻っていることを確認
        restored_episode = await repository.find_by_project_and_number(project_id, 1)
        assert restored_episode.content == "元の内容"

    @pytest.mark.spec("SPEC-901-DDD-REFACTORING")
    def test_golden_sample_pattern_compliance(self):
        """Golden Sampleパターンへの準拠性をテスト"""
        # Given: 各種コンポーネント
        container = create_test_hexagonal_container()
        factory = create_test_repository_factory()

        # When & Then: Golden Sampleのパターンに準拠していることを確認

        # 1. ポートインターフェースの抽象性
        from noveler.infrastructure.ports.repositories.episode_repository import EpisodeRepositoryPort
        assert hasattr(EpisodeRepositoryPort, '__abstractmethods__')
        assert len(EpisodeRepositoryPort.__abstractmethods__) > 0

        # 2. アダプターの具象実装
        repository = factory.create_episode_repository()
        assert hasattr(repository, 'save')
        assert hasattr(repository, 'find_by_id')
        assert callable(getattr(repository, 'save'))
        assert callable(getattr(repository, 'find_by_id'))

        # 3. ファクトリーパターンの実装
        assert hasattr(factory, 'create_episode_repository')
        assert hasattr(factory, 'create_advanced_episode_repository')

        # 4. DIコンテナの依存性注入
        episode_repo = container.get_episode_repository()
        factory_repo = factory.create_episode_repository()
        assert type(episode_repo) == type(factory_repo)  # 同じ型が作成される

    @pytest.mark.spec("SPEC-901-DDD-REFACTORING")
    def test_error_handling_and_exceptions(self):
        """エラーハンドリングと例外処理をテスト"""
        # Given: 異常系テスト用のセットアップ
        container = HexagonalDIContainer()

        # When & Then: 適切な例外が発生することを確認

        # 未初期化状態でのサービス取得
        with pytest.raises(Exception):  # DIContainerErrorまたはその他のエラー
            container.get_episode_repository()

        # 不正なアダプターモード設定
        with pytest.raises(Exception):  # DIContainerError
            container.set_adapter_mode("invalid_mode")

    def test_performance_and_caching(self):
        """パフォーマンスとキャッシュをテスト"""
        # Given: キャッシュ機能付きファクトリー
        from noveler.infrastructure.factories.repository_factory import (
            create_test_repository_factory,
            CachedRepositoryFactory,
            DefaultRepositoryFactory,
        )

        base_factory = DefaultRepositoryFactory()
        base_factory.config.configure(episode_repository_type="memory")
        cached_factory = CachedRepositoryFactory(base_factory)

        # When: 同じサービスを複数回作成
        repo1 = cached_factory.create_episode_repository()
        repo2 = cached_factory.create_episode_repository()

        # Then: キャッシュが機能していることを確認
        assert repo1 is repo2  # 同じインスタンス

        # キャッシュクリア後は異なるインスタンス
        cached_factory.clear_cache()
        repo3 = cached_factory.create_episode_repository()
        assert repo1 is not repo3


if __name__ == "__main__":
    # 単体テスト実行用のコード
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))

    async def run_basic_test():
        """基本的なテストを実行"""
        test_instance = TestPortAdapterIntegration()

        print("🧪 Port & Adapter分離統合テスト開始")

        try:
            await test_instance.test_memory_repository_adapter_basic_operations()
            print("✅ メモリリポジトリアダプター基本操作テスト: PASS")

            await test_instance.test_repository_factory_creates_correct_adapters()
            print("✅ リポジトリファクトリーテスト: PASS")

            await test_instance.test_hexagonal_di_container_test_mode()
            print("✅ ヘキサゴナルDIコンテナテスト: PASS")

            await test_instance.test_advanced_repository_query_functionality()
            print("✅ 高度なリポジトリクエリ機能テスト: PASS")

            await test_instance.test_repository_statistics_functionality()
            print("✅ リポジトリ統計機能テスト: PASS")

            test_instance.test_di_container_adapter_mode_switching()
            print("✅ DIコンテナアダプターモード切り替えテスト: PASS")

            await test_instance.test_backup_and_restore_functionality()
            print("✅ バックアップ・復元機能テスト: PASS")

            test_instance.test_golden_sample_pattern_compliance()
            print("✅ Golden Sampleパターン準拠性テスト: PASS")

            test_instance.test_error_handling_and_exceptions()
            print("✅ エラーハンドリング・例外処理テスト: PASS")

            test_instance.test_performance_and_caching()
            print("✅ パフォーマンス・キャッシュテスト: PASS")

            print("\n🎉 すべてのテストが成功しました！")
            print("✅ SPEC-901-DDD-REFACTORING: Port & Adapter分離実装完了")

        except Exception as e:
            print(f"❌ テスト失敗: {e}")
            import traceback
            traceback.print_exc()

    # 非同期テスト実行（手動実行時のみ）
    if __name__ == '__main__':
        import asyncio as _asyncio
        _asyncio.run(run_basic_test())
