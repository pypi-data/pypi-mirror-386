#!/usr/bin/env python3
"""ファイル品質チェックセッション リポジトリ インターフェース

SPEC-CLAUDE-002に基づく実装
"""

from abc import ABC, abstractmethod
from datetime import datetime

from noveler.domain.entities.file_quality_check_session import FileQualityCheckSession
from noveler.domain.value_objects.file_path import FilePath


class FileQualityCheckSessionRepository(ABC):
    """ファイル品質チェックセッション リポジトリ インターフェース"""

    @abstractmethod
    def save(self, session: FileQualityCheckSession) -> None:
        """セッション保存"""

    @abstractmethod
    def find_by_id(self, session_id: str) -> FileQualityCheckSession | None:
        """ID検索"""

    @abstractmethod
    def find_by_file_path(self, file_path: FilePath) -> list[FileQualityCheckSession]:
        """ファイルパス検索"""

    @abstractmethod
    def find_recent_sessions(self, limit: int = 10) -> list[FileQualityCheckSession]:
        """最近のセッション検索"""

    @abstractmethod
    def find_failed_sessions(self) -> list[FileQualityCheckSession]:
        """失敗セッション検索"""

    @abstractmethod
    def delete_by_id(self, session_id: str) -> bool:
        """ID削除"""

    @abstractmethod
    def delete_older_than(self, cutoff_date: datetime) -> int:
        """古いセッション削除"""

    @abstractmethod
    def count_by_status(self, status: str) -> int:
        """ステータス別カウント"""
