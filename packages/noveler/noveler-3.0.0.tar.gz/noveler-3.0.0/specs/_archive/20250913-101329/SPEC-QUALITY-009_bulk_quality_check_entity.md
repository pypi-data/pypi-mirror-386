# SPEC-QUALITY-009: BulkQualityCheck Entity Specification

## 概要
全話品質チェックのドメインエンティティ。複数エピソードの一括品質チェックと品質履歴管理を行う。

## エンティティ構成

### BulkQualityCheck（データクラス）
全話品質チェック設定

#### プロパティ
- `project_name: str` - プロジェクト名（必須）
- `episode_range: tuple[int, int] | None` - エピソード範囲（オプション）
- `parallel: bool` - 並列実行フラグ（デフォルト: False）
- `include_archived: bool` - アーカイブ済み含むフラグ（デフォルト: False）
- `force_recheck: bool` - 強制再チェックフラグ（デフォルト: False）

#### バリデーション
- `__post_init__`: プロジェクト名の空文字チェック

### QualityRecord（データクラス）
品質記録

#### プロパティ
- `episode_number: int` - エピソード番号
- `quality_score: float` - 品質スコア
- `category_scores: dict` - カテゴリ別スコア辞書
- `timestamp: datetime` - タイムスタンプ

### QualityTrend（データクラス）
品質トレンド

#### プロパティ
- `direction: str` - トレンド方向（"improving", "stable", "declining"）
- `slope: float` - 傾き値
- `confidence: float` - 信頼度（0.0-1.0）

### QualityHistory（クラス）
品質記録履歴管理

#### プロパティ
- `project_name: str` - プロジェクト名
- `records: list[QualityRecord]` - 品質記録リスト

#### メソッド
- `add_record(episode_number: int, quality_result: QualityCheckResult)` - 品質記録を追加
- `calculate_trend() -> QualityTrend` - 品質トレンドを計算
- `find_problematic_episodes(threshold: float = 70.0) -> list[int]` - 問題のあるエピソードを特定

## ビジネスルール

### BulkQualityCheck
1. プロジェクト名は空文字列や空白のみは不可
2. プロジェクト名は自動的にトリムされる

### QualityHistory
1. `add_record`時に現在時刻でタイムスタンプを設定
2. トレンド計算は2件以上の記録が必要
3. トレンド方向判定:
   - slope > 1.0: "improving"
   - slope < -1.0: "declining"
   - その他: "stable"
4. 信頼度計算: `min(abs(slope) / 5.0, 1.0)`
5. 問題のあるエピソード特定: デフォルト閾値は70.0

### トレンド計算アルゴリズム
線形回帰による傾き計算:
```
slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
```

## 例外処理
- `ValueError`: プロジェクト名が空の場合

## 依存関係
- `domain.value_objects.quality_check_result.QualityCheckResult`
