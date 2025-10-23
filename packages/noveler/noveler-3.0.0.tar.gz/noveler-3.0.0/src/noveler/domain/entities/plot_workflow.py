#!/usr/bin/env python3
# File: src/noveler/domain/entities/plot_workflow.py
# Purpose: Define the PlotWorkflow entity and orchestrate stage prerequisites for plot generation.
# Context: Used by plot creation services relying on workflow stage/value objects within the domain layer.

"""Domain.entities.plot_workflow
Where: Domain entity modelling plot workflows.
What: Tracks workflow stages, transitions, and metadata.
Why: Provides structured workflow data for plot management.
"""

from __future__ import annotations

"""プロット作成ワークフローエンティティ

プロット作成ワークフロー全体を管理するエンティティ
ビジネスルールと制約を実装
"""


from typing import Any, Protocol

from noveler.domain.entities.workflow_stage import WorkflowStage
from noveler.domain.value_objects.prerequisite_rule import PrerequisiteRule
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType


class FileChecker(Protocol):
    """ファイル存在確認のプロトコル"""

    def exists(self, path: str) -> bool:
        """ファイルが存在するかチェック"""
        ...

    def is_file(self, path: str) -> bool:
        """ファイルかどうかチェック"""
        ...

    def is_dir(self, path: str) -> bool:
        """ディレクトリかどうかチェック"""
        ...


class PlotWorkflow:
    """プロット作成ワークフローエンティティ"""

    def __init__(self, project_root: str) -> None:
        """Args:
        project_root: プロジェクトルートディレクトリのパス
        """
        self.project_root = project_root
        self.stages = self._initialize_stages()

    def _initialize_stages(self) -> list[WorkflowStage]:
        """ワークフロー段階を初期化"""
        stages = []

        # 全体構成作成段階
        master_plot_stage = WorkflowStage(
            stage_type=WorkflowStageType.MASTER_PLOT,
            prerequisites=[
                PrerequisiteRule("プロジェクト設定.yaml", True, "プロジェクト基本設定"),
                PrerequisiteRule("10_企画/企画書.yaml", True, "企画書・コンセプト"),
                PrerequisiteRule("30_設定集/キャラクター.yaml", True, "主要キャラクター設定"),
                PrerequisiteRule("30_設定集/世界観.yaml", True, "世界観・背景設定"),
            ],
            output_files=["20_プロット/全体構成.yaml"],
        )

        stages.append(master_plot_stage)

        # 章別プロット作成段階
        chapter_plot_stage = WorkflowStage(
            stage_type=WorkflowStageType.CHAPTER_PLOT,
            prerequisites=[
                PrerequisiteRule("20_プロット/全体構成.yaml", True, "全体構成(マスタープロット)"),
                PrerequisiteRule("30_設定集/キャラクター.yaml", True, "キャラクター設定"),
                PrerequisiteRule("30_設定集/世界観.yaml", False, "世界観設定"),
            ],
            output_files=[
                "20_プロット/章別プロット/chapter{chapter:02d}.yaml",
            ],
        )

        stages.append(chapter_plot_stage)

        # 話数別プロット作成段階
        episode_plot_stage = WorkflowStage(
            stage_type=WorkflowStageType.EPISODE_PLOT,
            prerequisites=[
                PrerequisiteRule("20_プロット/全体構成.yaml", True, "全体構成"),
                PrerequisiteRule(
                    "20_プロット/章別プロット/chapter{chapter:02d}.yaml",
                    True,
                    "所属章のプロット",
                ),
            ],
            output_files=[
                "20_プロット/話別プロット/episode{episode:03d}.yaml",
            ],
        )

        stages.append(episode_plot_stage)

        return stages

    def can_execute_stage(
        self, stage_type: WorkflowStageType, file_checker: FileChecker, **parameters: dict[str, Any]
    ) -> tuple[bool, list]:
        """指定段階が実行可能かチェック

        Args:
            stage_type: チェック対象の段階タイプ
            file_checker: ファイル存在確認オブジェクト
            **parameters: パラメータ

        Returns:
            Tuple[bool, List]: (実行可能か, チェック結果詳細)
        """
        target_stage = None
        for stage in self.stages:
            if stage.stage_type == stage_type:
                target_stage = stage
                break

        if target_stage is None:
            msg = f"不明なワークフロー段階: {stage_type}"
            raise ValueError(msg)

        return target_stage.check_prerequisites(file_checker, **parameters)

    def get_progress(self, file_checker: FileChecker) -> dict[str, dict[str, Any]]:
        """ワークフロー全体の進捗状況を取得

        Args:
            file_checker: ファイル存在確認オブジェクト

        Returns:
            Dict[str, Dict[str, Any]]: 進捗情報
        """
        progress = {}

        for stage in self.stages:
            stage_key = stage.stage_type.value

            # 出力ファイルの存在確認で完了判定
            completed = False
            if stage.output_files:
                output_file = stage.output_files[0]  # 最初の出力ファイルで判定
                # パラメータが必要な場合は簡易的に1で試行
                try:
                    test_path = output_file.format(chapter=1, episode=1)
                except KeyError:
                    test_path = output_file

                completed = file_checker.exists(test_path)

            progress[stage_key] = {
                "completed": completed,
                "stage_name": stage.stage_type.display_name(),
                "prerequisites_count": len(stage.prerequisites),
                "output_files": stage.output_files,
            }

        return progress

    def get_stage_by_type(self, stage_type: WorkflowStageType) -> WorkflowStage:
        """指定タイプの段階を取得

        Args:
            stage_type: 段階タイプ

        Returns:
            WorkflowStage: ワークフロー段階
        """
        for stage in self.stages:
            if stage.stage_type == stage_type:
                return stage

        msg = f"不明なワークフロー段階: {stage_type}"
        raise ValueError(msg)
