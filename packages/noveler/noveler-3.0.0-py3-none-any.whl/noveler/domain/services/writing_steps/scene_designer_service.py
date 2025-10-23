"""Domain.services.writing_steps.scene_designer_service
Where: Domain service module implementing a specific writing workflow step.
What: Provides helper routines and data structures for this writing step.
Why: Allows stepwise writing orchestrators to reuse consistent step logic.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""STEP 4: SceneDesignerService

A38執筆プロンプトガイドのSTEP 4に対応するマイクロサービス。
シーン設計・場面構成・詳細プランニングを担当。
"""

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService

from noveler.domain.services.writing_steps.base_writing_step import BaseWritingStep, WritingStepResponse


@dataclass
class SceneBlock:
    """シーンブロック"""

    # 基本情報
    block_id: str
    title: str
    position: str  # "opening", "development", "climax", "resolution"
    estimated_word_count: int

    # 場面要素
    location: str = ""
    time_context: str = ""
    characters_present: list[str] = field(default_factory=list)

    # 内容要素
    primary_purpose: str = ""  # "exposition", "conflict", "development", "resolution"
    key_events: list[str] = field(default_factory=list)
    dialogue_ratio: float = 0.3  # 0.0-1.0
    action_ratio: float = 0.2    # 0.0-1.0
    description_ratio: float = 0.5  # 0.0-1.0

    # 技術的要素
    pov_character: str = ""
    tension_level: int = 5  # 1-10
    emotional_tone: str = ""

    # 前後関係
    dependencies: list[str] = field(default_factory=list)
    transitions_to: list[str] = field(default_factory=list)


@dataclass
class SceneTransition:
    """シーン遷移"""

    from_block: str
    to_block: str
    transition_type: str  # "cut", "fade", "continuous", "time_jump"
    transition_text: str = ""

    # 遷移の詳細
    time_gap: str = "immediate"  # "immediate", "minutes", "hours", "days"
    location_change: bool = False
    character_change: bool = False
    mood_change: str = "maintain"  # "maintain", "shift", "contrast"


@dataclass
class SceneDesignPlan:
    """シーン設計プラン"""

    episode_number: int
    total_estimated_words: int
    scene_count: int

    # シーン構成
    scene_blocks: list[SceneBlock] = field(default_factory=list)
    transitions: list[SceneTransition] = field(default_factory=list)

    # 全体設計
    dominant_location: str = ""
    primary_characters: list[str] = field(default_factory=list)
    overall_mood: str = ""

    # 技術的設計
    complexity_level: str = "medium"  # "simple", "medium", "complex"
    special_requirements: list[str] = field(default_factory=list)


@dataclass
class SceneDesignerResponse(WritingStepResponse):
    """シーン設計サービス結果"""

    design_plan: SceneDesignPlan | None = None

    # パフォーマンス情報
    block_design_time_ms: float = 0.0
    transition_planning_time_ms: float = 0.0
    optimization_time_ms: float = 0.0

    # 統計情報
    blocks_created: int = 0
    transitions_planned: int = 0
    word_count_allocated: int = 0


