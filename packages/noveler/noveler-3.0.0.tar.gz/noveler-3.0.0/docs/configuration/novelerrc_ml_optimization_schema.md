# .novelerrc.yaml ML最適化設定スキーマ

## 概要

このドキュメントは `.novelerrc.yaml` に追加されたML最適化設定のスキーマ定義です。

**関連仕様**: SPEC-QUALITY-140 (ML強化品質最適化システム仕様書)

---

## 設定セクション

### `ml_optimization`

機械学習ベースの品質最適化を制御する設定。

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `enabled` | boolean | `false` | ML最適化を有効化 |
| `corpus_model_id` | string? | `null` | 使用するコーパスモデルID（`null`=自動選択） |
| `auto_optimize_weights` | boolean | `false` | 重み付けを自動最適化 |
| `use_dynamic_thresholds` | boolean | `false` | コーパス学習に基づく動的閾値を使用 |
| `use_dynamic_severity` | boolean | `true` | 位置・頻度を考慮した重大度推定を使用 |
| `learning_mode` | string | `"online"` | 学習モード: `online`/`batch`/`disabled` |

#### 学習モード

- **`online`**: インクリメンタル学習（推奨）
  - 評価結果を逐次フィードバックに追加
  - リアルタイムで学習データが蓄積
  - パフォーマンス: 軽量

- **`batch`**: バッチ再訓練
  - 定期的に全データで再訓練
  - 精度向上が期待できる
  - パフォーマンス: 重い（定期実行推奨）

- **`disabled`**: 学習無効
  - フィードバック記録のみ
  - ML最適化は実行されない

---

### `ml_optimization.auto_tune_gates`

品質ゲート閾値の自動チューニング設定。

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `enabled` | boolean | `false` | 自動チューニングを有効化（**明示的な有効化が必要**） |
| `adjustment_policy` | string | `"conservative"` | 調整ポリシー: `conservative`/`moderate`/`aggressive` |
| `target_false_positive_rate` | float | `0.05` | 目標偽陽性率（5%） |
| `target_false_negative_rate` | float | `0.10` | 目標偽陰性率（10%） |
| `review_before_apply` | boolean | `true` | 適用前にレビューを要求 |

#### 調整ポリシー

- **`conservative`**: 保守的な調整
  - 閾値変更は最小限
  - 安定性重視
  - 推奨: 初回導入時

- **`moderate`**: 中庸な調整
  - バランス重視
  - 推奨: 通常運用

- **`aggressive`**: 積極的な調整
  - 高速に最適化
  - 不安定になる可能性あり
  - 推奨: 実験的な使用

---

### `ml_optimization.feedback`

フィードバック収集設定。

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `auto_record` | boolean | `true` | 評価結果を自動的にフィードバックとして記録 |
| `collect_user_corrections` | boolean | `true` | ユーザー修正を収集 |
| `feedback_history_limit` | int | `50` | 学習に使用するフィードバック履歴数 |

---

### `ml_training`

MLモデル訓練設定（advanced）。

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `validation_split` | float | `0.2` | 検証データの割合（20%） |
| `optimization_objective` | string | `"f1_score"` | 最適化目標: `f1_score`/`precision`/`recall`/`rmse` |
| `min_training_samples` | int | `10` | 最小訓練サンプル数 |
| `cache_ttl_hours` | int | `24` | コーパスメトリクスのキャッシュ有効期限（時間） |

#### 最適化目標

- **`f1_score`**: F1スコア（精度と再現率の調和平均）
  - 推奨: バランス重視

- **`precision`**: 精度（偽陽性を最小化）
  - 推奨: 厳格な品質チェック

- **`recall`**: 再現率（偽陰性を最小化）
  - 推奨: 見逃しを防ぐ

- **`rmse`**: 二乗平均平方根誤差
  - 推奨: 人間評価との一致度を最大化

---

## 使用例

### 基本的なML最適化

