"""インタラクティブ執筆セッション エンティティ

Claude Code統合インタラクティブ執筆システムのセッション管理を行うドメインエンティティ。
10段階執筆プロセスの状態管理と品質ゲート統合を提供します。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import SimpleNamespace
from typing import Any

from noveler.domain.value_objects.project_time import project_now
from noveler.domain.value_objects.quality_check_result import QualityCheckResult


class SessionStatus(Enum):
    """セッション状態"""
    INITIALIZING = "initializing"
    IN_PROGRESS = "in_progress"
    WAITING_USER_CONFIRMATION = "waiting_confirmation"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class StepStatus(Enum):
    """ステップ実行状態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_USER = "waiting_user"


@dataclass
class UserFeedback:
    """ユーザーフィードバック"""
    step: int
    feedback: str
    timestamp: datetime
    feedback_type: str = "text"  # text, approval, modification_request

    def is_approval(self) -> bool:
        """承認フィードバックかどうか"""
        approval_keywords = ["承認", "ok", "オッケー", "良い", "進めて", "次へ"]
        return any(keyword in self.feedback.lower() for keyword in approval_keywords)

    def extract_modification_requests(self) -> list[str]:
        """修正指示を抽出"""
        modification_patterns = [
            "修正",
            "変更",
            "改善",
            "追加",
            "削除",
            "調整",
        ]

        # 日本語の依頼表現「〜してください」を含む文も修正指示として扱う
        polite_request_marker = "してください"

        requests = []
        sentences = [s.strip() for s in self.feedback.split("。") if s.strip()]

        for sentence in sentences:
            if any(p in sentence for p in modification_patterns) or polite_request_marker in sentence:
                requests.append(sentence)

        return requests


@dataclass
class StepExecutionResult:
    """ステップ実行結果"""
    step: int
    status: StepStatus
    output: dict[str, Any]
    summary: str
    user_prompt: str
    quality_check: QualityCheckResult | None = None
    execution_time_ms: int = 0
    file_references: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PendingConfirmation:
    """確認待ち情報"""
    step: int
    result: StepExecutionResult
    quality_check: QualityCheckResult
    timestamp: datetime
    confirmation_required: bool = True
    timeout_minutes: int = 60


