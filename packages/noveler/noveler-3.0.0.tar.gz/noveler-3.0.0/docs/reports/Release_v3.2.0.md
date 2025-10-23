# Release v3.2.0 - Quality Gate Workflow 完成とローカルCI統合

**リリース日**: 2025-09-28
**対象**: Quality Gate Workflow 最終形、TenStage 執筆パイプライン、高信頼ローカルCI基盤、DDD整備仕上げ
**影響範囲**: Quality チェック CLI/MCP、執筆ユースケース、CI/運用自動化、リポジトリ構造

## 🎯 主要トピック

### 1. Quality Gate Workflow 実装完了
- Gate B/C 閾値・出力先を `quality_gate_defaults.yaml` 経由で一元化。
- `run_quality_checks_ndjson.py` / RunQualityChecksTool が Gate メタデータを返却し、CI 連携が容易に。
- Gate C (Editorial 12-step checklist) 判定を自動化し、NDJSON に判定結果と失敗理由を添付。
- CLI ラッパー (`bin/check-core`, `bin/check-all`) が既定値を自動注入し、メタデータ差異を吸収。

### 2. TenStage 執筆パイプライン Phase 2/3
- `TenStageProgressUseCase` と `TenStageEpisodeWritingUseCase` を統合し、18 ステップ拡張ワークフローを支える進捗管理を追加。
- Phase 2-A/B/C で既存データフローを整理し、チャプター/エピソード単位の整合性を確保。
- 旧来のバックワード互換コードを整理し、ユニバーサル CLI/MCP パイプラインへ統一。

### 3. ローカル CI & アーカイブ自動化
- GitHub Actions からローカル CI への完全移行 (`make ci-smoke`, `scripts/ci/*`)。
- アーティファクト検証・受入 (`artifact acceptance validation`) を追加し、LLM 出力破損を早期検知。
- cron ベースのアーカイブクリーンアップ自動化 (`scripts/tools/cron_archive_cleanup.py`)。
- Markdown メタデータ検証ツールを導入し、ドキュメント品質を CI で担保。

### 4. MCP/CLI アーキテクチャ刷新
- `noveler` CLI を MCP ランタイム経由で実行する薄いラッパーに変更 (`noveler mcp call ...`)。
- Legacy alias を全廃し、SPEC-AUTOMATION-001 が定義する MCP コマンドセットへ移行。
- CLI ドキュメントを再生成し、 smoke テストを追加 (`bin/cli-smoke`)。

### 5. DDD/レイヤー依存性の仕上げ
- Domain → Application 逆流や Presentation 直参照を全て解消 (`fix(arch)` シリーズ)。
- PLC0415 (関数スコープ import) の残存箇所を排除し、import discipline を強化。
- ルート配下の補助スクリプトを `scripts/{migration,tests,tools}` に再配置し、ルートをクリーンアップ。

## 🔧 実装詳細

### Quality Gate
- `scripts/ci/run_quality_checks_ndjson.py` が Gate C 判定・NDJSON enrichment を実装。
- `quality_gate_processor` / `message_service` が `ConsoleServiceAdapter` を注入し、統一ロガーに準拠。
- `tests/unit/scripts/test_check_runners_minimal.py` を更新し、既定値注入・Gate C 判定をカバー。

### TenStage / A30
- `TenStageProgressUseCase`, `TenStageEpisodeWritingUseCase`, `TenStageProgressService` を段階実装。
- Phase 2/3 用テンプレート・ユースケースの同期調整を完了。
- A30 マイグレーション Phase 2-C / Phase 3 を締め、旧データフローとの互換性を保持しつつ最終フェーズへ移行。

### CI / Automation
- `scripts/ci/run_local_ci.py`, `scripts/ci/archive_cleanup.py`, `make ci-smoke` を追加。
- `acceptance/validators` にアーティファクト検証ロジックを追加し、アーカイブ投入前に自動チェック。
- `docs/migration/local_ci_from_github.md` を新設し、運用移行手順を共有。

### CLI & Docs
- `noveler` コマンドが MCP runtime を直接呼び出す構造へ変更 (`noveler mcp call ...`)。
- `docs/mcp/tools_usage_best_practices.md`, `docs/references/shared_components_catalog.md` を CLI ラッパー新仕様に合わせて更新。
- SPEC-AUTOMATION-001 を追加し、ローカル CI とアーカイブポリシーを正式化。

### DDD/Infrastructure 整備
- Domain 層のユースケース/サービスが `domain_console` + `ILogger` に統一 (
  `quality_gate_service`, `langsmith_*` など)。
- Application 層から `presentation.shared.shared_utilities` 参照を除去し、アダプター経由に統一。
- リポジトリ構造を `scripts/` 下へ整理し、OneDrive 由来の暫定ファイルを `make tidy-root` でクリーン化。

## 🧪 テスト & 品質
- Domain/CLI/MCP を横断する 30+ 件の新規ユニット／統合テストを追加。
- CLI smoke テスト (`pytest tests/smoke/test_cli_mapping.py`) を導入。
- `tests/unit/infrastructure/persistence/test_plot_viewpoint_repository_error_handling.py` など、パス依存テストのテンポラリディレクトリ化を完了。

## 📚 ドキュメント
- `docs/B35_統一ロギングシステムガイド.md` を刷新し、pre-commit 品質ゲートや移行手順を追記。
- `README.md` に統一ロガー品質ゲートと MCP ラッパー概要を追加。
- `CHANGELOG.md` を v3.2.0 項で更新（本リリース概要を反映）。

## ⚠️ 移行と注意事項
1. **Quality Gate**: Gate C 判定導入により、編集チェックリスト (`reports/editorial_checklist.md`) を最新化してから CI を流すこと。
2. **CLI**: `noveler` コマンドのラッパー変更に伴い、ローカルスクリプトで `python src/...` を直接叩いていた場合は `noveler mcp call` へ移行する。
3. **CI**: GitHub Actions は廃止。ローカル実行 (`make ci-smoke`) と cron 連携に切り替わるため、スケジュール設定とローカル権限を確認すること。
4. **リポジトリ構造**: ルート直下で扱っていた補助スクリプトは `scripts/` 以下へ移動済み。古いパスに依存する自動化処理は更新が必要。

---

これらの更新により、Quality Gate（Gate B/C）の本番運用が可能になり、執筆パイプラインとローカルCIが統合されました。DDD 準拠のアーキテクチャ整備も完了し、今後の拡張を安全に進められる基盤が整っています。
