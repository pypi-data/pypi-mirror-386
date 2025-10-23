"""Domain.value_objects.a30_prompt_template
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

from noveler.domain.utils.domain_console import console

"A30準拠プロンプトテンプレートシステム\n\nA38執筆プロンプトガイドに基づく詳細段階別プロンプトテンプレート。\nDetailedExecutionStageと連携し、A30の16STEPとの整合性を確保。\n\n外部YAMLファイルからのプロンプトテンプレート読み込みに対応。\n"
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

import yaml

from noveler.domain.value_objects.detailed_execution_stage import DetailedExecutionStage


class PromptTemplateType(Enum):
    """プロンプトテンプレートタイプ"""

    STRUCTURE_ANALYSIS = "structure_analysis"
    VERIFICATION = "verification"
    DESIGN = "design"
    GENERATION = "generation"
    QUALITY_CHECK = "quality_check"


@dataclass
class A30PromptTemplate:
    """A30準拠プロンプトテンプレート

    各DetailedExecutionStageに対応する詳細なプロンプトテンプレート。
    A38執筆プロンプトガイドのSTEP仕様に準拠。
    """

    stage: DetailedExecutionStage
    template_type: PromptTemplateType
    system_prompt: str
    user_prompt_template: str
    expected_output_format: str
    quality_criteria: list[str] = field(default_factory=list)
    a30_step_references: list[int] = field(default_factory=list)

    @property
    def template_id(self) -> str:
        """テンプレート識別子"""
        return f"{self.stage.value}_{self.template_type.value}"

    def format_user_prompt(self, **kwargs) -> str:
        """ユーザープロンプトの整形

        Args:
            **kwargs: テンプレート変数

        Returns:
            整形されたユーザープロンプト
        """
        try:
            return self.user_prompt_template.format(**kwargs)
        except KeyError as e:
            missing_var = str(e).strip("'")
            msg = f"必須テンプレート変数が不足: {missing_var}"
            raise ValueError(msg)


class A30PromptTemplateRegistry:
    """A30プロンプトテンプレート登録システム

    DetailedExecutionStageの各段階に対応するプロンプトテンプレートを管理。
    A38執筆プロンプトガイドとの整合性を保持。
    """

    _templates: ClassVar[dict[str, A30PromptTemplate]] = {}

    @classmethod
    def register_templates(cls) -> None:
        """全テンプレートの登録"""
        try:
            cls._register_external_templates()
        except Exception as e:
            console.print(f"外部テンプレート読み込みエラー、内部実装を使用: {e}")
            cls._register_logic_verification_templates()
            cls._register_character_consistency_templates()
            cls._register_dialogue_design_templates()
            cls._register_emotion_curve_templates()
            cls._register_scene_atmosphere_templates()

    @classmethod
    def get_template(cls, stage: DetailedExecutionStage, template_type: PromptTemplateType) -> A30PromptTemplate:
        """テンプレート取得

        Args:
            stage: 実行段階
            template_type: テンプレートタイプ

        Returns:
            対応するプロンプトテンプレート

        Raises:
            KeyError: 対応するテンプレートが存在しない場合
        """
        template_id = f"{stage.value}_{template_type.value}"
        if template_id not in cls._templates:
            msg = f"テンプレートが未登録: {template_id}"
            raise KeyError(msg)
        return cls._templates[template_id]

    @classmethod
    def _register_external_templates(cls) -> None:
        """外部YAMLファイルからのテンプレート登録"""
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent
        templates_dir = project_root / "templates" / "a30_prompts"
        if not templates_dir.exists():
            msg = f"A30プロンプトテンプレートディレクトリが存在しません: {templates_dir}"
            raise FileNotFoundError(msg)
        template_files = [
            "step5_logic_verification.yaml",
            "step6_character_consistency.yaml",
            "step7_dialogue_design.yaml",
            "step8_emotion_curve.yaml",
            "step9_scene_atmosphere.yaml",
        ]
        for template_file in template_files:
            file_path = templates_dir / template_file
            if file_path.exists():
                cls._load_yaml_template(file_path)
            else:
                console.print(f"警告: テンプレートファイルが見つかりません: {file_path}")

    @classmethod
    def _load_yaml_template(cls, yaml_file: Path) -> None:
        """個別YAMLテンプレートファイルの読み込み"""
        try:
            with open(yaml_file, encoding="utf-8") as f:
                yaml_data: dict[str, Any] = yaml.safe_load(f)
            metadata = yaml_data.get("metadata", {})
            prompts = yaml_data.get("prompts", {})
            quality_criteria = yaml_data.get("quality_criteria", [])
            stage_map = {
                "logic_verification": DetailedExecutionStage.LOGIC_VERIFICATION,
                "character_consistency": DetailedExecutionStage.CHARACTER_CONSISTENCY,
                "dialogue_design": DetailedExecutionStage.DIALOGUE_DESIGN,
                "emotion_curve": DetailedExecutionStage.EMOTION_CURVE,
                "scene_atmosphere": DetailedExecutionStage.SCENE_ATMOSPHERE,
            }
            type_map = {"verification": PromptTemplateType.VERIFICATION, "design": PromptTemplateType.DESIGN}
            stage = stage_map.get(metadata.get("stage"))
            template_type = type_map.get(metadata.get("template_type"))
            if not stage or not template_type:
                msg = f"無効な段階またはタイプ: {yaml_file}"
                raise ValueError(msg)
            template = A30PromptTemplate(
                stage=stage,
                template_type=template_type,
                system_prompt=prompts.get("system_prompt", ""),
                user_prompt_template=prompts.get("user_prompt_template", ""),
                expected_output_format=prompts.get("expected_output_format", ""),
                quality_criteria=quality_criteria,
                a30_step_references=metadata.get("a30_step_references", []),
            )
            template_id = metadata.get("template_id")
            if template_id:
                cls._templates[template_id] = template
                console.print(f"外部テンプレート読み込み成功: {template_id}")
            else:
                console.print(f"警告: template_idが設定されていません: {yaml_file}")
        except Exception as e:
            msg = f"YAMLテンプレート読み込みエラー {yaml_file}: {e}"
            raise Exception(msg)

    @classmethod
    def _register_logic_verification_templates(cls) -> None:
        """論理検証段階のテンプレート登録（A30 STEP 5対応）"""
        cls._templates["logic_verification_verification"] = A30PromptTemplate(
            stage=DetailedExecutionStage.LOGIC_VERIFICATION,
            template_type=PromptTemplateType.VERIFICATION,
            system_prompt="あなたはA30執筆プロンプトのSTEP 5「論理検証」の専門家です。\n\n【役割】\nプロットの因果関係、キャラクター動機、設定の整合性を詳細に検証し、\n論理的な矛盾や不自然な展開を特定・修正提案する。\n\n【検証基準】\n1. 因果関係の明確性（原因→結果の論理的つながり）\n2. キャラクター動機の合理性（行動の動機が明確で一貫している）\n3. 設定の整合性（世界観・ルールに矛盾がない）\n4. 展開の自然性（読者が納得できる流れ）",
            user_prompt_template="以下のプロット情報に基づいて、論理検証を実行してください。\n\n=== 検証対象プロット ===\n{plot_content}\n\n=== キャラクター設定 ===\n{character_settings}\n\n=== 世界観設定 ===\n{world_settings}\n\n【検証要求】\n1. 因果関係チェック: イベント間の論理的つながりを検証\n2. 動機分析: 各キャラクターの行動動機を検証\n3. 設定整合性: 世界観との矛盾を検出\n4. 論理的問題点: 発見した問題の重要度評価\n5. 修正提案: 具体的な改善案を提示\n\n必ず以下の形式で回答してください：\n{expected_output_format}",
            expected_output_format='```yaml\nlogic_verification_result:\n  causality_analysis:\n    - event: "発生イベント"\n      cause: "原因"\n      effect: "結果"\n      logical_connection: true/false\n      issues: ["問題点"]\n\n  motivation_analysis:\n    character_name:\n      actions: ["行動リスト"]\n      motivations: ["動機リスト"]\n      consistency_score: 0.0-1.0\n      issues: ["問題点"]\n\n  setting_consistency:\n    world_rule_violations: ["違反項目"]\n    character_contradictions: ["矛盾項目"]\n    timeline_issues: ["時系列問題"]\n\n  critical_issues:\n    - issue_id: "LOGIC_001"\n      severity: "high/medium/low"\n      description: "問題説明"\n      suggested_fix: "修正提案"\n\n  overall_score: 0.0-1.0\n```',
            quality_criteria=[
                "因果関係の論理性：各イベント間に明確な因果関係が存在する",
                "動機の合理性：キャラクター行動に納得できる動機が存在する",
                "設定の一貫性：世界観・ルールに矛盾が存在しない",
                "展開の自然性：読者が納得できる自然な流れが維持されている",
            ],
            a30_step_references=[5],
        )

    @classmethod
    def _register_character_consistency_templates(cls) -> None:
        """キャラクター一貫性段階のテンプレート登録（A30 STEP 6対応）"""
        cls._templates["character_consistency_verification"] = A30PromptTemplate(
            stage=DetailedExecutionStage.CHARACTER_CONSISTENCY,
            template_type=PromptTemplateType.VERIFICATION,
            system_prompt="あなたはA30執筆プロンプトのSTEP 6「キャラクター一貫性検証」の専門家です。\n\n【役割】\nキャラクターの性格・行動パターン・成長弧の一貫性を検証し、\nキャラクター破綻や不自然な変化を特定・修正提案する。\n\n【検証観点】\n1. 性格の一貫性（基本性格が場面で変わりすぎていないか）\n2. 行動パターン（そのキャラらしい行動選択をしているか）\n3. 成長弧の論理性（キャラクター成長が自然な流れか）\n4. 関係性の整合性（他キャラとの関係変化が適切か）",
            user_prompt_template="以下の情報に基づいて、キャラクター一貫性検証を実行してください。\n\n=== プロット内容 ===\n{plot_content}\n\n=== キャラクター設定 ===\n{character_settings}\n\n=== キャラクター成長履歴 ===\n{character_growth_history}\n\n【検証要求】\n1. 性格一貫性: 基本性格の維持度を評価\n2. 行動パターン: キャラらしさの維持度を評価\n3. 成長弧分析: 成長変化の自然性を評価\n4. 関係性変化: 他キャラとの関係性推移を検証\n5. 問題特定: 一貫性違反の具体的指摘\n6. 修正提案: キャラクター改善の具体案\n\n必ず以下の形式で回答してください：\n{expected_output_format}",
            expected_output_format='```yaml\ncharacter_consistency_result:\n  character_analysis:\n    character_name:\n      personality_consistency:\n        core_traits: ["基本特性"]\n        consistency_score: 0.0-1.0\n        violations: ["違反事例"]\n\n      behavioral_patterns:\n        expected_behaviors: ["期待行動"]\n        actual_behaviors: ["実際の行動"]\n        pattern_match_score: 0.0-1.0\n\n      growth_arc:\n        starting_state: "初期状態"\n        key_changes: ["重要な変化"]\n        ending_state: "最終状態"\n        growth_naturalness: 0.0-1.0\n\n  relationship_analysis:\n    - relationship: "キャラA-キャラB"\n      initial_dynamic: "初期関係"\n      final_dynamic: "最終関係"\n      change_justification: "変化の妥当性"\n      consistency_issues: ["問題点"]\n\n  critical_issues:\n    - character: "対象キャラ"\n      issue_type: "personality/behavior/growth/relationship"\n      description: "問題説明"\n      suggested_fix: "修正提案"\n\n  overall_consistency_score: 0.0-1.0\n```',
            quality_criteria=[
                "性格の一貫性：基本性格が一貫して表現されている",
                "行動の妥当性：キャラクター設定に沿った行動選択をしている",
                "成長の自然性：キャラクター成長が段階的で説得力がある",
                "関係性の整合性：他キャラクターとの関係変化が適切である",
            ],
            a30_step_references=[6],
        )

    @classmethod
    def _register_dialogue_design_templates(cls) -> None:
        """会話設計段階のテンプレート登録（A30 STEP 7対応）"""
        cls._templates["dialogue_design_design"] = A30PromptTemplate(
            stage=DetailedExecutionStage.DIALOGUE_DESIGN,
            template_type=PromptTemplateType.DESIGN,
            system_prompt="あなたはA30執筆プロンプトのSTEP 7「会話設計」の専門家です。\n\n【役割】\n目的駆動の台詞設計とキャラクター個性強化を通じて、\n自然で魅力的な会話を創出する。\n\n【設計原則】\n1. 目的明確性（各台詞が明確な目的を持つ）\n2. キャラクター個性（話し方・語彙選択でキャラを表現）\n3. 会話の自然性（リアルで違和感のない流れ）\n4. 情報伝達（必要な情報を効果的に伝達）",
            user_prompt_template="以下の情報に基づいて、会話設計を実行してください。\n\n=== シーン設定 ===\n{scene_setting}\n\n=== 参加キャラクター ===\n{participating_characters}\n\n=== 会話の目的 ===\n{dialogue_purpose}\n\n=== 伝達必要情報 ===\n{required_information}\n\n【設計要求】\n1. 台詞の目的設定: 各発言の目的を明確化\n2. キャラクター個性表現: 話し方・語彙でキャラを差別化\n3. 自然な会話流れ: リアルな対話の構築\n4. 情報伝達最適化: 必要情報の効果的な組み込み\n5. 感情表現: 台詞を通じた感情の表現\n\n必ず以下の形式で回答してください：\n{expected_output_format}",
            expected_output_format='```yaml\ndialogue_design_result:\n  conversation_structure:\n    - speaker: "話者名"\n      line: "台詞内容"\n      purpose: "発言目的"\n      character_voice_elements: ["個性要素"]\n      emotional_subtext: "感情的潜在意味"\n      information_conveyed: "伝達情報"\n\n  character_voice_analysis:\n    character_name:\n      speaking_style: "話し方の特徴"\n      vocabulary_level: "語彙レベル"\n      speech_patterns: ["話癖・口調"]\n      emotional_expression: "感情表現方法"\n\n  dialogue_quality_metrics:\n    naturalness_score: 0.0-1.0\n    character_distinctiveness: 0.0-1.0\n    purpose_clarity: 0.0-1.0\n    information_efficiency: 0.0-1.0\n\n  improvement_suggestions:\n    - aspect: "改善観点"\n      current_issue: "現在の問題"\n      suggested_change: "改善提案"\n```',
            quality_criteria=[
                "目的の明確性：各台詞が明確な目的を持っている",
                "キャラクター個性：話し方でキャラクターを差別化できている",
                "会話の自然性：リアルで違和感のない対話が構築されている",
                "情報効率：必要情報が効果的に伝達されている",
            ],
            a30_step_references=[7],
        )

    @classmethod
    def _register_emotion_curve_templates(cls) -> None:
        """感情曲線段階のテンプレート登録（A30 STEP 8対応）"""
        cls._templates["emotion_curve_design"] = A30PromptTemplate(
            stage=DetailedExecutionStage.EMOTION_CURVE,
            template_type=PromptTemplateType.DESIGN,
            system_prompt="あなたはA30執筆プロンプトのSTEP 8「感情曲線」の専門家です。\n\n【役割】\n内面感情の起伏と表現バリエーションを強化し、\n読者の感情移入を深める感情設計を行う。\n\n【設計要素】\n1. 感情の変遷（起点→変化→頂点→解決の流れ）\n2. 内面表現（思考・心理描写の詳細化）\n3. 外面表現（行動・表情による感情表現）\n4. 読者共感（読者が感情移入しやすい表現）",
            user_prompt_template="以下の情報に基づいて、感情曲線設計を実行してください。\n\n=== シーン構成 ===\n{scene_structure}\n\n=== 主要キャラクター ===\n{main_characters}\n\n=== 感情的転換点 ===\n{emotional_turning_points}\n\n【設計要求】\n1. 感情アーク設計: 感情の起伏を効果的に配置\n2. 内面表現強化: 思考・心理描写の詳細化\n3. 外面表現設計: 行動・表情による感情表現\n4. バリエーション拡充: 多様な感情表現手法\n5. 読者共感最適化: 感情移入を促進する表現\n\n必ず以下の形式で回答してください：\n{expected_output_format}",
            expected_output_format='```yaml\nemotion_curve_result:\n  emotional_arc:\n    - scene_point: "シーン位置"\n      character: "対象キャラ"\n      emotion_type: "感情種別"\n      intensity: 0.0-1.0\n      trigger: "感情の引き金"\n      expression_method: "表現方法"\n\n  internal_expression:\n    character_name:\n      thought_patterns: ["思考パターン"]\n      psychological_descriptions: ["心理描写"]\n      internal_conflicts: ["内面葛藤"]\n\n  external_expression:\n    character_name:\n      behavioral_cues: ["行動による表現"]\n      facial_expressions: ["表情表現"]\n      body_language: ["身体言語"]\n\n  expression_variations:\n    emotion_type:\n      - expression_technique: "表現技法"\n        description: "詳細説明"\n        example: "使用例"\n\n  reader_engagement:\n    empathy_triggers: ["共感誘発要素"]\n    emotional_hooks: ["感情的引っかかり"]\n    resonance_points: ["読者との共鳴点"]\n\n  quality_assessment:\n    emotional_depth: 0.0-1.0\n    expression_variety: 0.0-1.0\n    reader_connection: 0.0-1.0\n```',
            quality_criteria=[
                "感情の起伏：適切な感情アークが設計されている",
                "表現の多様性：内面・外面の多彩な感情表現がある",
                "読者共感：読者が感情移入しやすい表現が使われている",
                "自然性：感情変化が自然で説得力がある",
            ],
            a30_step_references=[8],
        )

    @classmethod
    def _register_scene_atmosphere_templates(cls) -> None:
        """情景・世界観段階のテンプレート登録（A30 STEP 9対応）"""
        cls._templates["scene_atmosphere_design"] = A30PromptTemplate(
            stage=DetailedExecutionStage.SCENE_ATMOSPHERE,
            template_type=PromptTemplateType.DESIGN,
            system_prompt="あなたはA30執筆プロンプトのSTEP 9「情景・五感・世界観」の専門家です。\n\n【役割】\n情景描写・五感表現・世界観の段階開示計画を通じて、\n没入感の高いシーン構築を行う。\n\n【設計要素】\n1. 情景構成（視覚・空間・時間の設定）\n2. 五感活用（視覚・聴覚・触覚・嗅覚・味覚の組み込み）\n3. 世界観開示（設定の効果的な提示）\n4. 雰囲気作り（シーンの気分・トーンの構築）",
            user_prompt_template="以下の情報に基づいて、情景・世界観設計を実行してください。\n\n=== シーン基本設定 ===\n{scene_basic_setting}\n\n=== 世界観詳細 ===\n{world_details}\n\n=== 雰囲気要求 ===\n{atmosphere_requirements}\n\n【設計要求】\n1. 情景構築: 視覚的・空間的なシーン設計\n2. 五感統合: 多感覚による没入感創出\n3. 世界観開示: 設定情報の効果的な織り込み\n4. 雰囲気制御: 目的に応じたトーン設定\n5. 段階開示計画: 情報提示のタイミング設計\n\n必ず以下の形式で回答してください：\n{expected_output_format}",
            expected_output_format='```yaml\nscene_atmosphere_result:\n  visual_composition:\n    setting_description: "場所・時間設定"\n    key_visual_elements: ["重要視覚要素"]\n    color_palette: ["色彩設計"]\n    lighting_conditions: "照明・光の状態"\n\n  sensory_integration:\n    visual: ["視覚的表現要素"]\n    auditory: ["聴覚的表現要素"]\n    tactile: ["触覚的表現要素"]\n    olfactory: ["嗅覚的表現要素"]\n    gustatory: ["味覚的表現要素"]\n\n  world_building_disclosure:\n    - information_type: "情報種別"\n      content: "開示内容"\n      disclosure_method: "提示方法"\n      timing: "提示タイミング"\n      purpose: "開示目的"\n\n  atmosphere_design:\n    target_mood: "目標雰囲気"\n    tone_elements: ["雰囲気構成要素"]\n    emotional_impact: "感情的効果"\n    reader_immersion_techniques: ["没入手法"]\n\n  progressive_revelation:\n    - revelation_stage: "段階番号"\n      world_element: "世界観要素"\n      reveal_trigger: "開示きっかけ"\n      reader_impact: "読者への影響"\n\n  quality_metrics:\n    immersion_level: 0.0-1.0\n    sensory_richness: 0.0-1.0\n    world_coherence: 0.0-1.0\n    atmospheric_effectiveness: 0.0-1.0\n```',
            quality_criteria=[
                "情景の鮮明性：読者が情景を明確にイメージできる",
                "五感の活用：多感覚による豊かな表現がある",
                "世界観の一貫性：設定が矛盾なく提示されている",
                "雰囲気の統一性：目的に適したトーンが維持されている",
            ],
            a30_step_references=[9],
        )


A30PromptTemplateRegistry.register_templates()
