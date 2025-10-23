"""10段階執筆システム用のセッション管理（SPEC-MCP-001 v2.2.0対応）"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .ten_stage_writing_execution import TenStageExecutionStage


@dataclass
class TenStageSessionContext:
    """10段階執筆セッションコンテキスト"""

    # セッション基本情報
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    episode_number: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # 執筆設定
    word_count_target: int = 4000
    genre: str = "ライトノベル"
    viewpoint: str = "三人称"
    viewpoint_character: str = "主人公"
    custom_requirements: list[str] = field(default_factory=list)

    # 段階別結果データ
    stage_outputs: dict[TenStageExecutionStage, dict[str, Any]] = field(default_factory=dict)
    completed_stages: set[TenStageExecutionStage] = field(default_factory=set)

    # 実行状況
    current_stage: TenStageExecutionStage | None = None
    total_turns_used: int = 0
    total_execution_time_ms: float = 0.0

    def mark_stage_completed(self, stage: TenStageExecutionStage, output_data: dict[str, Any]) -> None:
        """ステージ完了マーク"""
        self.completed_stages.add(stage)
        self.stage_outputs[stage] = output_data

    def is_stage_completed(self, stage: TenStageExecutionStage) -> bool:
        """ステージ完了確認"""
        return stage in self.completed_stages

    def get_stage_output(self, stage: TenStageExecutionStage) -> dict[str, Any]:
        """ステージ出力データ取得"""
        return self.stage_outputs.get(stage, {})

    def get_all_previous_outputs(self, current_stage: TenStageExecutionStage) -> dict[str, Any]:
        """現在ステージより前の全ての出力データを統合取得"""
        all_stages = TenStageExecutionStage.get_all_stages()
        current_index = all_stages.index(current_stage)

        combined_outputs = {}
        for stage in all_stages[:current_index]:
            if stage in self.stage_outputs:
                stage_data = self.stage_outputs[stage]
                combined_outputs.update(stage_data)

        return combined_outputs

    def get_completion_progress(self) -> tuple[int, int]:
        """完了進捗取得（完了済み数, 全体数）"""
        all_stages = TenStageExecutionStage.get_all_stages()
        return len(self.completed_stages), len(all_stages)

    def is_all_completed(self) -> bool:
        """全ステージ完了確認"""
        completed, total = self.get_completion_progress()
        return completed == total

    def update_performance_metrics(self, turns_used: int, execution_time_ms: float) -> None:
        """パフォーマンス指標更新"""
        self.total_turns_used += turns_used
        self.total_execution_time_ms += execution_time_ms

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換（永続化用）"""
        return {
            "session_id": self.session_id,
            "episode_number": self.episode_number,
            "created_at": self.created_at.isoformat(),
            "word_count_target": self.word_count_target,
            "genre": self.genre,
            "viewpoint": self.viewpoint,
            "viewpoint_character": self.viewpoint_character,
            "custom_requirements": self.custom_requirements,
            "stage_outputs": {stage.value: output for stage, output in self.stage_outputs.items()},
            "completed_stages": [stage.value for stage in self.completed_stages],
            "current_stage": self.current_stage.value if self.current_stage else None,
            "total_turns_used": self.total_turns_used,
            "total_execution_time_ms": self.total_execution_time_ms,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TenStageSessionContext":
        """辞書形式から復元（永続化からの読み込み用）"""
        context = cls(
            session_id=data.get("session_id", str(uuid.uuid4())),
            episode_number=data.get("episode_number", 1),
            word_count_target=data.get("word_count_target", 4000),
            genre=data.get("genre", "ライトノベル"),
            viewpoint=data.get("viewpoint", "三人称"),
            viewpoint_character=data.get("viewpoint_character", "主人公"),
            custom_requirements=data.get("custom_requirements", []),
            total_turns_used=data.get("total_turns_used", 0),
            total_execution_time_ms=data.get("total_execution_time_ms", 0.0),
        )

        # 日付復元
        if "created_at" in data:
            context.created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))

        # ステージ出力復元
        if "stage_outputs" in data:
            for stage_value, output in data["stage_outputs"].items():
                stage = TenStageExecutionStage(stage_value)
                context.stage_outputs[stage] = output

        # 完了ステージ復元
        if "completed_stages" in data:
            for stage_value in data["completed_stages"]:
                stage = TenStageExecutionStage(stage_value)
                context.completed_stages.add(stage)

        # 現在ステージ復元
        if data.get("current_stage"):
            context.current_stage = TenStageExecutionStage(data["current_stage"])

        return context
