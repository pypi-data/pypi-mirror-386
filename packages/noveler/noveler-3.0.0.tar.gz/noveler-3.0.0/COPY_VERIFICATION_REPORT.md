# プロジェクトコピー検証レポート

## コピー元
`C:\Users\bamboocity\OneDrive\Documents\9_小説\00_ガイド`

## コピー先
`C:\Users\bamboocity\Dropbox\noveler`

## 実行日時
2025-10-21

---

## コピーされた重要なディレクトリ (19個)

1. `bin/` - CLIスクリプト
2. `ci/` - CI/CD設定
3. `common/` - 共通ファイル
4. `config/` - 設定ファイル
5. `docs/` - ドキュメント
6. `domain/` - パッケージエントリポイント
7. `examples/` - サンプルコード
8. `goldensamples/` - テスト参照サンプル
9. `logs/` - ログディレクトリ（空）
10. `management/` - 管理スクリプト
11. `mcp_servers/` - MCPサーバー
12. `noveler/` - パッケージエントリポイント
13. `requirements/` - 依存関係定義
14. `schemas/` - スキーマ定義
15. `scripts/` - Pythonソースコード（DDD構造）
16. `specs/` - 仕様書
17. `src/` - ソースコード（noveler, mcp, mcp_servers）
18. `templates/` - テンプレート
19. `tests/` - テストコード

---

## コピーされた設定ファイル (15個)

1. `.anemic-domain.yaml` - アネミックドメインチェック設定
2. `.b20rc.yaml` - B20コンプライアンス設定
3. `.coveragerc` - カバレッジ設定
4. `.editorconfig` - エディタ設定
5. `.gitattributes` - Git属性
6. `.gitignore` - Git無視設定
7. `.gitmessage` - Gitコミットメッセージテンプレート
8. `.importlinter` - DDD層依存チェック
9. `.mcp.production.json` - MCP本番環境設定
10. `.novel_aliases` - コマンドエイリアス
11. `.novelerrc.yaml` - プロジェクト設定
12. `.pre-commit-config.yaml` - pre-commitフック設定
13. `.pre-commit-hook-b20-compliance.yaml` - B20コンプライアンスフック
14. `.ruff.toml` - Ruff linter設定
15. `.ruffignore` - Ruff無視設定

---

## コピーされた主要ドキュメント (9個)

1. `AGENTS.md` - 開発原則・ワークフロー
2. `ARCHITECTURE.md` - アーキテクチャドキュメント
3. `CHANGELOG.md` - 変更履歴
4. `CLAUDE.md` - Claude Code向けガイド ✅
5. `CODEMAP.yaml` - コードマップ
6. `CODEMAP_dependencies.yaml` - 依存関係マップ
7. `README.md` - プロジェクト概要
8. `TODO.md` - TODO管理
9. `conftest.py` - pytest設定

---

## コピーされたその他の重要ファイル (5個)

1. `app_config.yaml` - アプリケーション設定
2. `claude_code_config.json` - Claude Code設定
3. `codex.mcp.json` - Codex MCP設定
4. `Makefile` - ビルドコマンド
5. `package.json` - Node.js依存関係
6. `pyproject.toml` - Pythonパッケージ設定

---

## 除外されたディレクトリ（意図的）

以下は開発に不要なため除外：
- `.git/` - Gitリポジトリ（新規初期化推奨）
- `.venv/`, `venv/` - 仮想環境（再作成が必要）
- `node_modules/` - Node依存関係（npm installで再生成）
- `__pycache__/`, `.pytest_cache/`, `.benchmarks/` - キャッシュ
- `logs/`, `outputs/`, `reports/` - 実行時生成ファイル
- `archive/`, `backups/`, `b20-outputs/` - アーカイブ
- `dist/`, `build/` - ビルド成果物
- `20_プロット/`, `40_原稿/`, `50_管理資料/`, `60_プロンプト/` - プロジェクト固有データ
- `plots/`, `prompts/`, `workspace/`, `temp/` - 作業ディレクトリ
- `templates_backup_*` - バックアップ

---

## 最終統計

- **合計サイズ**: 約370MB（キャッシュ・一時ファイル除外済み）
- **ディレクトリ数**: 19個
- **ルートファイル数**: 33個

---

## 検証結果

✅ **コピー完了** - 重要なファイルとディレクトリは全て正常にコピーされました

### 次のステップ

1. **Git初期化**（推奨）
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Noveler project"
   ```

2. **仮想環境セットアップ**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   
   pip install -r requirements/requirements.txt
   ```

3. **動作確認**
   ```bash
   make test
   ```

---

## 重要な注意事項

1. `.env` ファイルは除外されています（機密情報保護のため）
2. Git履歴は含まれていません（新規リポジトリとして開始）
3. 仮想環境は再作成が必要です
4. OneDrive側のプロジェクトは元のまま保持されています

