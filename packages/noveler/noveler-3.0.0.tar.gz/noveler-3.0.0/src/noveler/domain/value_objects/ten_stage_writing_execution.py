"""10段階執筆システム用の実行段階定義（SPEC-MCP-001 v2.2.0対応）"""

from enum import Enum


class TenStageExecutionStage(Enum):
    """10段階執筆システムの実行段階定義"""

    # STEP 1: プロットデータ準備
    PLOT_DATA_PREPARATION = "plot_data_preparation"

    # STEP 2: プロット分析設計
    PLOT_ANALYSIS_DESIGN = "plot_analysis_design"

    # STEP 3: 感情関係性設計
    EMOTIONAL_RELATIONSHIP_DESIGN = "emotional_relationship_design"

    # STEP 4: ユーモア魅力設計
    HUMOR_CHARM_DESIGN = "humor_charm_design"

    # STEP 5: キャラ心理対話設計
    CHARACTER_PSYCHOLOGY_DIALOGUE_DESIGN = "character_psychology_dialogue_design"

    # STEP 6: 場面演出雰囲気設計
    SCENE_DIRECTION_ATMOSPHERE_DESIGN = "scene_direction_atmosphere_design"

    # STEP 7: 論理整合性調整
    LOGIC_CONSISTENCY_ADJUSTMENT = "logic_consistency_adjustment"

    # STEP 8: 原稿執筆
    MANUSCRIPT_WRITING = "manuscript_writing"

    # STEP 9: 品質仕上げ
    QUALITY_REFINEMENT = "quality_refinement"

    # STEP 10: 最終調整
    FINAL_ADJUSTMENT = "final_adjustment"

    @property
    def display_name(self) -> str:
        """表示名取得"""
        display_names = {
            TenStageExecutionStage.PLOT_DATA_PREPARATION: "STEP1: プロットデータ準備",
            TenStageExecutionStage.PLOT_ANALYSIS_DESIGN: "STEP2: プロット分析設計",
            TenStageExecutionStage.EMOTIONAL_RELATIONSHIP_DESIGN: "STEP3: 感情関係性設計",
            TenStageExecutionStage.HUMOR_CHARM_DESIGN: "STEP4: ユーモア魅力設計",
            TenStageExecutionStage.CHARACTER_PSYCHOLOGY_DIALOGUE_DESIGN: "STEP5: キャラ心理対話設計",
            TenStageExecutionStage.SCENE_DIRECTION_ATMOSPHERE_DESIGN: "STEP6: 場面演出雰囲気設計",
            TenStageExecutionStage.LOGIC_CONSISTENCY_ADJUSTMENT: "STEP7: 論理整合性調整",
            TenStageExecutionStage.MANUSCRIPT_WRITING: "STEP8: 原稿執筆",
            TenStageExecutionStage.QUALITY_REFINEMENT: "STEP9: 品質仕上げ",
            TenStageExecutionStage.FINAL_ADJUSTMENT: "STEP10: 最終調整",
        }
        return display_names[self]

    @property
    def step_number(self) -> int:
        """ステップ番号取得"""
        step_numbers = {
            TenStageExecutionStage.PLOT_DATA_PREPARATION: 1,
            TenStageExecutionStage.PLOT_ANALYSIS_DESIGN: 2,
            TenStageExecutionStage.EMOTIONAL_RELATIONSHIP_DESIGN: 3,
            TenStageExecutionStage.HUMOR_CHARM_DESIGN: 4,
            TenStageExecutionStage.CHARACTER_PSYCHOLOGY_DIALOGUE_DESIGN: 5,
            TenStageExecutionStage.SCENE_DIRECTION_ATMOSPHERE_DESIGN: 6,
            TenStageExecutionStage.LOGIC_CONSISTENCY_ADJUSTMENT: 7,
            TenStageExecutionStage.MANUSCRIPT_WRITING: 8,
            TenStageExecutionStage.QUALITY_REFINEMENT: 9,
            TenStageExecutionStage.FINAL_ADJUSTMENT: 10,
        }
        return step_numbers[self]

    @property
    def expected_turns(self) -> int:
        """予想ターン数（各ステップ独立5分タイムアウト想定）"""
        turn_estimates = {
            TenStageExecutionStage.PLOT_DATA_PREPARATION: 2,
            TenStageExecutionStage.PLOT_ANALYSIS_DESIGN: 2,
            TenStageExecutionStage.EMOTIONAL_RELATIONSHIP_DESIGN: 2,
            TenStageExecutionStage.HUMOR_CHARM_DESIGN: 2,
            TenStageExecutionStage.CHARACTER_PSYCHOLOGY_DIALOGUE_DESIGN: 2,
            TenStageExecutionStage.SCENE_DIRECTION_ATMOSPHERE_DESIGN: 2,
            TenStageExecutionStage.LOGIC_CONSISTENCY_ADJUSTMENT: 2,
            TenStageExecutionStage.MANUSCRIPT_WRITING: 3,  # 原稿執筆は少し多めに
            TenStageExecutionStage.QUALITY_REFINEMENT: 2,
            TenStageExecutionStage.FINAL_ADJUSTMENT: 1,
        }
        return turn_estimates[self]

    @property
    def timeout_seconds(self) -> int:
        """個別タイムアウト秒数（各ステップ独立300秒）"""
        return 300  # 5分 = 300秒

    @classmethod
    def get_all_stages(cls) -> list["TenStageExecutionStage"]:
        """全ステージを順序通りに取得"""
        return [
            cls.PLOT_DATA_PREPARATION,
            cls.PLOT_ANALYSIS_DESIGN,
            cls.EMOTIONAL_RELATIONSHIP_DESIGN,
            cls.HUMOR_CHARM_DESIGN,
            cls.CHARACTER_PSYCHOLOGY_DIALOGUE_DESIGN,
            cls.SCENE_DIRECTION_ATMOSPHERE_DESIGN,
            cls.LOGIC_CONSISTENCY_ADJUSTMENT,
            cls.MANUSCRIPT_WRITING,
            cls.QUALITY_REFINEMENT,
            cls.FINAL_ADJUSTMENT,
        ]

    def get_next_stage(self) -> "TenStageExecutionStage | None":
        """次のステージを取得"""
        all_stages = self.get_all_stages()
        try:
            current_index = all_stages.index(self)
            if current_index < len(all_stages) - 1:
                return all_stages[current_index + 1]
            return None
        except ValueError:
            return None

    def get_previous_stage(self) -> "TenStageExecutionStage | None":
        """前のステージを取得"""
        all_stages = self.get_all_stages()
        try:
            current_index = all_stages.index(self)
            if current_index > 0:
                return all_stages[current_index - 1]
            return None
        except ValueError:
            return None
