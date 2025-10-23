"""統一インポート管理ユーティリティ

統合インポート管理システムの一部として、インポートエラーを統一的に処理する
"""

import contextlib
import importlib
import warnings
from collections.abc import Callable
from functools import wraps
from typing import Any

from noveler.domain.value_objects.project_time import project_now


class ImportManager:
    """統一インポートマネージャー"""

    def __init__(self) -> None:
        self._optional_modules: dict[str, Any] = {}
        self._failed_imports: list[str] = []
        self._import_warnings: list[str] = []

    def optional_import(self, module_name: str, fallback: Any = None, error_message: str | None = None) -> Any:
        """オプショナルインポート実行

        Args:
            module_name: インポートするモジュール名
            fallback: インポート失敗時のフォールバック値
            error_message: カスタムエラーメッセージ

        Returns:
            インポートされたモジュールまたはフォールバック値
        """
        if module_name in self._optional_modules:
            return self._optional_modules[module_name]

        try:
            module = importlib.import_module(module_name)
            self._optional_modules[module_name] = module
            return module
        except ImportError as e:
            self._failed_imports.append(module_name)
            warning_msg = error_message or f"オプショナルモジュール '{module_name}' は利用できません: {e}"
            self._import_warnings.append(warning_msg)
            warnings.warn(warning_msg, ImportWarning, stacklevel=2)

            if fallback is not None:
                self._optional_modules[module_name] = fallback
                return fallback

            # None を返すことで呼び出し元で条件分岐可能
            return None

    def require_import(self, module_name: str, error_message: str | None = None) -> Any:
        """必須インポート実行(失敗時は例外発生)

        Args:
            module_name: インポートするモジュール名
            error_message: カスタムエラーメッセージ

        Returns:
            インポートされたモジュール

        Raises:
            ImportError: インポートに失敗した場合
        """
        try:
            return importlib.import_module(module_name)
        except ImportError as e:
            final_message = error_message or f"必須モジュール '{module_name}' をインポートできません: {e}"
            raise ImportError(final_message) from e

    def safe_import_from(self, module_name: str, item_name: str, fallback: Any = None) -> Any:
        """モジュールから特定のアイテムを安全にインポート

        Args:
            module_name: モジュール名
            item_name: インポートするアイテム名
            fallback: フォールバック値

        Returns:
            インポートされたアイテムまたはフォールバック値
        """
        try:
            module = importlib.import_module(module_name)
            return getattr(module, item_name)
        except (ImportError, AttributeError) as e:
            warning_msg = f"'{module_name}.{item_name}' をインポートできません: {e}"
            self._import_warnings.append(warning_msg)
            warnings.warn(warning_msg, ImportWarning, stacklevel=2)
            return fallback

    def get_import_status(self) -> dict[str, Any]:
        """インポート状況を取得

        Returns:
            インポート状況の辞書
        """
        return {
            "successful_imports": list(self._optional_modules.keys()),
            "failed_imports": self._failed_imports,
            "warnings": self._import_warnings,
            "timestamp": project_now().datetime.isoformat(),
        }

    def clear_cache(self) -> None:
        """インポートキャッシュをクリア"""
        self._optional_modules.clear()
        self._failed_imports.clear()
        self._import_warnings.clear()


# グローバルインスタンス
_import_manager = ImportManager()


def optional_import(module_name: str, fallback: Any = None, error_message: str | None = None) -> Any:
    """オプショナルインポート(関数版)"""
    return _import_manager.optional_import(module_name, fallback, error_message)


def require_import(module_name: str, error_message: str | None = None) -> Any:
    """必須インポート(関数版)"""
    return _import_manager.require_import(module_name, error_message)


def safe_import_from(module_name: str, item_name: str, fallback: Any = None) -> Any:
    """安全なfromインポート(関数版)"""
    return _import_manager.safe_import_from(module_name, item_name, fallback)


def import_status() -> dict[str, Any]:
    """インポート状況取得(関数版)"""
    return _import_manager.get_import_status()


def clear_import_cache() -> None:
    """インポートキャッシュクリア(関数版)"""
    _import_manager.clear_cache()


def suppress_import_errors(func: Callable) -> Callable:
    """インポートエラーを抑制するデコレータ"""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except ImportError as e:
            warnings.warn(f"インポートエラーを抑制しました: {e}", ImportWarning, stacklevel=2)
            return None

    return wrapper


@contextlib.contextmanager
def optional_import_context(module_name: str) -> None:
    """オプショナルインポート用コンテキストマネージャー

    使用例:
        with optional_import_context('janome') as janome:
            if janome:
                # janomeを使用した処理
                pass
            else:
                # フォールバック処理
                pass
    """
    module = optional_import(module_name)
    yield module


# 既存コードの移行を簡単にするためのヘルパー関数群
def try_import_janome() -> Any:
    """janomeのオプショナルインポート(既存コード互換)"""
    return optional_import(
        "janome", error_message="形態素解析機能が制限されます。janomeをインストールしてください: pip install janome"
    )


def try_import_yaml() -> Any:
    """PyYAMLのオプショナルインポート(既存コード互換)"""
    return optional_import(
        "yaml", error_message="YAML機能が制限されます。PyYAMLをインストールしてください: pip install PyYAML"
    )


def try_import_ruamel_yaml() -> Any:
    """ruamel.yamlのオプショナルインポート(既存コード互換)"""
    return optional_import(
        "ruamel.yaml",
        error_message="高度なYAML機能が制限されます。ruamel.yamlをインストールしてください: pip install ruamel.yaml",
    )


# 既存の try_import パターンの統一化
COMMON_OPTIONAL_MODULES = {
    "janome": try_import_janome,
    "yaml": try_import_yaml,
    "ruamel.yaml": try_import_ruamel_yaml,
}


def get_optional_module(module_name: str) -> Any:
    """共通オプショナルモジュールの取得"""
    if module_name in COMMON_OPTIONAL_MODULES:
        return COMMON_OPTIONAL_MODULES[module_name]()
    return optional_import(module_name)
