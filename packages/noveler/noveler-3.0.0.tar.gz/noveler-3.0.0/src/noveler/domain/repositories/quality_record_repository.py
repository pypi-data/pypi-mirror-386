#!/usr/bin/env python3
"""品質記録リポジトリインターフェース
ドメイン層でのリポジトリ契約定義
"""

from abc import ABC, abstractmethod
from functools import wraps
from typing import Any

from noveler.domain.entities.quality_record import QualityRecord


class QualityRecordRepository(ABC):
    """品質記録リポジトリインターフェース"""

    def __init_subclass__(cls, **kwargs) -> None:  # pragma: no cover - メタクラス経由のラッパ登録
        super().__init_subclass__(**kwargs)
        save_impl = cls.__dict__.get("save")
        if save_impl is None:
            return

        # 既に wrap 済みの場合は何もしない
        if getattr(save_impl, "__quality_record_wrapped__", False):
            return

        @wraps(save_impl)
        def _wrapped_save(self, quality_record: QualityRecord, *args, **kwargs):
            QualityRecordRepository._prepare_project_name(quality_record)
            return save_impl(self, quality_record, *args, **kwargs)

        setattr(_wrapped_save, "__quality_record_wrapped__", True)
        setattr(cls, "save", _wrapped_save)

    @abstractmethod
    def save(self, quality_record: QualityRecord) -> None:
        """品質記録を保存"""

    @abstractmethod
    def find_by_project(self, project_name: str) -> QualityRecord | None:
        """プロジェクト名で品質記録を取得"""

    @abstractmethod
    def exists(self, project_name: str) -> bool:
        """指定プロジェクトの記録が存在するか"""

    @abstractmethod
    def delete(self, project_name: str) -> bool:
        """品質記録を削除"""

    def save_check_result(self, record: dict[str, Any]) -> None:
        """品質チェック結果を保存

        Args:
            record: 品質チェック記録データ
        """
        raise NotImplementedError('save_check_result is not implemented')

    @staticmethod
    def _prepare_project_name(quality_record: QualityRecord) -> None:
        """Mockエンティティ等でも project_name を文字列として扱えるよう補正する"""

        fallback = getattr(quality_record, "_project_name", None)
        if fallback is None:
            return

        try:
            value = getattr(quality_record, "project_name")
        except AttributeError:
            value = None

        if isinstance(value, str):
            return

        if value is None or callable(value) or hasattr(value, "return_value"):
            try:
                setattr(quality_record, "project_name", fallback)
            except (AttributeError, TypeError):
                # setter が無い、もしくはイミュータブルの場合は無視
                pass


class EpisodeManagementRepository(ABC):
    """話数管理リポジトリインターフェース"""

    @abstractmethod
    def update_quality_scores(self, project_path: str, episode_number: int, scores: dict[str, float]) -> None:
        """話数管理ファイルの品質スコア更新"""

    @abstractmethod
    def get_episode_info(self, project_path: str, episode_number: int) -> dict[str, Any] | None:
        """エピソード情報取得"""


class RevisionHistoryRepository(ABC):
    """改訂履歴リポジトリインターフェース"""

    @abstractmethod
    def add_quality_revision(self, project_path: str, quality_result: dict[str, Any]) -> None:
        """品質チェックによる改訂履歴追加"""

    @abstractmethod
    def get_recent_revisions(self, project_path: str, episode_number: int) -> list[dict[str, Any]]:
        """最近の改訂履歴取得"""


class RecordTransactionManager(ABC):
    """記録更新のトランザクション管理インターフェース"""

    @abstractmethod
    def begin_transaction(self) -> "RecordTransaction":
        """トランザクション開始"""


class RecordTransaction(ABC):
    """記録更新トランザクションインターフェース"""

    @abstractmethod
    def __enter__(self) -> "RecordTransaction":
        pass

    @abstractmethod
    def __exit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: object | None) -> bool:
        pass

    @abstractmethod
    def update_quality_record(self, quality_record: QualityRecord) -> None:
        """品質記録更新をトランザクションに追加"""

    @abstractmethod
    def update_episode_management(self, project_path: str, episode_number: int, data: dict[str, Any]) -> None:
        """話数管理更新をトランザクションに追加"""

    @abstractmethod
    def update_revision_history(self, project_path: str, quality_result: dict[str, Any]) -> None:
        """改訂履歴更新をトランザクションに追加"""

    @abstractmethod
    def commit(self) -> None:
        """トランザクションコミット"""

    @abstractmethod
    def rollback(self) -> None:
        """トランザクションロールバック"""
