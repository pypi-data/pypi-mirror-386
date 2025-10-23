# SPEC-GENERAL-017: 初期評価ユースケース仕様書

## 概要
`InitialAssessmentUseCase`は、新規または既存の小説プロジェクトの初期評価を行うユースケースです。プロジェクト構造の分析、既存コンテンツの評価、品質ベースラインの設定、改善提案の生成を包括的に実施し、プロジェクトの現状把握と最適な開始地点の設定を支援します。

## クラス設計

### InitialAssessmentUseCase

**責務**
- プロジェクト構造の包括的分析
- 既存コンテンツの品質評価
- 執筆者レベルの判定
- ベースライン設定
- カスタマイズされた改善計画の作成
- プロジェクトリスクの特定

## データ構造

### AssessmentScope (Enum)
```python
class AssessmentScope(Enum):
    FULL = "full"                        # 完全評価
    STRUCTURE = "structure"              # 構造のみ
    CONTENT = "content"                  # コンテンツのみ
    QUALITY = "quality"                  # 品質のみ
    QUICK = "quick"                      # クイック評価
```

### ProjectMaturity (Enum)
```python
class ProjectMaturity(Enum):
    NEW = "new"                          # 新規プロジェクト
    EARLY = "early"                      # 初期段階
    DEVELOPING = "developing"            # 開発中
    MATURE = "mature"                    # 成熟
    COMPLETED = "completed"              # 完成
```

### WriterLevel (Enum)
```python
class WriterLevel(Enum):
    BEGINNER = "beginner"                # 初心者
    INTERMEDIATE = "intermediate"        # 中級者
    ADVANCED = "advanced"                # 上級者
    PROFESSIONAL = "professional"        # プロ
```

### AssessmentRequest (DataClass)
```python
@dataclass
class AssessmentRequest:
    project_name: str                    # プロジェクト名
    scope: AssessmentScope               # 評価範囲
    deep_analysis: bool = True           # 深層分析
    generate_recommendations: bool = True # 推奨事項生成
    set_baseline: bool = True            # ベースライン設定
    writer_info: dict[str, any] = {}     # 執筆者情報
```

### AssessmentResponse (DataClass)
```python
@dataclass
class AssessmentResponse:
    success: bool                        # 処理成功フラグ
    project_summary: ProjectSummary      # プロジェクトサマリー
    structure_analysis: StructureAnalysis # 構造分析結果
    content_evaluation: ContentEvaluation # コンテンツ評価
    quality_baseline: QualityBaseline    # 品質ベースライン
    writer_assessment: WriterAssessment  # 執筆者評価
    recommendations: list[Recommendation] # 推奨事項
    risk_analysis: RiskAnalysis          # リスク分析
    next_steps: list[str]                # 次のステップ
```

### ProjectSummary (DataClass)
```python
@dataclass
class ProjectSummary:
    project_name: str                    # プロジェクト名
    created_date: datetime               # 作成日
    maturity: ProjectMaturity            # 成熟度
    total_episodes: int                  # 総エピソード数
    total_words: int                     # 総文字数
    completion_rate: float               # 完成率
    genre: str                           # ジャンル
    target_audience: str                 # 対象読者
    unique_features: list[str]           # 独自の特徴
```

### StructureAnalysis (DataClass)
```python
@dataclass
class StructureAnalysis:
    directory_health: float              # ディレクトリ構造健全性
    file_organization: float             # ファイル整理度
    naming_consistency: float            # 命名一貫性
    missing_components: list[str]        # 不足コンポーネント
    structural_issues: list[str]         # 構造的問題
    optimization_opportunities: list[str] # 最適化機会
```

## パブリックメソッド

### assess_project()

**シグネチャ**
```python
def assess_project(self, request: AssessmentRequest) -> AssessmentResponse:
```

**目的**
プロジェクトの包括的な初期評価を実行する。

**引数**
- `request`: 評価リクエスト

**戻り値**
- `AssessmentResponse`: 評価結果

**処理フロー**
1. **プロジェクト検証**: プロジェクトの存在と基本情報確認
2. **構造分析**: ディレクトリとファイル構造の評価
3. **コンテンツ評価**: 既存コンテンツの品質分析
4. **執筆者分析**: スキルレベルと特性の判定
5. **ベースライン設定**: 初期品質基準の設定
6. **リスク評価**: 潜在的問題の特定
7. **推奨事項生成**: カスタマイズされた改善提案
8. **結果統合**: 包括的なレポート作成

