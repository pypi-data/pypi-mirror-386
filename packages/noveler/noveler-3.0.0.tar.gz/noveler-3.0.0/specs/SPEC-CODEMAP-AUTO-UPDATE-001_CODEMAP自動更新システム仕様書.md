# SPEC-CODEMAP-AUTO-UPDATE-001: CODEMAP自動更新・共通基盤整合システム仕様書

**最終更新**: 2025年10月13日  
**担当**: 開発基盤チーム（CODEMAP運用）  
**優先度**: 高（B20/B30品質基準準拠）

---

## 1. 概要

Git コミット／CI 実行時に CODEMAP.yaml を自動更新し、共通基盤コンポーネントの利用状況とメタデータを一貫性のある形で記録・監査するシステムを提供する。  
併せて、共通基盤が未採用となるリスクを低減するため、CODEMAP のスキーマ拡張・静的監査・開発体験改善を段階的に導入する。

### 1.1 ビジネス価値
- ドキュメント同期精度の維持と意思決定材料の可視化
- 共通基盤（Console／Logger／PathService 等）の採用率向上
- レビューや CI での準拠チェック自動化による工数削減

### 1.2 リスクとトリガー
- **知識ギャップ**: 新規実装時に CODEMAP 検索を行わず共通基盤を再実装する恐れ
- **例外フォルダの恒常化**: `mcp_server_exceptions` などの緩和設定が恒久化し、準拠率が低下する恐れ
- **スキーマ変化の追従漏れ**: 自動生成スクリプトと CODEMAP スキーマの不整合による更新失敗
- **静的チェックの重複検知**: 既存 `forbidden_patterns` と新規監査が競合し、誤検出が増える恐れ

これらを回避するため、本仕様では拡張要件とロールを明記し、実装優先度を段階的に整理する。

---

## 2. スコープ

| 項目 | 含む | 含まない |
| --- | --- | --- |
| CODEMAP.yaml スキーマ | `common_foundation.components.*` のメタ項目拡張、禁止・推奨パターン整備 | CODEMAP 外の仕様書自動更新 |
| 自動更新機構 | Git Hook／CI 連携、自動バックアップ、リカバリ | Git の設定管理そのもの |
| 静的監査 | 共通基盤利用率の測定、既存 forbidden パターンとの統合 | 任意ライブラリの静的解析全般 |
| 開発体験 | テンプレート／スキャフォールドの CODEMAP 参照 | IDE プラグイン開発 |

---

## 3. 機能要件

### REQ-1: CODEMAP メタデータ拡張と互換性管理

1. `common_foundation.components.<component>` に以下メタ項目を追加する。  
   - `layer`: 想定適用層（例: presentation / application）  
   - `consumers`: 代表利用先パス配列  
   - `owner`: 責任チーム／担当者識別子  
   - `stability`: `stable` / `beta` / `deprecated` のいずれか  
   - `integration_notes`: DI・初期化順序・特記事項（任意）  
   - `recipes`: 推奨利用コード断片（複数可・YAML マルチライン文字列）
2. `alternatives` には採用基準 `selection_policy`（例: `use when batch CLI`）を追加し、置換計画や廃止スケジュールを保管する。
3. スキーマバージョンを `common_foundation.version` とは別に `schema_version` として管理し、生成スクリプト `scripts/tools/update_codemap_foundation.py` で読み取る。  
   - バージョン更新時は `CHANGELOG.md` に互換性情報を出力する。
4. 自動更新処理は未知フィールドを破棄せず透過的に保持する。`schema_version` 不一致時は警告を出し、CI でブロックする。

### REQ-2: 準拠率監査と禁止パターン統合

1. `scripts/tools` に監査スクリプト `codemap_foundation_audit.py` を追加し、CODEMAP を読み込んで以下を算出する。  
   - 利用率指標: `console_shared_usage_rate` などを CODEMAP に書き戻し（`quality_prevention_integration.automated_prevention.metrics`）。  
   - 未採用箇所リスト: ファイルパス・理由の一覧を `reports/codemap_compliance/YYYYMMDD.jsonl` に出力。
2. 監査結果は既存 `forbidden_patterns` と統合する。  
   - 同一違反を二重検知しないよう、スクリプトは `CODEMAP.yaml` の禁止パターン ID と突き合わせ、既存 CI の結果を参照して抑止する。  
   - 新たに検出された違反は CODEMAP に `violations` セクションとして追記し、CI で通知する。
3. MCP 例外ディレクトリの適用期限を `mcp_server_exceptions.expiry`（ISO 日付）で管理し、期限超過時に警告する。

### REQ-3: 開発体験支援（共通基盤利用の強制力強化）

