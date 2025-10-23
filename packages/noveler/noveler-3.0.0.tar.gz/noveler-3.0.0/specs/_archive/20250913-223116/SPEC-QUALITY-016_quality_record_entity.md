# SPEC-QUALITY-016: QualityRecord Entity Specification

## SPEC-QUALITY-005: 品質記録エンティティ


## 概要
品質記録のドメインエンティティ。アグリゲートルートとして品質チェック結果の記録とトレンド分析を管理する。

## エンティティ構成

### QualityRecordEntry（不変オブジェクト）
品質記録エントリ

#### プロパティ
- `id: str` - エントリID（自動生成）
- `quality_result: QualityCheckResult` - 品質チェック結果
- `created_at: datetime` - 作成日時
- `metadata: dict[str, Any] | None` - メタデータ

#### メソッド
- `create_from_result(result: QualityCheckResult, metadata: dict[str, Any] | None = None) -> QualityRecordEntry` - 品質チェック結果からエントリを作成

### QualityRecord（アグリゲートルート）
品質記録エンティティ

#### プロパティ
- `project_name: str` - プロジェクト名（読み取り専用）
- `last_updated: datetime` - 最終更新日時（読み取り専用）
- `entries: list[QualityRecordEntry]` - 記録エントリのコピー（不変性保証）
- `entry_count: int` - 記録エントリ数

#### メソッド
- `add_quality_check_result(result: QualityCheckResult, metadata: dict[str, Any] | None = None) -> str` - 品質チェック結果を追加
- `get_latest_for_episode(episode_number: int) -> QualityRecordEntry | None` - 指定エピソードの最新記録を取得
- `get_quality_trend(episode_number: int, limit: int = 10) -> list[QualityScore]` - 品質スコアのトレンドを取得
- `calculate_average_score() -> QualityScore | None` - 全エピソードの平均品質スコア
- `get_episodes_below_threshold(threshold: QualityScore = None) -> list[int]` - 閾値以下の品質スコアのエピソード一覧
- `purge_old_entries(days_to_keep: int = 30) -> int` - 古い記録のパージ
- `get_domain_events() -> list[Any]` - ドメインイベント取得
- `clear_domain_events()` - ドメインイベントクリア
- `to_persistence_dict() -> dict[str, Any]` - 永続化用辞書変換

## ビジネスルール

### プロジェクト名検証
1. プロジェクト名は空文字列や空白のみは不可
2. プロジェクト名は自動的にトリムされる

### 重複チェック防止
1. 同じエピソード・同じ時刻（60秒以内）の重複エントリは作成不可
2. 重複検出時は `QualityRecordError` を発生させる

### 品質トレンド取得
1. 指定エピソードの記録を時系列順でソート
2. 最大件数制限（デフォルト10件）を適用
3. 新しい順から指定件数分を返す

### 閾値判定
1. デフォルト閾値は80.0
2. 各エピソードの最新記録ではなく、全記録から判定
3. 重複するエピソード番号は重複排除してソート

### 古い記録のパージ
1. 保持期間は1日以上必須
2. 指定日数より古い記録を削除
3. パージした件数を返す
4. パージ実行時にドメインイベントを発行

## ドメインイベント

### QualityCheckAdded
品質チェック結果追加時に発行
- `type`: "QualityCheckAdded"
- `entry_id`: エントリID
- `episode_number`: エピソード番号
- `score`: 総合スコア
- `timestamp`: 発行時刻

### OldEntriesPurged
古い記録パージ時に発行
- `type`: "OldEntriesPurged"
- `purged_count`: パージした件数
- `timestamp`: 発行時刻

## 例外処理
- `QualityRecordError`: ビジネスルール違反時に発生
  - プロジェクト名が空の場合
  - 重複エントリ追加時
  - 保持期間が0以下の場合

## 依存関係
- `domain.exceptions.QualityRecordError`
- `domain.value_objects.quality_check_result.*`
