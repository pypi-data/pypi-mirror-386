#!/usr/bin/env python3
"""ファイル変更イベントエンティティ

SPEC-CLAUDE-003に基づくファイル監視ドメインエンティティ
設定ファイルの変更とコードファイルの変更を統合管理
"""

import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.project_time import project_now


class ChangeType(str, Enum):
    """ファイル変更タイプ"""

    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"
    CREATED = "ADDED"  # 新規作成は追加扱い(エイリアス)
    MOVED = "MODIFIED"  # 移動は変更扱い(エイリアス)


# 後方互換性のためのエイリアス
FileChangeType = ChangeType


class FileEventStatus(Enum):
    """ファイルイベント処理ステータス"""

    DETECTED = "detected"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WatchMode:
    """監視モード値オブジェクト"""

    def __init__(self, mode: str) -> None:
        if mode not in ["continuous", "oneshot"]:
            msg = f"無効な監視モード: {mode}"
            raise ValueError(msg)
        self.mode = mode

    @classmethod
    def continuous(cls) -> "WatchMode":
        """継続監視モード"""
        return cls("continuous")

    @classmethod
    def oneshot(cls) -> "WatchMode":
        """ワンショット監視モード"""
        return cls("oneshot")


class FilePattern:
    """ファイルパターン値オブジェクト"""

    def __init__(self, include_patterns: list[str], exclude_patterns: list[str]) -> None:
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns

    def matches(self, file_path: Path) -> bool:
        """ファイルパスがパターンにマッチするかチェック"""
        file_str = str(file_path)

        # 除外パターンのチェック
        for exclude in self.exclude_patterns:
            if exclude in file_str or file_path.match(exclude):
                return False

        # 包含パターンのチェック
        return any(include in file_str or file_path.match(include) for include in self.include_patterns)

    @classmethod
    def python_files(cls) -> "FilePattern":
        """Pythonファイル用のデフォルトパターン"""
        return cls(
            include_patterns=["*.py"], exclude_patterns=["__pycache__", "*.pyc", "temp/", ".pytest_cache", "backup/"]
        )


