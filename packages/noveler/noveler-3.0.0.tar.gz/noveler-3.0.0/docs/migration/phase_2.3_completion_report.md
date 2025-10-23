# Phase 2.3 Completion Report: Repository Strict Mode Rollout

**Date**: 2025-10-11  
**Owner**: Codex  
**Related Phases**: Option A – Fallback Removal (Phase 2.1 / 2.2 / 2.3)

---

## 1. 概要 (Summary)

- Repository 層（ファイルベースリポジトリ）の暗黙フォールバックを排除し、strict mode 管理下に移行した。
- `StrictModeConfig` に `repository_service` を追加し、`NOVELER_STRICT_REPOSITORY` で挙動を制御できるようになった。
- ファイルリポジトリは明示的な `base_dir` 指定が必須となり、WARNING モードでは警告ログと安全なデフォルト、ERROR モードでは例外化を実施。
- ドメイン例外 `RepositoryFallbackError` / `RepositoryDataError` を導入し、strict mode 違反や不正データを可視化。

---

## 2. 実装内容 (Changes)

| 項目 | 内容 |
|------|------|
| Strict mode 拡張 | `StrictModeConfig` に repository レベルを追加し、`.env.example` / `CLAUDE.md` を更新。 |
| 例外クラス | `RepositoryFallbackError`（フォールバック禁止）、`RepositoryDataError`（データ不整合）を追加。 |
| FileEpisodeRepository | `base_dir` を strict-aware に解決。ERROR でフォールバック禁止、WARNING でログ警告。 |
| FileOutboxRepository | `base_dir` 必須化、JSON バリデーション、WARNING 時の安全なデフォルト、ERROR 時の即例外。 |
| YamlProjectInfoRepository | Path Service 取得失敗を strict mode に準拠させ、フォールバック可否を制御。 |
| 呼び出し側調整 | CLI / MCP / MessageBus 統合で明示的な保存ディレクトリを指定するよう改修。 |
| テスト | 新規ユニットテスト `tests/unit/infrastructure/adapters/test_repository_strict_mode.py` を追加。 |
| ドキュメント | `docs/migration/phase_2.3_design.md` と TODO.md を更新し、Phase 2.3 タスク状況を反映。 |

---

## 3. インパクトとリスク (Impact & Risks)

- **運用上の利点**: 暗黙ディレクトリ作成がなくなり、環境差異や OneDrive などでの意図せぬフォールバックが防止される。
- **BREAKING 変更**: 既存コードが `FileEpisodeRepository()` など引数なしで呼び出すと strict mode ERROR では `RepositoryFallbackError` となる。
- **データ欠損**: 既存 JSON に `payload` / `attempts` などが欠けている場合、ERROR モードで `RepositoryDataError` が発生。WARNING モードでは警告ログで検出可能。
- **ログ監視**: `NOVELER_STRICT_REPOSITORY=warning` 期間中に `[repository]` ログを監視し、本番切替前に欠損データを洗い出す必要がある。

---

## 4. テスト結果 (Testing)

| カテゴリ | 結果 |
|----------|------|
| Unit | `bin/test tests/unit/infrastructure/adapters/test_repository_strict_mode.py` ✅ |
| Integration | 主要統合テストは Phase 3 着手前に WARNING モードでスモーク予定（ログ監視を兼ねる）。 |
| Diagnostics | `scripts/diagnostics/test_strict_mode_warnings.py` / `test_config_strict_mode.py` は既存の Path/Config レポートを維持、Repository 用チェックは Phase 3 で拡張予定。 |

---

## 5. フォローアップ (Follow-up / T8)

1. WARNING モードで 1 週間ログを観測し、フォールバック警告 (`[repository]`) が出ないことを確認。
2. 必要に応じて既存 JSON/YAML データの欠損を修正し、WARNING ログがゼロになった時点で TODO.md のモニタリング項目を更新。
3. Phase 3 着手までに CI / 本番環境の環境変数を `NOVELER_STRICT_* = error` へ切り替える準備を整える。
4. `docs/migration/fallback_inventory.md` の Repository セクションを “✅ 完了” に更新（别タスク）。

---

## 6. 参考リンク (References)

- `docs/migration/phase_2.3_design.md`
- `src/noveler/infrastructure/config/strict_mode_config.py`
- `src/noveler/infrastructure/adapters/file_outbox_repository.py`
- `src/noveler/domain/exceptions/base.py`
- `tests/unit/infrastructure/adapters/test_repository_strict_mode.py`

