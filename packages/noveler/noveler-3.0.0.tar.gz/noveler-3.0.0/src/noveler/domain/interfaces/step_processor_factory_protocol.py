#!/usr/bin/env python3
"""ステップ処理器ファクトリプロトコル

StepProcessorFactoryの循環依存解決
Protocol基盤によるステップ処理器生成の抽象化インターフェース
"""

from abc import abstractmethod
from typing import Protocol, runtime_checkable
import importlib

from noveler.application.use_cases.step_processors.base_step_processor import BaseStepProcessor


@runtime_checkable
class StepProcessorFactoryProtocol(Protocol):
    """ステップ処理器ファクトリの抽象インターフェース"""

    @abstractmethod
    def get_processor(self, step: int | float) -> BaseStepProcessor:
        """ステップ処理器を取得

        Args:
            step: ステップ番号（整数または浮動小数点数）

        Returns:
            ステップ処理器インスタンス
        """
        ...


class LazyStepProcessorProxy:
    """遅延ロード対応のステップ処理器ファクトリプロキシ

    循環依存を回避しつつ、実際のStepProcessorFactoryの生成を遅延実行
    """

    def __init__(self) -> None:
        self._cached_factory: StepProcessorFactoryProtocol | None = None

    @property
    def factory(self) -> StepProcessorFactoryProtocol:
        """遅延ロードされるステップ処理器ファクトリ"""
        if self._cached_factory is None:
            # 初回アクセス時のみインスタンス化（importlibで遅延ロード）
            _spf = importlib.import_module(
                'noveler.application.use_cases.step_processors.step_processor_factory_impl'
            )
            StepProcessorFactoryImpl = getattr(_spf, 'StepProcessorFactoryImpl')
            self._cached_factory = StepProcessorFactoryImpl()
        return self._cached_factory

    def get_processor(self, step: int | float) -> BaseStepProcessor:
        """ステップ処理器を取得（遅延ロード）

        Args:
            step: ステップ番号

        Returns:
            ステップ処理器インスタンス
        """
        return self.factory.get_processor(step)


# グローバル遅延プロキシインスタンス（シングルトン）
_step_processor_factory_proxy = LazyStepProcessorProxy()


def get_step_processor_factory_manager() -> LazyStepProcessorProxy:
    """ステップ処理器ファクトリプロキシ取得（DI対応）"""
    return _step_processor_factory_proxy
