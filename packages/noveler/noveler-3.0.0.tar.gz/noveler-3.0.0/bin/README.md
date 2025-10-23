# 実行スクリプト集

このディレクトリには、執筆支援ワークフローで利用する各種スクリプトと CLI ツールを配置しています。

## 📂 ファイル一覧

### プロジェクト管理ツール
| コマンド | 用途 | 説明 |
|---------|------|------|
| create-project | 新規プロジェクト作成 | 標準ディレクトリ構成と初期設定を生成 |
| install.sh | システム初期化 | 依存関係とローカル環境をまとめてセットアップ |
| setup-git-aliases.sh | Git 設定 | 推奨エイリアスの登録とフックセットアップ |

### ユーティリティスクリプト
| コマンド | 用途 | 説明 |
|-----------|------|------|
| test_commands.sh | テスト起動ラッパー | Makefile ターゲットを統一形式で実行（人手/自動兼用） |

### CLI ツール（本番用）
| コマンド | 用途 | 説明 |
|---------|------|------|
| noveler | 統合 CLI | `mcp-server` / `mcp call` / `check` / `write` の 4 コマンドを提供 |

## ⚠️ 注意事項
- 旧 `novel-*` 系サブコマンド（例: `novel-analyze`）はアーカイブ済みです。必要に応じて `backup/bin_deprecated_*` を参照してください。
- `noveler` CLI は 4 つのコマンドに統一されました：`mcp-server` / `mcp call` / `check` / `write`。
- 2025 年 8 月 3 日に CLI ラッパーを整理し、現行フローへ統合しました。
- カスタムスクリプトを追加する場合は `bin/` に配置し、この README に追記してください。

## 🚀 基本的な使い方
```bash
noveler --help                           # コマンド一覧を表示
noveler mcp-server --port 3000           # MCP サーバーを起動
noveler check 1 --auto-fix               # 第1話の品質チェック
noveler write 1 --dry-run                # 書き込みなしで 18 ステップを確認
```

## 🔁 よく使うコマンド例
```bash
# エピソード執筆
noveler write 5

# 品質チェック（ファイル指定）
noveler check 40_本文/第005話.md --exclude-dialogue

# 詳細レポート生成
noveler mcp call run_quality_checks '{"episode_number":5,"additional_params":{"format":"detail"}}'

# 改稿の自動適用
noveler mcp call polish_manuscript_apply '{"episode_number":5,"additional_params":{"stages":["stage2","stage3"],"dry_run":false}}'

# アーティファクト管理
noveler mcp call list_artifacts '{"episode_number":5}'
```

## 🧪 テスト実行（人手確認用）
```bash
# 代表的なターゲット
./bin/test_commands.sh test-fast

# レイヤー別テスト
./bin/test_commands.sh test-domain      # ドメイン層
./bin/test_commands.sh test-app         # アプリケーション層
./bin/test_commands.sh test-infra       # インフラ層

# 直近失敗の再実行・カバレッジ
./bin/test_commands.sh test-failed
./bin/test_commands.sh test-coverage

# まとめて状況確認
./bin/test_commands.sh
```

## 🗃️ Legacy スクリプトの扱い
- 旧 `noveler health` 派生スクリプト（doctor / quality-check / error-monitor など）は `backup/bin_deprecated_20250803_*/` に移動しました。
- 現在は `noveler mcp call run_quality_checks` や `noveler mcp call improve_quality_until` で同等の検査が可能です。

## 🔐 実行権限の設定
各スクリプトは初回利用前に実行権限を付与してください。
```bash
# すべてのスクリプトに実行権限を付与
chmod +x bin/*

# シェルスクリプトのみ対象にする場合
chmod +x bin/*.sh

# PATH へ追加（任意）
export PATH="/path/to/00_ガイド/bin:$PATH"
```

## ➕ スクリプト追加手順
1. 本ディレクトリに新しいスクリプトを配置する。
2. 必要であれば `chmod +x` で実行権限を付与する。
3. 本 README の該当セクションに用途と説明を追記する。
4. CLI から呼び出す場合は `noveler` へのサブコマンド追加ではなく、MCP ツールまたは専用スクリプトとして提供する。

## 📝 命名と実装ガイド
### シェル／Python スクリプト
- シェル: POSIX 準拠を優先し、必要に応じて `#!/usr/bin/env bash` を利用。
- Python: shebang を `#!/usr/bin/env python3` に統一し、モジュール内部で UTF-8 を明示。
- 引数チェックやエラー処理は最小限でも良いのでメッセージを出力する。

### CLI ツール
- `noveler` 本体の 4 コマンドを基準にし、追加機能は MCP ツール経由で提供する。
- 旧スタイルの `noveler-` プレフィックス付きサブコマンドは新規に追加しません。

## 🔗 関連ドキュメント
- [CLI ガイド](../CLIガイド.md)
- [B50_DDD 開発ガイド](../B_設定ガイド/B50_開発プロセス/B50_DDD開発ガイド.md)
- [TDD 実装チェックリスト](../scripts/templates/ddd_implementation_checklist.md)
