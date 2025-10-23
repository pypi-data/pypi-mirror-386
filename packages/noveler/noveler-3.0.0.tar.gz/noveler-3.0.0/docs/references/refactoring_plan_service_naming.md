# サービス命名リファクタリング計画

## 背景
LLMセマンティック検索での発見性向上のため、サービス名を機能ベースの明確な命名に変更する。

## 原則
1. **What（何を）** を明確にする - `Manuscript`, `Novel`, `Writing`など
2. **Action（どうする）** を具体的に - `Generation`, `Validation`, `Evaluation`など
3. **略称・番号を避ける** - `A31` → `ManuscriptChecklist`
4. **技術名より役割** - `ClaudeCode` → `AIWritingAssistant`

## リファクタリング対象

### Phase 1: コア執筆サービス（優先度：高）
```python
# 変更前 → 変更後
FiveStageExecutionService → ManuscriptGenerationService
IndependentSessionExecutor → StageBasedWritingExecutor
ContentValidationService → ManuscriptQualityValidationService
```

### Phase 2: A31関連サービス（優先度：中）
```python
# 変更前 → 変更後
A31EvaluationService → ManuscriptChecklistEvaluationService
A31AutoFixService → ManuscriptAutoCorrectService
A31PriorityExtractorService → ChecklistPriorityAnalyzerService
A31ResultIntegrator → ChecklistResultIntegrationService
```

### Phase 3: 分析・支援サービス（優先度：中）
```python
# 変更前 → 変更後
ClaudeCodeIntegrationService → AIWritingAssistantService
DetailedAnalysisEngine → ManuscriptDetailedAnalyzer
SmartAutoEnhancementService → IntelligentManuscriptEnhancer
InSessionClaudeAnalyzer → InteractiveAIAnalyzer
```

### Phase 4: プロット・設定サービス（優先度：低）
```python
# 変更前 → 変更後
EnhancedPlotGenerationService → NovelPlotGeneratorService
ChapterStructureService → NovelChapterOrganizer（現状でも良い）
CharacterDevelopmentService → CharacterProgressionTracker（現状でも良い）
EpisodeTitleService → EpisodeTitleGenerator
```

## 実装手順

### Step 1: エイリアス作成（互換性維持）
```python
# src/noveler/infrastructure/services/__init__.py
from .manuscript_generation_service import ManuscriptGenerationService

# 後方互換性のためのエイリアス
FiveStageExecutionService = ManuscriptGenerationService
```

### Step 2: 新ファイル作成
1. 新しい名前でファイルをコピー
2. クラス名を変更
3. docstringを更新

### Step 3: 段階的移行
1. 新規コードは新名称を使用
2. テストを更新
3. 既存コードを段階的に更新

### Step 4: 旧名称の廃止
1. deprecation warning追加
2. 3ヶ月後に旧名称削除

## 期待効果
1. **検索性向上**: `manuscript generation`で検索可能（ManuscriptGenerationService）
2. **理解容易性**: 名前から機能が推測可能
3. **保守性向上**: 新規開発者の学習コスト削減
4. **AI親和性**: LLMが機能を正確に理解

## リスクと対策
- **リスク**: 既存コードの破壊
- **対策**: エイリアスによる互換性維持

## タイムライン
- Week 1: Phase 1実装
- Week 2: Phase 2実装
- Week 3: Phase 3実装
- Week 4: Phase 4実装・テスト
