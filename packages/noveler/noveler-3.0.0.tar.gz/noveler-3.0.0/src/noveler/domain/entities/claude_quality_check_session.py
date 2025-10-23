"""Claude品質チェックセッション ドメインエンティティ
仕様: Claude Code品質チェック統合システム
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from noveler.domain.value_objects.claude_quality_check_request import (
    ClaudeQualityCheckRequest,
    ClaudeQualityCheckResult,
)
from noveler.domain.value_objects.session_id import SessionId


class QualityCheckStatus(Enum):
    """品質チェック状態"""

    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QualityCheckStage(Enum):
    """品質チェック段階"""

    PREPARATION = "preparation"
    MANUSCRIPT_ANALYSIS = "manuscript_analysis"
    CREATIVE_EVALUATION = "creative_evaluation"
    READER_EXPERIENCE_CHECK = "reader_experience_check"
    STRUCTURAL_VALIDATION = "structural_validation"
    RESULT_COMPILATION = "result_compilation"
    COMPLETED = "completed"


@dataclass
class ClaudeQualityCheckSession:
    """Claude品質チェックセッション エンティティ

    Claude Codeによる品質評価の一連のプロセスを管理するドメインエンティティ
    品質チェックの状態、進捗、結果を一元管理する
    """

    # エンティティID（不変）
    session_id: SessionId = field(default_factory=lambda: SessionId(str(uuid.uuid4())))

    # 基本情報
    request: ClaudeQualityCheckRequest | None = None
    result: ClaudeQualityCheckResult | None = None

    # 状態管理
    status: QualityCheckStatus = QualityCheckStatus.PENDING
    current_stage: QualityCheckStage = QualityCheckStage.PREPARATION

    # タイムスタンプ
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # 進捗・メタデータ
    stage_progress: dict[QualityCheckStage, bool] = field(default_factory=dict)
    execution_metadata: dict[str, str] = field(default_factory=dict)
    error_log: list[str] = field(default_factory=list)

    # 分析データ
    intermediate_scores: dict[str, int] = field(default_factory=dict)
    analysis_notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """エンティティ初期化後処理"""
        # 全段階を未完了として初期化
        for stage in QualityCheckStage:
            if stage not in self.stage_progress:
                self.stage_progress[stage] = False

    def start_analysis(self, request: ClaudeQualityCheckRequest) -> None:
        """品質分析開始"""
        if self.status != QualityCheckStatus.PENDING:
            msg = f"セッション開始できません。現在の状態: {self.status}"
            raise ValueError(msg)

        self.request = request
        self.status = QualityCheckStatus.ANALYZING
        self.current_stage = QualityCheckStage.PREPARATION
        self.started_at = datetime.now(timezone.utc)

        self._add_analysis_note(f"品質分析開始: {request.get_context_summary()}")

    def advance_to_stage(self, next_stage: QualityCheckStage) -> None:
        """次段階への進行"""
        if self.status != QualityCheckStatus.ANALYZING:
            msg = f"段階進行できません。現在の状態: {self.status}"
            raise ValueError(msg)

        # 現在段階を完了としてマーク
        self.stage_progress[self.current_stage] = True

        # 次段階に進行
        self.current_stage = next_stage
        self._add_analysis_note(f"段階進行: {next_stage.value}")

    def record_intermediate_score(self, category: str, score: int) -> None:
        """中間スコア記録"""
        if not (0 <= score <= 100):
            msg = f"無効なスコア値: {score}"
            raise ValueError(msg)

        self.intermediate_scores[category] = score
        self._add_analysis_note(f"中間スコア記録: {category}={score}")

    def complete_analysis(self, result: ClaudeQualityCheckResult) -> None:
        """品質分析完了"""
        if self.status != QualityCheckStatus.ANALYZING:
            msg = f"分析完了できません。現在の状態: {self.status}"
            raise ValueError(msg)

        self.result = result
        self.status = QualityCheckStatus.COMPLETED
        self.current_stage = QualityCheckStage.COMPLETED
        self.completed_at = datetime.now(timezone.utc)

        # 全段階を完了としてマーク
        for stage in self.stage_progress:
            self.stage_progress[stage] = True

        self._add_analysis_note(f"品質分析完了: 総合スコア{result.total_score}点")

    def fail_analysis(self, error_message: str) -> None:
        """品質分析失敗"""
        self.status = QualityCheckStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error_log.append(f"{datetime.now(timezone.utc)}: {error_message}")
        self._add_analysis_note(f"分析失敗: {error_message}")

    def cancel_analysis(self, reason: str = "ユーザーによるキャンセル") -> None:
        """品質分析キャンセル"""
        if self.status in [QualityCheckStatus.COMPLETED, QualityCheckStatus.FAILED]:
            msg = f"キャンセルできません。現在の状態: {self.status}"
            raise ValueError(msg)

        self.status = QualityCheckStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc)
        self._add_analysis_note(f"分析キャンセル: {reason}")

    def get_execution_duration_seconds(self) -> float:
        """実行時間取得（秒）"""
        if not self.started_at:
            return 0.0

        end_time = self.completed_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()

    def get_progress_percentage(self) -> int:
        """進捗率取得（パーセント）"""
        completed_stages = sum(1 for completed in self.stage_progress.values() if completed)
        total_stages = len(QualityCheckStage)
        return int((completed_stages / total_stages) * 100)

    def is_completed(self) -> bool:
        """完了判定"""
        return self.status == QualityCheckStatus.COMPLETED

    def is_success(self) -> bool:
        """成功判定"""
        return self.is_completed() and self.result is not None

    def has_errors(self) -> bool:
        """エラー存在判定"""
        return len(self.error_log) > 0

    def get_current_stage_name(self) -> str:
        """現在段階名取得"""
        stage_names = {
            QualityCheckStage.PREPARATION: "準備",
            QualityCheckStage.MANUSCRIPT_ANALYSIS: "原稿解析",
            QualityCheckStage.CREATIVE_EVALUATION: "創作的評価",
            QualityCheckStage.READER_EXPERIENCE_CHECK: "読者体験チェック",
            QualityCheckStage.STRUCTURAL_VALIDATION: "構成検証",
            QualityCheckStage.RESULT_COMPILATION: "結果編纂",
            QualityCheckStage.COMPLETED: "完了",
        }
        return stage_names.get(self.current_stage, "不明")

    def get_session_summary(self) -> str:
        """セッション要約"""
        if not self.request:
            return f"セッション {self.session_id.value} (未開始)"

        status_text = {
            QualityCheckStatus.PENDING: "待機中",
            QualityCheckStatus.ANALYZING: "分析中",
            QualityCheckStatus.COMPLETED: "完了",
            QualityCheckStatus.FAILED: "失敗",
            QualityCheckStatus.CANCELLED: "キャンセル",
        }

        base_info = (
            f"セッション {self.session_id.value[:8]}... "
            f"({self.request.get_context_summary()}) "
            f"状態: {status_text.get(self.status, '不明')}"
        )

        if self.is_success() and self.result:
            base_info += f" スコア: {self.result.total_score}/100点"

        return base_info

    def add_execution_metadata(self, key: str, value: str) -> None:
        """実行メタデータ追加"""
        self.execution_metadata[key] = value

    def _add_analysis_note(self, note: str) -> None:
        """分析ノート追加（内部用）"""
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.analysis_notes.append(f"[{timestamp}] {note}")

    def get_detailed_progress_report(self) -> dict[str, any]:
        """詳細進捗レポート"""
        return {
            "session_id": self.session_id.value,
            "status": self.status.value,
            "current_stage": self.current_stage.value,
            "progress_percentage": self.get_progress_percentage(),
            "execution_duration_seconds": self.get_execution_duration_seconds(),
            "stage_progress": {stage.value: completed for stage, completed in self.stage_progress.items()},
            "intermediate_scores": self.intermediate_scores.copy(),
            "error_count": len(self.error_log),
            "analysis_notes_count": len(self.analysis_notes),
            "has_result": self.result is not None,
        }
