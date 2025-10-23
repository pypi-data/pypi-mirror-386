"""自動連鎖実行ステージエンティティ"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from noveler.domain.value_objects.episode_number import EpisodeNumber


class ChainStage(Enum):
    """実行ステージ"""

    STAGE_1 = "stage_1"
    STAGE_2 = "stage_2"
    STAGE_3 = "stage_3"
    STAGE_4 = "stage_4"


class ChainExecutionStatus(Enum):
    """実行状態"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageExecution:
    """ステージ実行情報"""

    stage: ChainStage
    status: ChainExecutionStatus
    start_time: datetime | None = None
    end_time: datetime | None = None
    error_message: str | None = None
    output_data: dict[str, Any] | None = None
    next_stage_command: str | None = None

    def start(self) -> None:
        """実行開始"""
        self.status = ChainExecutionStatus.IN_PROGRESS
        self.start_time = datetime.now(timezone.utc)

    def complete(self, output_data: dict[str, Any] | None = None, next_command: str | None = None) -> None:
        """実行完了"""
        self.status = ChainExecutionStatus.COMPLETED
        self.end_time = datetime.now(timezone.utc)
        self.output_data = output_data
        self.next_stage_command = next_command

    def fail(self, error_message: str) -> None:
        """実行失敗"""
        self.status = ChainExecutionStatus.FAILED
        self.end_time = datetime.now(timezone.utc)
        self.error_message = error_message

    def skip(self, reason: str) -> None:
        """実行スキップ"""
        self.status = ChainExecutionStatus.SKIPPED
        self.end_time = datetime.now(timezone.utc)
        self.error_message = reason

    @property
    def duration_seconds(self) -> float | None:
        """実行時間（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def is_completed(self) -> bool:
        """完了済みか"""
        return self.status == ChainExecutionStatus.COMPLETED

    def is_failed(self) -> bool:
        """失敗したか"""
        return self.status == ChainExecutionStatus.FAILED


class AutoChainingStage:
    """自動連鎖実行ステージエンティティ"""

    def __init__(self, episode_number: EpisodeNumber) -> None:
        self.episode_number = episode_number
        self.execution_id = f"auto_chain_{episode_number.value}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        self.stages: dict[ChainStage, StageExecution] = {}
        self.current_stage: ChainStage | None = None
        self.created_at = datetime.now(timezone.utc)
        self._initialize_stages()

    def _initialize_stages(self) -> None:
        """ステージを初期化"""
        for stage in ChainStage:
            self.stages[stage] = StageExecution(stage=stage, status=ChainExecutionStatus.PENDING)

    def start_stage(self, stage: ChainStage) -> None:
        """ステージ開始"""
        if stage not in self.stages:
            msg = f"Invalid stage: {stage}"
            raise ValueError(msg)

        self.current_stage = stage
        self.stages[stage].start()

    def complete_stage(
        self, stage: ChainStage, output_data: dict[str, Any] | None = None, next_command: str | None = None
    ) -> None:
        """ステージ完了"""
        if stage not in self.stages:
            msg = f"Invalid stage: {stage}"
            raise ValueError(msg)

        self.stages[stage].complete(output_data, next_command)

    def fail_stage(self, stage: ChainStage, error_message: str) -> None:
        """ステージ失敗"""
        if stage not in self.stages:
            msg = f"Invalid stage: {stage}"
            raise ValueError(msg)

        self.stages[stage].fail(error_message)

    def get_next_stage(self) -> ChainStage | None:
        """次のステージを取得"""
        stage_order = [ChainStage.STAGE_1, ChainStage.STAGE_2, ChainStage.STAGE_3, ChainStage.STAGE_4]

        if self.current_stage is None:
            return ChainStage.STAGE_1

        try:
            current_index = stage_order.index(self.current_stage)
            if current_index < len(stage_order) - 1:
                return stage_order[current_index + 1]
        except ValueError:
            pass

        return None

    def has_next_stage(self) -> bool:
        """次のステージがあるか"""
        return self.get_next_stage() is not None

    def get_stage_execution(self, stage: ChainStage) -> StageExecution | None:
        """ステージ実行情報を取得"""
        return self.stages.get(stage)

    def get_completed_stages(self) -> list[ChainStage]:
        """完了済みステージのリスト"""
        return [stage for stage, execution in self.stages.items() if execution.is_completed()]

    def get_failed_stages(self) -> list[ChainStage]:
        """失敗したステージのリスト"""
        return [stage for stage, execution in self.stages.items() if execution.is_failed()]

    def is_all_completed(self) -> bool:
        """全ステージ完了か"""
        return len(self.get_completed_stages()) == len(ChainStage)

    def has_failed_stage(self) -> bool:
        """失敗したステージがあるか"""
        return len(self.get_failed_stages()) > 0

    def get_progress_percentage(self) -> float:
        """進捗率（%）"""
        completed_count = len(self.get_completed_stages())
        total_count = len(ChainStage)
        return (completed_count / total_count) * 100.0

    def generate_summary(self) -> dict[str, Any]:
        """実行サマリーを生成"""
        return {
            "execution_id": self.execution_id,
            "episode_number": self.episode_number.value,
            "current_stage": self.current_stage.value if self.current_stage else None,
            "progress_percentage": self.get_progress_percentage(),
            "completed_stages": [s.value for s in self.get_completed_stages()],
            "failed_stages": [s.value for s in self.get_failed_stages()],
            "is_all_completed": self.is_all_completed(),
            "has_failed_stage": self.has_failed_stage(),
            "created_at": self.created_at.isoformat(),
            "stages_detail": {
                stage.value: {
                    "status": execution.status.value,
                    "duration_seconds": execution.duration_seconds,
                    "error_message": execution.error_message,
                    "has_output": execution.output_data is not None,
                    "has_next_command": execution.next_stage_command is not None,
                }
                for stage, execution in self.stages.items()
            },
        }