class SceneDesignerService(BaseWritingStep):
    """STEP 4: シーン設計マイクロサービス

    叙述構造を基に具体的なシーン構成を設計。
    各シーンブロックの詳細設計と最適な遷移計画を策定。
    """

    def __init__(
        self,
        logger_service: ILoggerService = None,
        **kwargs: Any
    ) -> None:
        """シーン設計サービス初期化"""
        super().__init__(step_number=4, step_name="scene_designer", **kwargs)

        self._logger_service = logger_service

    async def execute(
        self,
        episode_number: int,
        previous_results: dict[int, Any] | None = None
    ) -> SceneDesignerResponse:
        """シーン設計実行"""
        start_time = time.time()

        try:
            if self._logger_service:
                self._logger_service.info(f"STEP 4 シーン設計開始: エピソード={episode_number}")

            # 1. 前ステップ結果から設計情報取得
            narrative_structure, context_result, plot_analysis = \
                self._extract_design_inputs(previous_results)

            # 2. 基本設計パラメータ決定
            target_words = self._determine_target_word_count(previous_results)
            scene_count = self._calculate_optimal_scene_count(narrative_structure, target_words)

            # 3. シーンブロック設計
            block_start = time.time()
            scene_blocks = await self._design_scene_blocks(
                episode_number, scene_count, target_words,
                narrative_structure, context_result, plot_analysis
            )
            block_time = (time.time() - block_start) * 1000

            # 4. シーン遷移計画
            transition_start = time.time()
            transitions = await self._plan_scene_transitions(
                scene_blocks, narrative_structure
            )
            transition_time = (time.time() - transition_start) * 1000

            # 5. 設計最適化
            optimization_start = time.time()
            optimized_blocks, optimized_transitions = await self._optimize_scene_design(
                scene_blocks, transitions, target_words
            )
            optimization_time = (time.time() - optimization_start) * 1000

            # 6. 統合プラン作成
            design_plan = self._create_integrated_plan(
                episode_number, target_words, optimized_blocks, optimized_transitions,
                context_result
            )

            # 7. 成功応答作成
            execution_time = (time.time() - start_time) * 1000

            return SceneDesignerResponse(
                success=True,
                step_number=4,
                step_name="scene_designer",
                execution_time_ms=execution_time,
                design_plan=design_plan,

                # パフォーマンス情報
                block_design_time_ms=block_time,
                transition_planning_time_ms=transition_time,
                optimization_time_ms=optimization_time,

                # 統計情報
                blocks_created=len(optimized_blocks),
                transitions_planned=len(optimized_transitions),
                word_count_allocated=sum(block.estimated_word_count for block in optimized_blocks)
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_message = f"STEP 4 シーン設計エラー: {e}"

            if self._logger_service:
                self._logger_service.error(error_message)

            return SceneDesignerResponse(
                success=False,
                step_number=4,
                step_name="scene_designer",
                execution_time_ms=execution_time,
                error_message=error_message
            )

    def _extract_design_inputs(
        self,
        previous_results: dict[int, Any] | None
    ) -> tuple[Any | None, Any | None, Any | None]:
        """設計入力情報抽出"""
        narrative_structure = None
        context_result = None
        plot_analysis = None

        if previous_results:
            # STEP 3から叙述構造
            if 3 in previous_results:
                step3_result = previous_results[3]
                if hasattr(step3_result, "structure_result"):
                    narrative_structure = step3_result.structure_result

            # STEP 2からコンテキスト
            if 2 in previous_results:
                step2_result = previous_results[2]
                if hasattr(step2_result, "context_result"):
                    context_result = step2_result.context_result

            # STEP 1からプロット解析
            if 1 in previous_results:
                step1_result = previous_results[1]
                if hasattr(step1_result, "analysis_result"):
                    plot_analysis = step1_result.analysis_result

        return narrative_structure, context_result, plot_analysis

    def _determine_target_word_count(self, previous_results: dict[int, Any] | None) -> int:
        """目標文字数決定"""
        default_count = 4000

        if previous_results:
            for step_result in previous_results.values():
                if hasattr(step_result, "context_result"):
                    context_result = step_result.context_result
                    if (context_result and
                        hasattr(context_result, "technical_context") and
                        context_result.technical_context and
                        hasattr(context_result.technical_context, "target_word_count")):
                        return context_result.technical_context.target_word_count

        return default_count

    def _calculate_optimal_scene_count(
        self,
        narrative_structure: Any | None,
        target_words: int
    ) -> int:
        """最適シーン数計算"""
        # 基本シーン数（文字数ベース）
        base_scene_count = max(3, min(8, target_words // 800))

        # 叙述構造による調整
        if narrative_structure and hasattr(narrative_structure, "structural_elements"):
            structural_elements = narrative_structure.structural_elements
            if structural_elements and hasattr(structural_elements, "scene_count_estimate"):
                return structural_elements.scene_count_estimate

        return base_scene_count

    async def _design_scene_blocks(
        self,
        episode_number: int,
        scene_count: int,
        target_words: int,
        narrative_structure: Any | None,
        context_result: Any | None,
        plot_analysis: Any | None
    ) -> list[SceneBlock]:
        """シーンブロック設計"""
        blocks = []
        words_per_scene = target_words // scene_count

        # 基本シーン構成テンプレート
        scene_templates = self._get_scene_templates(scene_count)

        # 各シーンブロック作成
        for i, template in enumerate(scene_templates):
            block_id = f"scene_{i+1:02d}"

            # 文字数配分（重要度による調整）
            importance_factor = template.get("importance", 1.0)
            estimated_words = int(words_per_scene * importance_factor)

            # キャラクター配置
            characters_present = self._determine_scene_characters(
                template, context_result, i == 0  # 最初のシーンかどうか
            )

            # 場所・時間設定
            location, time_context = self._determine_scene_setting(
                template, context_result, i
            )

            # 内容要素設計
            key_events = self._design_scene_events(
                template, plot_analysis, episode_number, i
            )

            # 技術的要素設定
            pov_character = self._determine_pov_character(
                characters_present, narrative_structure
            )

            block = SceneBlock(
                block_id=block_id,
                title=template["title"],
                position=template["position"],
                estimated_word_count=estimated_words,
                location=location,
                time_context=time_context,
                characters_present=characters_present,
                primary_purpose=template["purpose"],
                key_events=key_events,
                dialogue_ratio=template.get("dialogue_ratio", 0.3),
                action_ratio=template.get("action_ratio", 0.2),
                description_ratio=template.get("description_ratio", 0.5),
                pov_character=pov_character,
                tension_level=template.get("tension", 5),
                emotional_tone=template.get("tone", "neutral")
            )

            blocks.append(block)

        return blocks

    def _get_scene_templates(self, scene_count: int) -> list[dict[str, Any]]:
        """シーンテンプレート取得"""
        if scene_count == 3:
            return [
                {
                    "title": "導入シーン",
                    "position": "opening",
                    "purpose": "exposition",
                    "importance": 0.9,
                    "tension": 3,
                    "tone": "setup"
                },
                {
                    "title": "展開シーン",
                    "position": "development",
                    "purpose": "conflict",
                    "importance": 1.3,
                    "tension": 8,
                    "tone": "intense",
                    "dialogue_ratio": 0.4,
                    "action_ratio": 0.3
                },
                {
                    "title": "結末シーン",
                    "position": "resolution",
                    "purpose": "resolution",
                    "importance": 0.8,
                    "tension": 4,
                    "tone": "conclusion"
                }
            ]

        if scene_count == 5:
            return [
                {
                    "title": "オープニング",
                    "position": "opening",
                    "purpose": "exposition",
                    "importance": 0.8,
                    "tension": 3
                },
                {
                    "title": "きっかけ",
                    "position": "inciting",
                    "purpose": "conflict",
                    "importance": 0.9,
                    "tension": 6
                },
                {
                    "title": "発展",
                    "position": "development",
                    "purpose": "development",
                    "importance": 1.2,
                    "tension": 7,
                    "dialogue_ratio": 0.4
                },
                {
                    "title": "クライマックス",
                    "position": "climax",
                    "purpose": "climax",
                    "importance": 1.4,
                    "tension": 9,
                    "action_ratio": 0.4
                },
                {
                    "title": "解決",
                    "position": "resolution",
                    "purpose": "resolution",
                    "importance": 0.7,
                    "tension": 3
                }
            ]

        # デフォルト（汎用的なテンプレート）
        templates = []
        for i in range(scene_count):
            position_map = {
                0: "opening",
                scene_count-1: "resolution"
            }
            position = position_map.get(i, "development")

            templates.append({
                "title": f"シーン{i+1}",
                "position": position,
                "purpose": "development" if position == "development" else position,
                "importance": 1.0,
                "tension": 5
            })

        return templates

    def _determine_scene_characters(
        self,
        template: dict[str, Any],
        context_result: Any | None,
        is_first_scene: bool
    ) -> list[str]:
        """シーンキャラクター決定"""
        characters = []

        if context_result and hasattr(context_result, "character_contexts"):
            # 主人公は基本的に全シーンに登場
            for char_context in context_result.character_contexts:
                if char_context.role == "protagonist":
                    characters.append(char_context.character_name)
                    break

            # 最初のシーンには主要キャラクターを多めに配置
            if is_first_scene:
                for char_context in context_result.character_contexts:
                    if (char_context.role in ["supporting", "antagonist"] and
                        len(characters) < 3):
                        characters.append(char_context.character_name)

            # シーン目的に応じてキャラクター追加
            purpose = template.get("purpose", "")
            if purpose in {"conflict", "climax"}:
                # 対立シーンには対立キャラクターを配置
                for char_context in context_result.character_contexts:
                    if (char_context.role == "antagonist" and
                        char_context.character_name not in characters):
                        characters.append(char_context.character_name)
                        break

        # 最低1人は確保
        if not characters:
            characters = ["主人公"]

        return characters

    def _determine_scene_setting(
        self,
        template: dict[str, Any],
        context_result: Any | None,
        scene_index: int
    ) -> tuple[str, str]:
        """シーン設定（場所・時間）決定"""
        location = "不明な場所"
        time_context = "現在"

        if context_result and hasattr(context_result, "world_context"):
            world_context = context_result.world_context
            if world_context and hasattr(world_context, "location"):
                location = world_context.location

        # シーン位置による時間設定
        position = template.get("position", "development")
        if position == "opening":
            time_context = "朝・序盤"
        elif position == "climax":
            time_context = "夕方・盛り上がり"
        elif position == "resolution":
            time_context = "夜・締めくくり"

        return location, time_context

    def _design_scene_events(
        self,
        template: dict[str, Any],
        plot_analysis: Any | None,
        episode_number: int,
        scene_index: int
    ) -> list[str]:
        """シーンイベント設計"""
        events = []

        purpose = template.get("purpose", "development")

        # プロット解析からイベント抽出
        if plot_analysis and hasattr(plot_analysis, "key_events"):
            available_events = plot_analysis.key_events.copy()

            # シーン目的に応じてイベント配置
            if purpose == "exposition" and available_events:
                events.append(f"状況説明: {available_events[0]}")
            elif purpose == "conflict" and len(available_events) > 1:
                events.append(f"対立発生: {available_events[1]}")
            elif purpose == "climax" and len(available_events) > 2:
                events.append(f"クライマックス: {available_events[2]}")

        # 基本イベントがない場合のフォールバック
        if not events:
            if purpose == "exposition":
                events = ["キャラクター紹介", "状況設定"]
            elif purpose == "conflict":
                events = ["問題発生", "対立表面化"]
            elif purpose == "development":
                events = ["関係発展", "状況変化"]
            elif purpose == "climax":
                events = ["重要な選択", "決定的瞬間"]
            elif purpose == "resolution":
                events = ["問題解決", "次への準備"]

        return events

    def _determine_pov_character(
        self,
        characters_present: list[str],
        narrative_structure: Any | None
    ) -> str:
        """視点キャラクター決定"""
        # 叙述構造から視点設定取得
        if (narrative_structure and
            hasattr(narrative_structure, "viewpoint_config") and
            narrative_structure.viewpoint_config and
            hasattr(narrative_structure.viewpoint_config, "viewpoint_character")):
            preferred_pov = narrative_structure.viewpoint_config.viewpoint_character
            if preferred_pov in characters_present:
                return preferred_pov

        # フォールバック: 最初のキャラクター
        return characters_present[0] if characters_present else "主人公"

    async def _plan_scene_transitions(
        self,
        scene_blocks: list[SceneBlock],
        narrative_structure: Any | None
    ) -> list[SceneTransition]:
        """シーン遷移計画"""
        transitions = []

        for i in range(len(scene_blocks) - 1):
            current_block = scene_blocks[i]
            next_block = scene_blocks[i + 1]

            # 遷移タイプ決定
            transition_type = self._determine_transition_type(current_block, next_block)

            # 時間ギャップ
            time_gap = self._calculate_time_gap(current_block, next_block)

            # 変化要素
            location_change = current_block.location != next_block.location
            character_change = (
                set(current_block.characters_present) !=
                set(next_block.characters_present)
            )

            # ムード変化
            mood_change = self._determine_mood_change(current_block, next_block)

            transition = SceneTransition(
                from_block=current_block.block_id,
                to_block=next_block.block_id,
                transition_type=transition_type,
                time_gap=time_gap,
                location_change=location_change,
                character_change=character_change,
                mood_change=mood_change
            )

            transitions.append(transition)

        return transitions

    def _determine_transition_type(
        self,
        current_block: SceneBlock,
        next_block: SceneBlock
    ) -> str:
        """遷移タイプ決定"""
        # 緊張レベルの変化に基づく
        tension_diff = next_block.tension_level - current_block.tension_level

        if abs(tension_diff) <= 2:
            return "continuous"  # 連続的
        if tension_diff > 2:
            return "cut"  # 急な転換
        return "fade"  # 緩やかな転換

    def _calculate_time_gap(
        self,
        current_block: SceneBlock,
        next_block: SceneBlock
    ) -> str:
        """時間ギャップ計算"""
        # 位置による基本的な時間ギャップ
        if current_block.position == "opening" and next_block.position == "development":
            return "minutes"
        if (current_block.position == "development" and next_block.position == "climax") or (current_block.position == "climax" and next_block.position == "resolution"):
            return "immediate"
        return "minutes"

    def _determine_mood_change(
        self,
        current_block: SceneBlock,
        next_block: SceneBlock
    ) -> str:
        """ムード変化決定"""
        if current_block.emotional_tone == next_block.emotional_tone:
            return "maintain"
        if (current_block.tension_level < next_block.tension_level):
            return "shift"
        return "contrast"

    async def _optimize_scene_design(
        self,
        scene_blocks: list[SceneBlock],
        transitions: list[SceneTransition],
        target_words: int
    ) -> tuple[list[SceneBlock], list[SceneTransition]]:
        """シーン設計最適化"""
        # 文字数配分最適化
        total_allocated = sum(block.estimated_word_count for block in scene_blocks)
        if total_allocated != target_words:
            ratio = target_words / total_allocated
            for block in scene_blocks:
                block.estimated_word_count = int(block.estimated_word_count * ratio)

        # バランス調整
        optimized_blocks = self._balance_scene_content(scene_blocks)

        return optimized_blocks, transitions

    def _balance_scene_content(self, scene_blocks: list[SceneBlock]) -> list[SceneBlock]:
        """シーンコンテンツバランス調整"""
        for block in scene_blocks:
            # 比率の正規化（合計を1.0に）
            total_ratio = (block.dialogue_ratio +
                          block.action_ratio +
                          block.description_ratio)

            if total_ratio != 1.0 and total_ratio > 0:
                block.dialogue_ratio /= total_ratio
                block.action_ratio /= total_ratio
                block.description_ratio /= total_ratio

        return scene_blocks

    def _create_integrated_plan(
        self,
        episode_number: int,
        target_words: int,
        scene_blocks: list[SceneBlock],
        transitions: list[SceneTransition],
        context_result: Any | None
    ) -> SceneDesignPlan:
        """統合プラン作成"""
        # 主要要素抽出
        primary_characters = []
        dominant_location = ""

        if context_result:
            if hasattr(context_result, "character_contexts"):
                for char_context in context_result.character_contexts:
                    if char_context.role in ["protagonist", "antagonist"]:
                        primary_characters.append(char_context.character_name)

            if (hasattr(context_result, "world_context") and
                context_result.world_context and
                hasattr(context_result.world_context, "location")):
                dominant_location = context_result.world_context.location

        # 複雑度評価
        complexity_level = "medium"
        if len(scene_blocks) <= 3:
            complexity_level = "simple"
        elif len(scene_blocks) >= 7:
            complexity_level = "complex"

        return SceneDesignPlan(
            episode_number=episode_number,
            total_estimated_words=target_words,
            scene_count=len(scene_blocks),
            scene_blocks=scene_blocks,
            transitions=transitions,
            dominant_location=dominant_location,
            primary_characters=primary_characters,
            overall_mood="dynamic",
            complexity_level=complexity_level,
            special_requirements=[]
        )
