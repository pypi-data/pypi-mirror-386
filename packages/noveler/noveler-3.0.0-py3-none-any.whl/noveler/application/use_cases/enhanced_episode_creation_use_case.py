#!/usr/bin/env python3
"""強化版エピソード作成ユースケース

Phase 5: Application層DI完全実装の参考実装
統一DIパターンによる依存性注入の模範例
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from noveler.application.services.domain_entity_factory import DomainEntityFactoryService
from noveler.domain.entities.episode import Episode
from noveler.domain.interfaces.logger_service import ILoggerService
from noveler.domain.repositories.episode_repository import EpisodeRepository


class IEpisodeCreationResult(Protocol):
    """エピソード作成結果インターフェース"""

    success: bool
    episode: Episode | None
    message: str


@dataclass
class EpisodeCreationResult:
    """エピソード作成結果"""

    success: bool
    episode: Episode | None
    message: str


@dataclass
class EnhancedEpisodeCreationUseCase:
    """強化版エピソード作成ユースケース

    Phase 5: 統一DIパターンの模範実装
    - Infrastructureへの直接依存なし
    - 全依存関係をコンストラクタ注入
    - Factory Method パターンによるDI解決
    """

    repository: EpisodeRepository
    entity_factory: DomainEntityFactoryService
    logger_service: ILoggerService

    def execute(self, number: int, title: str, target_words: int = 3000) -> IEpisodeCreationResult:
        """エピソード作成実行

        Args:
            number: エピソード番号
            title: エピソードタイトル
            target_words: 目標文字数

        Returns:
            IEpisodeCreationResult: 作成結果
        """
        try:
            self.logger_service.info("エピソード作成開始: %s (#%d)", title, number)

            # 重複チェック
            existing_episode = self.repository.find_by_number(number)
            if existing_episode:
                return EpisodeCreationResult(
                    success=False, episode=None, message=f"エピソード番号 {number} は既に存在します"
                )

            # Domain Entity Factory経由でエピソード作成
            episode = self.entity_factory.create_episode(number, title, target_words)

            # 保存
            self.repository.save(episode)

            self.logger_service.info("エピソード作成完了: %s", title)

            return EpisodeCreationResult(success=True, episode=episode, message="エピソードが正常に作成されました")

        except Exception as e:
            self.logger_service.exception("エピソード作成エラー")
            return EpisodeCreationResult(success=False, episode=None, message=f"エピソード作成に失敗しました: {e}")

    @classmethod
    def create_with_di(cls) -> "EnhancedEpisodeCreationUseCase":
        """DIを使用したインスタンス作成

        Phase 5統一DIパターン: Factory Method
        Infrastructure依存を抽象化し、テスタビリティを確保

        Returns:
            EnhancedEpisodeCreationUseCase: 設定済みインスタンス
        """
        try:
            # DIコンテナから依存関係解決

            from noveler.infrastructure.di.container import get_container

            container = get_container()

            # Interface経由で依存関係取得
            repository = container.get(EpisodeRepository)
            logger_service = container.get(ILoggerService)

            # Domain Entity Factory作成
            entity_factory = DomainEntityFactoryService(logger_service)

            return cls(repository=repository, logger_service=logger_service, entity_factory=entity_factory)

        except Exception:
            # フォールバック: Null実装使用

            from noveler.infrastructure.adapters.domain_logger_adapter import DomainLoggerAdapter
            from noveler.infrastructure.repositories.yaml_episode_repository import YamlEpisodeRepository

            logger_service = DomainLoggerAdapter()
            repository = YamlEpisodeRepository(Path.cwd() / "data")
            entity_factory = DomainEntityFactoryService(logger_service)

            return cls(repository=repository, logger_service=logger_service, entity_factory=entity_factory)


# Factory関数（便利メソッド）
def create_episode_creation_use_case() -> EnhancedEpisodeCreationUseCase:
    """エピソード作成ユースケースの簡単作成

    Phase 5統一パターン: Factory Function

    Returns:
        EnhancedEpisodeCreationUseCase: 設定済みインスタンス
    """
    return EnhancedEpisodeCreationUseCase.create_with_di()
