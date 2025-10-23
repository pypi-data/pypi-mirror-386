# SPEC-WRITE-001A: 10段階執筆アルゴリズム詳細仕様書

## 要件トレーサビリティ

**要件ID**: REQ-WRITE-001〜043 (AI協創執筆機能群)
**主要要件**:
- REQ-WRITE-001: 基本執筆フロー実装
- REQ-WRITE-012: キャラクター心理状態の詳細分析と対話設計
- REQ-WRITE-025: 感情・関係性設計（段階5）
- REQ-WRITE-037: 品質改善段階（段階9）

**実装状況**: ✅実装済み（基盤）／🔄アルゴリズム詳細化中
**関連仕様書**: SPEC-WRITE-INTERACTIVE-001-v2.md

## 概要

10段階構造化執筆システムの各段階における具体的なアルゴリズム・処理ロジックを詳細定義する。Claude Code連携での段階的原稿生成において、各段階が実行すべき処理内容と品質基準を明確にする。

## 1. 全体アーキテクチャ

### 1.1 10段階システム構成
```python
class TenStageWritingSystem:
    """10段階執筆システムの中核エンジン"""

    stages = [
        # 準備段階（1-3）
        Stage1PlotDataPreparation,      # プロットデータ準備
        Stage2PlotStructureAnalysis,    # プロット構造分析
        Stage3EmotionalFlowDesign,      # 感情・関係性設計

        # 設計段階（4-6）
        Stage4HumorElementsDesign,      # ユーモア・魅力要素設計
        Stage5CharacterDialogueDesign,  # キャラクター心理・対話設計
        Stage6SceneAtmosphereDesign,    # 場面演出・雰囲気設計

        # 調整段階（7-8）
        Stage7LogicConsistencyAdjust,   # 論理整合性調整
        Stage8ManuscriptDraftGenerate,  # 原稿執筆段階

        # 仕上げ段階（9-10）
        Stage9QualityRefinement,        # 品質改善段階
        Stage10FinalAdjustment,         # 最終調整段階
    ]
```

### 1.2 段階間データフロー
```yaml
stage_data_flow:
  input: PlotData (プロット情報)
  stage1_output: PreparedPlotData
  stage2_output: StructureAnalysisResult
  stage3_output: EmotionalFlowDesign
  stage4_output: HumorElementsDesign
  stage5_output: CharacterDialogueDesign
  stage6_output: SceneAtmosphereDesign
  stage7_output: LogicConsistencyResult
  stage8_output: DraftManuscript
  stage9_output: QualityRefinedManuscript
  stage10_output: FinalManuscript
```

## 2. 各段階詳細アルゴリズム

### Stage 1: プロットデータ準備段階

#### 2.1.1 処理概要
```python
class Stage1PlotDataPreparation:
    """プロットデータの構造化と前処理"""

    def execute(self, plot_input: str) -> PreparedPlotData:
        """
        段階1実行メイン処理

        Args:
            plot_input: 生プロット文字列

        Returns:
            PreparedPlotData: 構造化されたプロットデータ
        """
        # 1. プロット解析
        parsed_plot = self.parse_plot_structure(plot_input)

        # 2. キャラクター情報抽出
        characters = self.extract_characters(parsed_plot)

        # 3. 場面・シーン分析
        scenes = self.analyze_scenes(parsed_plot)

        # 4. 核心要素特定
        core_elements = self.identify_core_elements(parsed_plot)

        return PreparedPlotData(
            parsed_structure=parsed_plot,
            characters=characters,
            scenes=scenes,
            core_elements=core_elements
        )
```

#### 2.1.2 具体的処理アルゴリズム
```python
def parse_plot_structure(self, plot_input: str) -> ParsedPlotStructure:
    """プロット構造の解析"""
    # 起承転結の特定
    story_parts = self.identify_story_parts(plot_input)

    # キーイベントの抽出
    key_events = self.extract_key_events(plot_input)

    # 時系列整理
    timeline = self.organize_timeline(key_events)

    return ParsedPlotStructure(
        introduction=story_parts.get('起', ''),
        development=story_parts.get('承', ''),
        twist=story_parts.get('転', ''),
        conclusion=story_parts.get('結', ''),
        key_events=key_events,
        timeline=timeline
    )

def extract_characters(self, plot: ParsedPlotStructure) -> List[Character]:
    """キャラクター情報の抽出・構造化"""
    character_mentions = self.find_character_mentions(plot.full_text)

    characters = []
    for mention in character_mentions:
        character = Character(
            name=mention.name,
            role=self.determine_role(mention, plot),
            personality_traits=self.extract_traits(mention, plot),
            relationships=self.analyze_relationships(mention, character_mentions),
            story_function=self.determine_story_function(mention, plot)
        )
        characters.append(character)

    return characters

def analyze_scenes(self, plot: ParsedPlotStructure) -> List[SceneStructure]:
    """場面・シーン構造の分析"""
    scene_markers = self.identify_scene_breaks(plot.full_text)

    scenes = []
    for i, marker in enumerate(scene_markers):
        scene = SceneStructure(
            scene_id=f"scene_{i+1:03d}",
            location=self.extract_location(marker),
            time_context=self.extract_time_context(marker),
            characters_present=self.identify_present_characters(marker),
            scene_purpose=self.determine_scene_purpose(marker, plot),
            emotional_tone=self.analyze_emotional_tone(marker),
            expected_length_ratio=self.estimate_length_ratio(marker, plot)
        )
        scenes.append(scene)

    return scenes
```

