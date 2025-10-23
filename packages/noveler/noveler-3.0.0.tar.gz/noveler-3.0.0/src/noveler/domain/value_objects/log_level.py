"""Domain.value_objects.log_level
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

from __future__ import annotations

"""ログレベルを表す値オブジェクト"""


from enum import Enum


class LogLevel(Enum):
    """ログレベルを表す列挙型値オブジェクト


    ログの重要度を表し、重要度に基づいた比較機能を提供する。
    DEBUG < INFO < WARNING < ERROR < CRITICAL の順序。
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    @property
    def severity(self) -> int:
        """重要度を数値で返す

        Returns:
            重要度(0-4の範囲)
        """
        severity_map = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4,
        }
        return severity_map[self]

    @classmethod
    def from_string(cls, level_str: str) -> LogLevel:
        """文字列からLogLevelを作成する

        Args:
            level_str: ログレベルの文字列(大文字小文字を問わない)

        Returns:
            対応するLogLevel

        Raises:
            ValueError: 無効なログレベル文字列の場合
        """
        level_str = level_str.upper()
        try:
            return cls(level_str)
        except ValueError as e:
            valid_levels = [level.value for level in cls]
            msg = f"Invalid log level: {level_str}. Valid levels: {valid_levels}"
            raise ValueError(msg) from e

    def is_enabled_for(self, threshold: LogLevel) -> bool:
        """指定した閾値以上のログレベルかを判定する

        Args:
            threshold: 閾値となるログレベル

        Returns:
            このログレベルが閾値以上の場合True
        """
        return self.severity >= threshold.severity

    @classmethod
    def all_levels(cls) -> list[LogLevel]:
        """全てのログレベルを重要度順で返す

        Returns:
            重要度順のログレベルリスト
        """
        return [cls.DEBUG, cls.INFO, cls.WARNING, cls.ERROR, cls.CRITICAL]