### analyze_writing_patterns()

**シグネチャ**
```python
def analyze_writing_patterns(
    self,
    project_name: str
) -> WritingPatternAnalysis:
```

**目的**
執筆パターンを分析して執筆者の特性を把握する。

### set_quality_baseline()

**シグネチャ**
```python
def set_quality_baseline(
    self,
    project_name: str,
    writer_level: WriterLevel
) -> QualityBaseline:
```

**目的**
執筆者レベルに応じた品質ベースラインを設定する。

### generate_improvement_roadmap()

**シグネチャ**
```python
def generate_improvement_roadmap(
    self,
    assessment_result: AssessmentResponse
) -> ImprovementRoadmap:
```

**目的**
評価結果に基づいて段階的な改善ロードマップを生成する。

## プライベートメソッド

### _analyze_project_structure()

**シグネチャ**
```python
def _analyze_project_structure(
    self,
    project_path: Path
) -> StructureAnalysis:
```

**目的**
プロジェクトのディレクトリ構造を分析する。

**分析項目**
```python
structure_checks = {
    "required_directories": [
        "10_企画", "20_プロット", "30_設定集",
        "40_原稿", "50_管理資料"
    ],
    "file_patterns": {
        "manuscripts": r"第\d{3}話_.*\.md",
        "plots": r".*\.yaml",
        "settings": r".*\.yaml"
    },
    "health_indicators": {
        "empty_directories": float,
        "orphaned_files": float,
        "naming_violations": float
    }
}
```

### _evaluate_content_quality()

**シグネチャ**
```python
def _evaluate_content_quality(
    self,
    content_files: list[Path]
) -> ContentEvaluation:
```

**目的**
既存コンテンツの品質を評価する。

### _determine_writer_level()

**シグネチャ**
```python
def _determine_writer_level(
    self,
    writing_samples: list[str],
    metadata: dict[str, any]
) -> WriterLevel:
```

**目的**
執筆サンプルから執筆者のレベルを判定する。

**判定基準**
```python
level_criteria = {
    WriterLevel.BEGINNER: {
        "vocabulary_diversity": (0, 0.3),
        "sentence_complexity": (0, 0.3),
        "narrative_depth": (0, 0.3),
        "technical_errors": (0.7, 1.0)
    },
    WriterLevel.INTERMEDIATE: {
        "vocabulary_diversity": (0.3, 0.6),
        "sentence_complexity": (0.3, 0.6),
        "narrative_depth": (0.3, 0.6),
        "technical_errors": (0.3, 0.7)
    },
    WriterLevel.ADVANCED: {
        "vocabulary_diversity": (0.6, 0.8),
        "sentence_complexity": (0.6, 0.8),
        "narrative_depth": (0.6, 0.8),
        "technical_errors": (0.1, 0.3)
    }
}
```

### _identify_project_risks()

**シグネチャ**
```python
def _identify_project_risks(
    self,
    structure: StructureAnalysis,
    content: ContentEvaluation
) -> RiskAnalysis:
```

**目的**
プロジェクトの潜在的リスクを特定する。

### _create_customized_recommendations()

**シグネチャ**
```python
def _create_customized_recommendations(
    self,
    project_summary: ProjectSummary,
    writer_level: WriterLevel,
    identified_issues: list[str]
) -> list[Recommendation]:
```

**目的**
プロジェクトと執筆者に合わせた推奨事項を作成する。

## 評価基準

### 構造健全性スコア
```python
structure_score_weights = {
    "directory_completeness": 0.3,
    "file_organization": 0.2,
    "naming_consistency": 0.2,
    "metadata_presence": 0.15,
    "backup_existence": 0.15
}
```

### コンテンツ品質指標
```python
content_quality_metrics = {
    "readability": {
        "weight": 0.2,
        "factors": ["sentence_length", "vocabulary_level"]
    },
    "consistency": {
        "weight": 0.25,
        "factors": ["style_uniformity", "terminology_consistency"]
    },
    "engagement": {
        "weight": 0.25,
        "factors": ["dialogue_quality", "pacing", "hooks"]
    },
    "technical_quality": {
        "weight": 0.3,
        "factors": ["grammar", "spelling", "punctuation"]
    }
}
```