### Stage 2: プロット構造分析段階

#### 2.2.1 処理概要
```python
class Stage2PlotStructureAnalysis:
    """プロット構造の深度分析と最適化"""

    def execute(self, prepared_data: PreparedPlotData) -> StructureAnalysisResult:
        """段階2実行メイン処理"""
        # 1. 起承転結バランス分析
        balance_analysis = self.analyze_story_balance(prepared_data)

        # 2. ペース配分計算
        pacing_plan = self.calculate_pacing_distribution(prepared_data)

        # 3. 緊張感曲線の設計
        tension_curve = self.design_tension_curve(prepared_data)

        # 4. 伏線配置計画
        foreshadowing_plan = self.plan_foreshadowing_placement(prepared_data)

        return StructureAnalysisResult(
            balance_analysis=balance_analysis,
            pacing_plan=pacing_plan,
            tension_curve=tension_curve,
            foreshadowing_plan=foreshadowing_plan
        )
```

#### 2.2.2 具体的アルゴリズム
```python
def analyze_story_balance(self, data: PreparedPlotData) -> StoryBalanceAnalysis:
    """起承転結のバランス分析"""
    total_estimated_length = self.estimate_total_length(data)

    # 理想的配分比率（カスタマイズ可能）
    ideal_ratios = {
        '起': 0.15,  # 15% - 導入
        '承': 0.35,  # 35% - 発展
        '転': 0.35,  # 35% - 展開・クライマックス
        '結': 0.15   # 15% - 結末
    }

    current_ratios = {}
    for part_name, part_content in data.parsed_structure.story_parts.items():
        estimated_length = self.estimate_part_length(part_content, data)
        current_ratios[part_name] = estimated_length / total_estimated_length

    # バランス評価
    balance_score = self.calculate_balance_score(current_ratios, ideal_ratios)

    return StoryBalanceAnalysis(
        current_ratios=current_ratios,
        ideal_ratios=ideal_ratios,
        balance_score=balance_score,
        adjustment_suggestions=self.generate_balance_suggestions(current_ratios, ideal_ratios)
    )

def design_tension_curve(self, data: PreparedPlotData) -> TensionCurve:
    """緊張感曲線の設計"""
    scenes = data.scenes
    tension_points = []

    for i, scene in enumerate(scenes):
        # シーンの緊張度を計算
        tension_level = self.calculate_scene_tension(scene, data)

        # 物語進行における位置（0.0〜1.0）
        story_position = i / len(scenes)

        tension_points.append(TensionPoint(
            position=story_position,
            tension_level=tension_level,
            scene_id=scene.scene_id,
            justification=self.explain_tension_level(scene, tension_level)
        ))

    # 緊張曲線の滑らかさチェック
    smoothness_score = self.evaluate_curve_smoothness(tension_points)

    return TensionCurve(
        points=tension_points,
        smoothness_score=smoothness_score,
        peak_position=self.find_peak_tension(tension_points),
        optimization_suggestions=self.suggest_tension_optimizations(tension_points)
    )
```

### Stage 3: 感情・関係性設計段階

#### 2.3.1 処理概要（REQ-WRITE-025対応）
```python
class Stage3EmotionalFlowDesign:
    """キャラクター感情と関係性の動的設計"""

    def execute(self, structure_result: StructureAnalysisResult) -> EmotionalFlowDesign:
        """段階3実行メイン処理"""
        # 1. キャラクター感情アークの設計
        emotional_arcs = self.design_character_emotional_arcs(structure_result)

        # 2. 関係性変化パターンの計画
        relationship_dynamics = self.plan_relationship_dynamics(structure_result)

        # 3. 感情的クライマックスの配置
        emotional_peaks = self.place_emotional_peaks(structure_result)

        # 4. 感情表現技法の選択
        expression_techniques = self.select_expression_techniques(structure_result)

        return EmotionalFlowDesign(
            emotional_arcs=emotional_arcs,
            relationship_dynamics=relationship_dynamics,
            emotional_peaks=emotional_peaks,
            expression_techniques=expression_techniques
        )
```

