# SPEC-QUALITY-007: 適応的品質評価ユースケース仕様書

## 概要
`AdaptiveQualityEvaluationUseCase`は、プロジェクト固有の学習モデルを使用して標準品質チェック結果を適応的に調整するユースケースです。執筆者の傾向や作品の特性を学習し、より精度の高い品質評価を提供します。

## クラス設計

### AdaptiveQualityEvaluationUseCase

**責務**
- 学習モデルの可用性チェック
- 適応的品質評価の実行
- 標準評価へのフォールバック処理
- 評価結果の変換・統合

## パブリックメソッド

### evaluate_adaptively()

**シグネチャ**
```python
def evaluate_adaptively(
    self,
    project_id: str,
    standard_results: dict[str, Any],
    episode_file_path: str,
) -> dict[str, Any]:
```

**目的**
標準品質チェック結果を学習モデルで適応的に調整し、プロジェクト固有の品質評価を提供する。

**引数**
- `project_id`: プロジェクトID
- `standard_results`: 標準品質チェック結果
- `episode_file_path`: エピソードファイルパス

**戻り値**
```python
{
    "adaptive_enabled": bool,           # 適応的評価が有効かどうか
    "confidence_level": float,          # 信頼度レベル
    "adjusted_scores": dict[str, Any],  # 調整済みスコア
    "adaptation_summary": {             # 適応処理の要約
        "policy_id": str,
        "covered_metrics": list[str],
        "adaptation_count": int,
    },
    "fallback_reason": str,             # フォールバック時の理由
}
```

**処理フロー**
1. 学習モデルの可用性チェック
2. AdaptiveQualityEvaluatorの作成
3. 評価コンテキストの構築
4. 適応ポリシーの生成・適用
5. 標準スコアの適応的評価
6. 結果の統合・返却

**例外処理**
- モデルが利用できない場合：標準評価にフォールバック
- 評価エラー発生時：標準評価にフォールバック

## プライベートメソッド

### _fallback_to_standard()

**目的**
適応的評価が利用できない場合に標準評価結果を返す。

**引数**
- `standard_results`: 標準品質チェック結果
- `reason`: フォールバック理由

### _build_evaluation_context()

**目的**
適応的評価に必要なコンテキスト情報を構築する。

**引数**
- `standard_results`: 標準品質チェック結果
- `episode_file_path`: エピソードファイルパス

**戻り値**
- `EvaluationContext`: 評価コンテキスト

### _convert_to_quality_scores()

**目的**
標準チェック結果をQualityScoreオブジェクトに変換する。

### _convert_from_quality_scores()

**目的**
QualityScoreオブジェクトを辞書形式に変換する。

## 依存関係

### ドメイン層
- `AdaptiveQualityEvaluator`: 適応的品質評価器エンティティ
- `QualityAdaptationService`: 品質適応サービス
- `EvaluationContext`: 評価コンテキスト値オブジェクト
- `QualityScore`: 品質スコア値オブジェクト

### インフラ層
- `model_repository`: 学習モデルリポジトリ（依存性注入）

## 設計原則遵守

### DDD準拠
- ✅ ドメインロジックは`AdaptiveQualityEvaluator`に委譲
- ✅ 値オブジェクト（`QualityScore`, `EvaluationContext`）を適切に使用
- ✅ リポジトリパターンで永続化を抽象化

### TDD準拠
- ✅ 明確な責務分離
- ✅ 例外処理の網羅
- ✅ 型安全な実装

## 使用例

```python
# 依存性注入でリポジトリを設定
use_case = AdaptiveQualityEvaluationUseCase(model_repository)

# 適応的品質評価の実行
result = use_case.evaluate_adaptively(
    project_id="debug_log_reader",
    standard_results={
        "episode_number": 3,
        "checks": {
            "basic_writing_style": {"score": 85.0},
            "story_structure": {"score": 90.0},
        }
    },
    episode_file_path="/path/to/episode003.md"
)

# 結果の確認
if result["adaptive_enabled"]:
    adjusted_scores = result["adjusted_scores"]
    confidence = result["confidence_level"]
else:
    fallback_reason = result["fallback_reason"]
```

## テスト観点

### 単体テスト
- モデル利用可能時の正常処理
- モデル利用不可時のフォールバック
- 評価エラー時のフォールバック
- スコア変換の正確性

### 統合テスト
- 実際の学習モデルとの連携
- ドメインサービスとの協調動作

## 品質基準

- **可用性**: モデル利用不可時の適切なフォールバック
- **信頼性**: 例外安全な実装
- **保守性**: 明確な責務分離と型安全性
- **拡張性**: 新しい適応ポリシーへの対応
