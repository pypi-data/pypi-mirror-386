# Release v2.2.3 (2025-09-21)

## MCP接続安定化 🔧

**背景**: WSL環境でのMCPサーバー接続における環境依存問題があり、Claude Codeとの連携が不安定でした。

**実装**:
- Serena依存の削除: WSL環境でインストール問題があったSerenaサーバーを設定から除去
- Novelerサーバー最適化: 安定したNovelerサーバーのみを使用する構成に変更
- 軽量出力の強化: `MCP_LIGHTWEIGHT_DEFAULT=1`でB20ポリシー準拠の軽量出力を有効化
- 設定ファイル更新: `codex.mcp.json`と`.mcp/config.json`でSerena設定削除、安定化

**解決した問題**:
- WSL環境でのSerenaコマンド未インストール問題
- MCPサーバー起動時の依存関係エラー
- Claude Code環境での軽量出力制御

## プロンプト保存機能強化

主要変更
- feat: `PlotGenerationUseCase` が `generate_episode_plot_auto` 実行時に前話プレビューの `preview/quality/source/config` 情報を `reference_sections` として保存するよう拡張し、後続プロンプトや CLI で再利用しやすくしました。
- test: `_save_enhanced_prompt` を直接検証するユニットテストを追加し、前話メタデータが確実に保存リクエストへ転記されることを保証しました。
- test: ProgressiveCheckManager の状態ファイル仕様変更に追随するようユニットテストを修正し、セッションIDベースのディレクトリ構成を検証します。
- chore: `tests/conftest.py` の `import os` インデント崩れを修正して Python 3.10 でも安定動作するようにし、TODO の該当項目を完了扱いに更新しました。

背景
- プロンプト保存時に前話メタデータが失われており、品質記録や CLI から参照できないというフィードバックがあったため、`content_sections` に過去情報を残す必要がありました。
- ProgressiveCheckManager の実装がセッションIDベースのファイル命名へ移行していたものの、テストが旧仕様のままで定期的に赤くなる状況でした。

実装ハイライト
- `src/noveler/application/use_cases/plot_generation_use_case.py` で `content_sections` を組み立てる処理を整理し、前話の `preview_text` や `score` も `reference_sections` に含めるようにしました。
- 新しいユニットテストではテンプレートサービスと保存ユースケースをモンキーパッチし、生成される `PromptSaveRequest` を直接検証しています。
- ProgressiveCheckManager テストはセッションIDベースのディレクトリ／ファイルを期待するよう更新し、実装と乖離していたASSERTを修正しました。
- conftest の import 修正と TODO の整理で、Python 3.10 環境でもテストが確実に動作するよう整備しました。

品質確認
- `python3 -m pytest tests/unit/application/use_cases/test_plot_generation_preview_context.py`
- `python3 -m pytest tests/unit/domain/services/test_progressive_check_manager.py`
- 追加で `test_check_command_integration` / `test_codemap_quality_gate_integration` / `test_enhanced_prompt_save_integration` の主要ケースを個別実行し、リグレッションを確認済みです。

移行影響
- 既存の API や CLI フラグに変更はありません。保存される YAML に `reference_sections` が追加されますが、後方互換です（新キーが存在しない場合は何も変わりません）。