### Stage 5: キャラクター心理・対話設計段階（REQ-WRITE-012重点対応）

#### 2.5.1 処理概要
```python
class Stage5CharacterDialogueDesign:
    """キャラクター心理状態の詳細分析と対話設計"""

    def execute(self, scene_design: SceneAtmosphereDesign) -> CharacterDialogueDesign:
        """段階5実行メイン処理（REQ-WRITE-012準拠）"""
        # 1. キャラクター心理状態の多層分析
        psychological_states = self.analyze_multilayer_psychology(scene_design)

        # 2. 成長段階の追跡
        growth_tracking = self.track_character_growth(scene_design)

        # 3. 対立構造の心理的背景分析
        conflict_psychology = self.analyze_conflict_psychology(scene_design)

        # 4. 対話設計（個性・感情・成長反映）
        dialogue_design = self.design_character_dialogue(psychological_states, growth_tracking)

        return CharacterDialogueDesign(
            psychological_states=psychological_states,
            growth_tracking=growth_tracking,
            conflict_psychology=conflict_psychology,
            dialogue_design=dialogue_design
        )
```

#### 2.5.2 心理分析詳細アルゴリズム
```python
def analyze_multilayer_psychology(self, scene_design: SceneAtmosphereDesign) -> Dict[str, MultilayerPsychology]:
    """キャラクター心理の多層分析"""
    psychological_states = {}

    for character in scene_design.characters:
        # 表層感情（意識的感情）
        surface_emotions = self.identify_surface_emotions(character, scene_design)

        # 深層感情（無意識的感情・抑圧された感情）
        deep_emotions = self.identify_deep_emotions(character, scene_design)

        # 防御機制の分析
        defense_mechanisms = self.analyze_defense_mechanisms(character, scene_design)

        # 価値観・信念システム
        belief_system = self.analyze_belief_system(character, scene_design)

        # 内的対立・葛藤
        internal_conflicts = self.identify_internal_conflicts(character, scene_design)

        psychological_states[character.name] = MultilayerPsychology(
            surface_emotions=surface_emotions,
            deep_emotions=deep_emotions,
            defense_mechanisms=defense_mechanisms,
            belief_system=belief_system,
            internal_conflicts=internal_conflicts,
            integration_score=self.calculate_psychology_integration(surface_emotions, deep_emotions, internal_conflicts)
        )

    return psychological_states

def design_character_dialogue(self, psychological_states: Dict[str, MultilayerPsychology], growth_tracking: Dict[str, GrowthStage]) -> DialogueDesign:
    """心理状態・成長段階を反映した対話設計"""
    dialogue_elements = {}

    for character_name, psychology in psychological_states.items():
        growth_stage = growth_tracking[character_name]

        # 口調パターン（心理状態による変化）
        speech_patterns = self.generate_speech_patterns(psychology, growth_stage)

        # 対話の深度レベル（表面的〜深層的）
        dialogue_depth_levels = self.calculate_dialogue_depth(psychology)

        # 感情表現スタイル
        emotional_expression_style = self.determine_emotional_expression(psychology, growth_stage)

        # 対話の個性化要素
        individuality_markers = self.generate_individuality_markers(psychology, growth_stage)

        dialogue_elements[character_name] = DialogueElements(
            speech_patterns=speech_patterns,
            depth_levels=dialogue_depth_levels,
            emotional_expression=emotional_expression_style,
            individuality_markers=individuality_markers
        )

    return DialogueDesign(
        dialogue_elements=dialogue_elements,
        interaction_dynamics=self.design_interaction_dynamics(dialogue_elements),
        conflict_expression_patterns=self.design_conflict_expressions(dialogue_elements, psychological_states)
    )
```

### Stage 8: 原稿執筆段階

#### 2.8.1 処理概要
```python
class Stage8ManuscriptDraftGenerate:
    """全設計要素を統合した原稿生成"""

    def execute(self, logic_result: LogicConsistencyResult) -> DraftManuscript:
        """段階8実行メイン処理"""
        # 1. 統合設計データの最終チェック
        integrated_design = self.integrate_all_design_elements(logic_result)

        # 2. シーン別原稿生成
        scene_manuscripts = self.generate_scene_manuscripts(integrated_design)

        # 3. 全体統合・接続処理
        full_manuscript = self.integrate_scenes(scene_manuscripts)

        # 4. 初期品質チェック
        quality_assessment = self.assess_initial_quality(full_manuscript)

        return DraftManuscript(
            full_text=full_manuscript,
            scene_breakdown=scene_manuscripts,
            quality_assessment=quality_assessment,
            improvement_suggestions=self.generate_improvement_suggestions(quality_assessment)
        )
```

