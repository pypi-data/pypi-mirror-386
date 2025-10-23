---
spec_id: SPEC-QUALITY-019
status: draft
owner: bamboocity
last_reviewed: 2025-09-17
category: QUALITY
sources: [REQ]
tags: [quality, adaptive, learning]
requirements:
  - REQ-QUALITY-003
  - REQ-QUALITY-001
  - REQ-DATA-001
---
# SPEC-QUALITY-019: 適応的品質評価システム仕様書

## 1. 概要

### 1.1 目的
執筆者の経験値・ジャンル特性・読者フィードバックを踏まえ、大域的品質スコアを個別最適化する「適応的品質評価システム」を定義する。標準化されたA31品質チェック結果に対して、プロジェクト固有の学習データを用いた基準調整と提案生成を行う。

### 1.2 スコープ
- `AdaptiveQualityEvaluator`（アプリケーション層）による適応評価オーケストレーション
- `AdaptiveQualityService`（ドメイン層）による個別基準の調整・学習
- `QualityAdaptationPolicy` / `AdaptiveQualityEvaluator`（ドメインエンティティ）による適応度管理
- `JSONConversionServer` 経由でMCPツールから供給される品質スコアデータを入力とした評価フロー

## 2. 要求事項

| 要件ID | 説明 | 対応セクション |
| --- | --- | --- |
| REQ-QUALITY-003 | 適応的品質評価をDDD準拠で実装する | §3, §4 |
| REQ-QUALITY-001 | ベースになる品質アスペクト（readability/composition/style等）の調整 | §3.3 |
| REQ-DATA-001 | CLI/MCPで生成された品質スコアJSONの取り扱い | §5 |

## 3. システム構成

### 3.1 アプリケーション層コンポーネント
- `AdaptiveQualityEvaluator` (`src/noveler/application/use_cases/adaptive_quality_evaluation_use_case.py`)
  - 依存性: `ISettingsRepositoryFactory`, `WriterLevelService`, `QualityStandardFactory`
  - 公開API: `evaluate_with_adaptive_standards(quality_scores: dict[str, float]) -> dict[str, Any]`
  - インフラ層への直接依存を避け、DIされたファクトリーからリポジトリを取得

### 3.2 ドメイン層コンポーネント
- `AdaptiveQualityService` (`src/noveler/domain/learning/services.py`)
  - 作家プロフィールや読者フィードバックを用いた基準調整
  - `adjust_criteria_for_author`, `update_criteria_from_feedback`, `optimize_quality_standards`
- `AdaptiveQualityEvaluator` (`src/noveler/domain/quality/entities.py`)
  - 適応ポリシーと学習モデルの状態を保持
  - `evaluate_adaptively` で標準スコアを適応スコアへ変換
- `QualityAdaptationPolicy` (`src/noveler/domain/quality/entities.py`)
  - メトリック別の適応強度 (`AdaptationStrength`) を管理

### 3.3 品質アスペクト
対象とする品質指標は以下のとおり。
- `overall`（総合スコア）
- `readability`（可読性）
- `composition`（構成）
- `style`（文体）
- `dialogue`（会話表現）
- `narrative_depth`（描写・内面深度）
それぞれ `QualityStandard` が閾値(`minimum/target/excellent`) と重み(`weight`)を提供する。

### 3.4 適応パラメータ
- 執筆者レベル判定: `WriterLevelService.determine_level(completed_episodes, average_score)`
- ジャンル推定: プロジェクト設定 → ジャンル文字列 → `Genre` 列挙体マッピング
- 改善提案: `MAX_SUGGESTIONS=3`, `URGENT_THRESHOLD=50`
- スコア調整: 重み <1 で緩和 (スコア上昇), 重み >1 で厳格化 (スコア減少)

## 4. 処理フロー

