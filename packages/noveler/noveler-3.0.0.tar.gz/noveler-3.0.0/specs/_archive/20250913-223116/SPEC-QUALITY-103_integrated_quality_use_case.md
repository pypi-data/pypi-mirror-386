# SPEC-QUALITY-103: 統合品質管理ユースケース仕様書

## 概要
`IntegratedQualityUseCase`は、小説プロジェクトの品質を統合的に管理するユースケースです。複数の品質チェッカーの統合実行、品質メトリクスの一元管理、自動修正の調整、品質トレンドの分析、包括的なレポート生成を提供し、プロジェクト全体の品質向上を実現します。

## クラス設計

### IntegratedQualityUseCase

**責務**
- 複数品質チェッカーの統合管理
- 品質メトリクスの集約と分析
- 自動修正の優先順位付けと実行
- 品質トレンドの追跡
- カスタマイズ可能な品質基準の適用
- 包括的品質レポートの生成

## データ構造

### QualityDimension (Enum)
```python
class QualityDimension(Enum):
    BASIC_STYLE = "basic_style"          # 基本文体
    COMPOSITION = "composition"          # 構成
    NARRATIVE = "narrative"              # 物語性
    CHARACTER = "character"              # キャラクター
    DIALOGUE = "dialogue"                # 対話
    CONSISTENCY = "consistency"          # 一貫性
    TECHNICAL = "technical"              # 技術的正確性
```

### QualityCheckMode (Enum)
```python
class QualityCheckMode(Enum):
    FULL = "full"                        # 完全チェック
    QUICK = "quick"                      # クイックチェック
    FOCUSED = "focused"                  # 特定項目に焦点
    PROGRESSIVE = "progressive"          # 段階的チェック
    CUSTOM = "custom"                    # カスタムチェック
```

### IntegratedQualityRequest (DataClass)
```python
@dataclass
class IntegratedQualityRequest:
    project_name: str                    # プロジェクト名
    target_episodes: list[int] = []      # 対象エピソード（空=全て）
    check_mode: QualityCheckMode = QualityCheckMode.FULL
    dimensions: list[QualityDimension] = [] # チェック項目（空=全て）
    auto_fix: bool = False               # 自動修正有効
    fix_threshold: float = 0.8           # 自動修正閾値
    generate_report: bool = True         # レポート生成
    compare_baseline: bool = True        # ベースライン比較
```

### IntegratedQualityResponse (DataClass)
```python
@dataclass
class IntegratedQualityResponse:
    success: bool                        # 処理成功フラグ
    overall_score: float                 # 総合品質スコア
    dimension_scores: dict[QualityDimension, float] # 次元別スコア
    issues_found: list[QualityIssue]    # 検出された問題
    fixes_applied: list[AppliedFix]     # 適用された修正
    quality_trend: QualityTrend          # 品質トレンド
    recommendations: list[QualityRecommendation] # 改善推奨事項
    report_path: Path | None = None      # レポートファイルパス
```

### QualityIssue (DataClass)
```python
@dataclass
class QualityIssue:
    issue_id: str                        # 問題ID
    dimension: QualityDimension          # 品質次元
    severity: str                        # 重要度（low/medium/high/critical）
    episode: int                         # エピソード番号
    location: str                        # 位置情報
    description: str                     # 問題説明
    suggestion: str                      # 改善提案
    auto_fixable: bool                   # 自動修正可能
    confidence: float                    # 検出信頼度
```

### QualityProfile (DataClass)
```python
@dataclass
class QualityProfile:
    project_name: str                    # プロジェクト名
    baseline_scores: dict[QualityDimension, float] # ベースラインスコア
    target_scores: dict[QualityDimension, float]   # 目標スコア
    weight_distribution: dict[QualityDimension, float] # 重み配分
    custom_rules: list[CustomRule]       # カスタムルール
    quality_standards: str               # 品質基準（basic/standard/premium）
```

## パブリックメソッド

### check_quality()

**シグネチャ**
```python
def check_quality(
    self,
    request: IntegratedQualityRequest
) -> IntegratedQualityResponse:
```

**目的**
統合的な品質チェックを実行する。

**引数**
- `request`: 品質チェックリクエスト

**戻り値**
- `IntegratedQualityResponse`: 品質チェック結果

**処理フロー**
1. **品質プロファイル読込**: プロジェクト固有の設定
2. **チェッカー選択**: モードに応じたチェッカー選択
3. **並列実行**: 複数チェッカーの効率的実行
4. **結果集約**: 各チェッカーの結果統合
5. **スコア計算**: 重み付き総合スコア算出
6. **自動修正**: 閾値を超える問題の修正
7. **トレンド分析**: 過去データとの比較
8. **レポート生成**: 包括的レポート作成

### create_quality_profile()

