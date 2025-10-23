"""
段階的プロンプト生成における段階を表現する値オブジェクト

SPEC-STAGED-001: PromptStage値オブジェクトの実装
- 段階番号（1-5）の検証
- 段階固有の属性管理
- 不変性の保証
"""

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class PromptStage:
    """プロンプト生成の段階を表現する値オブジェクト

    段階的プロンプト生成システムにおける各段階の定義と制約を管理する。
    不変オブジェクトとして実装し、段階固有の情報を提供する。
    """

    stage_number: int
    stage_name: str
    estimated_duration_minutes: int
    required_elements: tuple[str, ...]
    completion_criteria: tuple[str, ...]

    # 段階定義の定数
    STAGE_1: ClassVar["PromptStage"] = None  # 後で初期化
    STAGE_2: ClassVar["PromptStage"] = None
    STAGE_3: ClassVar["PromptStage"] = None
    STAGE_4: ClassVar["PromptStage"] = None
    STAGE_5: ClassVar["PromptStage"] = None

    def __post_init__(self) -> None:
        """初期化後のバリデーション"""
        if not 1 <= self.stage_number <= 5:
            msg = f"Stage number must be between 1 and 5, got: {self.stage_number}"
            raise ValueError(msg)

        if not self.stage_name.strip():
            msg = "Stage name cannot be empty"
            raise ValueError(msg)

        if self.estimated_duration_minutes <= 0:
            msg = f"Duration must be positive, got: {self.estimated_duration_minutes}"
            raise ValueError(msg)

        if not self.required_elements:
            msg = "Required elements cannot be empty"
            raise ValueError(msg)

        if not self.completion_criteria:
            msg = "Completion criteria cannot be empty"
            raise ValueError(msg)

    def is_basic_stage(self) -> bool:
        """基本段階（Stage 1-2）判定"""
        return self.stage_number <= 2

    def is_advanced_stage(self) -> bool:
        """高度段階（Stage 4-5）判定"""
        return self.stage_number >= 4

    def get_quality_level_stars(self) -> str:
        """段階に応じた品質レベル表示"""
        return "⭐" * self.stage_number

    def can_advance_to(self, next_stage: "PromptStage") -> bool:
        """指定段階への進行可能性判定"""
        return next_stage.stage_number == self.stage_number + 1

    def can_rollback_to(self, previous_stage: "PromptStage") -> bool:
        """指定段階への戻り可能性判定"""
        return previous_stage.stage_number < self.stage_number


# 段階定義の初期化
PromptStage.STAGE_1 = PromptStage(
    stage_number=1,
    stage_name="基本骨格設定",
    estimated_duration_minutes=15,
    required_elements=("episode_number", "title", "chapter", "theme", "purpose", "synopsis"),
    completion_criteria=("必須5項目入力済み", "synopsis 400字程度記述済み", "YAML構文エラーなし", "ファイル保存済み"),
)


PromptStage.STAGE_2 = PromptStage(
    stage_number=2,
    stage_name="構造展開",
    estimated_duration_minutes=20,
    required_elements=("story_structure", "setup", "confrontation", "resolution"),
    completion_criteria=(
        "三幕構成が論理的に設計済み",
        "基本シーン構成（3シーン以上）完成",
        "章プロットとの整合性確認済み",
        "ファイル更新保存済み",
    ),
)


PromptStage.STAGE_3 = PromptStage(
    stage_number=3,
    stage_name="詳細深化",
    estimated_duration_minutes=25,
    required_elements=("detailed_scenes", "emotional_arc", "character_details", "scene_five_elements"),
    completion_criteria=(
        "全シーンにシーン5要素実装済み",
        "感情アーク4段階設計済み",
        "キャラクター詳細肉付け済み",
        "表現の豊かさ・深度が適切",
    ),
)


PromptStage.STAGE_4 = PromptStage(
    stage_number=4,
    stage_name="統合要素",
    estimated_duration_minutes=20,
    required_elements=(
        "foreshadowing_integration",
        "technical_elements",
        "thematic_elements",
        "next_episode_connection",
    ),
    completion_criteria=(
        "伏線要素の適切な統合済み",
        "技術要素の教育的進行確認済み",
        "テーマ・謎要素の一貫性確保済み",
        "次話への連携設計済み",
    ),
)


PromptStage.STAGE_5 = PromptStage(
    stage_number=5,
    stage_name="品質確認・完成",
    estimated_duration_minutes=15,
    required_elements=(
        "quality_metrics",
        "consistency_checks",
        "beta_feedback",
        "publication_readiness",
    ),
    completion_criteria=(
        "品質スコアが基準を満たしている",
        "整合性チェック完了",
        "改善提案の主要項目を反映",
        "公開準備が完了している",
    ),
)


def get_all_stages() -> list[PromptStage]:
    """全段階のリストを取得"""
    return [
        PromptStage.STAGE_1,
        PromptStage.STAGE_2,
        PromptStage.STAGE_3,
        PromptStage.STAGE_4,
        PromptStage.STAGE_5,
    ]


def get_stage_by_number(stage_number: int) -> PromptStage:
    """段階番号から段階オブジェクトを取得"""
    stage_map = {
        1: PromptStage.STAGE_1,
        2: PromptStage.STAGE_2,
        3: PromptStage.STAGE_3,
        4: PromptStage.STAGE_4,
        5: PromptStage.STAGE_5,
    }

    if stage_number not in stage_map:
        msg = f"Invalid stage number: {stage_number}"
        raise ValueError(msg)

    return stage_map[stage_number]
