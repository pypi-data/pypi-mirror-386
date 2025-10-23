#!/usr/bin/env python3
# File: src/noveler/domain/entities/plot_creation_task.py
# Purpose: Provide the PlotCreationTask aggregate responsible for generating
#          plot output filenames and tracking execution state for plot stages.
# Context: Consumed by application services orchestrating plot generation; relies
#          on workflow stage enums and project time utilities within the domain.
"""Plot creation task entity module.

This module defines the PlotCreationTask entity which manages
the state and business rules for plot creation workflows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from noveler.domain.value_objects.merge_strategy import MergeStrategy
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class PlotCreationTask:
    """プロット作成タスクエンティティ"""

    def __init__(
        self,
        stage_type: WorkflowStageType,
        project_root: Path,
        parameters: dict[str, Any] | None = None,
        merge_strategy: MergeStrategy = MergeStrategy.MERGE,
    ) -> None:
        """Args:
        stage_type: ワークフロー段階タイプ
        project_root: プロジェクトルートディレクトリのパス
        parameters: タスクパラメータ
        merge_strategy: マージ戦略(デフォルトはMERGE)
        """
        self.stage_type = stage_type
        self.project_root = project_root
        self.parameters = parameters or {}
        self.merge_strategy = merge_strategy

        # タスク状態
        self.status = "pending"
        self.created_at = project_now().datetime
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None
        self.failed_at: datetime | None = None
        self.error_message: str | None = None
        self.created_files: list[str] = []

    def start_execution(self) -> None:
        """タスク実行を開始"""
        if self.status != "pending":
            msg = f"タスクは既に実行中または完了しています: {self.status}"
            raise ValueError(msg)

        self.status = "in_progress"
        self.started_at = project_now().datetime

    def complete_execution(self, created_files: list[str]) -> None:
        """タスク実行を完了"""
        if self.status != "in_progress":
            msg = f"タスクは実行中ではありません: {self.status}"
            raise ValueError(msg)

        self.status = "completed"
        self.completed_at = project_now().datetime
        self.created_files = created_files.copy()

    def fail_execution(self, error_message: str) -> None:
        """タスク実行を失敗"""
        if self.status not in ["pending", "in_progress"]:
            msg = f"タスクは既に完了または失敗しています: {self.status}"
            raise ValueError(msg)

        self.status = "failed"
        self.failed_at = project_now().datetime
        self.error_message = error_message

    def generate_output_path(self) -> str:
        """パラメータから出力ファイルパスを生成

        Returns:
            str: 出力ファイルパス
        """
        base_dir = f"{self.project_root}/20_プロット"

        if self.stage_type == WorkflowStageType.MASTER_PLOT:
            return f"{base_dir}/全体構成.yaml"

        if self.stage_type == WorkflowStageType.CHAPTER_PLOT:
            chapter = int(self.parameters.get("chapter", 1))
            return f"{base_dir}/章別プロット/chapter{chapter:02d}.yaml"

        if self.stage_type == WorkflowStageType.EPISODE_PLOT:
            episode = int(self.parameters.get("episode", 1))
            return f"{base_dir}/話別プロット/episode{episode:03d}.yaml"

        msg = f"不明なワークフロー段階: {self.stage_type}"
        raise ValueError(msg)

    def is_completed(self) -> bool:
        """タスクが完了しているかどうか"""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """タスクが失敗しているかどうか"""
        return self.status == "failed"

    def is_in_progress(self) -> bool:
        """タスクが実行中かどうか"""
        return self.status == "in_progress"
