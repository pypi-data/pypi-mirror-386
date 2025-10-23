"""インフラストラクチャ層のユーティリティモジュール"""

from noveler.infrastructure.utils.yaml_utils import (
    YAMLHandler,
    check_yaml_syntax,
    get_yaml_errors,
)


def config_schema() -> dict:
    """軽量な設定スキーマのスタブ実装"""

    return {}


def retry_handler(*_args, **_kwargs) -> None:
    """軽量なリトライハンドラーのスタブ実装"""

    return None


__all__ = [
    "YAMLHandler",
    "check_yaml_syntax",
    "get_yaml_errors",
    "config_schema",
    "retry_handler",
]
