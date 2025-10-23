# ディレクトリ構成ガイド
Created: 2025-09-21

## 本番コード
- `src/` - メインソースコード
- `dist/` - ビルド成果物
- `bin/` - 実行可能ファイル

## 開発・テスト
- `tests/` - テストコード
- `temp/` - 一時ファイル（自動生成）
- `.dev/` - 開発用キャッシュ（.gitignore対象）
  - `ruff_cache/` - Ruffリンターキャッシュ
  - `import_linter_cache/` - インポートリンターキャッシュ
  - `hypothesis/` - Hypothesisテストキャッシュ

## ドキュメント・設定
- `docs/` - ドキュメント
- `specs/` - 仕様書
- `config/` - 設定ファイル

## 出力・レポート（CI参照）
- `reports/` - 品質レポート
- `logs/` - ログファイル
- `outputs/` - その他の出力

## バックアップ・アーカイブ
- `backups/` - バックアップファイル
- `archive/` - アーカイブ済みコード

## プロジェクト関連（小説執筆）
- `40_原稿/` - 執筆原稿
- `50_管理資料/` - 管理・分析資料
- `60_プロンプト/` - プロンプトテンプレート

## ワークスペース
- `workspace/` - 作業領域
  - `worktrees/` - Git worktrees（ブランチ別作業エリア）
  - `temp/` - 一時作業ファイル

## Git管理
- `.git` - gitdirポインタファイル（実際のGitデータは`~/.git-noveler`）
- `.gitignore` - Git除外設定
- `.github/` - GitHub Actions設定

## 注意事項
- キャッシュディレクトリ（.dev配下）は.gitignoreで除外
- reports/, logs/, outputs/はCI・スクリプトから参照されるため移動注意
- workspace/worktreesはGit worktree機能で自動管理
- OneDrive Git最適化により.gitは実際には~/.git-novelerを参照
