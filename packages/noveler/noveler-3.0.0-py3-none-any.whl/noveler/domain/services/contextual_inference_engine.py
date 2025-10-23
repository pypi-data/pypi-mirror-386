"""動的コンテキスト推論エンジン"""

from dataclasses import dataclass, field
from typing import Any

from noveler.domain.entities.chapter_plot import ChapterPlot
from noveler.domain.entities.previous_episode_context import PreviousEpisodeContext
from noveler.domain.value_objects.episode_number import EpisodeNumber


@dataclass
class ContextualInference:
    """コンテキスト推論結果"""

    inference_type: str
    confidence_score: float  # 0.0-1.0
    inferred_content: dict[str, Any]
    reasoning_notes: list[str] = field(default_factory=list)
    source_indicators: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """初期化後の型安全性チェック"""
        # confidence_scoreの型安全性を強制
        if not isinstance(self.confidence_score, int | float):
            if isinstance(self.confidence_score, list) and len(self.confidence_score) > 0:
                # リスト型の場合は最初の要素を使用
                self.confidence_score = float(self.confidence_score[0])
            else:
                # その他の場合はデフォルト値
                self.confidence_score = 0.5

        # floatに変換して範囲チェック
        self.confidence_score = float(self.confidence_score)
        self.confidence_score = max(0.0, min(1.0, self.confidence_score))

    def to_yaml_dict(self) -> dict[str, Any]:
        """YAML形式の辞書に変換"""
        return {
            "inference_type": self.inference_type,
            "confidence_score": self.confidence_score,
            "inferred_content": self.inferred_content,
            "reasoning_notes": self.reasoning_notes,
            "source_indicators": self.source_indicators,
        }


@dataclass
class DynamicPromptContext:
    """動的プロンプトコンテキスト"""

    episode_number: EpisodeNumber
    story_phase: str  # introduction, development, climax, resolution
    character_growth_stage: str
    technical_complexity_level: str
    emotional_focus_areas: list[str] = field(default_factory=list)
    adaptive_elements: dict[str, Any] = field(default_factory=dict)
    inferences: list[ContextualInference] = field(default_factory=list)

    def add_inference(self, inference: ContextualInference) -> None:
        """推論結果を追加"""
        self.inferences.append(inference)

    def get_high_confidence_inferences(self, threshold: float = 0.7) -> list[ContextualInference]:
        """高信頼度推論結果を取得（型安全性対応版）"""
        high_confidence_inferences = []
        for inf in self.inferences:
            try:
                # 型安全な比較
                if isinstance(inf.confidence_score, int | float) and inf.confidence_score >= threshold:
                    high_confidence_inferences.append(inf)
                elif isinstance(inf.confidence_score, list):
                    # リストの場合は最初の要素で比較
                    if len(inf.confidence_score) > 0:
                        score = float(inf.confidence_score[0])
                        if score >= threshold:
                            high_confidence_inferences.append(inf)
                else:
                    # その他の型の場合は除外
                    continue
            except (TypeError, ValueError):
                # 比較できない場合は除外
                continue
        return high_confidence_inferences

    def to_yaml_dict(self) -> dict[str, Any]:
        """YAML形式の辞書に変換"""
        return {
            "episode_number": self.episode_number.value,
            "story_phase": self.story_phase,
            "character_growth_stage": self.character_growth_stage,
            "technical_complexity_level": self.technical_complexity_level,
            "emotional_focus_areas": self.emotional_focus_areas,
            "adaptive_elements": self.adaptive_elements,
            "inferences": [inf.to_yaml_dict() for inf in self.inferences],
        }


