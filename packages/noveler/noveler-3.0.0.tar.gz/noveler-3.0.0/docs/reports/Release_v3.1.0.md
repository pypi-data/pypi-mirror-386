# Release v3.1.0 — Progressive Check dry_run拡張・セッション自動再開・テスト安定化

リリース日: 2025-09-27
対象: Progressive Check/LangGraph, パフォーマンス監視, テスト運用/ドキュメント

## 🎯 ハイライト

- Progressive Check: dry_run 拡張（擬似スコア返却・入出力/manifest生成）
- セッション自動再開と completed_steps マージ補助
- PerformanceProfiler: ネスト対応（デコレータ多段呼び出しでの RuntimeError 解消）
- FileIOOptimizer: `batch_read(...)` を追加
- パフォーマンス最適化ユーティリティの軽量フォールバック（psutil/PyYAML 不在でも基本動作）
- pytest-timeout を signal 方式に統一し、ローカル安定化ガイドを追加
- A32/ガイド/MCP文書の更新（挙動・設定・トラブルシュートを明記）

## ✅ 追加・変更

### Progressive Check（LangGraph）
- `execute_check_step(..., dry_run=true)` 時に:
  - 依存関係をバイパスして擬似結果 `execution_result.overall_score` を返却。
  - `*_input.json`/`*_output.json`/`manifest.json` を `.noveler/checks/<session_id>/` に生成。
- セッション自動再開: `.noveler/checks/EP{episode}_YYYYMMDDHHMM` を自動検出して再開。
- 直近セッションの `completed_steps` を現行へマージする救済ロジックを追加。

### パフォーマンス監視
- PerformanceProfiler をネスト対応化（内部でセッションスタック管理）。
- デコレータ多段構成での `Profiling session has not been started` を解消。

### I/O最適化
- `FileIOOptimizer.batch_read(paths)` を追加（`[(Path, content, ok), ...]` を返却）。
- ComprehensivePerformanceOptimizer に軽量フォールバック（psutil/PyYAML 不在時は tracemalloc ベース等）。

### テスト運用・設定
- `pyproject.toml` の pytest 既定に signal タイムアウトを適用。
- `scripts/run_pytest.py` で `PYTEST_TIMEOUT_METHOD=signal` を既定化。
- ローカル安定化ガイドを各ドキュメントに追記（-n=1/2 推奨、重いプラグイン無効化オプション）。

## 🧩 ドキュメント更新
- `docs/mcp/progressive_check_api.md`: LangGraph必須、session_id/ログ出力、dry_run仕様、自動再開。
- `docs/A32_執筆コマンドガイド.md`: 既存ファイル衝突時は確認要求（auto_confirm注意）。
- `docs/claude_code/noveler_config.md`: ~/.claude.json の実例と dist ラッパーのトラブルシュート。
- `docs/B33_MCPツール統合ガイド.md`: 運用ポイントの明確化、dry_run のふるまい。
- `docs/guides/{developer_guide,quick_start}.md`, `docs/B20_Claude_Code開発作業指示書.md`: テスト安定化の既定・対処集。
- `requirements/README.md`: LangGraph必須（Progressive Check）と pytest 設定の補足。

## 🐛 主な修正
- A31 自動修正 E2E の監視ネストエラーを解消。
- Progressive Check 復旧ユニット/E2E の dry_run スコア・入出力不足を解消。

## 互換性
- API 互換性: 保持（dry_run の返却内容が拡張）。
- 実行環境: signal タイムアウトを既定化（WSL2 などでの安定性向上）。

## 移行ガイド
- E2E で `final_quality_score` を評価している場合は、dry_run でも 0 にならないことを前提に検証を更新してください。
- ローカル検証で `can't start new thread` 等が出る場合は `-n=1`（または `-n=2`）とし、`PYTEST_TIMEOUT_METHOD=signal` に変更してください。

