#!/usr/bin/env python3
# File: src/noveler/domain/protocols/serializable.py
# Purpose: Protocol for objects that can be serialized at presentation boundaries
# Context: Used by MCP/CLI adapters to ensure safe JSON serialization

"""MCP/CLI境界でのシリアライズプロトコル

SPEC-MCP-001: MCP境界での型安全なシリアライズ保証
DDD準拠: ドメイン層はPathで型安全、境界でstr変換
"""

from abc import ABC, abstractmethod
from typing import Any


class SerializableRequest(ABC):
    """MCP/CLI境界で使用されるリクエストの基底クラス

    Pathオブジェクトなど、JSONシリアライズ不可能な型を含むドメインモデルは
    このクラスを継承し、to_dict()メソッドでシリアライズ可能な辞書に変換する。

    契約:
    - to_dict()は全てのフィールドをJSONシリアライズ可能な型に変換すること
    - Pathオブジェクトはstrに変換すること
    - ネストされたオブジェクトも再帰的に変換すること
    """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """境界でのシリアライズ用辞書を返す

        Returns:
            JSONシリアライズ可能な辞書
            - Path → str
            - datetime → ISO8601文字列
            - Enum → value
            など、全ての型がJSONシリアライズ可能であること
        """
        pass


class SerializableResponse(ABC):
    """MCP/CLI境界で返されるレスポンスの基底クラス

    リクエストと同様に、レスポンスもJSONシリアライズ可能な形式で返す必要がある。
    """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """境界でのシリアライズ用辞書を返す

        Returns:
            JSONシリアライズ可能な辞書
        """
        pass
