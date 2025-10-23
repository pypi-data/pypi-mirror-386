"""Domain.value_objects.workflow_stage_type
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""ワークフロー段階タイプ値オブジェクト

プロット作成ワークフローの段階を表現する値オブジェクト
"""


from enum import Enum


class WorkflowStageType(Enum):
    """ワークフロー段階タイプ"""

    MASTER_PLOT = "master_plot"
    CHAPTER_PLOT = "chapter_plot"
    EPISODE_PLOT = "episode_plot"

    def display_name(self) -> str:
        """表示用名称を取得

        Returns:
            str: 表示用名称
        """
        display_names = {
            "master_plot": "全体構成作成",
            "chapter_plot": "章別プロット作成",
            "episode_plot": "話数別プロット作成",
        }
        return display_names.get(self.value, self.value)

    @classmethod
    def get_execution_order(cls) -> list[WorkflowStageType]:
        """ワークフロー段階の実行順序を取得

        Returns:
            list[WorkflowStageType]: 実行順序のリスト
        """
        return [
            cls.MASTER_PLOT,
            cls.CHAPTER_PLOT,
            cls.EPISODE_PLOT,
        ]