@dataclass
class InteractiveWritingSession:
    """インタラクティブ執筆セッション

    Claude Code統合で使用されるインタラクティブ執筆の状態管理エンティティ。
    10段階執筆プロセス、品質ゲート、ユーザーフィードバックを統合管理します。
    """
    session_id: str
    episode_number: int
    project_root: str
    status: SessionStatus
    current_step: int
    created_at: datetime
    updated_at: datetime

    # 段階別データ
    data: dict[str, Any] = field(default_factory=dict)

    # 品質チェック履歴
    quality_history: list[QualityCheckResult] = field(default_factory=list)

    # ユーザーフィードバック履歴
    feedback_history: list[UserFeedback] = field(default_factory=list)

    # ステップ実行履歴
    step_results: dict[int, StepExecutionResult] = field(default_factory=dict)

    # 確認待ち情報
    pending_confirmation: PendingConfirmation | None = None

    # セッション設定
    configuration: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初期化後処理"""
        # デフォルト設定
        if not self.configuration:
            self.configuration = {
                "quality_threshold": {
                    1: {"pass": 70, "warning": 60},   # プロット準備
                    2: {"pass": 75, "warning": 65},   # 構造分析
                    3: {"pass": 72, "warning": 62},   # 感情設計
                    4: {"pass": 70, "warning": 60},   # ユーモア要素
                    5: {"pass": 75, "warning": 65},   # キャラ対話設計
                    6: {"pass": 73, "warning": 63},   # 場面演出
                    7: {"pass": 80, "warning": 70},   # 論理整合調整
                    8: {"pass": 85, "warning": 75},   # 原稿執筆（厳格）
                    9: {"pass": 82, "warning": 72},   # 品質改善
                    10: {"pass": 90, "warning": 80}   # 最終調整（最厳格）
                },
                "auto_proceed_threshold": 85,  # この点数以上なら自動で次に進む
                "session_timeout_hours": 24,
                "step_timeout_minutes": 60
            }

    def can_proceed_to_step(self, step: int) -> bool:
        """指定ステップに進めるかチェック"""
        if step <= 1:
            return True

        # 前ステップが完了しているか確認
        prev_step = step - 1
        if prev_step not in self.step_results:
            return False

        prev_result = self.step_results[prev_step]
        return prev_result.status == StepStatus.COMPLETED

    def get_current_quality_score(self) -> float | None:
        """現在のステップの品質スコアを取得"""
        if self.quality_history:
            return self.quality_history[-1].overall_score
        return None

    def requires_user_confirmation(self) -> bool:
        """ユーザー確認が必要か"""
        return (
            self.pending_confirmation is not None and
            self.pending_confirmation.confirmation_required
        )

    def add_step_result(self, result: StepExecutionResult) -> None:
        """ステップ結果を追加"""
        self.step_results[result.step] = result
        self.current_step = result.step
        self.updated_at = project_now().datetime

    def add_quality_result(self, quality_result: QualityCheckResult) -> None:
        """品質チェック結果を追加"""
        self.quality_history.append(quality_result)
        self.updated_at = project_now().datetime

    def add_user_feedback(self, feedback: UserFeedback) -> None:
        """ユーザーフィードバックを追加"""
        self.feedback_history.append(feedback)
        self.updated_at = project_now().datetime

        # 確認待ち状態をクリア
        if self.pending_confirmation and self.pending_confirmation.step == feedback.step:
            self.pending_confirmation = None

    def set_pending_confirmation(
        self,
        step: int,
        result: StepExecutionResult,
        quality_check: QualityCheckResult
    ) -> None:
        """確認待ち状態を設定"""
        self.pending_confirmation = PendingConfirmation(
            step=step,
            result=result,
            quality_check=quality_check,
            timestamp=project_now().datetime
        )
        self.status = SessionStatus.WAITING_USER_CONFIRMATION
        self.updated_at = project_now().datetime

    def get_step_quality_threshold(self, step: int) -> dict[str, int]:
        """ステップの品質しきい値を取得"""
        default_threshold = {"pass": 80, "warning": 70}
        return self.configuration["quality_threshold"].get(step, default_threshold)

    def is_session_expired(self) -> bool:
        """セッションが期限切れか"""
        timeout_hours = self.configuration["session_timeout_hours"]
        elapsed = project_now().datetime - self.updated_at
        return elapsed.total_seconds() > (timeout_hours * 3600)

    def get_completion_percentage(self) -> float:
        """完了率を計算"""
        completed_steps = sum(
            1 for result in self.step_results.values()
            if result.status == StepStatus.COMPLETED
        )
        return (completed_steps / 10) * 100

    def get_average_quality_score(self) -> float:
        """平均品質スコアを計算"""
        if not self.quality_history:
            return 0.0

        return sum(qr.overall_score for qr in self.quality_history) / len(self.quality_history)

    def get_last_user_feedback(self) -> UserFeedback | None:
        """最後のユーザーフィードバックを取得"""
        return self.feedback_history[-1] if self.feedback_history else None

    def should_auto_proceed(self, quality_score: float) -> bool:
        """自動で次ステップに進むべきか"""
        auto_threshold = self.configuration["auto_proceed_threshold"]
        return quality_score >= auto_threshold

    def generate_session_summary(self) -> dict[str, Any]:
        """セッション要約を生成"""
        return {
            "session_id": self.session_id,
            "episode_number": self.episode_number,
            "status": self.status.value,
            "current_step": self.current_step,
            "completion_percentage": self.get_completion_percentage(),
            "average_quality_score": self.get_average_quality_score(),
            "total_feedback_count": len(self.feedback_history),
            "session_duration_minutes": (
                (self.updated_at - self.created_at).total_seconds() / 60
            ),
            "steps_completed": [
                step for step, result in self.step_results.items()
                if result.status == StepStatus.COMPLETED
            ],
            "pending_confirmation": self.pending_confirmation is not None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def to_dict(self) -> dict[str, Any]:
        """辞書形式で出力（永続化用）"""
        def _safe_mapping(value: Any) -> dict[str, Any]:
            if isinstance(value, dict):
                return value
            # Mockなどが来ても空dictにフォールバック
            return {}

        def _safe_str(v: Any) -> str:
            try:
                return str(v)
            except Exception:
                return ""

        return {
            "session_id": self.session_id,
            "episode_number": self.episode_number,
            "project_root": self.project_root,
            "status": self.status.value,
            "current_step": self.current_step,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "data": self.data,
            "quality_history": [
                (qr.to_dict() if hasattr(qr, "to_dict") else {"overall_score": getattr(qr, "overall_score", 0.0)})
                for qr in self.quality_history
            ],
            "feedback_history": [
                {
                    "step": fb.step,
                    "feedback": fb.feedback,
                    "timestamp": fb.timestamp.isoformat(),
                    "feedback_type": fb.feedback_type
                }
                for fb in self.feedback_history
            ],
            "step_results": {
                str(step): {
                    "step": result.step,
                    "status": getattr(result.status, "value", _safe_str(getattr(result, "status", ""))),
                    "output": getattr(result, "output", {}),
                    "summary": getattr(result, "summary", ""),
                    "user_prompt": getattr(result, "user_prompt", ""),
                    "execution_time_ms": int(getattr(result, "execution_time_ms", 0) or 0),
                    "file_references": _safe_mapping(getattr(result, "file_references", {})),
                    "metadata": _safe_mapping(getattr(result, "metadata", {})),
                }
                for step, result in self.step_results.items()
            },
            "pending_confirmation": {
                "step": self.pending_confirmation.step,
                "timestamp": self.pending_confirmation.timestamp.isoformat(),
                "confirmation_required": self.pending_confirmation.confirmation_required
            } if self.pending_confirmation else None,
            "configuration": self.configuration
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InteractiveWritingSession":
        """辞書から復元（永続化からの復元用）"""
        # 基本フィールド
        session = cls(
            session_id=data["session_id"],
            episode_number=data["episode_number"],
            project_root=data["project_root"],
            status=SessionStatus(data["status"]),
            current_step=data["current_step"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )

        # データ復元
        session.data = data.get("data", {})
        session.configuration = data.get("configuration", {})

        # 品質履歴復元（フォールバックに寛容）
        session.quality_history = []
        for qr in data.get("quality_history", []):
            try:
                # 本来のValueObjectにfrom_dictがある場合のみ使用
                if hasattr(QualityCheckResult, "from_dict") and callable(getattr(QualityCheckResult, "from_dict")):
                    session.quality_history.append(QualityCheckResult.from_dict(qr))  # type: ignore[attr-defined]
                    continue
            except Exception:
                # 失敗時はフォールバックへ
                pass

            # フォールバック: シンプルなオブジェクトで再構築
            if isinstance(qr, dict):
                if "overall_score" in qr:
                    session.quality_history.append(SimpleNamespace(overall_score=float(qr["overall_score"])) )
                elif "category_scores" in qr and isinstance(qr["category_scores"], dict):
                    scores = list(qr["category_scores"].values())
                    avg = sum(scores) / len(scores) if scores else 0.0
                    session.quality_history.append(SimpleNamespace(overall_score=float(avg)))
                else:
                    session.quality_history.append(SimpleNamespace(overall_score=0.0))
            elif isinstance(qr, (int, float)):
                session.quality_history.append(SimpleNamespace(overall_score=float(qr)))
            else:
                session.quality_history.append(SimpleNamespace(overall_score=0.0))

        # フィードバック履歴復元
        session.feedback_history = [
            UserFeedback(
                step=fb["step"],
                feedback=fb["feedback"],
                timestamp=datetime.fromisoformat(fb["timestamp"]),
                feedback_type=fb.get("feedback_type", "text")
            )
            for fb in data.get("feedback_history", [])
        ]

        # ステップ結果復元
        step_results_data = data.get("step_results", {})
        for step_str, result_data in step_results_data.items():
            step = int(step_str)
            result = StepExecutionResult(
                step=result_data["step"],
                status=StepStatus(result_data["status"]),
                output=result_data["output"],
                summary=result_data["summary"],
                user_prompt=result_data["user_prompt"],
                execution_time_ms=result_data.get("execution_time_ms", 0),
                file_references=result_data.get("file_references", {}),
                metadata=result_data.get("metadata", {})
            )
            session.step_results[step] = result

        # 確認待ち状態復元
        pending_data = data.get("pending_confirmation")
        if pending_data:
            session.pending_confirmation = PendingConfirmation(
                step=pending_data["step"],
                result=session.step_results.get(pending_data["step"]),
                quality_check=session.quality_history[-1] if session.quality_history else None,
                timestamp=datetime.fromisoformat(pending_data["timestamp"]),
                confirmation_required=pending_data.get("confirmation_required", True)
            )

        return session
