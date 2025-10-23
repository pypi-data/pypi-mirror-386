#!/usr/bin/env python3
"""
Simple DI Container - 軽量依存性注入コンテナ

Purpose: プロジェクト全体の"TODO: DI"箇所を段階的に解決
Architecture: Infrastructure Layer (DDD準拠)
Dependencies: None (標準ライブラリのみ)
"""

import inspect
import threading
from collections.abc import Callable
from typing import Any, TypeVar, get_type_hints

T = TypeVar("T")


class DIContainer:
    """軽量依存性注入コンテナ

    Features:
    - シングルトン・トランジェント登録サポート
    - コンストラクタ注入の自動解決
    - インターフェース→実装のマッピング
    - スレッドセーフ
    """

    def __init__(self) -> None:
        self._singletons: dict[type, Any] = {}
        self._transients: dict[type, Callable[[], Any]] = {}
        self._interfaces: dict[type, type] = {}
        self._lock = threading.Lock()

    def register_singleton(self, interface: type[T], implementation: type[T]) -> "DIContainer":
        """シングルトン登録 (アプリケーション全体で1インスタンス)"""
        with self._lock:
            self._interfaces[interface] = implementation
            # インスタンス生成は初回取得時に遅延実行
        return self

    def register_transient(self, interface: type[T], implementation: type[T]) -> "DIContainer":
        """トランジェント登録 (取得時に毎回新しいインスタンス)"""
        with self._lock:
            self._interfaces[interface] = implementation
            self._transients[interface] = lambda: self._create_instance(implementation)
        return self

    def register_instance(self, interface: type[T], instance: T) -> "DIContainer":
        """既存インスタンスの登録 (テスト時のモック等で使用)"""
        with self._lock:
            self._singletons[interface] = instance
        return self

    def get(self, interface: type[T]) -> T:
        """依存性の取得 (自動的にコンストラクタ注入を解決)"""
        with self._lock:
            # シングルトンキャッシュをチェック
            if interface in self._singletons:
                return self._singletons[interface]

            # トランジェント登録をチェック
            if interface in self._transients:
                return self._transients[interface]()

            # インターフェース→実装マッピングをチェック
            if interface in self._interfaces:
                implementation = self._interfaces[interface]
                instance = self._create_instance(implementation)

                # シングルトンとして登録されていない場合はキャッシュしない
                if interface not in self._transients:
                    self._singletons[interface] = instance

                return instance

            # 直接実装クラスが渡された場合
            if inspect.isclass(interface):
                instance = self._create_instance(interface)
                self._singletons[interface] = instance
                return instance

            msg = f"Interface {interface} is not registered in DI container"
            raise ValueError(msg)

    def _create_instance(self, cls: type[T]) -> T:
        """コンストラクタ注入によるインスタンス生成"""
        try:
            # コンストラクタの型ヒント取得
            type_hints = get_type_hints(cls.__init__)
            type_hints.pop("return", None)  # 戻り値の型ヒントを除去

            # 'self' パラメータを除去
            sig = inspect.signature(cls.__init__)
            params = list(sig.parameters.keys())[1:]  # 'self' を除く

            # 依存性の再帰的解決
            dependencies = {}
            for param_name in params:
                if param_name in type_hints:
                    param_type = type_hints[param_name]
                    dependencies[param_name] = self.get(param_type)

            return cls(**dependencies)

        except Exception as e:
            # DI解決失敗時のフォールバック（引数なしコンストラクタ）
            try:
                return cls()
            except Exception:
                msg = f"Failed to create instance of {cls}: {e}"
                raise ValueError(msg)


# Global DI Container Instance (Singleton Pattern)
_container = DIContainer()


def get_container() -> DIContainer:
    """グローバルDIコンテナの取得

    Usage:
        container = get_container()
        container.register_singleton(IRepository, YamlRepository)
        repository = container.get(IRepository)
    """
    return _container


def configure_dependencies() -> None:
    """アプリケーション起動時の依存関係設定

    Note: 各モジュールの"TODO: DI"箇所をここで段階的に解決していく
    """
    container = get_container()

    # Phase 1 Week 1-2: Domain純粋性回復 - Logger Service DI注入
    try:
        from noveler.domain.interfaces.logger_service import ILoggerService
        from noveler.infrastructure.adapters.logger_service_adapter import LoggerServiceAdapter

        # LoggerServiceFactoryを作成
        class LoggerServiceFactory:
            def __init__(self) -> None:
                pass

        # LoggerServiceをシングルトンとして登録し、インスタンスを直接作成
        logger_instance = LoggerServiceAdapter("noveler.domain")
        container.register_instance(ILoggerService, logger_instance)

    except ImportError:
        # フォールバック: インポートエラー時はスキップ
        pass

        # 段階的実装予定:
        # 1. Repository Pattern
        # container.register_singleton(IEpisodeRepository, YamlEpisodeRepository)
        #
        # 2. Service Pattern
        # container.register_transient(IQualityService, QualityService)
        #
        # 3. Adapter Pattern
        # container.register_singleton(IClaudeAdapter, ClaudeCodeAdapter)


        # Decorator for automatic DI (Future Implementation)
def inject(func: Callable) -> Callable:
        """依存性注入デコレータ (将来実装予定)

        Usage:
        @inject
        def my_function(repository: IRepository):
            pass
        """
        # TODO: 将来実装予定
        return func
