"""Smart Auto-Enhancement Domain Entity

SPEC-SAE-001: Smart Auto-Enhancement エンティティ仕様
- novel check コマンドの自動拡張機能を管理するドメインエンティティ
- 基本チェック → A31評価 → Claude分析の統合フローを表現
- DDD原則に基づく不変条件の実装
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.project_info import ProjectInfo
from noveler.domain.value_objects.quality_score import QualityScore


class EnhancementStage(Enum):
    """拡張チェック段階"""

    BASIC_CHECK = 1
    A31_EVALUATION = 2
    CLAUDE_ANALYSIS = 3
    COMPLETED = 4
    FAILED = 5


class EnhancementMode(Enum):
    """拡張モード種別"""

    STANDARD = "standard"  # 従来の段階的実行
    SMART_AUTO = "smart_auto"  # Smart Auto-Enhancement
    DETAILED = "detailed"  # 詳細表示モード
    ENHANCED = "enhanced"  # 全機能統合モード


@dataclass(frozen=True)
class EnhancementRequest:
    """拡張リクエスト バリューオブジェクト"""

    episode_number: EpisodeNumber
    project_info: ProjectInfo
    mode: EnhancementMode
    skip_basic: bool = False
    skip_a31: bool = False
    skip_claude: bool = False
    auto_fix: bool = False
    show_detailed_review: bool = False
    rhythm_analysis: bool = False

    def __post_init__(self) -> None:
        """不変条件の検証"""
        if self.mode == EnhancementMode.SMART_AUTO:
            # Smart Auto-Enhancement では全段階実行が前提
            if self.skip_basic and self.skip_a31 and self.skip_claude:
                msg = "Smart Auto-Enhancement では全段階スキップは無効"
                raise ValueError(msg)

        if self.mode == EnhancementMode.ENHANCED:
            # Enhanced モードでは詳細表示が必須
            object.__setattr__(self, "show_detailed_review", True)


@dataclass
class EnhancementResult:
    """拡張結果 バリューオブジェクト"""

    stage: EnhancementStage
    basic_score: QualityScore | None
    a31_score: QualityScore | None
    claude_score: QualityScore | None
    execution_time_ms: float
    improvements_count: int
    error_message: str | None
    analysis_data: dict | None = None  # 詳細分析データ（Claude分析結果など）

    def get_final_score(self) -> QualityScore | None:
        """最終品質スコアを取得"""
        if self.claude_score:
            return self.claude_score
        if self.a31_score:
            return self.a31_score
        if self.basic_score:
            return self.basic_score
        return None

    def is_success(self) -> bool:
        """成功判定"""
        return self.error_message is None


class SmartAutoEnhancement:
    """Smart Auto-Enhancement エンティティ

    ドメイン不変条件:
    - リクエストは有効なエピソード番号とプロジェクト情報を持つ
    - Smart Auto-Enhancement モードでは全段階を自動実行
    - 各段階の結果は累積的に管理される
    - 失敗時は適切なエラー情報を保持する
    """

    def __init__(self, request: EnhancementRequest) -> None:
        self._request = request
        self._current_stage = EnhancementStage.BASIC_CHECK
        self._results: dict[EnhancementStage, EnhancementResult] = {}
        self._started_at = datetime.now(timezone.utc)
        self._completed_at: datetime | None = None

        # 不変条件検証
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        """ドメイン不変条件の検証"""
        if not self._request.episode_number.value > 0:
            msg = "エピソード番号は1以上である必要があります"
            raise ValueError(msg)

        if not self._request.project_info.name:
            msg = "プロジェクト名は必須です"
            raise ValueError(msg)

    @property
    def request(self) -> EnhancementRequest:
        """拡張リクエスト"""
        return self._request

    @property
    def current_stage(self) -> EnhancementStage:
        """現在の段階"""
        return self._current_stage

    @property
    def is_smart_auto_mode(self) -> bool:
        """Smart Auto-Enhancement モード判定"""
        return self._request.mode == EnhancementMode.SMART_AUTO

    @property
    def is_enhanced_mode(self) -> bool:
        """Enhanced モード判定"""
        return self._request.mode == EnhancementMode.ENHANCED

    def should_execute_stage(self, stage: EnhancementStage) -> bool:
        """指定段階の実行要否判定"""
        if self.is_smart_auto_mode:
            # Smart Auto-Enhancement では全段階実行
            return True

        # 通常モードではスキップオプションを考慮
        if stage == EnhancementStage.BASIC_CHECK:
            return not self._request.skip_basic
        if stage == EnhancementStage.A31_EVALUATION:
            return not self._request.skip_a31
        if stage == EnhancementStage.CLAUDE_ANALYSIS:
            return not self._request.skip_claude

        return True

    def advance_to_stage(self, stage: EnhancementStage) -> None:
        """段階を進める"""
        if stage.value < self._current_stage.value:
            msg = f"段階を後退させることはできません: {stage} <- {self._current_stage}"
            raise ValueError(msg)

        self._current_stage = stage

        if stage == EnhancementStage.COMPLETED:
            self._completed_at = datetime.now(timezone.utc)

    def add_stage_result(self, stage: EnhancementStage, result: EnhancementResult) -> None:
        """段階結果を追加"""
        self._results[stage] = result

        # 失敗時は完了状態に移行
        if not result.is_success():
            self._current_stage = EnhancementStage.FAILED
            self._completed_at = datetime.now(timezone.utc)

    def get_stage_result(self, stage: EnhancementStage) -> EnhancementResult | None:
        """段階結果を取得"""
        return self._results.get(stage)

    def get_final_result(self) -> EnhancementResult | None:
        """最終結果を取得"""
        if EnhancementStage.CLAUDE_ANALYSIS in self._results:
            return self._results[EnhancementStage.CLAUDE_ANALYSIS]
        if EnhancementStage.A31_EVALUATION in self._results:
            return self._results[EnhancementStage.A31_EVALUATION]
        if EnhancementStage.BASIC_CHECK in self._results:
            return self._results[EnhancementStage.BASIC_CHECK]
        return None

    def is_completed(self) -> bool:
        """完了判定"""
        return self._current_stage in [EnhancementStage.COMPLETED, EnhancementStage.FAILED]

    def is_success(self) -> bool:
        """成功判定"""
        return self._current_stage == EnhancementStage.COMPLETED and all(
            result.is_success() for result in self._results.values()
        )

    def get_execution_duration_ms(self) -> float:
        """実行時間を取得（ミリ秒）"""
        end_time = self._completed_at or datetime.now(timezone.utc)
        return (end_time - self._started_at).total_seconds() * 1000

    def get_total_improvements_count(self) -> int:
        """総改善提案数を取得"""
        return sum(result.improvements_count for result in self._results.values())
