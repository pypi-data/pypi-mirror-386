"""プロット関連ドメインイベント

SPEC-901-DDD-REFACTORING対応:
- プロット生成・管理に関するドメインイベント
- Message Bus経由でのイベント駆動処理
"""

from dataclasses import dataclass
from typing import Any

from noveler.domain.events.base import DomainEvent


@dataclass
class PlotGenerationStarted(DomainEvent):
    """プロット生成開始イベント"""

    command_id: str = ""
    episode_number: int | None = None
    chapter_title: str | None = None
    generation_mode: str = "ai_enhanced"

    def __post_init__(self):
        """初期化後処理"""
        super().__post_init__()
        if not self.command_id:
            msg = "command_id is required"
            raise ValueError(msg)


@dataclass
class PlotGenerationCompleted(DomainEvent):
    """プロット生成完了イベント"""

    command_id: str = ""
    plot_file_path: str = ""
    generation_stats: dict[str, Any] = None
    quality_score: float | None = None

    def __post_init__(self):
        """初期化後処理"""
        super().__post_init__()
        if not self.command_id:
            msg = "command_id is required"
            raise ValueError(msg)
        if not self.plot_file_path:
            msg = "plot_file_path is required"
            raise ValueError(msg)
        if self.generation_stats is None:
            self.generation_stats = {}


@dataclass
class PlotGenerationFailed(DomainEvent):
    """プロット生成失敗イベント"""

    command_id: str = ""
    error_message: str = ""
    error_type: str = ""
    retry_count: int = 0

    def __post_init__(self):
        """初期化後処理"""
        super().__post_init__()
        if not self.command_id:
            msg = "command_id is required"
            raise ValueError(msg)
        if not self.error_message:
            msg = "error_message is required"
            raise ValueError(msg)


@dataclass
class PlotQualityCheckCompleted(DomainEvent):
    """プロット品質チェック完了イベント"""

    plot_file_path: str = ""
    quality_score: float = 0.0
    quality_metrics: dict[str, Any] = None
    passed_validation: bool = False

    def __post_init__(self):
        """初期化後処理"""
        super().__post_init__()
        if not self.plot_file_path:
            msg = "plot_file_path is required"
            raise ValueError(msg)
        if self.quality_metrics is None:
            self.quality_metrics = {}


@dataclass
class PlotSaved(DomainEvent):
    """プロット保存完了イベント"""

    file_path: str = ""
    backup_path: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        """初期化後処理"""
        super().__post_init__()
        if not self.file_path:
            msg = "file_path is required"
            raise ValueError(msg)


@dataclass
class MasterPlotUpdated(DomainEvent):
    """マスタープロット更新完了イベント"""

    master_plot_path: str = ""
    episode_count: int = 0
    integration_mode: str = ""
    updated_sections: list[str] = None

    def __post_init__(self):
        """初期化後処理"""
        super().__post_init__()
        if not self.master_plot_path:
            msg = "master_plot_path is required"
            raise ValueError(msg)
        if not self.integration_mode:
            msg = "integration_mode is required"
            raise ValueError(msg)
        if self.updated_sections is None:
            self.updated_sections = []