class ContextualInferenceEngine:
    """動的コンテキスト推論エンジン

    前話情報と章別プロット情報から、次話の執筆に最適化された
    コンテキストを動的に推論・生成する。

    推論対象:
    - ストーリーフェーズの自動判定
    - キャラクター成長段階の推定
    - 技術的複雑度レベルの調整
    - 感情的フォーカス領域の特定
    - 適応的要素の動的生成
    """

    def __init__(self) -> None:
        """推論エンジン初期化"""
        # ストーリーフェーズ推論用の重み係数
        self._phase_weights = {
            "introduction": {"setup": 0.8, "character_intro": 0.7, "world_building": 0.6},
            "development": {"conflict": 0.7, "growth": 0.8, "complication": 0.6},
            "climax": {"tension": 0.9, "resolution": 0.8, "revelation": 0.7},
            "resolution": {"conclusion": 0.8, "reflection": 0.7, "closure": 0.9},
        }

        # キャラクター成長指標
        self._growth_indicators = {
            "beginner": ["初めて", "わからない", "教えて", "難しい"],
            "learning": ["理解", "わかった", "できそう", "挑戦"],
            "practicing": ["やってみる", "実践", "練習", "応用"],
            "competent": ["できる", "上手", "教える", "指導"],
            "expert": ["マスター", "完璧", "極める", "創造"],
        }

        # 技術複雑度指標
        self._complexity_indicators = {
            "basic": ["基礎", "入門", "簡単", "初級"],
            "intermediate": ["応用", "中級", "実践", "組み合わせ"],
            "advanced": ["高度", "上級", "複雑", "統合"],
            "expert": ["最先端", "革新", "独創", "理論"],
        }

    def generate_dynamic_context(
        self,
        episode_number: EpisodeNumber,
        chapter_plot: ChapterPlot | None,
        previous_context: PreviousEpisodeContext | None,
    ) -> DynamicPromptContext:
        """動的コンテキスト生成

        Args:
            episode_number: 現在のエピソード番号
            chapter_plot: 章別プロット情報
            previous_context: 前話コンテキスト情報

        Returns:
            動的プロンプトコンテキスト
        """
        # 基本コンテキスト初期化
        dynamic_context = DynamicPromptContext(
            episode_number=episode_number,
            story_phase="development",  # デフォルト
            character_growth_stage="learning",  # デフォルト
            technical_complexity_level="intermediate",  # デフォルト
        )

        # ストーリーフェーズ推論
        story_phase_inference = self._infer_story_phase(episode_number, chapter_plot, previous_context)
        dynamic_context.story_phase = story_phase_inference.inferred_content.get("phase", "development")
        dynamic_context.add_inference(story_phase_inference)

        # キャラクター成長段階推論
        growth_inference = self._infer_character_growth_stage(previous_context, chapter_plot)
        dynamic_context.character_growth_stage = growth_inference.inferred_content.get("stage", "learning")
        dynamic_context.add_inference(growth_inference)

        # 技術複雑度レベル推論
        complexity_inference = self._infer_technical_complexity(episode_number, previous_context, chapter_plot)
        dynamic_context.technical_complexity_level = complexity_inference.inferred_content.get("level", "intermediate")
        dynamic_context.add_inference(complexity_inference)

        # 感情フォーカス推論
        emotional_inference = self._infer_emotional_focus_areas(previous_context, dynamic_context)
        dynamic_context.emotional_focus_areas = emotional_inference.inferred_content.get("focus_areas", [])
        dynamic_context.add_inference(emotional_inference)

        # 適応的要素推論
        adaptive_inference = self._infer_adaptive_elements(dynamic_context, previous_context, chapter_plot)
        dynamic_context.adaptive_elements = adaptive_inference.inferred_content.get("adaptive_elements", {})
        dynamic_context.add_inference(adaptive_inference)

        return dynamic_context

    def _infer_story_phase(
        self,
        episode_number: EpisodeNumber,
        chapter_plot: ChapterPlot | None,
        previous_context: PreviousEpisodeContext | None,
    ) -> ContextualInference:
        """ストーリーフェーズ推論

        Args:
            episode_number: エピソード番号
            chapter_plot: 章別プロット
            previous_context: 前話コンテキスト

        Returns:
            ストーリーフェーズ推論結果
        """
        reasoning_notes = []
        source_indicators = []

        # エピソード番号による基本推論
        total_episodes = 100  # 仮の総エピソード数
        progress_ratio = episode_number.value / total_episodes

        if progress_ratio <= 0.25:
            base_phase = "introduction"
            reasoning_notes.append("エピソード進行率から導入部と推定")
        elif progress_ratio <= 0.75:
            base_phase = "development"
            reasoning_notes.append("エピソード進行率から展開部と推定")
        elif progress_ratio <= 0.9:
            base_phase = "climax"
            reasoning_notes.append("エピソード進行率からクライマックス部と推定")
        else:
            base_phase = "resolution"
            reasoning_notes.append("エピソード進行率から解決部と推定")

        # 前話コンテキストによる調整
        confidence_score = 0.6  # 基本信頼度

        if previous_context and previous_context.has_sufficient_context():
            story_momentum = previous_context.story_progression.story_momentum

            if story_momentum == "climactic":
                base_phase = "climax"
                confidence_score = 0.9
                reasoning_notes.append("前話のストーリーモメンタムが最高潮のため、クライマックス部に調整")
                source_indicators.append("前話ストーリーモメンタム: climactic")
            elif story_momentum == "high" and progress_ratio > 0.5:
                if base_phase == "development":
                    base_phase = "climax"
                    confidence_score = 0.8
                    reasoning_notes.append("前話の高いモメンタムから、クライマックス部への移行を推定")
                    source_indicators.append("前話ストーリーモメンタム: high")

            # 未解決要素の影響
            unresolved_count = len(previous_context.unresolved_elements)
            if unresolved_count > 3 and base_phase != "resolution":
                reasoning_notes.append(f"未解決要素{unresolved_count}件により、展開継続を推定")
                source_indicators.append(f"未解決要素数: {unresolved_count}")
                confidence_score *= 1.1

        # 章別プロットによる調整
        if chapter_plot:
            current_episode_info = chapter_plot.get_episode_info(episode_number.value)
            if current_episode_info:
                key_themes = current_episode_info.get("key_themes", [])
                if "解決" in key_themes or "完了" in key_themes:
                    base_phase = "resolution"
                    confidence_score = 0.9
                    reasoning_notes.append("章別プロットのテーマから解決部と判定")
                    source_indicators.append(f"章別プロットテーマ: {key_themes}")
                elif "対立" in key_themes or "困難" in key_themes:
                    if base_phase != "resolution":
                        base_phase = "development"
                        confidence_score = 0.85
                        reasoning_notes.append("章別プロットの対立テーマから展開部と判定")
                        source_indicators.append(f"章別プロットテーマ: {key_themes}")

        return ContextualInference(
            inference_type="story_phase",
            confidence_score=min(confidence_score, 1.0),
            inferred_content={"phase": base_phase},
            reasoning_notes=reasoning_notes,
            source_indicators=source_indicators,
        )

    def _infer_character_growth_stage(
        self, previous_context: PreviousEpisodeContext | None, chapter_plot: ChapterPlot | None
    ) -> ContextualInference:
        """キャラクター成長段階推論

        Args:
            previous_context: 前話コンテキスト
            chapter_plot: 章別プロット

        Returns:
            成長段階推論結果
        """
        reasoning_notes = []
        source_indicators = []

        # デフォルト設定
        inferred_stage = "learning"
        confidence_score = 0.5

        if previous_context and previous_context.has_sufficient_context():
            # 前話の技術学習状態から推論
            tech_learning = previous_context.technical_learning
            difficulty_level = tech_learning.difficulty_level
            mastered_count = len(tech_learning.mastered_concepts)

            if mastered_count == 0:
                inferred_stage = "beginner"
                confidence_score = 0.8
                reasoning_notes.append("前話で習得概念がゼロのため、初心者段階と推定")
            elif mastered_count <= 2:
                inferred_stage = "learning"
                confidence_score = 0.8
                reasoning_notes.append(f"前話で{mastered_count}件の概念習得により、学習段階と推定")
            elif mastered_count <= 5:
                inferred_stage = "practicing"
                confidence_score = 0.85
                reasoning_notes.append(f"前話で{mastered_count}件の概念習得により、実践段階と推定")
            else:
                inferred_stage = "competent"
                confidence_score = 0.9
                reasoning_notes.append(f"前話で{mastered_count}件の多数概念習得により、習熟段階と推定")

            source_indicators.append(f"前話習得概念数: {mastered_count}")
            source_indicators.append(f"前話難易度レベル: {difficulty_level}")

            # 難易度レベルによる調整
            if difficulty_level == "advanced" and inferred_stage in ["beginner", "learning"]:
                inferred_stage = "practicing"
                reasoning_notes.append("前話の高難易度から実践段階に調整")
                confidence_score = 0.75

            # キャラクター状態からの成長指標
            main_characters = ["直人", "あすか"]
            for char_name in main_characters:
                char_state = previous_context.get_character_state(char_name)
                if char_state:
                    development_stage = char_state.character_development_stage
                    if "熟練" in development_stage or "上達" in development_stage:
                        if inferred_stage in ["beginner", "learning"]:
                            inferred_stage = "practicing"
                            reasoning_notes.append(f"{char_name}の成長段階から実践段階に調整")
                            source_indicators.append(f"{char_name}成長段階: {development_stage}")

        return ContextualInference(
            inference_type="character_growth_stage",
            confidence_score=confidence_score,
            inferred_content={"stage": inferred_stage},
            reasoning_notes=reasoning_notes,
            source_indicators=source_indicators,
        )

    def _infer_technical_complexity(
        self,
        episode_number: EpisodeNumber,
        previous_context: PreviousEpisodeContext | None,
        chapter_plot: ChapterPlot | None,
    ) -> ContextualInference:
        """技術複雑度レベル推論

        Args:
            episode_number: エピソード番号
            previous_context: 前話コンテキスト
            chapter_plot: 章別プロット

        Returns:
            技術複雑度推論結果
        """
        reasoning_notes = []
        source_indicators = []

        # エピソード進行による基本レベル設定
        if episode_number.value <= 10:
            base_level = "basic"
            reasoning_notes.append("初期エピソードにより基礎レベルと推定")
        elif episode_number.value <= 50:
            base_level = "intermediate"
            reasoning_notes.append("中期エピソードにより中級レベルと推定")
        elif episode_number.value <= 80:
            base_level = "advanced"
            reasoning_notes.append("後期エピソードにより上級レベルと推定")
        else:
            base_level = "expert"
            reasoning_notes.append("終盤エピソードにより専門レベルと推定")

        confidence_score = 0.6

        # 前話の技術学習状況による調整
        if previous_context and previous_context.has_sufficient_context():
            tech_learning = previous_context.technical_learning

            # 習得概念数による調整
            mastered_count = len(tech_learning.mastered_concepts)
            if mastered_count >= 5 and base_level == "basic":
                base_level = "intermediate"
                confidence_score = 0.8
                reasoning_notes.append("前話の多数習得概念により中級レベルに調整")
            elif mastered_count >= 10 and base_level == "intermediate":
                base_level = "advanced"
                confidence_score = 0.85
                reasoning_notes.append("前話の豊富な習得概念により上級レベルに調整")

            source_indicators.append(f"前話習得概念数: {mastered_count}")

            # 実践的応用による調整
            practical_apps = len(tech_learning.practical_applications)
            if practical_apps >= 3:
                if base_level == "basic":
                    base_level = "intermediate"
                    confidence_score = 0.8
                reasoning_notes.append("前話の実践的応用により複雑度を上方調整")
                source_indicators.append(f"前話実践応用数: {practical_apps}")

        # 章別プロットの技術要素による調整
        if chapter_plot:
            current_episode_info = chapter_plot.get_episode_info(episode_number.value)
            if current_episode_info:
                technical_elements = current_episode_info.get("technical_elements", [])

                complex_indicators = ["統合", "高度", "応用", "システム", "アーキテクチャ"]
                if any(indicator in str(technical_elements) for indicator in complex_indicators):
                    if base_level in ["basic", "intermediate"]:
                        base_level = "advanced"
                        confidence_score = 0.9
                        reasoning_notes.append("章別プロットの高度技術要素により上級レベルに調整")
                        source_indicators.append(f"章技術要素: {technical_elements}")

        return ContextualInference(
            inference_type="technical_complexity_level",
            confidence_score=confidence_score,
            inferred_content={"level": base_level},
            reasoning_notes=reasoning_notes,
            source_indicators=source_indicators,
        )

    def _infer_emotional_focus_areas(
        self, previous_context: PreviousEpisodeContext | None, dynamic_context: DynamicPromptContext
    ) -> ContextualInference:
        """感情フォーカス領域推論

        Args:
            previous_context: 前話コンテキスト
            dynamic_context: 動的コンテキスト

        Returns:
            感情フォーカス推論結果
        """
        reasoning_notes = []
        source_indicators = []
        focus_areas = []

        # ストーリーフェーズによる基本フォーカス
        phase_focus_mapping = {
            "introduction": ["好奇心", "期待", "不安"],
            "development": ["挑戦", "成長", "困難克服"],
            "climax": ["緊張", "決意", "達成感"],
            "resolution": ["満足", "安堵", "未来への希望"],
        }

        story_phase = dynamic_context.story_phase
        if story_phase in phase_focus_mapping:
            focus_areas.extend(phase_focus_mapping[story_phase])
            reasoning_notes.append(f"ストーリーフェーズ「{story_phase}」による基本感情フォーカス設定")

        # キャラクター成長段階による調整
        growth_emotional_mapping = {
            "beginner": ["不安", "好奇心", "驚き"],
            "learning": ["理解の喜び", "発見", "達成感"],
            "practicing": ["自信", "挑戦", "集中"],
            "competent": ["誇り", "指導する喜び", "責任感"],
            "expert": ["創造の喜び", "完成感", "伝承の意欲"],
        }

        growth_stage = dynamic_context.character_growth_stage
        if growth_stage in growth_emotional_mapping:
            growth_emotions = growth_emotional_mapping[growth_stage]
            focus_areas.extend(growth_emotions)
            reasoning_notes.append(f"成長段階「{growth_stage}」による感情フォーカス追加")

        # 前話の感情の流れによる継続性
        if previous_context and previous_context.has_sufficient_context():
            emotional_flow = previous_context.emotional_flow
            if emotional_flow:
                # 最後の感情状態を継続・発展させる
                last_emotion = emotional_flow[-1] if emotional_flow else ""
                if "→" in last_emotion:
                    final_emotion = last_emotion.split("→")[-1].strip()
                    focus_areas.append(final_emotion)
                    reasoning_notes.append(f"前話の感情終了状態「{final_emotion}」を継続")
                    source_indicators.append(f"前話最終感情: {final_emotion}")

            # キャラクター状態の感情
            for char_name, char_state in previous_context.character_states.items():
                if char_state.emotional_state and char_state.emotional_state != "平静":
                    focus_areas.append(char_state.emotional_state)
                    reasoning_notes.append(f"{char_name}の前話感情状態を継続")
                    source_indicators.append(f"{char_name}前話感情: {char_state.emotional_state}")

        # 重複除去と重要度順にソート
        focus_areas = list(dict.fromkeys(focus_areas))  # 順序を保持した重複除去
        focus_areas = focus_areas[:5]  # 最大5つまで

        confidence_score = 0.8 if previous_context and previous_context.has_sufficient_context() else 0.6

        return ContextualInference(
            inference_type="emotional_focus_areas",
            confidence_score=confidence_score,
            inferred_content={"focus_areas": focus_areas},
            reasoning_notes=reasoning_notes,
            source_indicators=source_indicators,
        )

    def _infer_adaptive_elements(
        self,
        dynamic_context: DynamicPromptContext,
        previous_context: PreviousEpisodeContext | None,
        chapter_plot: ChapterPlot | None,
    ) -> ContextualInference:
        """適応的要素推論

        Args:
            dynamic_context: 動的コンテキスト
            previous_context: 前話コンテキスト
            chapter_plot: 章別プロット

        Returns:
            適応的要素推論結果
        """
        reasoning_notes = []
        source_indicators = []
        adaptive_elements = {}

        episode_number = dynamic_context.episode_number

        # プロンプト調整レベル
        complexity_level = dynamic_context.technical_complexity_level
        if complexity_level == "basic":
            adaptive_elements["prompt_detail_level"] = "detailed"
            adaptive_elements["explanation_depth"] = "thorough"
            reasoning_notes.append("基礎レベルにより詳細な説明モードに設定")
        elif complexity_level == "advanced":
            adaptive_elements["prompt_detail_level"] = "concise"
            adaptive_elements["explanation_depth"] = "essential"
            reasoning_notes.append("上級レベルにより簡潔な説明モードに設定")
        else:
            adaptive_elements["prompt_detail_level"] = "balanced"
            adaptive_elements["explanation_depth"] = "moderate"

        # 継続性要素の強調
        if previous_context and previous_context.has_sufficient_context():
            unresolved_count = len(previous_context.unresolved_elements)
            if unresolved_count > 0:
                adaptive_elements["continuity_emphasis"] = "high"
                adaptive_elements["unresolved_integration"] = True
                reasoning_notes.append(f"{unresolved_count}件の未解決要素により継続性を強調")
                source_indicators.append(f"未解決要素数: {unresolved_count}")

            # シーン継続性
            continuity_notes = len(previous_context.scene_continuity_notes)
            if continuity_notes > 0:
                adaptive_elements["scene_transition_support"] = True
                reasoning_notes.append("前話のシーン継続性により移行サポートを有効化")
                source_indicators.append(f"継続性ノート数: {continuity_notes}")

        # エピソード位置による特別調整
        if episode_number.value == 1:
            adaptive_elements["introduction_mode"] = True
            adaptive_elements["world_building_emphasis"] = "high"
            reasoning_notes.append("第1話により導入モードと世界観構築強調を設定")
        elif episode_number.value % 10 == 0:  # 10の倍数話
            adaptive_elements["milestone_episode"] = True
            adaptive_elements["reflection_element"] = "enhanced"
            reasoning_notes.append("節目エピソードによりマイルストーンモードを設定")

        # 感情フォーカスによる調整
        emotional_focus_count = len(dynamic_context.emotional_focus_areas)
        if emotional_focus_count > 3:
            adaptive_elements["emotional_depth"] = "enhanced"
            reasoning_notes.append("多数の感情フォーカス領域により感情描写を強化")
        elif emotional_focus_count == 0:
            adaptive_elements["emotional_depth"] = "basic"
            adaptive_elements["action_focus"] = "enhanced"
            reasoning_notes.append("感情フォーカス不足によりアクション重視に調整")

        # 章別プロットによる特別調整
        if chapter_plot:
            current_episode_info = chapter_plot.get_episode_info(episode_number.value)
            if current_episode_info:
                estimated_length = current_episode_info.get("estimated_length", 6000)
                if estimated_length > 8000:
                    adaptive_elements["length_expansion"] = True
                    adaptive_elements["scene_detail_level"] = "enhanced"
                    reasoning_notes.append("想定文字数の多さにより詳細描写を強化")
                elif estimated_length < 4000:
                    adaptive_elements["length_constraint"] = True
                    adaptive_elements["scene_detail_level"] = "concise"
                    reasoning_notes.append("想定文字数の少なさにより簡潔描写に調整")

                source_indicators.append(f"想定文字数: {estimated_length}")

        confidence_score = 0.85 if len(adaptive_elements) > 3 else 0.7

        return ContextualInference(
            inference_type="adaptive_elements",
            confidence_score=confidence_score,
            inferred_content={"adaptive_elements": adaptive_elements},
            reasoning_notes=reasoning_notes,
            source_indicators=source_indicators,
        )