### Stage 9: 品質改善段階（REQ-WRITE-037対応）

#### 2.9.1 処理概要
```python
class Stage9QualityRefinement:
    """多角的品質改善処理"""

    def execute(self, draft: DraftManuscript) -> QualityRefinedManuscript:
        """段階9実行メイン処理"""
        # 1. 五感描写の強化
        sensory_enhanced = self.enhance_sensory_descriptions(draft)

        # 2. 感情表現の深化
        emotion_deepened = self.deepen_emotional_expressions(sensory_enhanced)

        # 3. 文章リズムの調整
        rhythm_adjusted = self.adjust_sentence_rhythm(emotion_deepened)

        # 4. A31チェックリスト準拠の改善
        a31_compliant = self.apply_a31_improvements(rhythm_adjusted)

        return QualityRefinedManuscript(
            refined_text=a31_compliant,
            improvement_log=self.generate_improvement_log(),
            quality_score_before=draft.quality_assessment.overall_score,
            quality_score_after=self.assess_refined_quality(a31_compliant)
        )
```

### Stage 10: 最終調整段階

#### 2.10.1 処理概要
```python
class Stage10FinalAdjustment:
    """最終調整・完成処理"""

    def execute(self, refined: QualityRefinedManuscript) -> FinalManuscript:
        """段階10実行メイン処理"""
        # 1. ラストシーン演出の強化
        enhanced_ending = self.enhance_ending_scene(refined)

        # 2. 成長描写の深化
        growth_deepened = self.deepen_character_growth_depiction(enhanced_ending)

        # 3. 全体統一性の最終チェック
        consistency_checked = self.final_consistency_check(growth_deepened)

        # 4. 読後感の最適化
        optimized_impression = self.optimize_reading_impression(consistency_checked)

        return FinalManuscript(
            final_text=optimized_impression,
            completion_status=CompletionStatus.COMPLETE,
            final_quality_score=self.calculate_final_quality_score(optimized_impression),
            completion_report=self.generate_completion_report()
        )
```

## 3. 品質保証・評価システム

### 3.1 段階別品質基準
```yaml
quality_standards:
  stage_1_to_3:  # 準備段階
    completeness_threshold: 95%
    data_integrity_score: 90%

  stage_4_to_6:  # 設計段階
    design_coherence_score: 85%
    character_consistency_score: 90%

  stage_7_to_8:  # 調整・執筆段階
    logic_consistency_score: 95%
    narrative_flow_score: 80%

  stage_9_to_10: # 仕上げ段階
    a31_compliance_score: 75%
    reading_experience_score: 85%
    final_quality_threshold: 80%
```

### 3.2 エラーハンドリング・復旧戦略
```python
class StageExecutionController:
    """段階実行制御・エラー復旧"""

    def execute_stage_with_recovery(self, stage: int, input_data: Any) -> StageResult:
        """段階実行（エラー復旧付き）"""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                result = self.execute_stage(stage, input_data)

                if self.validate_stage_result(result):
                    return result
                else:
                    # 品質基準未達の場合の再実行戦略
                    input_data = self.adjust_input_for_retry(input_data, result)

            except Exception as e:
                if attempt == max_retries - 1:
                    # 最終試行失敗時のフォールバック
                    return self.execute_fallback_strategy(stage, input_data, e)
                else:
                    # リトライ前の調整
                    input_data = self.adjust_input_for_error_recovery(input_data, e)

        return self.generate_error_result(stage, input_data)
```

## 4. 実装クラス設計

### 4.1 核心インターフェース
```python
from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic

T = TypeVar('T')
U = TypeVar('U')

class StageProcessor(ABC, Generic[T, U]):
    """段階処理の基底インターフェース"""

    @abstractmethod
    def execute(self, input_data: T) -> U:
        """段階固有の処理実行"""
        pass

    @abstractmethod
    def validate_input(self, input_data: T) -> bool:
        """入力データの妥当性検証"""
        pass

    @abstractmethod
    def validate_output(self, output_data: U) -> bool:
        """出力データの品質検証"""
        pass

class TenStageOrchestrator:
    """10段階システム全体の統制"""

    def __init__(self):
        self.stages = self._initialize_stages()
        self.quality_controller = QualityController()
        self.error_recovery = StageExecutionController()

    def execute_full_writing_process(self, plot_input: str) -> FinalManuscript:
        """10段階フル実行"""
        current_data = plot_input

        for stage_num, stage_processor in enumerate(self.stages, 1):
            stage_result = self.error_recovery.execute_stage_with_recovery(
                stage_num, current_data
            )

            if not stage_result.success:
                return self._handle_stage_failure(stage_num, stage_result)

            current_data = stage_result.output_data

        return current_data  # FinalManuscript
```

