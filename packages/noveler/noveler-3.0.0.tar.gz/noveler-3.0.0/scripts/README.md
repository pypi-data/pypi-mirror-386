# Scripts ディレクトリ

プロジェクト管理・環境設定スクリプト集

> **最終更新**: 2025年8月29日（Python標準構造対応・scripts整理）

## 📁 ディレクトリ構成

```
scripts/
├── setup/                    # 環境設定・初期化
│   └── setenv.sh            # 環境変数・エイリアス設定
├── tools/                    # 開発・運用ツール
│   └── (開発支援スクリプト)
└── project_novel_shortcut.sh # プロジェクト用ショートカット
```

## 🛠️ 主要スクリプト詳細

### setup/setenv.sh
**環境設定・開発支援エイリアス**

- **使用方法**: `source scripts/setup/setenv.sh`
- **機能**: 環境変数設定、便利なエイリアス定義
- **更新履歴**: Python標準構造対応（テストパス等更新済み）

### project_novel_shortcut.sh
**プロジェクト専用のnovelコマンドショートカット**

- **用途**: 各小説プロジェクトフォルダでの簡単なnovelコマンド実行
- **対応システム**: bin/noveler（Python標準構造対応済み）

#### セットアップ方法
```bash
# プロジェクトフォルダに移動
cd /path/to/your/novel/project

# ショートカットスクリプトをコピー
cp /path/to/00_ガイド/scripts/project_novel_shortcut.sh ./novel

# 実行権限を付与
chmod +x ./novel

# プロジェクト固有のコマンド実行
./novel status
./novel write 1
```

#### 動作要件
- プロジェクトルートに `プロジェクト設定.yaml` が存在すること
- 小説執筆支援システム（00_ガイド）がアクセス可能な場所にあること
- bin/novelerコマンドが正常に動作すること

#### 提供機能
- ✅ プロジェクト個別の環境で実行
- ✅ パスを意識せずにnovelコマンドを利用可能
- ✅ プロジェクト名の自動表示
- ✅ エラー時の詳細メッセージ（絵文字付き）
- ✅ 00_ガイドディレクトリの自動検索

#### 技術詳細
- **実行対象**: `$GUIDE_DIR/bin/noveler`
- **環境変数**: `PROJECT_ROOT` を自動設定
- **エラーハンドリング**: 段階的な問題特定とユーザーフレンドリーなメッセージ

## 🔄 移行履歴（2025年8月29日）

### 移動・整理されたファイル
- ✅ `src/noveler/setup/setenv.sh` → `scripts/setup/setenv.sh`
- ✅ `templates/novel_shortcut.sh` → `scripts/project_novel_shortcut.sh`

### 更新内容
- **setenv.sh**: テストパス修正（src/noveler/tests/ → tests/）
- **project_novel_shortcut.sh**: bin/noveler対応、エラーメッセージ改善
- **README.md**: 標準的なドキュメント構造に整理

## 📝 開発者向け情報

### 新規スクリプト追加時の注意
1. **命名規則**: `kebab-case.sh` 形式を推奨
2. **実行権限**: `chmod +x` を忘れずに
3. **ドキュメント**: このREADME.mdに用途・使用方法を追記
4. **テスト**: 実際の環境での動作確認を実施

### エラー対応
スクリプトの問題が発生した場合：
1. まずは `./novel diagnose` でシステム診断
2. エラーメッセージを確認
3. 該当スクリプトの実行権限を確認
4. 必要に応じてパス設定を再確認


### run_pytest.py（統一テストランナー）
プロジェクトの単一入口としてpytestを実行します（環境統一・出力統一）。

- 基本: `python3 scripts/run_pytest.py -q`
- 個別/絞り込み: `python3 scripts/run_pytest.py tests/unit/foo_test.py::TestFoo::test_bar -vv -k 'not slow' -m unit`
- 直近失敗: `python3 scripts/run_pytest.py --last-failed -x`
- 差分のみ: `python3 scripts/run_pytest.py --changed --range 'origin/master...HEAD'`
- 並列（ある場合）: `python3 scripts/run_pytest.py --xdist-auto`
- 乾式: `python3 scripts/run_pytest.py --dry-run -q`

オプション:
- `--json-only`: 標準出力に最終要約JSON（reports/llm_summary.jsonl の最終行）のみを出力（pytestの標準出力は抑止、終了コードは維持）。

### setup/update_slash_commands.py（/test 系スラッシュコマンド紐付け）
Claude Code/Codex向けに `/test`, `/test-failed`, `/test-changed` を bin/* に紐付けます。

- 全体更新: `python3 scripts/setup/update_slash_commands.py`
- 乾式: `python3 scripts/setup/update_slash_commands.py --dry-run`
- リポジトリのみ: `python3 scripts/setup/update_slash_commands.py --no-user`
- ユーザー設定のみ: `python3 scripts/setup/update_slash_commands.py --no-repo`

生成/更新:
- `.claude/settings.local.json` の permissions.allow に `Bash(bin/test*)` を追記
- `.codex/commands.json` に `/test*` → `bin/test*` マッピングを生成
- ユーザーの `claude_desktop_config.json` にも permissions.allow を追記（OS自動検出）


### 高速クリーンアップ（LLM向け）
- `LLM_FAST_CLEANUP=1` を設定すると、pytestセッション終了時の重いクリーンアップをスキップします。
  - 用途: LLM対話や部分実行での待ち時間短縮（デフォルトは従来の完全クリーンアップ）。


### Fail-only NDJSON streaming（CI既定ON）
- CIでは `LLM_REPORT_STREAM_FAIL=1` を既定有効化。失敗フェーズのみをNDJSONで逐次記録します。
  - ワーカー別: `reports/stream/llm_fail_<worker>.ndjson`
  - 集約: セッション終了時に `reports/llm_fail.ndjson` へ統合し、`session_summary` を1行追記
  - スキーマ: `{ts,event,test_id,phase,outcome,duration_s,worker_id}` + summary（failed/error/crashed件数など）
- ローカルで無効化したい場合: `LLM_REPORT_STREAM_FAIL=0` を設定
