---
spec_id: SPEC-QUALITY-031
status: draft
owner: quality-engineering
last_reviewed: 2025-10-01
category: QUALITY
tags: [quality, scoring, value_object]
---
# SPEC-QUALITY-031: 品質スコア値オブジェクト仕様

## 1. 目的
- 原稿チェック結果を 0〜100 のスコアで表現し、品質ゲートやレポート生成で再利用できる共通フォーマットを提供する。
- ステージ別（構成・文章・読者体験）に加重平均を適用し、ビジネス要件に合わせた基準値を定義する。

## 2. 前提条件
- 入力となる各評価指標（例: 読みやすさ、構造、テンポ）は 0〜1 の正規化済み値で受け取る。
- スコア計算は順序保証のため不変値（`dataclass(frozen=True)`）で実装する。
- 閾値は設定ファイル `quality_gate_defaults.yaml` から読み込む。

## 3. 主要な振る舞い
- `QualityScore.compose(subscores, weights)` で総合スコアを算出し、小数第 2 位で丸める。
- 基準値を下回った場合は `QualityScoreStatus.FAIL` を返し、ドメインイベントを通じて通知する。
- 異なる査定バージョン間で比較し、改善傾向（上昇／下降）を算出するメソッドを備える。

## 4. インターフェース仕様
- `QualityScore.from_components(structure: float, prose: float, experience: float) -> QualityScore`
- プロパティ: `value: float`, `status: QualityScoreStatus`, `trend: Optional[QualityScoreTrend]`
- メソッド: `is_passing(threshold: float) -> bool`, `to_dict() -> dict[str, float]`

## 5. エラーハンドリング
- コンポーネントが範囲外 (0 未満または 1 を超過) の場合は `QualityScoreValidationError` を送出する。
- 欠損値がある場合は `QualityScoreMissingComponentError` を送出し、どの指標が不足しているかを詳細に含める。