```mermaid
sequenceDiagram
    participant Tool as MCP Tool (run_quality_checks)
    participant JSON as JSONConversionServer
    participant App as AdaptiveQualityEvaluator
    participant Domain as AdaptiveQualityService

    Tool->>JSON: 品質スコアJSON出力
    JSON->>App: quality_scores (dict[str, float])
    App->>App: _determine_writer_level()
    App->>App: _get_project_genre()
    App->>Domain: create_standard(writer_level, genre)
    Domain-->>App: QualityStandard
    App->>App: _adjust_scores()
    App->>App: _evaluate_against_standard()
    App->>App: _generate_improvement_suggestions()
    App-->>Tool: 調整結果・提案を含むレスポンス
```

### 4.1 入力検証
- スコア辞書が空の場合は `AdaptiveQualityEvaluationError`
- 各スコアは `0 <= value <= 100`
- プロジェクトルート未指定時はエラー

### 4.2 結果構造
```json
{
  "writer_level": "intermediate",
  "writer_level_description": "中級者: 安定した執筆が可能",
  "genre": "fantasy",
  "original_scores": {"overall": 78.0, ...},
  "adjusted_scores": {"overall": 82.4, ...},
  "overall_score": 82.4,
  "evaluation": {"overall": "良好", "readability": "要改善", ...},
  "thresholds": {"overall": {"minimum": 60, "target": 75, "excellent": 90}, ...},
  "improvement_suggestions": [{"area": "readability", "suggestion": "短い文と長い文を交互に配置し、リズムを作りましょう。"}],
  "encouragement": "読者が読みやすく感じる文章です。次は描写の深さを増やしましょう。"
}
```

## 5. データ連携

- 入力は `run_quality_checks` / `export_quality_report` などMCPツール経由で取得した品質スコアJSON。
- `JSONConversionServer` が `temp/json_output/` 以下に保存し、`convert_cli_to_json` ツールで参照可能。
- 適応評価結果は CLI / MCP レスポンスに含める。

## 6. テスト

| テスト | 目的 |
| --- | --- |
| `tests/test_ddd_compliance_adaptive_quality.py` | DI・依存制約・後方互換のDDD準拠検証 |
| `tests/unit/domain/learning/test_learning_services.py` | `AdaptiveQualityService` の基準調整・学習ロジック |
| `tests/unit/domain/quality/test_quality_entities.py` | `AdaptiveQualityEvaluator` エンティティの適応処理 |
| `tests/unit/domain/test_domain_adaptive_quality_integration.py` | アプリケーション/ドメイン統合テスト |

## 7. セキュリティ・非機能
- 設定・進捗リポジトリへのアクセスは `ISettingsRepositoryFactory` 経由で認証済みストレージに限定
- JSON出力は `FileIOCache` により再利用し、重複処理を50%以上削減
- 適応調整の計算は同期実行で100ms以内（平均ケース）

## 8. 更新履歴

| Version | Date | Summary |
| --- | --- | --- |
| 1.0.0 | 2025-09-17 | As-built版として再構築。アプリケーション/ドメイン構成と品質アスペクト定義を明文化。 |


### 9. デバイス混在・毎日更新プロファイル（mixed_device_daily_6k_10k）
- narration_p25_p75: 14–60（chars）
- short_run_max: 3 / long_run_max: 2
- window_avg_range: 18–70、in_range_ratio >= 0.85
- paragraph_len_main: 1–3文中心
- sections_per_episode: 7–12、section_len: 700–1,100
- hooks: minor 40–60%、mini 80–90%、main=末尾必須
- target_length: ConfigResolverの確定値（必須）。欠落/不正時は QC-009/QC-010 として中断
- dialogue_warnings: same_ending<=4、punctuation_runs>=3 を警告

---

## 10. ML強化適応評価への拡張 (SPEC-QUALITY-140)

### 10.1 概要
SPEC-QUALITY-140 で定義されるML学習機能と統合し、静的な適応基準からデータ駆動型の動的最適化へ移行する。

### 10.2 拡張ポイント

#### 10.2.1 AdaptiveQualityService の ML拡張
既存の `AdaptiveQualityService` に ML学習機能を追加:

