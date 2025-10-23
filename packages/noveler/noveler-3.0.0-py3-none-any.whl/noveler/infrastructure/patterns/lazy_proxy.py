"""Lazy Proxyパターン実装

重いオブジェクトの遅延初期化を透過的に実現する。
循環依存を回避しつつ、パフォーマンスを向上させる。
"""

from collections.abc import Callable
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class LazyProxy(Generic[T]):
    """遅延初期化プロキシ基底クラス

    ファクトリー関数を受け取り、最初のアクセス時に実際のオブジェクトを生成。
    以降のアクセスは生成済みオブジェクトに透過的に委譲する。

    循環依存を回避しつつ、パフォーマンスを最適化する。
    """

    def __init__(self, factory: Callable[[], T]) -> None:
        """初期化

        Args:
            factory: 実際のオブジェクトを生成するファクトリー関数
        """
        self._factory = factory
        self._instance: T | None = None
        self._initialized = False

    def _get_instance(self) -> T:
        """実際のインスタンスを取得（遅延初期化）

        Returns:
            初期化済みのインスタンス
        """
        if not self._initialized:
            self._instance = self._factory()
            self._initialized = True
        return self._instance  # type: ignore[return-value]

    def __getattr__(self, name: str) -> Any:
        """属性アクセスを実際のインスタンスに委譲

        Args:
            name: 属性名

        Returns:
            実際のインスタンスの属性値
        """
        instance = self._get_instance()
        return getattr(instance, name)

    def __setattr__(self, name: str, value: Any) -> None:
        """属性設定を実際のインスタンスに委譲

        Args:
            name: 属性名
            value: 設定する値
        """
        if name in ("_factory", "_instance", "_initialized"):
            # プロキシ自体の属性は直接設定
            super().__setattr__(name, value)
        else:
            # その他の属性は実際のインスタンスに委譲
            instance = self._get_instance()
            setattr(instance, name, value)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """呼び出しを実際のインスタンスに委譲

        Args:
            *args: 位置引数
            **kwargs: キーワード引数

        Returns:
            実際のインスタンスの呼び出し結果
        """
        instance = self._get_instance()
        return instance(*args, **kwargs)

    def __bool__(self) -> bool:
        """真偽値評価を実際のインスタンスに委譲

        Returns:
            実際のインスタンスの真偽値
        """
        instance = self._get_instance()
        return bool(instance)

    def __str__(self) -> str:
        """文字列表現を実際のインスタンスに委譲

        Returns:
            実際のインスタンスの文字列表現
        """
        instance = self._get_instance()
        return str(instance)

    def __repr__(self) -> str:
        """repr表現を実際のインスタンスに委譲

        Returns:
            実際のインスタンスのrepr表現
        """
        instance = self._get_instance()
        return repr(instance)

    def __eq__(self, other: object) -> bool:
        """等価性比較を実際のインスタンスに委譲

        Args:
            other: 比較対象

        Returns:
            等価性比較結果
        """
        instance = self._get_instance()
        return instance == other

    def __hash__(self) -> int:
        """ハッシュ値を実際のインスタンスに委譲

        Returns:
            実際のインスタンスのハッシュ値
        """
        instance = self._get_instance()
        return hash(instance)

    @property
    def is_initialized(self) -> bool:
        """初期化済みかどうかを確認

        Returns:
            初期化済みの場合True
        """
        return self._initialized