**シグネチャ**
```python
def create_quality_profile(
    self,
    project_name: str,
    writer_level: str,
    genre: str
) -> QualityProfile:
```

**目的**
プロジェクト用の品質プロファイルを作成する。

### analyze_quality_trends()

**シグネチャ**
```python
def analyze_quality_trends(
    self,
    project_name: str,
    period_days: int = 30
) -> QualityTrendAnalysis:
```

**目的**
品質の経時的変化を分析する。

### apply_fixes_interactively()

**シグネチャ**
```python
def apply_fixes_interactively(
    self,
    issues: list[QualityIssue]
) -> list[AppliedFix]:
```

**目的**
品質問題を対話的に修正する。

## プライベートメソッド

### _execute_quality_checkers()

**シグネチャ**
```python
def _execute_quality_checkers(
    self,
    episodes: list[Episode],
    dimensions: list[QualityDimension]
) -> dict[QualityDimension, CheckResult]:
```

**目的**
品質チェッカーを並列実行する。

**実行戦略**
```python
checker_mapping = {
    QualityDimension.BASIC_STYLE: BasicStyleChecker,
    QualityDimension.COMPOSITION: CompositionChecker,
    QualityDimension.NARRATIVE: NarrativeChecker,
    QualityDimension.CHARACTER: CharacterChecker,
    QualityDimension.DIALOGUE: DialogueChecker,
    QualityDimension.CONSISTENCY: ConsistencyChecker,
    QualityDimension.TECHNICAL: TechnicalChecker
}
```

### _calculate_integrated_score()

**シグネチャ**
```python
def _calculate_integrated_score(
    self,
    dimension_scores: dict[QualityDimension, float],
    weights: dict[QualityDimension, float]
) -> float:
```

**目的**
重み付き総合品質スコアを計算する。

### _prioritize_issues()

**シグネチャ**
```python
def _prioritize_issues(
    self,
    issues: list[QualityIssue]
) -> list[QualityIssue]:
```

**目的**
品質問題を優先順位付けする。

**優先順位基準**
```python
priority_factors = {
    "severity_weight": 0.4,      # 重要度の重み
    "fix_difficulty": 0.2,       # 修正難易度
    "reader_impact": 0.3,        # 読者への影響
    "cumulative_effect": 0.1     # 累積効果
}
```

### _apply_auto_fixes()

**シグネチャ**
```python
def _apply_auto_fixes(
    self,
    issues: list[QualityIssue],
    threshold: float
) -> list[AppliedFix]:
```

**目的**
信頼度の高い問題を自動修正する。

### _generate_quality_report()

**シグネチャ**
```python
def _generate_quality_report(
    self,
    response: IntegratedQualityResponse,
    profile: QualityProfile
) -> Path:
```

**目的**
包括的な品質レポートを生成する。

## 品質チェック統合

### チェッカー連携
```python
checker_dependencies = {
    "character": ["dialogue", "consistency"],
    "narrative": ["composition", "basic_style"],
    "consistency": ["character", "narrative"]
}
```

### 品質メトリクス集約
```python
def _aggregate_metrics(self, checker_results: list[CheckResult]) -> dict:
    aggregated = {
        "total_issues": sum(r.issue_count for r in checker_results),
        "critical_issues": sum(r.critical_count for r in checker_results),
        "auto_fixable": sum(r.fixable_count for r in checker_results),
        "average_confidence": mean(r.confidence for r in checker_results),
        "coverage": self._calculate_coverage(checker_results)
    }
    return aggregated
```

## 依存関係

### 品質チェッカー
- `BasicStyleChecker`: 基本文体チェック
- `CompositionChecker`: 構成チェック
- `NarrativeChecker`: 物語性チェック
- `CharacterChecker`: キャラクターチェック
- `DialogueChecker`: 対話チェック
- `ConsistencyChecker`: 一貫性チェック
- `TechnicalChecker`: 技術的チェック

### ドメインサービス
- `QualityCalculator`: 品質スコア計算
- `TrendAnalyzer`: トレンド分析
- `FixPrioritizer`: 修正優先順位付け

### リポジトリ
- `QualityProfileRepository`: 品質プロファイル管理
- `QualityHistoryRepository`: 品質履歴管理
- `FixHistoryRepository`: 修正履歴管理

## 設計原則遵守

### DDD準拠
- ✅ エンティティ（`QualityProfile`, `QualityIssue`）の適切な使用
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
basic_style_checker = BasicStyleChecker()
composition_checker = CompositionChecker()
narrative_checker = NarrativeChecker()
character_checker = CharacterChecker()
dialogue_checker = DialogueChecker()
consistency_checker = ConsistencyChecker()
technical_checker = TechnicalChecker()
quality_calculator = QualityCalculator()
trend_analyzer = TrendAnalyzer()
fix_prioritizer = FixPrioritizer()
quality_profile_repo = QualityProfileRepository()
quality_history_repo = QualityHistoryRepository()
fix_history_repo = FixHistoryRepository()

