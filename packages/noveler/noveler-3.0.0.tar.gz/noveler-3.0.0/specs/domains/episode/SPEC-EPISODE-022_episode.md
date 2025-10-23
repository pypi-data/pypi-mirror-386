---
spec_id: SPEC-EPISODE-022
status: draft
owner: narrative-design
last_reviewed: 2025-10-01
category: EPISODE
tags: [entity, storyline, management]
---
# SPEC-EPISODE-022: エピソードエンティティ仕様

## 1. 目的
- プロット・原稿・進捗管理で使用するエピソード情報のスキーマを定義し、一貫したデータアクセスを提供する。
- 各エピソードのメタデータ（タイトル、番号、ステータス、ターゲット文字数）を集約し、サービス層・リポジトリ層間の契約を明確にする。

## 2. 前提条件
- エピソード番号は `EpisodeNumber` 値オブジェクト (SPEC-EPISODE-027) で管理する。
- ターゲット文字数は `WordCountEntity` (SPEC-ENTITY-009) を利用し、最小/最大値を保持する。
- エピソード状態は列挙型 `EpisodeStatus`（draft, in_review, approved, archived）に制限する。

## 3. 主要な振る舞い
- エピソード作成時に必須フィールド（番号・タイトル・ターゲット文字数）をバリデーションする。
- 状態遷移のルール（例: `approved` → `archived` のみ許可）を強制する。
- 進捗情報（最新チェック日、品質スコア、最終更新者）を更新履歴として保持し、変更イベントを発行する。

## 4. インターフェース仕様
- `Episode.create(number: EpisodeNumber, title: EpisodeTitle, target_length: WordCountEntity) -> Episode`
- インスタンスプロパティ: `number`, `title`, `status`, `target_length`, `quality_score`, `metadata`
- メソッド: `episode.update_status(new_status: EpisodeStatus)`, `episode.as_dict() -> dict[str, Any]`

## 5. エラーハンドリング
- 不正な状態遷移では `EpisodeStateTransitionError` を送出し、旧状態・新状態を詳細に含める。
- 必須フィールド欠落または関連値オブジェクトの検証エラーは `EpisodeValidationError` に集約する。