class FileChangeEvent:
    """ファイル変更イベントエンティティ"""

    def __init__(
        self,
        file_path: str | None = None,
        change_type: ChangeType | str = ChangeType.MODIFIED,
        timestamp: datetime | None = None,
        event_id: str | None = None,
        details: dict[str, Any] | None = None,
        file_name: str | None = None,
    ) -> None:
        """Args:
        file_path: 変更されたファイルのパス(文字列)
        change_type: 変更タイプ(ADDED/MODIFIED/DELETED/CREATED/MOVED)
        timestamp: 変更発生時刻
        event_id: イベントID(watchdog統合用)
        """
        if file_path is None and file_name is None:
            msg = "file_path か file_name のどちらかは必須です"
            raise ValueError(msg)

        resolved_file_path = str(file_path or file_name or "")
        resolved_file_name = file_name or Path(resolved_file_path).name

        try:
            change_type_member = change_type if isinstance(change_type, ChangeType) else ChangeType(change_type)
        except ValueError as exc:
            msg = f"無効な変更タイプ: {change_type}"
            raise ValueError(msg) from exc

        self.file_path = resolved_file_path
        self.file_name = resolved_file_name
        self.change_type: ChangeType = change_type_member
        self.timestamp = timestamp or project_now().datetime
        self.details = details or {}

        # watchdog統合用の新フィールド
        self.event_id = event_id or str(uuid.uuid4())
        self.status = FileEventStatus.DETECTED
        self.processed_at: datetime | None = None
        self.error_message: str | None = None
        self.should_trigger_export = False
        self.debounce_group: str | None = None

        # ビジネスルール検証
    def is_settings_file(self) -> bool:
        """設定ファイルかどうかの判定

        Returns:
            bool: 30_設定集ディレクトリ内のファイルの場合True
        """
        return "30_設定集" in str(self.file_path)

    def requires_extraction(self) -> bool:
        """固有名詞抽出が必要かどうかの判定

        Returns:
            bool: 抽出が必要な場合True
        """
        # 設定ファイルのYAML変更のみ抽出対象
        if not self.is_settings_file():
            return False

        # YAMLファイルのみ対象
        file_path_lower = str(self.file_path).lower()
        if not file_path_lower.endswith((".yaml", ".yml")):
            return False

        # 削除・変更・追加いずれも抽出対象
        return self.change_type in {ChangeType.ADDED, ChangeType.MODIFIED, ChangeType.DELETED}

    def get_file_category(self) -> str | None:
        """ファイルのカテゴリを取得

        Returns:
            Optional[str]: ファイルカテゴリ(キャラクター、世界観等)
        """
        # ファイル名の取得
        file_name = self.file_path.split("/")[-1].lower()

        if "キャラクター" in file_name or "character" in file_name:
            return "character"
        if "世界観" in file_name or "world" in file_name:
            return "world"
        if "用語集" in file_name or "term" in file_name:
            return "terminology"
        if "魔法" in file_name or "magic" in file_name:
            return "magic"
        if "技術" in file_name or "tech" in file_name:
            return "technology"
        return "other"

    def is_deletion(self) -> bool:
        """削除イベントかどうか"""
        return self.change_type == ChangeType.DELETED

    def is_addition(self) -> bool:
        """追加イベントかどうか"""
        return self.change_type == ChangeType.ADDED

    def is_modification(self) -> bool:
        """変更イベントかどうか"""
        return self.change_type == ChangeType.MODIFIED

    def get_priority(self) -> int:
        """処理優先度を取得

        Returns:
            int: 優先度(数値が小さいほど高優先度)
        """
        # 削除 > 変更 > 追加の順で処理
        priority_map = {
            ChangeType.DELETED: 1,
            ChangeType.MODIFIED: 2,
            ChangeType.ADDED: 3,
        }
        return priority_map.get(self.change_type, 99)

    def __eq__(self, other: object) -> bool:
        """等価比較"""
        if not isinstance(other, FileChangeEvent):
            return False
        return self.file_path == other.file_path and self.change_type == other.change_type

    def __hash__(self) -> int:
        """ハッシュ値"""
        return hash((str(self.file_path), self.change_type))

    def __str__(self) -> str:
        """文字列表現"""
        return f"FileChangeEvent(file={self.file_name}, change_type={self.change_type})"

    def __repr__(self) -> str:
        """デバッグ用文字列表現"""
        return (
            f"FileChangeEvent(file_path={self.file_path}, change_type={self.change_type}, timestamp={self.timestamp})"
        )

    # watchdog統合用の新しいメソッド

    def start_processing(self) -> None:
        """処理開始"""
        if self.status != FileEventStatus.DETECTED:
            msg = f"処理開始できないステータス: {self.status}"
            raise ValueError(msg)

        self.status = FileEventStatus.PROCESSING
        self.processed_at = project_now().datetime

    def complete_processing(self, trigger_export: bool = False) -> None:
        """処理完了"""
        if self.status != FileEventStatus.PROCESSING:
            msg = f"処理完了できないステータス: {self.status}"
            raise ValueError(msg)

        self.status = FileEventStatus.COMPLETED
        self.should_trigger_export = trigger_export

    def fail_processing(self, error_message: str) -> None:
        """処理失敗"""
        if self.status != FileEventStatus.PROCESSING:
            msg = f"処理失敗できないステータス: {self.status}"
            raise ValueError(msg)

        self.status = FileEventStatus.FAILED
        self.error_message = error_message

    def skip_processing(self, reason: str) -> None:
        """処理スキップ"""
        self.status = FileEventStatus.SKIPPED
        self.error_message = reason

    def is_python_file(self) -> bool:
        """Pythonファイルかどうか判定"""
        return str(self.file_path).endswith(".py")

    def is_in_scripts_directory(self) -> bool:
        """scriptsディレクトリ内のファイルかどうか判定"""
        return "scripts" in str(self.file_path)

    def should_process(self, file_pattern: FilePattern) -> bool:
        """処理すべきイベントかどうか判定"""
        # 削除イベントは処理しない
        if self.change_type == ChangeType.DELETED:
            return False

        # ファイルパターンにマッチしない場合は処理しない
        file_path_obj = Path(self.file_path)
        if not file_pattern.matches(file_path_obj):
            return False

        # ファイルが存在しない場合は処理しない
        return file_path_obj.exists()

    def set_debounce_group(self, group_id: str) -> None:
        """デバウンスグループを設定"""
        self.debounce_group = group_id

    def get_processing_duration(self) -> float | None:
        """処理時間を取得(秒)"""
        if not self.processed_at:
            return None

        if self.status in [FileEventStatus.PROCESSING]:
            return (project_now().datetime - self.processed_at).total_seconds()

        return (project_now().datetime - self.processed_at).total_seconds()

    def to_dict(self) -> dict[str, any]:
        """辞書形式に変換"""
        return {
            "event_id": self.event_id,
            "file_path": str(self.file_path),
            "change_type": self.change_type.value,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "detected_at": self.timestamp.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "should_trigger_export": self.should_trigger_export,
            "error_message": self.error_message,
            "debounce_group": self.debounce_group,
        }