## 依存関係

### ドメインサービス
- `StructureAnalyzer`: 構造分析
- `ContentAnalyzer`: コンテンツ分析
- `WriterProfiler`: 執筆者プロファイリング
- `RiskAssessor`: リスク評価

### リポジトリ
- `ProjectRepository`: プロジェクト情報管理
- `AssessmentRepository`: 評価結果管理
- `BaselineRepository`: ベースライン管理

## 設計原則遵守

### DDD準拠
- ✅ エンティティ（`ProjectSummary`, `WriterAssessment`）の適切な使用
- ✅ 値オブジェクト（列挙型）の活用
- ✅ ドメインサービスの適切な活用
- ✅ リポジトリパターンによるデータアクセス抽象化

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的なエラーハンドリング
- ✅ 型安全な実装
- ✅ 列挙型による型安全性

## 使用例

```python
# 依存関係の準備
structure_analyzer = StructureAnalyzer()
content_analyzer = ContentAnalyzer()
writer_profiler = WriterProfiler()
risk_assessor = RiskAssessor()
project_repo = YamlProjectRepository()
assessment_repo = AssessmentRepository()
baseline_repo = BaselineRepository()

# ユースケース作成
use_case = InitialAssessmentUseCase(
    structure_analyzer=structure_analyzer,
    content_analyzer=content_analyzer,
    writer_profiler=writer_profiler,
    risk_assessor=risk_assessor,
    project_repository=project_repo,
    assessment_repository=assessment_repo,
    baseline_repository=baseline_repo
)

# 完全な初期評価の実行
assessment_request = AssessmentRequest(
    project_name="fantasy_adventure",
    scope=AssessmentScope.FULL,
    deep_analysis=True,
    generate_recommendations=True,
    set_baseline=True,
    writer_info={
        "experience_years": 2,
        "previous_works": 1,
        "genre_familiarity": "intermediate"
    }
)

response = use_case.assess_project(assessment_request)

if response.success:
    # プロジェクトサマリー表示
    summary = response.project_summary
    print(f"=== プロジェクト評価: {summary.project_name} ===")
    print(f"成熟度: {summary.maturity.value}")
    print(f"総エピソード数: {summary.total_episodes}")
    print(f"総文字数: {summary.total_words:,}文字")
    print(f"完成率: {summary.completion_rate:.1f}%")

    # 構造分析結果
    structure = response.structure_analysis
    print(f"\n=== 構造分析 ===")
    print(f"ディレクトリ健全性: {structure.directory_health:.1f}/100")
    print(f"ファイル整理度: {structure.file_organization:.1f}/100")
    print(f"命名一貫性: {structure.naming_consistency:.1f}/100")

    if structure.missing_components:
        print(f"\n不足コンポーネント:")
        for component in structure.missing_components:
            print(f"  - {component}")

    # 執筆者評価
    writer = response.writer_assessment
    print(f"\n=== 執筆者評価 ===")
    print(f"判定レベル: {writer.level.value}")
    print(f"強み: {', '.join(writer.strengths)}")
    print(f"改善点: {', '.join(writer.areas_for_improvement)}")

    # 品質ベースライン
    baseline = response.quality_baseline
    print(f"\n=== 品質ベースライン設定 ===")
    print(f"目標品質スコア: {baseline.target_score}")
    print(f"最低許容スコア: {baseline.minimum_score}")
    print(f"段階的目標:")
    for phase, target in baseline.phased_targets.items():
        print(f"  {phase}: {target}")

    # リスク分析
    risks = response.risk_analysis
    print(f"\n=== リスク分析 ===")
    print(f"全体リスクレベル: {risks.overall_risk_level}")

    if risks.high_priority_risks:
        print(f"\n高優先度リスク:")
        for risk in risks.high_priority_risks:
            print(f"  - {risk.description}")
            print(f"    影響度: {risk.impact} | 対策: {risk.mitigation}")

    # 推奨事項
    print(f"\n=== 推奨事項 ===")
    for i, rec in enumerate(response.recommendations[:5], 1):
        print(f"\n{i}. {rec.title}")
        print(f"   優先度: {rec.priority}")
        print(f"   期待効果: {rec.expected_impact}")
        print(f"   実施方法: {rec.implementation}")

    # 次のステップ
    print(f"\n=== 次のステップ ===")
    for step in response.next_steps:
        print(f"  ✓ {step}")

# 執筆パターン分析
pattern_analysis = use_case.analyze_writing_patterns("fantasy_adventure")

print(f"\n=== 執筆パターン分析 ===")
print(f"平均執筆速度: {pattern_analysis.average_speed}文字/時間")
print(f"最も生産的な時間帯: {pattern_analysis.peak_hours}")
print(f"執筆リズム: {pattern_analysis.rhythm_pattern}")
print(f"一貫性スコア: {pattern_analysis.consistency_score:.1f}")

# 改善ロードマップの生成
roadmap = use_case.generate_improvement_roadmap(response)

print(f"\n=== 改善ロードマップ ===")
for phase in roadmap.phases:
    print(f"\n{phase.name} ({phase.duration})")
    print(f"目標: {phase.goals}")
    print(f"アクション:")
    for action in phase.actions:
        print(f"  - {action.description}")
        print(f"    期限: {action.deadline}")
        print(f"    成果指標: {action.success_metrics}")

# クイック評価（既存プロジェクトの状態確認）
quick_request = AssessmentRequest(
    project_name="fantasy_adventure",
    scope=AssessmentScope.QUICK,
    deep_analysis=False,
    generate_recommendations=False,
    set_baseline=False
)

quick_response = use_case.assess_project(quick_request)

print(f"\n=== クイック評価結果 ===")
print(f"健全性スコア: {quick_response.health_score:.1f}/100")
print(f"要対応項目: {quick_response.action_items}")
print(f"推定作業時間: {quick_response.estimated_work_hours}時間")
```

