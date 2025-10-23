#!/usr/bin/env python3
"""段階管理プロトコル

循環依存解決のためのステージ管理抽象化インターフェース
遅延インポート問題を根本解決するProtocolベース設計
"""

from abc import abstractmethod
from enum import Enum
from typing import Any, Protocol, runtime_checkable
import importlib


class StageType(Enum):
    """ステージタイプの定義（循環依存回避）"""

    PREPARATION = "preparation"
    EXECUTION = "execution"
    VALIDATION = "validation"
    COMPLETION = "completion"


@runtime_checkable
class StageNumberProtocol(Protocol):
    """ステージ番号の抽象インターフェース"""

    @property
    def value(self) -> int:
        """ステージ番号値"""
        ...

    @property
    def stage_type(self) -> StageType:
        """ステージタイプ"""
        ...

    def is_valid_transition_to(self, target: "StageNumberProtocol") -> bool:
        """指定ステージへの遷移可能性チェック"""
        ...


@runtime_checkable
class ExecutionContextProtocol(Protocol):
    """実行コンテキストの抽象インターフェース"""

    @property
    def episode_number(self) -> int:
        """エピソード番号"""
        ...

    @property
    def current_stage(self) -> StageNumberProtocol:
        """現在のステージ"""
        ...

    @abstractmethod
    def transition_to_stage(self, target_stage: StageNumberProtocol) -> bool:
        """ステージ遷移実行"""
        ...


@runtime_checkable
class StageManagementServiceProtocol(Protocol):
    """ステージ管理サービスの抽象インターフェース"""

    @abstractmethod
    def validate_stage_transition(
        self, context: ExecutionContextProtocol, target_stage: StageNumberProtocol
    ) -> dict[str, Any]:
        """ステージ遷移の妥当性検証"""
        ...

    @abstractmethod
    def create_stage_number(self, stage_value: int) -> StageNumberProtocol:
        """ステージ番号インスタンス生成（Factory Method）"""
        ...

    @abstractmethod
    def get_rollback_recommendations(
        self, current_stage: StageNumberProtocol, target_stage: StageNumberProtocol
    ) -> list[str]:
        """ロールバック推奨事項生成"""
        ...


class LazyStageManagerProxy:
    """遅延ロード対応のステージ管理プロキシ

    循環依存を回避しつつ、実際のStageNumberの生成を遅延実行
    """

    def __init__(self) -> None:
        self._cached_service: StageManagementServiceProtocol | None = None

    @property
    def service(self) -> StageManagementServiceProtocol:
        """遅延ロードされるステージ管理サービス"""
        if self._cached_service is None:
            # 初回アクセス時のみインポート・インスタンス化（importlibで遅延）
            _svc_mod = importlib.import_module('noveler.domain.services.stage_management_service')
            StageManagementService = getattr(_svc_mod, 'StageManagementService')
            self._cached_service = StageManagementService()
        return self._cached_service

    def create_stage_number(self, stage_value: int) -> StageNumberProtocol:
        """ステージ番号生成（遅延ロード）"""
        return self.service.create_stage_number(stage_value)

    def validate_transition(
        self, context: ExecutionContextProtocol, target_stage: StageNumberProtocol
    ) -> dict[str, Any]:
        """遷移検証（遅延ロード）"""
        return self.service.validate_stage_transition(context, target_stage)


# グローバル遅延プロキシインスタンス（シングルトン）
_stage_manager_proxy = LazyStageManagerProxy()


def get_stage_manager() -> LazyStageManagerProxy:
    """ステージ管理プロキシ取得（DI対応）"""
    return _stage_manager_proxy
