"""Domain.services.status_mapping_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""ステータスマッピングサービス"""


from noveler.domain.exceptions import InvalidStatusError


class StatusMappingService:
    """エピソードステータスの短縮形と完全形をマッピングするサービス"""

    def __init__(self) -> None:
        """マッピングテーブルの初期化"""
        # 短縮形 -> 完全形
        self._short_to_full = {
            "未着": "未着手",
            "未着手": "未着手",
            "執筆中": "執筆中",
            "執筆済": "執筆済み",
            "推敲済": "推敲済み",
            "公開済": "公開済み",
        }

        # 完全形 -> 短縮形
        self._full_to_short = {
            "未着手": "未着",
            "執筆中": "執筆中",
            "執筆済み": "執筆済",
            "推敲済み": "推敲済",
            "公開済み": "公開済",
        }

        # 全ての有効なステータス
        self._all_statuses = set(self._short_to_full.keys()) | set(self._full_to_short.keys())

    def to_full(self, status: str) -> str:
        """短縮形から完全形へ変換"""
        if not status:
            msg = "ステータスが空です"
            raise InvalidStatusError(msg)

        # すでに完全形の場合はそのまま返す
        if status in self._full_to_short:
            return status

        # 短縮形から完全形へ変換
        if status in self._short_to_full:
            return self._short_to_full[status]

        msg = f"無効なステータス: {status}"
        raise InvalidStatusError(msg)

    def to_short(self, status: str) -> str:
        """完全形から短縮形へ変換"""
        if not status:
            msg = "ステータスが空です"
            raise InvalidStatusError(msg)

        # すでに短縮形の場合はそのまま返す
        if status in self._short_to_full and status != "未着手":
            return status

        # 完全形から短縮形へ変換
        if status in self._full_to_short:
            return self._full_to_short[status]

        msg = f"無効なステータス: {status}"
        raise InvalidStatusError(msg)

    def is_valid(self, status: str | None) -> bool:
        """有効なステータスかチェック"""
        if status is None or status == "":
            return False
        return status in self._all_statuses

    def get_short_statuses(self) -> list[str]:
        """短縮形ステータスのリストを取得"""
        return list(self._short_to_full.keys())

    def get_full_statuses(self) -> list[str]:
        """完全形ステータスのリストを取得"""
        return list(self._full_to_short.keys())
