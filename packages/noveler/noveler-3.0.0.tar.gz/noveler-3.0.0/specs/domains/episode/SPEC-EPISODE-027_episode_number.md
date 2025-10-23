---
spec_id: SPEC-EPISODE-027
status: draft
owner: domain-architecture
last_reviewed: 2025-10-01
category: EPISODE
tags: [value_object, episode, numbering]
---
# SPEC-EPISODE-027: エピソード番号値オブジェクト仕様

## 1. 目的
- 各エピソードを一意に識別する番号体系を定義し、バリデーションと整合性を担保する。
- ドメイン層での話数計算・整列処理を簡潔にし、外部への整合した番号付与を保証する。

## 2. 前提条件
- 番号は 1 以上の整数またはゼロ埋め 3 桁文字列とする（例: `1`, `"001"`）。
- エピソード管理ファイルは既存の `話数管理.yaml` を参照し、欠番は許容しない。
- 国際化・翻訳要件は対象外とする。

## 3. 主要な振る舞い
- 入力値を正規化し、内部的には整数で保持する。
- フォーマット指定に応じて `"EP{number:03d}"` 形式などを生成する。
- シーケンス検証をサポートし、欠番または逆順を検知した際は警告イベントを発行する。

## 4. インターフェース仕様
- `EpisodeNumber.from_raw(value: str | int) -> EpisodeNumber`
- `EpisodeNumber.as_int() -> int`
- `EpisodeNumber.as_label(format: Literal["short", "long"]) -> str`
- `EpisodeNumber.next(delta: int = 1) -> EpisodeNumber`

## 5. エラーハンドリング
- 0 以下、非数値、負数など無効値は `EpisodeNumberValidationError` を送出する。
- 欠番検出時は `DomainWarningEvent` を発行し、詳細コンテキストにギャップ情報を含める。
