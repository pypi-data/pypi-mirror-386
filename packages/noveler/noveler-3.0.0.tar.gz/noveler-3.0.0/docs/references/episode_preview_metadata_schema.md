# File: docs/episode_preview_metadata_schema.md
# Purpose: Document the EpisodePreviewGenerationService metadata contract for horizontal reuse.
# Context: Consumed by CLI/MCP adapters, plot structure services, and analytics pipelines that depend on preview metadata.

## はじめに
EpisodePreviewGenerationService はプレビュー生成と品質評価を担うドメインサービスです。本仕様書では、サービスが返す `PreviewResult.metadata` の標準スキーマを定義し、依存コンポーネントが一貫した形でメタデータを扱えるようにします。B20 サイクルで得た教訓（影響調査 → RED/ GREEN/ REFACTOR → 段階統合）を後続チームや LLM ワークフローに水平展開するためのリファレンスとして利用してください。

## スキーマ全体像
- **schema_version**: `"1.1.0"` 固定。互換性判定の基準。
- **トップレベル互換フィールド**: 既存ワークフローのために残しているキー。
  - `original_word_count` （実際は日本語文字数ベースのカウント）
  - `preview_word_count`／`preview_character_count`
  - `sentence_count`／`preview_sentence_count`
  - `has_dialogue`、`dialogue_sentence_count`
  - `estimated_reading_time`／`preview_estimated_reading_time`
  - `preview_style`、`content_filters`
  - `dominant_sentiment`、`sentiment_distribution`
  - `hook`
  - `quality_score`、`quality_minimum_threshold`、`quality_passed`
- **構造化セクション**
  - `source`: 原稿基準の統計集（文字数、文数、フィルタヒット、感情分布など）。
  - `preview`: 生成プレビュー側の統計（文字数、文数、読書時間、対話有無、hook、ellipsis 有無）。
  - `config`: 使用した `PreviewConfiguration` のスナップショット。
  - `quality`: 品質スコアと受入閾値のまとめ。
  - `episode`: エピソード文脈メタデータ（タイトル、話数、ジャンル、タグ）。

## フィールド定義
| セクション | フィールド | 型 | 説明 |
| --- | --- | --- | --- |
| top-level | `schema_version` | str | メタデータ仕様のバージョン (`1.1.0`) |
| top-level | `preview_word_count` | int | プレビュー文字数（日本語のため文字カウントを採用） |
| top-level | `preview_character_count` | int | 上記と同値。互換目的で重複提供 |
| top-level | `sentiment_distribution` | dict[str, int] | sentence ベースの感情ヒット数 (`positive`, `negative`, `neutral`) |
| top-level | `hook` | str | プレビューの導入（質問・ティザー文優先） |
| source | `character_count` | int | 原文の文字数 |
| source | `content_filter_hits` | dict | dialogue/action/emotion/description の文ヒット数と `active_filters` |
| source | `reading_time_seconds` | int | 原文の推定読書時間（秒） |
| preview | `character_count` | int | プレビュー文字数 |
| preview | `sentence_count` | int | プレビューの文数 |
| preview | `contains_dialogue` | bool | `「」` の有無（片側欠落でも true） |
| preview | `hook` | str | 上位と同一値（サブセクション経由で参照可能） |
| preview | `ends_with_ellipsis` | bool | スタイルの省略記号が単一回で終端しているか |
| preview | `reading_time_seconds` | int | プレビューの読書時間（秒） |
| config | `preview_style` | str | `summary` / `excerpt` / `teaser` / `dialogue_focus` |
| config | `content_filters` | list[str] | 適用したフィルタ値 |
| config | `quality_thresholds` | list[dict] | `QualityThreshold.to_dict()` の配列 |
| quality | `score` | float | 算出済み品質スコア |
| quality | `minimum_required` | float | `PreviewConfiguration#get_minimum_quality_score()` |
| quality | `passed` | bool | スコアが閾値以上か |
| episode | `episode_title` | str | エピソードタイトル（入力メタから統合） |
| episode | `episode_number` | int | 話数 |
| episode | `genre`, `tags` | str, list[str] | 任意の補助情報 |

> **備考**: `original_word_count` は現状、日本語テキストの性質上「文字数」を意味します。英語など分かち書き言語では空白分割で近似します。

## 生成ロジック要約
1. 重要文抽出後にティザースタイル専用のサフィックス補正 (`_ensure_teaser_suffix`) を実施。
2. 品質スコアを算出し、メタデータ組み立て時点で `quality` セクションへ格納。
3. 文分割は `re.findall(r"[^。！？!?…]+(?:[。！？!?…]+)?")` を使用し、`…` 系列や全角記号をカバー。
4. 感情分布は文単位でポジティブ／ネガティブ語を集計し、中立は残余文数として計上。
5. `preview` セクションでは対話、読み時間、hook、ellipsis 終端フラグを提供。
6. `source` セクションでフィルタヒット数とアクション／感情／ミステリー文カウントを公開。

## 依存関係マッピング
| コンポーネント | 利用目的 |
| --- | --- |
| `plot_structure_service._adapt_resolution_for_serial` | `metadata["hook"]` をシリアル構成の setup 文に利用 |
| CLI/MCP ツール (noveler.mcp.*) | プレビュー統計をUI表示/ログ出力で参照 |
| 品質レポート生成系 | `quality` セクションと `sentiment_distribution` を分析指標として利用 |

## 品質保証
- ユニットテスト: `tests/unit/domain/services/test_episode_preview_generation_service.py`、`tests/unit/domain/plot_episode/services/test_episode_preview_generation_service.py`
  - スキーマ存在、hook、感情分布、dialogue 判定、ティザー末尾などを検証。
- 影響調査: `python scripts/tools/impact_audit.py --pattern "preview" --output temp/impact_audit/episode-preview.md`
  - 既存依存が追加フィールドに追従済みか確認。
- フォールバック: バッチ生成時の `episode_metadata` は `metadata["episode"]` へ統合しつつ、トップレベル互換キーも維持。

## 運用チェックリスト
- [ ] RED: 追加フィールドを検証するテストを作成（metadata schema, teaser suffix, dialogue 判定）。
- [ ] GREEN: `EpisodePreviewGenerationService` のメタデータ構築ロジック更新、サフィックス補正、文分割改善。
- [ ] REFACTOR: 補助メソッド（`_ensure_teaser_suffix`, `_analyze_sentiment_details`, `_calculate_content_filter_hits`）で意図を明確化。
- [ ] テスト実行: `pytest tests/unit/domain/services/test_episode_preview_generation_service.py tests/unit/domain/plot_episode/services/test_episode_preview_generation_service.py`
- [ ] ドキュメント更新: 本ファイルおよび必要に応じた README/ガイド差分。

## サンプル
```python
result = service.generate_preview(content, PreviewConfiguration.create_teaser())
print(result.metadata["preview"]["hook"])  # ➜ "ここは...どこだ? ..."
print(result.metadata["quality"])           # ➜ {"score": 0.78, "minimum_required": 0.7, "passed": True}
```

本仕様をベースに、EpisodePreview 関連の CLI・MCP ツールや可視化ドキュメントを更新することで、各チームが共通のメタデータ契約を参照できるようになります。
