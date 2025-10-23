"""Infrastructure.config.deal_config
Where: Infrastructure module describing deal configuration defaults.
What: Provides typed configuration structures and constants for deal integrations.
Why: Keeps deal-related settings organised and reusable across infrastructure services.
"""

from noveler.presentation.shared.shared_utilities import console

"Design by Contract 設定\n\npython-dealの設定とヘルパー関数\n"
import sys
from collections.abc import Callable
from typing import Any

import deal

from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager

config_manager = get_configuration_manager()
CONTRACTS_ENABLED = config_manager.get_system_setting("CONTRACTS_ENABLED", "true").lower() == "true"
if "pytest" in sys.modules:
    CONTRACTS_ENABLED = True


def enable_contracts() -> None:
    """契約を有効化"""
    if CONTRACTS_ENABLED:
        deal.activate()


def disable_contracts() -> None:
    """契約を無効化"""
    deal.deactivate()


def contract_invariant(condition: Callable[..., bool]) -> Callable[..., Any]:
    """不変条件デコレータ

    クラスの不変条件を定義するためのヘルパー
    """
    return deal.inv(condition)


def contract_ensure(condition: Callable[..., bool]) -> Callable[..., Any]:
    """事後条件デコレータ

    メソッドの事後条件を定義するためのヘルパー
    """
    return deal.ensure(condition)


def contract_require(condition: Callable[..., bool]) -> Callable[..., Any]:
    """事前条件デコレータ

    メソッドの事前条件を定義するためのヘルパー
    """
    return deal.require(condition)


enable_contracts()


class CommonContracts:
    """共通の契約条件"""

    @staticmethod
    def is_positive_integer(value: object) -> bool:
        """正の整数チェック"""
        return isinstance(value, int) and value > 0

    @staticmethod
    def is_non_negative_integer(value: object) -> bool:
        """非負の整数チェック"""
        return isinstance(value, int) and value >= 0

    @staticmethod
    def is_valid_percentage(value: object) -> bool:
        """有効なパーセンテージ(0-100)チェック"""
        return isinstance(value, int | float) and 0 <= value <= 100

    @staticmethod
    def is_non_empty_string(value: object) -> bool:
        """非空文字列チェック"""
        return isinstance(value, str) and value.strip()

    @staticmethod
    def is_valid_word_count(value: object) -> bool:
        """有効な文字数チェック"""
        return isinstance(value, int) and 0 <= value <= 1000000

    @staticmethod
    def is_valid_episode_number(value: object) -> bool:
        """有効な話数チェック"""
        return isinstance(value, int) and 1 <= value <= 9999


def handle_contract_error(error: object) -> None:
    """契約エラーのハンドラー"""
    if CONTRACTS_ENABLED:
        console.print(f"Contract violation: {error}")
        if hasattr(error, "contract"):
            console.print(f"Contract: {error.contract}")
        if hasattr(error, "args") and error.args:
            console.print(f"Arguments: {error.args}")
    msg = f"Invalid operation: {error}"
    raise ValueError(msg)


def check_contract(condition: bool, message: str) -> None:
    """手動契約チェック"""
    if not condition:
        if CONTRACTS_ENABLED:
            raise deal.ContractError(message)
        raise ValueError(message)


def print_contract_info() -> None:
    """契約設定の情報を表示"""
    console.print(f"Contracts enabled: {CONTRACTS_ENABLED}")
    console.print(f"Deal active: {deal.activate is not None}")
    console.print(f"Python version: {sys.version}")
    console.print(f"Deal version: {deal.__version__}")
