"""プロット関連ドメインコマンド

SPEC-901-DDD-REFACTORING対応:
- プロット生成・管理に関するドメインコマンド
- Message Bus経由でのCQRS実装
"""

from dataclasses import dataclass, field
from typing import Any

from noveler.domain.commands.base import DomainCommand


@dataclass
class GeneratePlotCommand(DomainCommand):
    """プロット生成コマンド

    既存のPlotGenerationUseCaseをコマンドベースに統合
    """

    # プロット生成パラメータ（必須だが、dataclassのフィールド順序制約によりデフォルト値設定）
    project_root: str = ""

    # プロット生成パラメータ（オプション）
    episode_number: int | None = None
    chapter_title: str | None = None
    target_length: int | None = None
    genre: str | None = None

    # 生成オプション
    use_ai_enhancement: bool = True
    quality_check: bool = True
    auto_save: bool = True

    # コンテキスト情報
    existing_plots: list[str] | None = None
    character_list: list[str] | None = None
    story_context: dict[str, Any] | None = None

    def __post_init__(self):
        """初期化後処理"""
        super().__post_init__()
        if not self.project_root:
            msg = "project_root is required"
            raise ValueError(msg)


@dataclass
class ValidatePlotCommand(DomainCommand):
    """プロット品質チェックコマンド"""

    plot_content: str = ""
    validation_criteria: dict[str, Any] = field(default_factory=dict)
    project_root: str = ""

    def __post_init__(self):
        """初期化後処理"""
        super().__post_init__()
        if not self.plot_content:
            msg = "plot_content is required"
            raise ValueError(msg)
        if not self.project_root:
            msg = "project_root is required"
            raise ValueError(msg)


@dataclass
class SavePlotCommand(DomainCommand):
    """プロット保存コマンド"""

    plot_content: str = ""
    file_path: str = ""
    backup_existing: bool = True
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        """初期化後処理"""
        super().__post_init__()
        if not self.plot_content:
            msg = "plot_content is required"
            raise ValueError(msg)
        if not self.file_path:
            msg = "file_path is required"
            raise ValueError(msg)


@dataclass
class UpdateMasterPlotCommand(DomainCommand):
    """マスタープロット更新コマンド"""

    episode_plot_path: str = ""
    master_plot_path: str = ""
    integration_mode: str = "append"  # "append", "merge", "replace"

    def __post_init__(self):
        """初期化後処理"""
        super().__post_init__()
        if not self.episode_plot_path:
            msg = "episode_plot_path is required"
            raise ValueError(msg)
        if not self.master_plot_path:
            msg = "master_plot_path is required"
            raise ValueError(msg)