1. CLI スキャフォールド（`bin/noveler scaffold use-case` など）は CODEMAP を参照し、  
   - 生成コードに `logger = get_logger(__name__)` 等の共通基盤呼び出しをデフォルト挿入する。  
   - テンプレート差し込み時に `recipes` のコード断片を優先採用する。
2. Pull Request テンプレート／レビュー チェックリストに `共通基盤参照欄` を追加し、自動で CODEMAP リンクを埋め込む。
3. 準拠率レポートは四半期ごとに `reports/codemap_compliance/summary-YYYYQ.txt` として CI が生成し、Slack 通知連携を行う。

---

## 4. 非機能要件

- **信頼性**: CODEMAP 更新処理は失敗時にバックアップへロールバックする（既存 `REQ-2.1` 継承）。  
- **互換性**: スキーマ変更は `schema_version` と `CHANGELOG` で明示し、旧バージョンの `update_codemap_foundation.py` 実行時には互換モードで動作する。  
- **性能**: 自動監査は CI（`make test`）に追加して 60 秒以内に完了する。  
- **監査証跡**: メトリクス算出結果と修正履歴を `reports/` に保存し、最低 12 か月保持する。

---

## 5. 実装計画（段階導入）

| フェーズ | 目的 | 主タスク | 判定基準 |
| --- | --- | --- | --- |
| Phase 1 (短期) | スキーマ拡張最小実装 | メタ項目追加・透過更新・CI 警告導入 | CODEMAP 自動更新が schema_version=1.1 を扱える |
| Phase 2 (中期) | 監査とレポート | `codemap_foundation_audit.py` 実装、CI 組み込み、violation 追記 | 準拠率レポート生成・CI ブロックが稼働 |
| Phase 3 (中期) | 開発体験整備 | スキャフォールド改修、PR テンプレート反映 | 新規ユースケース生成で共通基盤が自動注入 |
| Phase 4 (長期) | 例外縮小 | MCP 例外期限管理・月次レビュー運用 | 期限切れ例外が自動通報される |

各フェーズの切り戻しは `schema_version` と `CHANGELOG` で管理し、Phase 1 完了後に以降のリリースを段階的に投入する。

---

## 6. 運用とガバナンス

- **ロール**  
  - `CODEMAP Maintainer`: スキーマ管理、CHANGELOG 記載、例外期限レビュー  
  - `Dev Productivity`: 監査スクリプト保守、CI 連携、レポート配信  
  - `Feature Teams`: スキャフォールド利用、PR チェックリスト確認、準拠率改善アクション
- **レビューサイクル**  
  - 月次: CODEMAP スキーマ差分レビューと例外期限の更新  
  - 四半期: 準拠率レポート評価と改善ロードマップ策定
- **インシデント対応**  
  - 自動更新失敗時はバックアップを復元し、原因を `logs/codemap_update/YYYYMMDD.log` に記録  
  - スキーマ互換性エラーは `schema_version` 差分を確認し、必要に応じてツールを更新

---

## 7. 既存実装との整合

- `scripts/tools/update_codemap_foundation.py` を本仕様に合わせ改修し、未知フィールド透過・schema_version ハンドリングを実装。  
- `docs/guides/logging_guidelines.md` など関連ドキュメントへのリンクは CODEMAP の `recipes` と `integration_notes` から参照可能にする。  
- 既存 `forbidden_patterns` の検出結果は監査スクリプトで再利用し、重複報告を抑止する。

---

## 8. テスト要件

- **単体テスト**: メタ項目追加処理、schema_version 差分処理、監査メトリクス計算。  
- **統合テスト**: Git Hook 経由で CODEMAP 更新→監査→レポート生成の E2E。  
- **回帰テスト**: 既存禁止パターン検出（console 再生成など）と新監査が競合しないことを確認。

---

## 9. 成功指標

- CODEMAP スキーマ更新成功率 99%以上（直近 30 日間）。  
- 共通基盤準拠率（Console/Logger/PathService）が 1 四半期で既定閾値 +5% 改善。  
- 例外期限切れ件数が四半期レビュー時に 0 件。  
- スキャフォールド利用案件で共通基盤未導入コードレビュー指摘件数が 50% 以上減少。

---

## 10. 関連資料

- `CODEMAP.yaml`（最新版）  
- `CODEMAP_dependencies.yaml`（依存関係レポート）  
- `docs/guides/logging_guidelines.md`（ログ出力方針）  
- `B20 開発作業指示書`

---

## 11. 更新履歴

| 日付 | 版 | 変更内容 | 担当 |
| --- | --- | --- | --- |
| 2025-10-13 | 1.1 | スキーマ拡張、監査統合、段階導入計画を追加 | 開発基盤チーム |
| 2025-08-09 | 1.0 | 初版作成（自動更新機能要件定義） | Claude Code実装チーム |

