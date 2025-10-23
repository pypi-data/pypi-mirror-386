---
spec_id: SPEC-EPISODE-029
status: draft
owner: narrative-design
last_reviewed: 2025-10-01
category: EPISODE
tags: [value_object, title, localization]
---
# SPEC-EPISODE-029: エピソードタイトル値オブジェクト仕様

## 1. 目的
- 各エピソードのタイトル表記を統一し、文字数制限・使用禁止文字・装飾規則を明文化する。
- 出版物・プラットフォームごとのフォーマット差分を吸収し、再利用可能な API を提供する。

## 2. 前提条件
- タイトルは UTF-8 で保存し、最大 60 文字（全角換算）までを許容する。
- 半角記号のうち `@`, `#`, `\n` 等は使用禁止とする。
- ルビや強調などの装飾はマークアップ層（例: Markdown 拡張）に委譲する。

## 3. 主要な振る舞い
- 入力文字列を正規化し、先頭末尾の空白を除去する。
- 長さ超過時は自動で警告イベントを発行し、設定に応じてトリミングを提案する。
- タイトル生成ユースケース向けに、テンプレート結合 (`{episode_number}:{base_title}`) をサポートする。

## 4. インターフェース仕様
- `EpisodeTitle.validate(raw: str) -> EpisodeTitle`
- `EpisodeTitle.text` プロパティで正規化済みタイトルを取得。
- `EpisodeTitle.with_suffix(suffix: str) -> EpisodeTitle`
- `EpisodeTitle.to_label(style: Literal["plain", "with_number"]) -> str`

## 5. エラーハンドリング
- 禁止文字または空文字の場合は `EpisodeTitleValidationError` を送出する。
- 長さ超過時は `EpisodeTitleLengthWarning` を返却し、イベントパブリッシャー経由で通知する。
