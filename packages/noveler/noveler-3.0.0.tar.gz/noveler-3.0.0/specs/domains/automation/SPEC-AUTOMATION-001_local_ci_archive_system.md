# SPEC-AUTOMATION-001: ローカルCI・アーカイブ統合自動化システム

## 概要

GitHub Actionsからローカル実行へのCI/CD移行と、アーカイブ・クリーンアップ自動化を統合したシステムの仕様書。

## 背景

- 本プロジェクトはローカルGit管理のため、GitHub Actionsが実行されない
- 週次アーカイブクリーンアップの手動実行が運用負荷となっている
- セキュリティ脆弱性のないローカルCI実装が必要

## 要件

### 機能要件

#### FR-001: セキュリティ強化Gitフック
- null終端ファイル処理によるコマンドインジェクション対策
- 3コミットサイクル検証
- メッセージフォーマット検証
- テスト実行、カバレッジレポート生成

#### FR-002: インクリメンタル・スマートチェック
- 変更量に応じた最適化（6時間閾値）
- ステージング機能（変更ファイル数による段階的チェック）
- パフォーマンス測定とログ出力

#### FR-003: 包括的監視・ヘルス機能
- エラートラッキングとパフォーマンス測定
- システムヘルスチェック（依存関係、設定、権限）
- 自動ログローテーション（1MB超過時）
- ヘルスレポート生成（Markdown形式）

#### FR-004: 代替実装ツール
- DDD準拠性チェッカー（`check_tdd_ddd_compliance_simple.py`）
- インポート検証ツール（`import_validator_simple.py`）

#### FR-005: アーカイブ・クリーンアップ自動化
- 週次cronジョブによる自動実行（日曜21時）
- `*.disabled.json`/`*.backup`ファイルの規約フォルダ移動
- ドライラン機能

### 非機能要件

#### NFR-001: セキュリティ
- コマンドインジェクション対策（null終端処理）
- ファイルパスのサニタイゼーション
- 権限チェック

#### NFR-002: パフォーマンス
- インクリメンタルチェックによる実行時間短縮
- 段階的チェック（変更量による最適化）
- ログローテーションによるディスク容量管理

#### NFR-003: 可用性
- フォールバック機能
- エラーハンドリング
- 復旧機能

## アーキテクチャ

### コンポーネント構成

```
scripts/
├── local-ci/
│   ├── enhanced_pre_commit_secure.sh      # セキュリティ強化pre-commit
│   ├── enhanced_commit_msg.sh             # commit-msg検証
│   ├── enhanced_post_commit.sh            # post-commit処理
│   ├── enhanced_monitoring.sh             # 監視・ヘルス機能
│   ├── incremental_check.sh               # インクリメンタルチェック
│   └── remove_github_directory.sh         # GitHub削除
├── setup/
│   ├── migrate_to_local_ci.sh            # 統合移行スクリプト
│   ├── setup_local_ci_cron.sh            # cronジョブ設定
│   ├── integrate_enhanced_git_hooks.sh    # Gitフック統合
│   └── setup_weekly_cleanup_cron.sh       # 週次クリーンアップ設定
└── tools/
    ├── archive_disabled_configs.py        # アーカイブツール
    ├── check_tdd_ddd_compliance_simple.py # DDD準拠性チェック
    └── import_validator_simple.py         # インポート検証
```

### Makefileターゲット

```makefile
# 品質チェック統合
quality-full: lint ddd-check import-check test

# インクリメンタル・スマートチェック
check-smart: # 自動選択（インクリメンタル/フル）
check-incremental: # 変更ファイルのみ

# 監視・ヘルス
health-check: # システムヘルス確認
health-report: # 包括的レポート生成

# アーカイブ
archive-cleanup: # 実行
archive-cleanup-dry-run: # ドライラン
```

## インターフェース仕様

### セキュリティ強化Gitフック

#### enhanced_pre_commit_secure.sh
```bash
# 入力: git diff --cached --name-only --diff-filter=AM -z
# 出力: 成功=0, 失敗=1
# エラーハンドリング: set -euo pipefail
```

#### enhanced_commit_msg.sh
```bash
# 入力: $1 (commit message file)
# 検証: 3コミットサイクル、フォーマット
# 出力: 成功=0, 失敗=1
```

### インクリメンタルチェック

