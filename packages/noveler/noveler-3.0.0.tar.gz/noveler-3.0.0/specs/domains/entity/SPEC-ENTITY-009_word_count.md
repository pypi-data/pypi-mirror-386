---
spec_id: SPEC-ENTITY-009
status: draft
owner: quality-engineering
last_reviewed: 2025-10-01
category: ENTITY
tags: [entity, metrics, manuscript]
---
# SPEC-ENTITY-009: ワードカウントエンティティ仕様

## 1. 目的
- 原稿・プロット・チェックレポートで共通使用する語数メトリクスを統一し、計測精度と一貫性を保証する。
- メトリクス結果をライター向けダッシュボードや品質ゲートに受け渡すためのデータ構造を定義する。

## 2. 前提条件
- 対象テキストは UTF-8 で提供され、全角・半角スペースを区切りとして扱う。
- 日本語混在を考慮し、形態素切り出しを行わない簡易カウント方式を採用する（将来拡張可）。
- 改行・タブは空白に正規化したうえで計測する。

## 3. 主要な振る舞い
- 入力テキストから総語数、ユニーク語数、平均語長を算出する。
- 章・セクション単位でのサマリー集計をサポートし、差分比較（前回比 ±%）を提供する。
- 許容閾値（例: 4000 ±20%）を超過した場合はコンプライアンス警告イベントを発行する。

## 4. インターフェース仕様
- `WordCountResult(total_words: int, unique_words: int, average_length: float)`
- `WordCountAnalyzer.compute(text: str, *, locale: str = "ja_JP") -> WordCountResult`
- `WordCountAnalyzer.diff(current: WordCountResult, baseline: WordCountResult) -> WordCountDelta`

## 5. エラーハンドリング
- 入力が `None` または空文字の場合は `WordCountInputError` を送出する。
- 極端に大きな入力（10MB 超）では `WordCountLimitExceeded` を発行し、部分計測またはサンプリングへフォールバックする。
