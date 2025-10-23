"""
強化プロンプトテンプレートサービス

SPEC-PROMPT-SAVE-001: プロンプト保存機能仕様書準拠
前回分析の詳細化要件実装
"""

from dataclasses import dataclass
from typing import Any

from noveler.domain.entities.chapter_plot import ChapterPlot


@dataclass
class EnhancedPromptContext:
    """強化プロンプト生成コンテキスト"""

    episode_number: int
    episode_title: str
    chapter_plot: ChapterPlot
    previous_episodes: list[dict[str, Any]]
    following_episodes: list[dict[str, Any]]
    project_context: dict[str, Any]


@dataclass
class EnhancedPromptTemplate:
    """強化プロンプトテンプレート"""

    template_sections: dict[str, str]
    required_sections: list[str]
    quality_targets: dict[str, int]
    template_version: str = "2.0"


class EnhancedPromptTemplateService:
    """強化プロンプトテンプレートサービス

    責務:
    - 既存プロットレベル（150-200行）の詳細プロンプト生成
    - 11主要セクション + 詳細サブセクション構造化
    - 前回分析で特定された情報量不足問題の解決
    """

    def __init__(self) -> None:
        """サービス初期化"""
        self._enhanced_template = self._create_enhanced_template()

    def generate_enhanced_prompt(self, context: EnhancedPromptContext) -> str:
        """強化プロンプト生成

        Args:
            context: 生成コンテキスト

        Returns:
            str: 生成された詳細プロンプト（150-200行目標）
        """
        sections = []

        # 1. エピソード基本情報（詳細化）
        sections.append(self._generate_episode_basic_info(context))

        # 2. 前話振り返り（詳細化）
        sections.append(self._generate_previous_episode_summary(context))

        # 3. 今話概要（詳細化）
        sections.append(self._generate_current_episode_summary(context))

        # 4. シーン構成（大幅詳細化）
        sections.append(self._generate_detailed_scene_structure(context))

        # 5. キャラクター成長（詳細化）
        sections.append(self._generate_character_development(context))

        # 6. 技術要素（詳細化）
        sections.append(self._generate_technical_elements(context))

        # 7. 伏線管理（3層構造化）
        sections.append(self._generate_foreshadowing_structure(context))

        # 8. 品質チェック項目（6項目詳細化）
        sections.append(self._generate_quality_checklist(context))

        # 9. 執筆時注意点（詳細化）
        sections.append(self._generate_writing_notes(context))

        # 10. 重要成果（成果明確化）
        sections.append(self._generate_key_outcomes(context))

        # 11. 次話への引き（継続性強化）
        sections.append(self._generate_next_episode_hook(context))

        return "\n\n".join(sections)

    def _generate_episode_basic_info(self, context: EnhancedPromptContext) -> str:
        """エピソード基本情報生成（詳細化）"""
        return f"""# 第{context.episode_number:03d}話：{context.episode_title}

# EPISODE_PLOT_SCHEMA準拠
episode_number: {context.episode_number}
title: "{context.episode_title}"
chapter: {context.chapter_plot.chapter_number.value}
stage: "{self._determine_episode_stage(context)}"
word_count_target: {self._calculate_word_count_target(context)}"""

    def _generate_previous_episode_summary(self, context: EnhancedPromptContext) -> str:
        """前話振り返り生成（詳細化）"""
        if not context.previous_episodes:
            return """# 前話の振り返り
previous_episode_summary: "第1話のため前話なし。物語の開始エピソード。\""""

        prev_episode = context.previous_episodes[-1]  # 直前のエピソード

        return f"""# 前話の振り返り
previous_episode_summary: "第{prev_episode.get("episode_number", context.episode_number - 1):03d}話で{prev_episode.get("summary", "物語が進展")}。キャラクターの状況変化と今話への影響を詳細に記述。\""""

    def _generate_current_episode_summary(self, context: EnhancedPromptContext) -> str:
        """今話概要生成（詳細化）"""
        episode_info = context.chapter_plot.get_episode_info(context.episode_number)
        base_summary = episode_info.get("summary", "エピソードの詳細展開") if episode_info else "エピソードの詳細展開"

        return f"""# 今話の概要
summary: "{base_summary}。具体的な場面展開、キャラクターの心境変化、重要な出来事の詳細を含む包括的な概要。"

# 今話の目的
purpose: "{self._determine_episode_purpose(context)}" """

    def _generate_detailed_scene_structure(self, context: EnhancedPromptContext) -> str:
        """詳細シーン構成生成（大幅詳細化）"""
        scenes = []
        scene_count = self._determine_optimal_scene_count(context)

        for i in range(1, scene_count + 1):
            scene = f"""  scene_{i:02d}:
    location: "[シーン{i}の具体的場所設定]"
    time: "[時間帯・タイミング設定]"
    duration: "{self._calculate_scene_duration(i, scene_count)}文字"
    description: "[シーン{i}の詳細な内容・目的説明]"
    participants: {self._get_scene_participants(context, i)}
    key_events:
      - "[シーン{i}の重要イベント1]"
      - "[シーン{i}の重要イベント2]"
      - "[シーン{i}の重要イベント3]"
    dialogue_highlights:
      - "[キャラクター名]：「具体的な台詞例1」（感情・意図説明）"
      - "[キャラクター名]：「具体的な台詞例2」（感情・意図説明）"
      - "[キャラクター名]：「具体的な台詞例3」（感情・意図説明）"
    technical_elements:
      - "[シーン{i}の技術的要素1]"
      - "[シーン{i}の技術的要素2]"
    emotional_beats:
      - "[シーン{i}の感情的ハイライト1]"
      - "[シーン{i}の感情的ハイライト2]\""""

            if i < scene_count:  # 最後のシーン以外:
                scene += """
    character_development:
      - "[キャラクター成長要素]"
    foreshadowing:
      - "[このシーンで張られる伏線]" """

            scenes.append(scene)

        return f"""# シーン構成
scene_structure:
    {chr(10).join(scenes)}"""

    def _generate_character_development(self, context: EnhancedPromptContext) -> str:
        """キャラクター成長生成（詳細化）"""
        main_characters = self._get_main_characters(context)
        character_sections = []

        for char_name in main_characters:
            char_section = f"""  {char_name.lower().replace(" ", "_")}:
    growth: "[{char_name}の内面的・技術的成長の具体的描写]"
    new_skills: "[今話で獲得・向上するスキルや能力]"
    emotional_state: "[今話終了時点での心境・感情状態]"
    relationship_changes: "[他キャラクターとの関係性変化]"
    future_impact: "[今後の物語への影響予測]" """
            character_sections.append(char_section)

        return f"""# キャラクター成長
character_development:
    {chr(10).join(character_sections)}"""

    def _generate_technical_elements(self, context: EnhancedPromptContext) -> str:
        """技術要素生成（詳細化）"""
        return """# 技術要素
technical_elements:
  programming_concepts:
    - "[プログラミング概念1の詳細説明]"
    - "[プログラミング概念2の詳細説明]"
    - "[プログラミング概念3の詳細説明]"
  magic_system:
    - "[魔術システム要素1の詳細]"
    - "[魔術システム要素2の詳細]"
    - "[魔術システム要素3の詳細]"
  debug_elements:
    - "[デバッグ要素1の具体的活用]"
    - "[デバッグ要素2の具体的活用]"
  world_building:
    - "[世界観構築要素1]"
    - "[世界観構築要素2]" """

    def _generate_foreshadowing_structure(self, context: EnhancedPromptContext) -> str:
        """伏線管理生成（3層構造化）"""
        return """# 伏線要素
foreshadowing:
  immediate: "[次話への直接的な繋がり・期待感醸成]"
  short_term: "[2-5話先への中期的伏線・キャラ関係発展]"
  long_term: "[章・部全体への長期的伏線・重要設定]"
  character_relationships: "[人間関係の変化・新たな関係性への布石]"
  mystery_elements: "[謎要素の深化・新たな謎の提示]"
  plot_advancement: "[メインプロット進展への布石]"""

    def _generate_quality_checklist(self, context: EnhancedPromptContext) -> str:
        """品質チェック項目生成（6項目詳細化）"""
        return """# 品質チェック項目
quality_checklist:
  narrative_flow: "[物語の流れと論理的一貫性の確保]"
  character_consistency: "[キャラクター言動の一貫性と成長の自然さ]"
  technical_accuracy: "[プログラミング・魔術設定の正確性維持]"
  emotional_resonance: "[読者の感情的共感と満足度の確保]"
  pacing_balance: "[シーン展開のテンポと緊張感の調整]"
  foreshadowing_integration: "[伏線の適切な配置と回収の準備]"""

    def _generate_writing_notes(self, context: EnhancedPromptContext) -> str:
        """執筆時注意点生成（詳細化）"""
        return """# 執筆時の注意点
writing_notes:
  viewpoint: "[視点管理の具体的指針と一人称視点の活用]"
  tone: "[エピソード全体のトーンと感情表現の統一]"
  pacing: "[シーン間のテンポ配分と読者の関心維持]"
  dialogue_style: "[キャラクター固有の話し方と自然な会話流れ]"
  technical_balance: "[技術解説と物語進展のバランス調整]"
  emotional_climax: "[感情的ハイライトの効果的配置]"""

    def _generate_key_outcomes(self, context: EnhancedPromptContext) -> str:
        """重要成果生成（成果明確化）"""
        return """# 重要な成果
key_outcomes:
  plot_advancement: "[メインプロット進展の具体的成果]"
  character_growth: "[主要キャラクターの成長成果]"
  relationship_development: "[人間関係の発展・変化成果]"
  world_building_expansion: "[世界観拡張・新設定導入成果]"
  mystery_progression: "[謎要素の進展・新たな発見成果]"
  reader_engagement: "[読者の関心・期待向上成果]"""

    def _generate_next_episode_hook(self, context: EnhancedPromptContext) -> str:
        """次話への引き生成（継続性強化）"""
        return """# 次話への引き
next_episode_hook: "[今話の成果を踏まえた次話への期待感醸成。新たな課題・謎・関係性の予告。読者の継続的関心を引く具体的な展望。]"

# 次話準備要素
next_episode_setup:
  - "[次話で展開予定の要素1]"
  - "[次話で展開予定の要素2]"
  - "[次話で展開予定の要素3]" """

    def _create_enhanced_template(self) -> EnhancedPromptTemplate:
        """強化テンプレート作成"""
        return EnhancedPromptTemplate(
            template_sections={
                "basic_info": "エピソード基本情報",
                "previous_summary": "前話振り返り",
                "current_summary": "今話概要",
                "scene_structure": "詳細シーン構成",
                "character_development": "キャラクター成長",
                "technical_elements": "技術要素",
                "foreshadowing": "伏線管理",
                "quality_checklist": "品質チェック",
                "writing_notes": "執筆注意点",
                "key_outcomes": "重要成果",
                "next_hook": "次話への引き",
            },
            required_sections=[
                "basic_info",
                "scene_structure",
                "character_development",
                "foreshadowing",
                "quality_checklist",
            ],
            quality_targets={
                "total_lines": 180,  # 150-200行目標の中央値
                "scene_count": 4,  # 4シーン標準
                "character_count": 3,  # 主要3キャラクター
                "foreshadowing_layers": 3,  # 3層伏線構造
            },
        )

    # ヘルパーメソッド群
    def _determine_episode_stage(self, context: EnhancedPromptContext) -> str:
        """エピソード段階決定"""
        total_episodes = len(context.chapter_plot.episodes) if context.chapter_plot.episodes else 1
        if context.episode_number <= total_episodes // 3:
            return "導入・展開期"
        if context.episode_number <= total_episodes * 2 // 3:
            return "発展・深化期"
        return "クライマックス・解決期"

    def _calculate_word_count_target(self, context: EnhancedPromptContext) -> int:
        """目標文字数計算"""
        base_count = 3500
        episode_importance = self._assess_episode_importance(context)
        return base_count + (episode_importance * 500)

    def _determine_optimal_scene_count(self, context: EnhancedPromptContext) -> int:
        """最適シーン数決定"""
        return 4  # 標準4シーン構成

    def _calculate_scene_duration(self, scene_index: int, total_scenes: int) -> int:
        """シーン文字数計算"""
        base_duration = 1000
        if scene_index == total_scenes:  # 最終シーンは短く:
            return 600
        if scene_index == total_scenes - 1:  # クライマックスシーンは長く
            return 1200
        return base_duration

    def _get_scene_participants(self, context: EnhancedPromptContext, scene_index: int) -> list[str]:
        """シーン参加者取得"""
        return ['"直人"', '"あすか"', '"レガシー先輩"']

    def _get_main_characters(self, context: EnhancedPromptContext) -> dict[str, str]:
        """主要キャラクター取得"""
        return {"naoto": "主人公", "asuka": "ヒロイン・研究パートナー", "legacy_senpai": "メンター・先輩"}

    def _determine_episode_purpose(self, context: EnhancedPromptContext) -> str:
        """エピソード目的決定"""
        return f"第{context.episode_number}話の物語進展・キャラクター成長・重要情報提示"

    def _assess_episode_importance(self, context: EnhancedPromptContext) -> int:
        """エピソード重要度評価"""
        # 1-3のスケールで重要度を評価
        return 2  # 標準重要度