## 評価レポート例

```
========================================
小説プロジェクト初期評価レポート
========================================

プロジェクト: ファンタジーアドベンチャー
評価日: 2024-01-20
評価者: InitialAssessmentSystem v1.0

【総合評価】
プロジェクト成熟度: 開発中 (60%)
執筆者レベル: 中級者
全体健全性: 75/100

【構造分析】
✅ 必須ディレクトリ: 5/5 完備
⚠️ ファイル命名: 一部不整合あり
✅ バックアップ: 定期実行確認

【コンテンツ評価】
文章品質: 72/100
- 可読性: ★★★★☆
- 一貫性: ★★★☆☆
- 魅力度: ★★★★☆
- 技術的正確性: ★★★☆☆

【執筆者プロファイル】
強み:
- 豊かな描写力
- キャラクター造形
- 対話の自然さ

改善機会:
- 文体の一貫性
- ペーシング管理
- 伏線の活用

【リスク評価】
1. 中期的な執筆速度低下の可能性 (中)
2. プロット後半の整合性課題 (高)
3. キャラクター成長曲線の不明確さ (中)

【推奨アクション】
1. 週次品質チェックの導入
2. プロット整合性レビュー
3. キャラクターアーク再定義
4. 執筆リズム最適化
5. 段階的品質向上プログラム

【次の30日間の目標】
- 品質スコア: 72 → 78
- 執筆速度: +15%
- 整合性問題: 5件解決
```

## エラーハンドリング

### プロジェクト不存在
```python
if not self.project_repository.exists(request.project_name):
    return AssessmentResponse(
        success=False,
        error_message="プロジェクトが見つかりません",
        recommendations=[
            Recommendation(
                title="新規プロジェクト作成",
                description="novel init コマンドでプロジェクトを初期化してください"
            )
        ]
    )
```

### 不完全な評価データ
```python
if len(content_files) < MIN_CONTENT_FOR_ASSESSMENT:
    logger.warning("コンテンツ不足のため限定的な評価を実行")
    return self._perform_limited_assessment(project_path)
```

## テスト観点

### 単体テスト
- 各分析ロジックの正確性
- レベル判定アルゴリズム
- リスク評価の妥当性
- 推奨事項生成

### 統合テスト
- 様々な成熟度のプロジェクト
- 異なる執筆者レベル
- 大規模プロジェクトでの性能

## 品質基準

- **包括性**: プロジェクト全体の網羅的評価
- **的確性**: 執筆者レベルの正確な判定
- **実用性**: 具体的で実行可能な推奨事項
- **カスタマイズ**: 個別状況に応じた提案
- **追跡性**: 評価結果の記録と比較可能性
