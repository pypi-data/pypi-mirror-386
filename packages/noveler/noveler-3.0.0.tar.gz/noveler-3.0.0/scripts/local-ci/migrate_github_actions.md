# GitHub Actionsワークフローのローカル実装移行計画

## 移行方針

GitHub Actionsで実行していた品質チェックをローカルGitフック + cronジョブで実現します。

## 1. Gitフック拡張 (即座実行)

### pre-commit (品質ゲート)
```bash
# 既存: ~/.git-noveler/hooks/pre-commit に追加
- Ruff (linting)
- mypy (型チェック)
- DDD準拠性チェック
- インポートチェック
```

### commit-msg (メッセージ検証)
```bash
# 既存: ~/.git-noveler/hooks/commit-msg に追加
- 3コミットサイクル検証
- メッセージフォーマット検証
```

### post-commit (テスト・レポート)
```bash
# 既存: ~/.git-noveler/hooks/post-commit に追加
- ユニットテスト実行
- カバレッジレポート生成
- LLM要約生成
```

## 2. 定期実行 (cronジョブ)

### 日次 (深夜2時)
```bash
# ~/.crontab または /etc/cron.d/ に追加
0 2 * * * cd /path/to/project && make daily-checks
```

### 週次 (日曜21時、既存)
```bash
# 既存のアーカイブクリーンアップ + 品質レポート
0 21 * * 0 cd /path/to/project && make weekly-full-check
```

## 3. Makefileターゲット

### 即座実行用
```makefile
# 品質チェック統合
quality-full: lint type-check ddd-check import-check test

# DDD準拠性
ddd-check:
	python scripts/tools/check_tdd_ddd_compliance.py --level=strict

# インポートチェック
import-check:
	python scripts/tools/import_validator.py

# 3コミット検証
three-commit-check:
	python scripts/tools/three_commit_validator.py
```

### 定期実行用
```makefile
# 日次チェック
daily-checks: quality-full coverage-report

# 週次統合チェック
weekly-full-check: archive-cleanup quality-full coverage-report system-health
```

## 4. 移行対象ワークフロー詳細

| GitHub Actions | ローカル実装 | 実行タイミング |
|---|---|---|
| python-ci.yml | pre-commit + post-commit | コミット時 |
| quality-gate.yml | pre-commit | コミット時 |
| ddd-compliance.yml | make ddd-check | pre-commit |
| three_commit_enforcement.yml | commit-msg | コミット時 |
| architecture-enforcement.yml | make arch-check | 日次cron |
| coverage_improvement.yml | post-commit | コミット時 |
| import-check.yml | pre-commit | コミット時 |
| spec_test_consistency.yml | make spec-check | 日次cron |
| update_codemap.yml | post-commit | コミット時 |

## 5. 実装順序

1. ✅ **Makefileターゲット作成** - 各チェックの統合
2. ✅ **Gitフック拡張** - 既存フックに機能追加
3. ✅ **cronジョブ設定** - 定期実行スケジュール
4. ✅ **ログ・レポート** - 実行結果の可視化
5. ✅ **.github削除** - 不要なワークフロー除去

## 6. 実装されたスクリプト

### セットアップスクリプト
- `scripts/setup/migrate_to_local_ci.sh` - 統合移行スクリプト（推奨）
- `scripts/setup/setup_local_ci_cron.sh` - cronジョブ設定
- `scripts/setup/integrate_enhanced_git_hooks.sh` - Gitフック統合

### 実行スクリプト
- `scripts/local-ci/enhanced_pre_commit_secure.sh` - セキュリティ強化版pre-commitチェック
- `scripts/local-ci/enhanced_commit_msg.sh` - 拡張commit-msgチェック
- `scripts/local-ci/enhanced_post_commit.sh` - 拡張post-commitチェック
- `scripts/local-ci/remove_github_directory.sh` - .github削除

### 品質チェックツール
- `scripts/tools/check_tdd_ddd_compliance_simple.py` - DDD準拠性チェック
- `scripts/tools/import_validator_simple.py` - インポート検証

### 拡張機能（Codexレビュー対応）
- `scripts/local-ci/enhanced_monitoring.sh` - 監視・ログ・ヘルス機能
- `scripts/local-ci/incremental_check.sh` - インクリメンタル品質チェック

### 使用方法
```bash
# 一括移行（推奨）
bash scripts/setup/migrate_to_local_ci.sh

# 個別セットアップ
bash scripts/setup/setup_local_ci_cron.sh
bash scripts/setup/integrate_enhanced_git_hooks.sh
bash scripts/local-ci/remove_github_directory.sh
```

## 6. メリット

- **即座のフィードバック**: pre-commitでコミット前にエラー検出
- **ローカル完結**: ネットワーク不要
- **柔軟性**: 必要に応じてスキップ可能
- **軽量**: 必要な分だけ実行
- **セキュリティ強化**: コマンドインジェクション対策済み
- **インテリジェント**: 変更量に応じた最適化
- **監視機能**: エラートラッキング・パフォーマンス測定

## 7. 拡張機能

### インクリメンタルチェック
```bash
make check-smart       # 自動選択（インクリメンタル/フル）
make check-incremental # 変更ファイルのみチェック
```

### 監視・ヘルス機能
```bash
make health-check      # システムヘルス確認
make health-report     # 包括的レポート生成
```

### ログ・レポート
- エラーログ: `temp/ci/logs/errors.log`
- パフォーマンスログ: `temp/ci/logs/performance.log`
- ヘルスレポート: `temp/ci/logs/health_report.md`

## 8. 注意点

- **Gitフック迂回**: `git commit --no-verify` で回避可能
- **環境依存**: Python環境・依存関係が必要
- **実行時間**: 重いチェックは pre-push に移動推奨
- **ログ管理**: 1MB超過時に自動ローテーション