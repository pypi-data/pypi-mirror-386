"""Domain.value_objects.sync_result
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""同期結果値オブジェクト
話数管理.yaml自動同期機能のドメイン層
"""


from dataclasses import dataclass


@dataclass(frozen=True)
class SyncResult:
    """同期結果値オブジェクト"""

    success: bool
    updated_fields: list[str]
    error_message: str | None = None
    backup_created: bool = False

    def is_successful(self) -> bool:
        """同期が成功したかどうか"""
        return self.success

    def has_error(self) -> bool:
        """エラーがあるかどうか"""
        return self.error_message is not None

    def get_updated_field_count(self) -> int:
        """更新されたフィールド数"""
        return len(self.updated_fields)

    def __hash__(self) -> int:
        """不変データとしてハッシュ値を提供"""
        return hash((self.success, tuple(self.updated_fields), self.error_message, self.backup_created))
