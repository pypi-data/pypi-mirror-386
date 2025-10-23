# 移行ガイド: novel → noveler

## 概要

2025年9月16日をもって、レガシーCLIコマンド `novel` は完全に廃止されました。今後はすべての機能を `noveler` コマンドまたはMCPサーバー経由で利用してください。

この文書では、既存の `novel` コマンドユーザーが新しい `noveler` システムへスムーズに移行するための手順を説明します。

## なぜ novel が廃止されたか

1. **アーキテクチャの近代化**: DDD（ドメイン駆動設計）準拠のクリーンアーキテクチャへの移行
2. **MCP対応**: Claude Code などの AI エージェントとの統合を強化
3. **保守性向上**: レガシーコードの削除により、コードベースの保守性と拡張性が向上
4. **統一インターフェース**: CLI と MCP サーバーの機能を統一し、一貫性のある操作体験を提供

## コマンドマッピング表

| 旧コマンド (novel) | 新コマンド (noveler) | 説明 |
|------------------|-------------------|------|
| `novel init` | `noveler project init` | プロジェクト初期化 |
| `novel write <ep>` | `noveler write <ep>` | エピソード執筆 |
| `novel check <ep>` | `noveler check <ep>` | 品質チェック |
| `novel analyze` | `noveler analyze` | 原稿分析 |
| `novel plot generate` | `noveler plot generate` | プロット生成 |
| `novel plot validate` | `noveler plot validate` | プロット検証 |
| `novel status` | `noveler status` | ステータス確認 |
| `novel polish <ep>` | `noveler polish <ep>` | 原稿推敲 |
| `novel test` | `noveler test` | テスト実行 |

### MCP サーバー経由の実行

Claude Code などの AI エージェントを使用する場合:

```bash
# MCPサーバーの起動
noveler mcp-server

# MCP経由でのツール実行例
noveler mcp call noveler_write episode_number=1
noveler mcp call noveler_check episode_number=1
```

## 段階的移行プロセス

### ステップ1: 環境の確認

```bash
# novelerコマンドが利用可能か確認
which noveler
noveler --version

# 旧コマンドが削除されていることを確認
which novel  # 何も表示されないはず
```

### ステップ2: エイリアスの更新（オプション）

シェル設定ファイル（`.bashrc`, `.zshrc` など）に `novel` エイリアスがある場合:

```bash
# 旧設定
alias novel='/path/to/novel'

# 新設定
alias novel='noveler'  # 互換性のため一時的に維持
```

### ステップ3: スクリプトの更新

自動化スクリプト内の `novel` コマンドを `noveler` に置換:

```bash
# すべてのスクリプトで置換を実行
find scripts/ -type f -name "*.sh" | xargs sed -i 's/bin\/novel/bin\/noveler/g'
find scripts/ -type f -name "*.py" | xargs sed -i 's/"novel /"noveler /g'
```

### ステップ4: 設定ファイルの移行

プロジェクト設定は自動的に引き継がれます:

- `.novelerrc.yaml`: プロジェクト設定（変更不要）
- `.novel_aliases`: 歴史的理由により維持（将来的に `.noveler_aliases` への改名を検討）

## FAQ

### Q: 既存のプロジェクトはそのまま使えますか？

A: はい、プロジェクト構造に変更はありません。単にコマンドを `novel` から `noveler` に変更するだけです。

### Q: MCPサーバーは必須ですか？

A: いいえ、通常のCLI使用には不要です。Claude Code などのAIエージェントと統合する場合のみ必要です。

### Q: エラー「command not found: novel」が出ます

A: 正常です。`novel` コマンドは削除されました。代わりに `noveler` を使用してください。

### Q: 古いドキュメントに `novel` の記載があります

A: 歴史的資料として残されています。実際の使用時は `noveler` に読み替えてください。

## テスト計画

移行が成功したことを確認するための検証手順:

### 1. 基本コマンドの動作確認

```bash
# ヘルプ表示
noveler --help

# プロジェクトステータス
noveler status

# 品質チェック（既存エピソードがある場合）
noveler check 1
```

### 2. MCP サーバーの動作確認

```bash
# サーバー起動テスト
timeout 5 noveler mcp-server 2>&1 | head -10

# ツール一覧確認
noveler mcp list-tools
```

### 3. 統合テストの実行

```bash
# 全テストスイート実行
make test

# MCPサーバー統合テスト
pytest tests/integration/test_mcp_server_integration.py -v
```

## dist ディレクトリの再生成

開発者向け: `src` から `dist` への同期が必要な場合:

### 同期タイミング

- `src/` 配下のPythonコードを変更した後
- 新機能追加またはバグ修正後
- リリース前のビルド時

### 再生成手順

```bash
# 1. 既存のdistをクリーンアップ
rm -rf dist/

# 2. ビルドツールで再生成
python -m build

# または、setup.pyを使用
python setup.py sdist bdist_wheel

# 3. 動作確認
python -m noveler --version
```

### 検証コマンド

```bash
# distの内容確認
ls -la dist/

# パッケージ構造の確認
tar -tzf dist/noveler-*.tar.gz | head -20

# インストール可能性の確認（仮想環境推奨）
pip install dist/noveler-*.whl --dry-run
```

## 関連ドキュメント

- [B50 システム運用基礎](./B50_システム運用基礎.md): `noveler` コマンドの詳細な使用方法
- [A32 レガシーガイド](./guides/A32_レガシーガイド.md): 歴史的経緯と旧システムの記録
- [CHANGELOG](../CHANGELOG.md): バージョン2.2.2での廃止に関する詳細

## サポート

移行に関する問題が発生した場合:

1. Issue を作成: プロジェクトのGitHubリポジトリ
2. ドキュメント参照: `docs/` ディレクトリ内の最新ガイド
3. テストログ確認: `reports/` ディレクトリ内のテスト結果

---

最終更新: 2025-09-28
バージョン: 1.0.0