# ユースケース作成
use_case = IntegratedQualityUseCase(
    checkers={
        QualityDimension.BASIC_STYLE: basic_style_checker,
        QualityDimension.COMPOSITION: composition_checker,
        QualityDimension.NARRATIVE: narrative_checker,
        QualityDimension.CHARACTER: character_checker,
        QualityDimension.DIALOGUE: dialogue_checker,
        QualityDimension.CONSISTENCY: consistency_checker,
        QualityDimension.TECHNICAL: technical_checker
    },
    quality_calculator=quality_calculator,
    trend_analyzer=trend_analyzer,
    fix_prioritizer=fix_prioritizer,
    quality_profile_repository=quality_profile_repo,
    quality_history_repository=quality_history_repo,
    fix_history_repository=fix_history_repo
)

# 完全品質チェックの実行
full_check_request = IntegratedQualityRequest(
    project_name="fantasy_adventure",
    target_episodes=[],  # 全エピソード
    check_mode=QualityCheckMode.FULL,
    auto_fix=True,
    fix_threshold=0.9,  # 90%以上の信頼度で自動修正
    generate_report=True,
    compare_baseline=True
)

response = use_case.check_quality(full_check_request)

if response.success:
    print(f"=== 統合品質チェック結果 ===")
    print(f"総合品質スコア: {response.overall_score:.1f}/100")

    # 次元別スコア表示
    print(f"\n次元別スコア:")
    for dimension, score in response.dimension_scores.items():
        trend = "↑" if score > baseline_scores.get(dimension, 0) else "↓"
        print(f"  {dimension.value}: {score:.1f} {trend}")

    # 検出された問題
    print(f"\n検出された問題: {len(response.issues_found)}件")

    # 重要度別分類
    severity_counts = {}
    for issue in response.issues_found:
        severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1

    for severity, count in severity_counts.items():
        print(f"  {severity}: {count}件")

    # 自動修正結果
    if response.fixes_applied:
        print(f"\n自動修正: {len(response.fixes_applied)}件適用")
        for fix in response.fixes_applied[:5]:  # 最初の5件
            print(f"  - {fix.issue_id}: {fix.description}")

    # 品質トレンド
    trend = response.quality_trend
    print(f"\n品質トレンド (過去30日):")
    print(f"  改善率: {trend.improvement_rate:.1f}%")
    print(f"  最高スコア: {trend.peak_score:.1f} ({trend.peak_date})")
    print(f"  安定性: {trend.stability_score:.1f}/10")

    # 推奨事項
    print(f"\n主要推奨事項:")
    for rec in response.recommendations[:3]:
        print(f"\n{rec.priority}優先度: {rec.title}")
        print(f"  影響: {rec.expected_improvement:.1f}ポイント向上")
        print(f"  実施方法: {rec.action_steps[0]}")

    # レポート生成
    if response.report_path:
        print(f"\n詳細レポート: {response.report_path}")

# 特定次元に焦点を当てたチェック
focused_request = IntegratedQualityRequest(
    project_name="fantasy_adventure",
    target_episodes=[10, 11, 12],  # 特定エピソード
    check_mode=QualityCheckMode.FOCUSED,
    dimensions=[
        QualityDimension.DIALOGUE,
        QualityDimension.CHARACTER
    ],
    auto_fix=False,  # 手動確認
    generate_report=True
)

focused_response = use_case.check_quality(focused_request)

# 対話的修正の実行
if focused_response.issues_found:
    print(f"\n=== 対話的修正 ===")
    fixable_issues = [i for i in focused_response.issues_found if i.auto_fixable]

    applied_fixes = use_case.apply_fixes_interactively(fixable_issues)

    print(f"修正完了: {len(applied_fixes)}件")

# 品質プロファイルの作成/更新
profile = use_case.create_quality_profile(
    project_name="fantasy_adventure",
    writer_level="intermediate",
    genre="fantasy"
)

print(f"\n=== 品質プロファイル ===")
print(f"品質基準: {profile.quality_standards}")
print(f"\nベースラインスコア:")
for dim, score in profile.baseline_scores.items():
    print(f"  {dim.value}: {score:.1f}")

print(f"\n目標スコア:")
for dim, score in profile.target_scores.items():
    print(f"  {dim.value}: {score:.1f}")

# 品質トレンド分析
trend_analysis = use_case.analyze_quality_trends(
    project_name="fantasy_adventure",
    period_days=90
)

