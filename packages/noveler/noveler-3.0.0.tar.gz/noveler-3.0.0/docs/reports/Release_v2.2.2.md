# Release v2.2.2 (2025-09-21)

## 主要変更
- feat: TestResultAnalysisTool に差分分析・エラーグルーピング・階層コンテキストを導入し、pytest-json-report からLLMに渡すメタデータの精度とトークン効率を改善しました。
- feat: `TestResultCacheService` を追加し、前回のテスト結果を管理ディレクトリ配下に永続化して差分分析の自動参照を可能にしました（保持上限は既定5件、設定可）。
- chore: ToolRequest の `episode_number` を任意入力化し、非エピソード系ツールでも `require_episode_number` フラグで安全に実行できるようにしました。
- docs: レガシーCLI（`bin/novel`）廃止に伴う移行ガイドを新設し、運用ドキュメントを `noveler` / MCP ワークフローに差し替えました。
- test: SPEC-TEST-001 のユニット/統合テストを14ケースに拡充し、フォールバック提案・`extract_common` 戦略・NullLoggerフォールバックを検証しました。

## 背景
- 旧 `bin/novel` CLI を前提とした資料やGitフックが散見されており、統合CLI `noveler` への移行が完了していませんでした。
- TestResultAnalysisTool は前回結果との比較が手動指定前提だったため、連続実行時の改善率可視化やキャッシュ最適化が課題でした。

## 実装ハイライト
- `src/mcp_servers/noveler/tools/test_result_analysis_tool.py` に `enable_delta_analysis` / `enable_error_grouping` / `context_detail_level` / `store_results` / `max_cache_history` を追加し、解析結果メタデータに `delta_analysis` と `error_groups` を出力。
- `src/noveler/infrastructure/services/test_result_cache_service.py` を新設し、キャッシュ書き込み時に 1MB 超過を警告する監視を導入。
- Git フック (`src/noveler/infrastructure/repositories/git_hook_repository.py`) を `noveler` ベースのコマンドに更新し、プロットバージョン管理は `python -m noveler.infrastructure.git.hooks.plot_version_post_commit` を利用。
- `docs/B50_システム運用基礎.md` を `noveler` ワークフローに合わせて再編集し、旧CLIの手順は「レガシーCLI資料（参照のみ）」セクションへ隔離。
- `docs/migration/novel_to_noveler.md` を新規作成し、コマンド置換表、Gitフックの更新手順、テスト計画を整理。

## 品質確認
- `pytest tests/unit/domain/services/test_automatic_recommendation_generator.py`
- `pytest tests/integration/test_nih_prevention_integration.py`
- `pytest tests/unit/mcp_servers/noveler/tools/test_enhanced_test_result_analysis.py`

## 移行影響
- 旧 `bin/novel` を参照するスクリプトはエラーになります。`docs/migration/novel_to_noveler.md` の手順に従い、`./bin/noveler` または MCP ツール呼び出しに置き換えてください。
- Git フックを再生成する場合は、`python scripts/setup-git-aliases.sh` を再実行するか、`noveler` ベースのテンプレートを手動適用してください。
- TestResultAnalysisTool の入力スキーマに `store_results` / `max_cache_history` を追加したため、ツールを直接呼び出す場合は新しいフラグを許容するようクライアントを更新してください。