```python
class AdaptiveQualityService:
    """Extended with ML-based learning capabilities."""

    def __init__(
        self,
        corpus_analyzer: CorpusAnalyzer,
        weight_optimizer: WeightOptimizer,
        feedback_repository: IFeedbackRepository
    ):
        self.corpus_analyzer = corpus_analyzer
        self.weight_optimizer = weight_optimizer
        self.feedback_repository = feedback_repository

    def adjust_criteria_with_ml(
        self,
        base_criteria: QualityStandard,
        project_context: ProjectContext,
        learning_mode: LearningMode = LearningMode.ONLINE
    ) -> MLAdjustedCriteria:
        """
        Adjust quality criteria using ML-learned patterns.

        Returns:
            MLAdjustedCriteria with:
            - corpus_adjusted_thresholds: Learned from similar works
            - optimized_weights: Data-driven weight optimization
            - confidence_scores: Statistical confidence for adjustments
        """
```

#### 10.2.2 静的適応から動的学習へ

**現行 (静的):**
```python
# 作家レベル別の固定閾値
WRITER_LEVEL_THRESHOLDS = {
    "beginner": {"overall": 60, "readability": 55},
    "intermediate": {"overall": 75, "readability": 70},
    "advanced": {"overall": 85, "readability": 80}
}
```

**ML拡張後 (動的):**
```python
# コーパス学習 + フィードバック最適化
def get_dynamic_thresholds(
    writer_level: str,
    genre: Genre,
    feedback_history: list[QualityFeedback]
) -> DynamicThresholds:
    # 1. コーパスから学習したベースライン
    corpus_baseline = corpus_analyzer.build_baseline_metrics(genre)

    # 2. 作家レベル別の調整係数
    level_coefficient = _get_level_coefficient(writer_level)

    # 3. フィードバックから学習した最適閾値
    optimized = weight_optimizer.optimize_thresholds(feedback_history)

    return DynamicThresholds(
        overall=corpus_baseline.overall * level_coefficient + optimized.delta,
        readability=corpus_baseline.readability * level_coefficient + optimized.delta,
        confidence=optimized.confidence
    )
```

#### 10.2.3 学習サイクル

```mermaid
graph TD
    A[品質チェック実行] --> B{ML有効?}
    B -->|Yes| C[コーパスベースライン取得]
    B -->|No| Z[静的基準使用]
    C --> D[フィードバック履歴読込]
    D --> E[重み最適化]
    E --> F[動的閾値計算]
    F --> G[ML強化スコア算出]
    G --> H[結果とフィードバック記録]
    H --> I[次回評価で学習結果活用]
    I --> A
    Z --> A
```

### 10.3 移行戦略

#### Phase 1: 並行実行 (検証フェーズ)
- 静的適応とML適応を両方実行
- 結果を比較し、ML適応の精度を検証
- `metadata.ml_vs_static_comparison` に差分を記録

#### Phase 2: ML優先 (移行フェーズ)
- ML適応を主評価に切り替え
- 静的適応はフォールバックとして維持
- ML失敗時は静的適応にフォールバック

#### Phase 3: 完全移行
- ML適応のみ使用
- 静的閾値は初期化パラメータとしてのみ保持

### 10.4 後方互換性

既存の `AdaptiveQualityEvaluator` 使用ケースはそのまま動作:
- `ml_mode=false` (デフォルト) で静的適応を維持
- `ml_mode=true` で ML強化適応を有効化

```python
# 既存コード (変更不要)
result = adaptive_evaluator.evaluate_with_adaptive_standards(
    quality_scores=base_scores
)

# ML拡張版 (オプトイン)
result = adaptive_evaluator.evaluate_with_adaptive_standards(
    quality_scores=base_scores,
    ml_mode=True,
    corpus_model_id="fantasy_ya_v1"
)
```

### 10.5 テスト拡張

| テスト | 目的 |
| --- | --- |
| `tests/unit/domain/learning/test_ml_adaptive_integration.py` | ML適応と静的適応の統合テスト |
| `tests/unit/domain/learning/test_adaptive_quality_service_ml.py` | ML拡張 AdaptiveQualityService の単体テスト |
| `tests/integration/test_ml_adaptive_evaluation_use_case.py` | End-to-end ML適応評価のシナリオテスト |
