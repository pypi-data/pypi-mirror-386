#!/usr/bin/env python3
"""
プロンプト生成エンティティ

A24ガイドベースのプロンプト生成処理を管理するドメインエンティティ。
DDD設計に基づき、プロンプト生成のビジネスルールと状態を管理する。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from noveler.domain.value_objects.project_time import project_now


class A24Stage(Enum):
    """A24ガイドの4段階プロセス"""

    SKELETON = "骨格構築"  # Stage 1: 基本情報・概要定義
    THREE_ACT = "三幕構成設計"  # Stage 2: 物語構造設計
    SCENE_DETAIL = "シーン肉付け"  # Stage 3: シーン詳細化
    TECH_INTEGRATION = "技術伏線統合"  # Stage 4: 技術要素・伏線統合


class ContextElementType(Enum):
    """コンテキスト要素の種類"""

    FORESHADOWING = "伏線要素"
    IMPORTANT_SCENE = "重要シーン"
    CHAPTER_CONNECTION = "章間連携"
    TECHNICAL_ELEMENT = "技術要素"


class OptimizationTarget(Enum):
    """最適化ターゲット"""

    CLAUDE_CODE = "Claude Code"
    CLAUDE_WEB = "Claude Web"
    CHATGPT = "ChatGPT"
    GENERIC = "汎用"


@dataclass(frozen=True)
class ContextElement:
    """コンテキスト要素バリューオブジェクト

    プロンプト生成に使用される追加情報の単位。
    伏線、重要シーン、技術要素など様々なコンテキストを統一的に扱う。
    """

    element_type: ContextElementType
    content: str
    priority: float  # 0.0-1.0, 1.0が最高優先度
    integration_stage: A24Stage
    source_file: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """データ妥当性検証"""
        if not 0.0 <= self.priority <= 1.0:
            msg = f"優先度は0.0-1.0の範囲である必要があります: {self.priority}"
            raise ValueError(msg)

        if not self.content.strip():
            msg = "コンテンツは空にできません"
            raise ValueError(msg)


@dataclass(frozen=True)
class A24StagePrompt:
    """A24段階別プロンプトバリューオブジェクト

    A24ガイドの各段階に対応するプロンプト構成要素。
    段階ごとの指示、検証基準、期待される出力を定義する。
    """

    stage: A24Stage
    instructions: list[str]
    validation_criteria: list[str]
    expected_output_format: str
    context_integration_points: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """データ妥当性検証"""
        if not self.instructions:
            msg = "指示リストは空にできません"
            raise ValueError(msg)

        if not self.expected_output_format.strip():
            msg = "期待出力フォーマットは空にできません"
            raise ValueError(msg)


@dataclass
class PromptGenerationSession:
    """プロンプト生成セッション エンティティ

    1回のプロンプト生成処理の状態と履歴を管理するエンティティ。
    生成過程の追跡、品質管理、エラーハンドリングを担当する。
    """

    session_id: UUID = field(default_factory=uuid4)
    episode_number: int = 0
    project_name: str = ""
    created_at: datetime = field(default_factory=lambda: project_now().datetime)

    # 生成設定
    context_level: str = "基本"  # 基本|拡張|完全
    optimization_target: OptimizationTarget = OptimizationTarget.CLAUDE_CODE
    include_foreshadowing: bool = True
    include_important_scenes: bool = True

    # 生成状態
    current_stage: A24Stage | None = None
    completed_stages: list[A24Stage] = field(default_factory=list)
    generated_content: dict[A24Stage, str] = field(default_factory=dict)
    integrated_context: list[ContextElement] = field(default_factory=list)

    # 生成結果
    final_prompt: str = ""
    token_estimate: int = 0
    generation_time_ms: int = 0

    # エラー管理
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def start_generation(self, episode_number: int, project_name: str) -> None:
        """プロンプト生成開始"""
        if self.is_completed():
            msg = "既に完了したセッションです"
            raise ValueError(msg)

        self.episode_number = episode_number
        self.project_name = project_name
        self.current_stage = A24Stage.SKELETON
        self.created_at = project_now().datetime

    def advance_to_stage(self, stage: A24Stage) -> None:
        """指定段階に進行"""
        if self.current_stage and self.current_stage not in self.completed_stages:
            self.completed_stages.append(self.current_stage)

        self.current_stage = stage

    def complete_current_stage(self, generated_content: str) -> None:
        """現在段階の完了"""
        if not self.current_stage:
            msg = "アクティブな段階がありません"
            raise ValueError(msg)

        self.generated_content[self.current_stage] = generated_content
        if self.current_stage not in self.completed_stages:
            self.completed_stages.append(self.current_stage)

    def add_context_element(self, element: ContextElement) -> None:
        """コンテキスト要素追加"""
        self.integrated_context.append(element)

    def finalize_prompt(self, final_prompt: str, token_estimate: int, generation_time_ms: int) -> None:
        """プロンプト生成完了"""
        self.final_prompt = final_prompt
        self.token_estimate = token_estimate
        self.generation_time_ms = generation_time_ms

        # 全段階完了確認
        all_stages = list(A24Stage)
        missing_stages = [stage for stage in all_stages if stage not in self.completed_stages]
        if missing_stages:
            stage_names = [stage.value for stage in missing_stages]
            self.warnings.append(f"未完了段階があります: {', '.join(stage_names)}")

    def add_error(self, error_message: str) -> None:
        """エラー追加"""
        self.errors.append(f"{project_now().datetime.isoformat()}: {error_message}")

    def add_warning(self, warning_message: str) -> None:
        """警告追加"""
        self.warnings.append(f"{project_now().datetime.isoformat()}: {warning_message}")

    def is_completed(self) -> bool:
        """生成完了判定"""
        return len(self.final_prompt) > 0 and len(self.errors) == 0

    def is_success(self) -> bool:
        """生成成功判定"""
        return self.is_completed() and len(self.completed_stages) >= 3  # 最低3段階は完了必要

    def get_completion_rate(self) -> float:
        """完了率取得 (0.0-1.0)"""
        total_stages = len(list(A24Stage))
        completed_count = len(self.completed_stages)
        return min(1.0, completed_count / total_stages)

    def get_context_summary(self) -> dict[str, int]:
        """コンテキストサマリ取得"""
        summary = {}
        for element_type in ContextElementType:
            count = len([e for e in self.integrated_context if e.element_type == element_type])
            summary[element_type.value] = count
        return summary

    def get_session_statistics(self) -> dict[str, Any]:
        """セッション統計取得"""
        return {
            "session_id": str(self.session_id),
            "episode_number": self.episode_number,
            "project_name": self.project_name,
            "completion_rate": self.get_completion_rate(),
            "context_summary": self.get_context_summary(),
            "token_estimate": self.token_estimate,
            "generation_time_ms": self.generation_time_ms,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "success": self.is_success(),
        }