print(f"\n=== 品質トレンド分析 (90日間) ===")
print(f"開始時スコア: {trend_analysis.start_score:.1f}")
print(f"現在スコア: {trend_analysis.current_score:.1f}")
print(f"改善率: {trend_analysis.improvement_rate:.1f}%")
print(f"最も改善した項目: {trend_analysis.most_improved_dimension}")
print(f"要注意項目: {trend_analysis.declining_dimensions}")

# カスタムチェックの実行
custom_request = IntegratedQualityRequest(
    project_name="fantasy_adventure",
    check_mode=QualityCheckMode.CUSTOM,
    dimensions=[],  # カスタムルールのみ使用
    custom_rules=[
        {
            "name": "chapter_hooks",
            "description": "各章の最初と最後にフックがあるか",
            "severity": "medium"
        },
        {
            "name": "character_growth",
            "description": "主要キャラの成長が描かれているか",
            "severity": "high"
        }
    ]
)

custom_response = use_case.check_quality(custom_request)
```

## 品質レポート例

```markdown
# 統合品質チェックレポート

プロジェクト: ファンタジーアドベンチャー
実行日時: 2024-01-20 14:30:00
チェック範囲: 全50エピソード

## 総合評価

**総合品質スコア: 82.5/100** ⬆️ +3.2

### 次元別スコア

| 品質次元 | スコア | 前回比 | 目標 |
|---------|-------|--------|------|
| 基本文体 | 85.0 | +2.0 | 85.0 |
| 構成 | 78.5 | +5.0 | 80.0 |
| 物語性 | 83.0 | +3.5 | 85.0 |
| キャラクター | 88.0 | +1.0 | 90.0 |
| 対話 | 79.5 | +4.0 | 80.0 |
| 一貫性 | 81.0 | +2.5 | 85.0 |
| 技術的正確性 | 82.5 | +3.0 | 80.0 |

## 主要な発見

### 🔴 重大な問題 (5件)

1. **キャラクター一貫性** - 第15話
   - 主人公の性格が前話と矛盾
   - 推奨: キャラクターシートの確認と修正

2. **プロット矛盾** - 第23話
   - タイムラインの不整合
   - 推奨: 時系列の再確認

### 🟡 中程度の問題 (23件)

- 対話タグの過剰使用 (8件)
- 描写不足のシーン (7件)
- ペーシングの問題 (8件)

### 🟢 軽微な問題 (45件)

- 句読点の不統一
- 漢字/ひらがなの揺れ
- 段落構成の改善余地

## 自動修正結果

**32件を自動修正済み**
- 対話タグの簡素化: 15件
- 文末表現の統一: 10件
- 明らかな誤字脱字: 7件

## 品質トレンド

```
品質スコア推移（過去30日）
90 |                    ╱
85 |                ╱╲╱
80 |            ╱╲╱
75 |        ╱╲╱
70 |    ╱╲╱
65 |╱╲╱
   └─────────────────────
     30日前        現在
```

## 推奨アクション

### 優先度: 高

1. **キャラクター一貫性の総点検**
   - 影響: +3.0ポイント
   - 推定時間: 4時間
   - 対象: 第15-20話

2. **対話の自然さ向上**
   - 影響: +2.5ポイント
   - 推定時間: 3時間
   - 対象: 全エピソード

### 優先度: 中

3. **描写の充実**
   - 影響: +2.0ポイント
   - 推定時間: 6時間
   - 対象: アクションシーン

## 次回チェック予定

推奨: 2週間後（修正適用後）
```

## エラーハンドリング

### チェッカー実行エラー
```python
failed_checkers = []
for dimension, checker in self.checkers.items():
    try:
        result = checker.check(episodes)
        results[dimension] = result
    except CheckerError as e:
        logger.error(f"{dimension}チェッカーエラー: {e}")
        failed_checkers.append(dimension)
        # 部分的な結果で続行
```

### 自動修正の安全性確保
```python
def _safe_auto_fix(self, issue: QualityIssue, content: str) -> str:
    try:
        # バックアップ作成
        backup = self._create_content_backup(content)

        # 修正適用
        fixed_content = self._apply_fix(issue, content)

        # 修正後の再チェック
        if self._verify_fix(fixed_content, issue):
            return fixed_content
        else:
            # ロールバック
            return backup
    except Exception as e:
        logger.error(f"自動修正エラー: {e}")
        return content  # 元のコンテンツを返す
```

## テスト観点

### 単体テスト
- 各チェッカーの統合
- スコア計算ロジック
- 優先順位付けアルゴリズム
- 自動修正の精度

### 統合テスト
- 大規模プロジェクトでの性能
- 並列実行の正確性
- レポート生成
- トレンド分析の精度

## 品質基準

- **包括性**: 全品質次元の網羅的チェック
- **効率性**: 並列処理による高速実行
- **精度**: 誤検出の最小化
- **実用性**: 実行可能な改善提案
- **追跡性**: 品質変化の可視化