```yaml
ml_optimization:
  enabled: true
  learning_mode: "online"
```

### 重み付け自動最適化

```yaml
ml_optimization:
  enabled: true
  auto_optimize_weights: true
  learning_mode: "online"
```

### コーパスベースの動的閾値

```yaml
ml_optimization:
  enabled: true
  use_dynamic_thresholds: true
  corpus_model_id: "fantasy_ya_v1"
```

### Gate自動チューニング

```yaml
ml_optimization:
  enabled: true
  auto_tune_gates:
    enabled: true
    adjustment_policy: "moderate"
    target_false_positive_rate: 0.03
    review_before_apply: true
```

### フル機能有効化

```yaml
ml_optimization:
  enabled: true
  corpus_model_id: "fantasy_ya_v1"
  auto_optimize_weights: true
  use_dynamic_thresholds: true
  use_dynamic_severity: true
  learning_mode: "online"

  auto_tune_gates:
    enabled: true
    adjustment_policy: "moderate"
    target_false_positive_rate: 0.03
    target_false_negative_rate: 0.08

  feedback:
    auto_record: true
    collect_user_corrections: true
    feedback_history_limit: 100

ml_training:
  validation_split: 0.2
  optimization_objective: "f1_score"
  min_training_samples: 20
  cache_ttl_hours: 12
```

---

## マイグレーションパス

### Phase 1: Feedback収集 (2週間)

```yaml
ml_optimization:
  enabled: false  # ML無効、フィードバックのみ収集
  feedback:
    auto_record: true
    collect_user_corrections: true
```

### Phase 2: ML試験運用 (1週間)

```yaml
ml_optimization:
  enabled: true
  learning_mode: "online"
  use_dynamic_severity: true  # まず重大度推定のみ有効化
```

### Phase 3: 完全有効化

```yaml
ml_optimization:
  enabled: true
  auto_optimize_weights: true
  use_dynamic_thresholds: true
  use_dynamic_severity: true
  learning_mode: "online"
```

---

## パフォーマンス影響

| 設定 | 追加レイテンシ | メモリ使用量 |
|------|--------------|-------------|
| `enabled: false` | 0秒 | 0MB |
| `enabled: true` (基本) | +2-5秒 | +50MB |
| `auto_optimize_weights: true` | +1-2秒 | +20MB |
| `use_dynamic_thresholds: true` | +1-3秒 | +30MB |
| `use_dynamic_severity: true` | +0.1秒/issue | +10MB |
| **合計（フル有効化）** | **+5-10秒** | **+110MB** |

---

## トラブルシューティング

### ML最適化が遅い

- `learning_mode: "disabled"` に変更してフィードバック収集のみ
- `cache_ttl_hours` を延長してキャッシュヒット率向上
- コーパスサンプル数を削減

### 誤検出が多い

- `auto_tune_gates.target_false_positive_rate` を下げる
- `auto_tune_gates.adjustment_policy: "aggressive"` で高速調整
- フィードバック履歴を増やす（`feedback_history_limit: 100`）

### 見逃しが多い

- `auto_tune_gates.target_false_negative_rate` を下げる
- `ml_training.optimization_objective: "recall"` に変更

---

## 関連ドキュメント

- [SPEC-QUALITY-140](../../specs/domains/quality/SPEC-QUALITY-140_ml_enhanced_quality_optimization.md) - ML強化品質最適化システム仕様書
- [SPEC-QUALITY-110](../../specs/domains/quality/SPEC-QUALITY-110_progressive_check_flow.md) - 段階的品質チェックフロー
- [SPEC-QUALITY-019](../../specs/domains/quality/SPEC-QUALITY-019_adaptive_quality_evaluation.md) - 適応的品質評価

---

## 更新履歴

| Version | Date | Summary |
|---------|------|---------|
| 1.0.0 | 2025-10-11 | 初版: ML最適化設定スキーマ定義 |
