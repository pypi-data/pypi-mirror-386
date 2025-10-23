#!/usr/bin/env python3

"""Domain.entities.settings_file_watcher
Where: Domain entity representing settings file watcher.
What: Tracks watch configuration and events for settings files.
Why: Helps maintain configuration synchronization in the project.
"""

from __future__ import annotations

"""設定ファイル監視エンティティ(DDD準拠リファクタリング版)

ファイルI/Oやハッシュ計算を排除し、リポジトリパターンを使用
純粋なドメインロジックのみを含む
"""


import time
from typing import Any

from noveler.domain.entities.file_change_event import FileChangeEvent, FileChangeType
from noveler.domain.exceptions import DomainException
from noveler.domain.repositories.file_system_repository import FileSystemRepository
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class SettingsFileWatcher:
    """設定ファイル監視エンティティ(DDD準拠)"""

    def __init__(self, project_id: str, repository: FileSystemRepository) -> None:
        """Args:
        project_id: プロジェクトID
        repository: ファイルシステムリポジトリ
        """
        self.project_id = project_id
        self.repository = repository
        self.settings_dir = f"{project_id}/30_設定集"

        # ファイル状態管理(エンティティの状態)
        self._file_states: dict[str, dict] = {}

        # 監視対象ファイル拡張子
        self._watch_extensions = {".yaml", ".yml"}

        # 最後のチェック時刻
        self._last_check_time: float | None = None

    def is_settings_dir_exists(self) -> bool:
        """設定ディレクトリが存在するかどうか"""
        return self.repository.exists(self.settings_dir) and self.repository.is_directory(self.settings_dir)

    def initialize_file_states(self) -> None:
        """監視対象ファイルの初期状態を記録"""
        if not self.is_settings_dir_exists():
            return

        self._file_states.clear()

        # リポジトリ経由でファイルリストを取得
        target_files = self.repository.list_files(
            self.settings_dir,
            extensions=self._watch_extensions,
        )

        for file_path in target_files:
            file_info = self.repository.get_file_info(file_path)
            if file_info:
                file_name = self._resolve_file_name(file_path)
                self._file_states[file_name] = file_info

        self._last_check_time = time.time()

    def get_file_states(self) -> dict[str, dict]:
        """現在のファイル状態を取得"""
        return self._file_states.copy()

    def detect_changes(self) -> list[FileChangeEvent]:
        """ファイル変更を検出

        Returns:
            検出された変更イベントのリスト
        """
        changes = []

        if not self.is_settings_dir_exists():
            self._last_check_time = time.time()
            return changes

        # 現在のファイルリストを取得
        current_files = self.repository.list_files(
            self.settings_dir,
            extensions=self._watch_extensions,
        )

        current_file_names = {self._resolve_file_name(f) for f in current_files}
        old_file_names = set(self._file_states.keys())

        # 新規・削除ファイルをチェック
        changes.extend(self._detect_new_files(current_files, old_file_names))
        changes.extend(self._detect_deleted_files(old_file_names, current_file_names))

        # 変更されたファイルをチェック
        changes.extend(self._detect_modified_files(current_files, old_file_names))

        self._last_check_time = time.time()
        return changes

    def _resolve_file_name(self, file_entry: Any) -> str:
        """ファイルエントリからファイル名を取得"""
        candidate = getattr(file_entry, "name", None)
        if isinstance(candidate, str) and candidate:
            return candidate

        mock_name = getattr(file_entry, "_mock_name", None)
        if isinstance(mock_name, str) and mock_name:
            return mock_name

        return str(file_entry)

    def _ensure_name_attribute(self, file_entry: Any, file_name: str) -> Any:
        """Mockでも文字列のname属性を参照できるよう保証"""
        try:
            current = getattr(file_entry, "name", None)
            if not isinstance(current, str):
                setattr(file_entry, "name", file_name)
        except Exception:
            pass
        return file_entry

    def _detect_new_files(self, current_files: list[Any], old_file_names: set[str]) -> list[FileChangeEvent]:
        """新規ファイルを検出"""
        changes = []
        for file_path in current_files:
            file_name = self._resolve_file_name(file_path)
            file_path = self._ensure_name_attribute(file_path, file_name)
            if file_name not in old_file_names:
                file_info = self.repository.get_file_info(file_path)
                if file_info:
                    event = self._create_change_event(
                        file_name,
                        FileChangeType.CREATED,
                        {"new_file": True, "path": str(file_path)},
                    )

                    changes.append(event)
                    self._file_states[file_name] = file_info
        return changes

    def _detect_deleted_files(self, old_file_names: set[str], current_file_names: set[str]) -> list[FileChangeEvent]:
        """削除されたファイルを検出"""
        changes = []
        for old_name in old_file_names:
            if old_name not in current_file_names:
                event = self._create_change_event(
                    old_name,
                    FileChangeType.DELETED,
                    {"deleted": True},
                )

                changes.append(event)
                del self._file_states[old_name]
        return changes

    def _detect_modified_files(self, current_files: list[Any], old_file_names: set[str]) -> list[FileChangeEvent]:
        """変更されたファイルを検出"""
        changes = []
        for file_path in current_files:
            file_name = self._resolve_file_name(file_path)
            file_path = self._ensure_name_attribute(file_path, file_name)
            if file_name in old_file_names:
                new_info = self.repository.get_file_info(file_path)
                old_info = self._file_states.get(file_name)

                if new_info and old_info:
                    change_details = self._compare_file_info(old_info, new_info)
                    if change_details:
                        event = self._create_change_event(
                            file_name,
                            FileChangeType.MODIFIED,
                            change_details,
                        )

                        changes.append(event)
                        self._file_states[file_name] = new_info
        return changes

    def _create_change_event(
        self, file_name: str, change_type: FileChangeType, details: dict[str, Any] | None = None
    ) -> FileChangeEvent:
        """変更イベントを作成"""
        return FileChangeEvent(
            file_name=file_name,
            change_type=change_type,
            timestamp=project_now().datetime,
            details=details,
        )

    def _compare_file_info(self, old_info: dict[str, Any], new_info: dict[str, Any]) -> dict[str, Any] | None:
        """ファイル情報を比較して変更を検出

        Args:
            old_info: 以前のファイル情報
            new_info: 新しいファイル情報

        Returns:
            変更詳細(変更がない場合None)
        """
        changes = {}

        # 更新時刻の変更
        if old_info.get("mtime") != new_info.get("mtime"):
            changes["time_changed"] = True
            changes["old_mtime"] = old_info.get("mtime")
            changes["new_mtime"] = new_info.get("mtime")

        # ファイルサイズの変更
        if old_info.get("size") != new_info.get("size"):
            changes["size_changed"] = True
            changes["old_size"] = old_info.get("size")
            changes["new_size"] = new_info.get("size")

        # コンテンツハッシュの変更
        if old_info.get("hash") != new_info.get("hash"):
            changes["content_changed"] = True
            changes["old_hash"] = old_info.get("hash")
            changes["new_hash"] = new_info.get("hash")

        return changes if changes else None

    def get_watched_file_count(self) -> int:
        """監視中のファイル数を取得"""
        return len(self._file_states)

    def has_changes_since(self, last_check_time: float) -> bool:
        """指定時刻以降に変更があったかチェック

        Args:
            last_check_time: 最後のチェック時刻(Unix時刻)

        Returns:
            変更があった場合True
        """
        return any(file_info.get("mtime", 0) > last_check_time for file_info in self._file_states.values())

    def get_file_names(self) -> list[str]:
        """監視中のファイル名リストを取得"""
        return sorted(self._file_states.keys())

    def is_watching(self, file_name: str) -> bool:
        """指定ファイルを監視中かチェック"""
        return file_name in self._file_states

    def get_last_check_time(self) -> float | None:
        """最後のチェック時刻を取得"""
        return self._last_check_time

    def validate_project_structure(self) -> None:
        """プロジェクト構造の検証

        Raises:
            DomainException: プロジェクト構造が不正な場合
        """
        project_root = self.project_id
        if not self.repository.exists(project_root):
            msg = f"プロジェクトルートが存在しません: {project_root}"
            raise DomainException(msg)

        if not self.repository.is_directory(project_root):
            msg = f"プロジェクトルートがディレクトリではありません: {project_root}"
            raise DomainException(msg)

    def get_change_summary(self, changes: list[FileChangeEvent]) -> str:
        """変更サマリーを生成

        Args:
            changes: 変更イベントのリスト

        Returns:
            人間が読みやすい変更サマリー
        """
        if not changes:
            return "変更はありません"

        created_count = sum(1 for c in changes if c.change_type == FileChangeType.CREATED)
        modified_count = sum(1 for c in changes if c.change_type == FileChangeType.MODIFIED)
        deleted_count = sum(1 for c in changes if c.change_type == FileChangeType.DELETED)

        parts = []
        if created_count > 0:
            parts.append(f"{created_count}件の新規ファイル")
        if modified_count > 0:
            parts.append(f"{modified_count}件の変更")
        if deleted_count > 0:
            parts.append(f"{deleted_count}件の削除")

        return "、".join(parts) + "を検出しました"