#### incremental_check.sh
```bash
# 入力: 変更ファイルリスト
# 閾値: 6時間（フル/インクリメンタル判定）
# ステージング: 変更数によるチェック段階切替
# 出力: パフォーマンス測定結果、ログ
```

### 監視・ヘルス

#### enhanced_monitoring.sh
```bash
# 機能:
#   - エラートラッキング
#   - パフォーマンス測定
#   - システムヘルスチェック
#   - ログローテーション（1MB超過時）
# 出力: temp/ci/logs/ 配下にログファイル
```

## データ仕様

### ログ形式

#### エラーログ
```
[TIMESTAMP] [LEVEL] [COMPONENT] MESSAGE
```

#### パフォーマンスログ
```json
{
  "timestamp": "2025-09-27T21:00:00Z",
  "component": "incremental_check",
  "duration_ms": 1234,
  "files_processed": 15,
  "optimization": "incremental"
}
```

#### ヘルスレポート
```markdown
# システムヘルスレポート
## 依存関係チェック
- Python: ✅ 3.9.0
- Git: ✅ 2.40.0
## 設定チェック
- .git-noveler/: ✅ 存在
## 権限チェック
- scripts/実行権限: ✅ OK
```

## セキュリティ考慮事項

### コマンドインジェクション対策
```bash
# 脆弱: スペースを含むファイル名で失敗
git diff --cached --name-only | while read file; do
    process "$file"  # 危険
done

# 安全: null終端処理
git diff --cached --name-only -z | while IFS= read -r -d '' file; do
    process "$file"  # 安全
done
```

### ファイルパス検証
```bash
# サニタイゼーション
if [[ "$file" =~ ^[a-zA-Z0-9._/-]+$ && -f "$file" ]]; then
    process_file "$file"
fi
```

## 運用仕様

### 設定・セットアップ

#### 統合移行
```bash
# ワンコマンド移行
bash scripts/setup/migrate_to_local_ci.sh
```

#### 個別設定
```bash
# cronジョブ設定
bash scripts/setup/setup_local_ci_cron.sh

# Gitフック統合
bash scripts/setup/integrate_enhanced_git_hooks.sh

# 週次クリーンアップ
bash scripts/setup/setup_weekly_cleanup_cron.sh
```

### 日常運用

#### 手動実行
```bash
# 品質チェック
make quality-full

# スマートチェック
make check-smart

# ヘルスチェック
make health-check

# アーカイブクリーンアップ
make archive-cleanup-dry-run  # 確認
make archive-cleanup          # 実行
```

#### 自動実行
- pre-commit: 品質チェック
- commit-msg: メッセージ検証
- post-commit: テスト・レポート生成
- cron (日曜21時): アーカイブクリーンアップ

### 監視・メンテナンス

#### ログ確認
```bash
# エラーログ
tail -f temp/ci/logs/errors.log

# パフォーマンスログ
tail -f temp/ci/logs/performance.log

# ヘルスレポート
cat temp/ci/logs/health_report.md
```

#### トラブルシューティング
- Gitフック迂回: `git commit --no-verify`
- ログローテーション: 1MB超過時自動実行
- 復旧: バックアップからの復元機能

## テスト仕様

### 単体テスト
- 各スクリプトの正常系・異常系
- セキュリティ機能の検証
- パフォーマンス測定

### 統合テスト
- Gitフック連携
- cronジョブ実行
- Makefileターゲット

### セキュリティテスト
- コマンドインジェクション耐性
- ファイルパス操作安全性
- 権限エスカレーション防止

## 実装履歴

### 2025-09-27: 初期実装完了
- [x] セキュリティ強化Gitフック実装
- [x] インクリメンタルチェック機能実装
- [x] 監視・ヘルス機能実装
- [x] 代替実装ツール作成
- [x] Makefile拡張
- [x] 統合セットアップスクリプト実装
- [x] ドキュメント更新
- [x] GitHub Actions削除・バックアップ

## 関連仕様書

- SPEC-QUALITY-001: A31チェックリスト自動修正システム
- SPEC-901-DDD-REFACTORING: DDD準拠リファクタリング
- SPEC-CONFIG-002: ファイルテンプレート管理

## 変更履歴

| バージョン | 日付 | 変更内容 |
|------------|------|----------|
| 1.0.0 | 2025-09-27 | 初版作成・実装完了 |