## 5. テスト仕様

### 5.1 段階別ユニットテスト
```python
class TestStage5CharacterDialogueDesign:
    """段階5アルゴリズムの詳細テスト"""

    def test_multilayer_psychology_analysis(self):
        """多層心理分析の正確性テスト"""
        # テストデータ準備
        test_scene_design = self._create_test_scene_design()
        stage5 = Stage5CharacterDialogueDesign()

        # 実行
        result = stage5.analyze_multilayer_psychology(test_scene_design)

        # 検証
        assert len(result) == len(test_scene_design.characters)
        for char_name, psychology in result.items():
            assert psychology.surface_emotions is not None
            assert psychology.deep_emotions is not None
            assert 0 <= psychology.integration_score <= 100

    def test_character_growth_tracking(self):
        """キャラクター成長追跡の精度テスト"""
        # REQ-WRITE-012の成長段階追跡機能テスト
        pass

    def test_dialogue_design_individuality(self):
        """対話設計の個性化テスト"""
        # キャラクター別対話パターンの差別化テスト
        pass
```

### 5.2 統合テスト
```python
class TestTenStageIntegration:
    """10段階システム統合テスト"""

    def test_full_stage_execution_flow(self):
        """1〜10段階の完全実行フローテスト"""
        test_plot = self._load_test_plot()
        orchestrator = TenStageOrchestrator()

        result = orchestrator.execute_full_writing_process(test_plot)

        assert isinstance(result, FinalManuscript)
        assert result.final_quality_score >= 80.0
        assert len(result.final_text) >= 4000  # 最小文字数

    def test_error_recovery_mechanisms(self):
        """エラー復旧機構テスト"""
        # 各段階でのエラー復旧テスト
        pass
```

## 6. パフォーマンス要件

### 6.1 実行時間制限
```yaml
performance_requirements:
  stage_1_to_3: 30秒以内
  stage_4_to_6: 60秒以内
  stage_7: 45秒以内
  stage_8: 180秒以内  # 原稿生成は最も時間を要する
  stage_9: 120秒以内
  stage_10: 60秒以内
  total_execution_time: 600秒以内（10分以内）
```

### 6.2 メモリ使用量制限
```yaml
memory_limits:
  maximum_heap_size: 2GB
  stage_data_retention: 前段階のみ保持（メモリ効率化）
  cache_size_limit: 500MB
```

## 7. 設定・カスタマイズ

### 7.1 アルゴリズム調整パラメータ
```yaml
algorithm_parameters:
  # 段階1: プロット解析感度
  plot_parsing_sensitivity: 0.8

  # 段階2: 構造バランス重視度
  structure_balance_weight: 0.7

  # 段階5: 心理分析深度
  psychology_analysis_depth: 0.85

  # 段階8: 原稿生成詳細度
  manuscript_detail_level: 0.9

  # 段階9: 品質改善強度
  quality_improvement_intensity: 0.8
```

## 8. 成功基準

1. **機能要件充足**: REQ-WRITE-001〜043の全要件を満たすアルゴリズム実装
2. **品質基準達成**: A31チェックリスト68項目で75%以上のスコア
3. **パフォーマンス基準**: 10分以内でのフル実行完了
4. **安定性基準**: エラー復旧機構による99%以上の成功率
5. **拡張性基準**: 新段階・新アルゴリズムの容易な追加可能性

## 9. 実装優先順位

### Phase 1: 中核段階実装（優先度：最高）
1. Stage 5: キャラクター心理・対話設計（REQ-WRITE-012対応）
2. Stage 8: 原稿執筆段階
3. Stage 9: 品質改善段階

### Phase 2: 基盤段階実装（優先度：高）
4. Stage 1-3: 準備段階群
5. Stage 6-7: 調整段階群
6. Stage 10: 最終調整段階

### Phase 3: 統合・最適化（優先度：中）
7. TenStageOrchestrator実装
8. エラー復旧機構完成
9. パフォーマンス最適化

**推定実装工数**: Phase 1（7-10日）、Phase 2（5-7日）、Phase 3（3-5日）、合計15-22日
