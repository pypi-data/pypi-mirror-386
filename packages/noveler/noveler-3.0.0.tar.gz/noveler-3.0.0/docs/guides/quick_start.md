# 🔰 初心者向け詳細ウォークスルーガイド

> **最終更新**: 2025年8月30日（novelerコマンド・MCPサーバー統合対応）
> **すぐに始めたい方**: [README.md](../README.md) の「5分で始めるクイックスタート

> dist ラッパー生成: CIは `scripts/ci/ensure_dist_wrapper.py`、ローカルは `make build-dist-wrapper`。MCP設定は相対パス+`cwd: .`、`PYTHONPATH=.:./dist`。`-u` は使わず `PYTHONUNBUFFERED=1` をenvで付与。」をご覧ください

## 🎯 このガイドの目的

**小説執筆が初めての方**や**システムに慣れていない方**向けに、一歩ずつ丁寧に解説します。

### 👥 こんな方におすすめ
- 小説執筆が初めての方
- コマンドライン操作に不慣れな方
- システムの全体像を理解したい方
- トラブル時の詳しい対処法を知りたい方

## 📖 詳細ウォークスルー

> **注意**: このガイドは詳細な手順説明です。すぐに始めたい方は [README.md](../README.md) をご覧ください。

### ℹ️ CLI実行メモ（dist優先/自動フォールバック）
- 本ガイドでは簡潔に `noveler` コマンドを使用します。`./bin/noveler` は本番用 `dist/` を優先し、`dist` が不在または古い場合は `src/` に自動フォールバックします（警告表示あり）。
- `noveler check` は互換ラッパーで、内部的に MCP ツール `run_quality_checks`（必要に応じて `fix_quality_issues`）を呼び出します。MCPツールを直接使う場合は `noveler mcp call <tool> '{...JSON}'` をご利用ください。

### 🔧 事前準備：システムの動作確認

#### 🔍 最短のテスト確認（任意）
```bash
# まずは全体を一度通す（LLM要約は自動出力）
make test

# 失敗が出たら直近失敗のみ再実行（高速）
make test-last

# 直pytestで要約を出す場合
bin/test -q
# LLM最小出力（JSON要約のみ）
bin/test-json -q

# 補足: `bin/test*` は `pytest-timeout` プラグインを利用します。未導入の場合は
#   pip install pytest-timeout
# を実行してから再試行してください。
```

#### 1. 必須ソフトウェアの確認
```bash
# Python のバージョン確認（3.10以上が必要）
python3 --version
# 例: Python 3.10.12

# Git の確認
git --version
# 例: git version 2.34.1
```

**💡 確認結果が期待と違う場合**
- Python が古い → 新しいバージョンをインストール
- Git がない → Git をインストール（Ubuntu: `sudo apt install git`）

#### 2. ディレクトリ構造の理解
```
📁 あなたのフォルダ/
├── 📁 01_小説/                 ← ここに作品を保存
│   ├── 📁 01_作品名1/
│   ├── 📁 02_作品名2/
│   └── ...
└── 📁 00_ガイド/              ← システム本体
    ├── 📁 bin/               ← コマンド実行ファイル
    ├── 📁 src/               ← プログラムソースコード
    │   └── 📁 noveler/         ← メインプログラム
    ├── 📁 scripts/           ← 各種スクリプト・設定
    ├── 📁 tests/             ← テストコード
    ├── 📁 templates/         ← テンプレートファイル
    ├── 📁 docs/              ← ドキュメント
    └── README.md
```

### 🛠️ Step 1: システムのインストール（詳細版）

#### 1-1. インストールスクリプトの実行
```bash
# 00_ガイドフォルダに移動
cd 00_ガイド

# 実行権限を確認・付与
ls -la bin/install.sh
chmod +x bin/install.sh  # 実行権限がない場合

# インストール実行
./bin/install.sh
```

#### 1-2. MCPサーバー機能の有効化（Claude Code連携用）
```bash
# MCPサーバー起動（Claude Code統合機能用）
# この機能により、Claude Codeから直接novelerシステムを操作できます
noveler mcp-server --port 3000

# バックグラウンドで起動する場合
nohup noveler mcp-server --port 3000 &

# 🔍 MCPサーバー動作確認
curl http://localhost:3000/health
# → {"status": "ok"} が返れば正常
```

**💡 MCPサーバーとは？**
- Claude Codeと連携して、AIによる執筆支援を可能にします
- JSON形式でのデータ変換により、95%のトークン削減を実現
- Claude Codeからnovelerコマンドを直接実行できます

**⚠️ エラーが発生した場合**
```bash
# エラー例: "Permission denied"
sudo chmod +x bin/install.sh
./bin/install.sh

# エラー例: "python3: command not found"
# → Python をインストールしてから再実行

# エラー例: "No such file or directory"
# → 正しいディレクトリにいるか確認
pwd  # 現在のディレクトリを表示
```

#### 1-3. PATH設定の確認と手動設定
```bash
# インストール後の動作確認
noveler --help

# もし「command not found」が出る場合は手動設定
export PATH="$PWD/bin:$PATH"

# 設定を永続化（bashの場合）
echo 'export PATH="/path/to/00_ガイド/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 設定を永続化（zshの場合）
echo 'export PATH="/path/to/00_ガイド/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 📂 Step 2: 初回プロジェクト作成（詳細版）

#### 2-1. 作品フォルダの準備
```bash
# 小説保存用ディレクトリに移動
cd ../9_小説
pwd  # 現在地確認: /path/to/9_小説

# 新規プロジェクト作成
noveler create "転生したら最強の魔法使いだった件"
```

**💡 作品名の決め方**
- 日本語OK：「転生したら魔法使いだった」
- 英数字OK：「My Novel Project」
- 特殊文字は避ける：`/`, `*`, `?` など

#### 2-2. プロジェクト設定の詳細編集
```bash
# プロジェクトフォルダに移動
cd "05_転生したら最強の魔法使いだった件"
ls  # フォルダ内容を確認

# 設定ファイルを開く（エディタ例）
nano プロジェクト設定.yaml     # nano エディタ
code プロジェクト設定.yaml     # VS Code
vim プロジェクト設定.yaml      # vim エディタ
```

**📝 設定ファイル例**
```yaml
project_name: "転生したら最強の魔法使いだった件"
author: "あなたの名前"
genre: "ファンタジー"
ncode: "N1234AB"  # なろうコード（後で設定可）
target_audience: "一般"
```

### ✍️ Step 3: 第1話執筆（詳細版）

#### 3-1. 新規エピソード作成
```bash
# 第1話の執筆を開始
noveler write 1

# 実行後の確認
ls 40_原稿/  # 第001話.md が作成されているか確認
```

**💡 実行後に起こること**
1. `40_原稿/第001話.md` が作成される
2. 基本的なテンプレートが挿入される
3. 自動的に品質チェックが実行される

#### 3-2. 原稿の編集
```bash
# 原稿ファイルを開く
nano 40_原稿/第001話.md
```

**📝 執筆のコツ**
- タイトルは自動で設定されます
- `# 第001話 タイトル` の形式で始める
- 本文は普通に書けばOK

#### 3-3. 品質チェックの詳細実行
```bash
# 🔰 初心者におすすめ（全自動）
noveler check 1

# 🔍 詳細情報を見たい場合
noveler check 1 --verbose

# 🛠️ 自動修正も実行したい場合
noveler check 1 --auto-fix
```

**📊 品質チェック結果の見方**
```
✅ 品質スコア: 75.2点 (良好)
📊 文字数: 3,247文字
🎭 視点: 一人称・内省型
⚠️  改善提案: 2件
```

## 💡 初心者向けコマンド基礎

### 🔰 毎日使う基本の3コマンド
```bash
# ✍️ 執筆開始（話数で指定）
noveler write 1      # 第1話を書く
noveler write 2      # 第2話を書く

# 🔍 品質チェック（話数で指定）
noveler check 1      # 第1話をチェック

# ✅ 完成処理
noveler complete-episode 1  # 第1話を完成にする
```

### 📊 品質チェックのオプション詳細
```bash
# 🔰 基本（初心者におすすめ）
noveler check 1                    # 全自動品質チェック

# 🔍 詳細情報を見たい場合
noveler check 1 --verbose          # 詳しい分析結果を表示

# 🛠️ 自動修正も実行
noveler check 1 --auto-fix         # チェック＋自動修正

# 📋 改善提案を詳しく見る
noveler check 1 --show-review      # 具体的な改善案を表示
```

### 🎯 プロジェクト管理コマンド
```bash
# 📋 プロジェクト状況確認
noveler show                       # 現在の執筆状況を表示

# 🔧 設定確認
noveler config show                # 設定を確認

# 🏥 問題があるときの診断
noveler diagnose                   # システム診断
noveler diagnose --repair          # 問題の自動修復
```

## 🧱 ビルドと MCP サーバー（stdio）

本プロジェクトの MCP サーバーは stdio トランスポート準拠です。通常はクライアント（Claude Code）の `mcp.json` から起動します。

### ビルド
```bash
cd 00_ガイド
python build.py
```

ビルド時は、既存の MCP サーバープロセスを自動停止します。`psutil` が導入されている環境ではより安全に停止できますが、未導入でも `tracemalloc` ベースの軽量計測・フォールバックで動作します（詳細計測は限定されます）。

### 自動起動（必要な場合のみ）
ビルド直後に MCP サーバーを自動で起動したい場合は、環境変数を有効化して実行します。

```bash
NOVELER_AUTOSTART_MCP=1 python build.py
```

ただし、stdio サーバーはクライアント接続が前提のため、単独でターミナルから起動すると I/O エラーになる場合があります。基本的にはクライアント（Claude Code）の `mcp.json` から起動してください。

## 🚀 実際に始めてみよう！

### 📝 練習用プロジェクトでお試し
初心者の方は、まず練習用プロジェクトで動作を確認してみましょう。

```bash
# 練習用プロジェクトを作成
cd 9_小説
noveler create "練習用プロジェクト"
cd "05_練習用プロジェクト"

# 簡単なテストエピソードを書く
noveler write 1
# → 40_原稿/第001話.md が作成されます

# エディタで簡単な文章を書く
nano 40_原稿/第001話.md
# 例: 「今日はいい天気だった。空が青く、雲が白かった。」

# 品質チェックを試す
noveler check 1
```

### 🎯 次のステップガイド

#### 🔰 初心者コース
1. **基本操作に慣れる** → このガイドで練習
2. **執筆技法を学ぶ** → [A30_執筆ワークフロー.md](A30_執筆ワークフロー.md)
3. **品質向上の方法** → [A33_執筆品質管理チェック.md](A33_執筆品質管理チェック.md)

#### 🔧 コマンド詳細を知りたい方
- **全コマンドリファレンス** → [A32_執筆コマンドガイド.md](A32_執筆コマンドガイド.md)
- **プロット作成方法** → [A28_話別プロットプロンプト.md](A28_話別プロットプロンプト.md)

#### 🆘 トラブル解決
- **エラー対処法** → [04_よくあるエラーと対処法.md](04_よくあるエラーと対処法.md)
- **システム診断** → `noveler diagnose`

## 🆘 よくあるトラブルと詳細解決法

### ❌ 問題1: 「noveler: command not found」
**症状**: コマンドが認識されない

**解決方法（段階的）**:
```bash
# 1. 現在地確認
pwd
# /path/to/00_ガイド にいることを確認

# 2. ファイル存在確認
ls bin/noveler
# ファイルがあるか確認

# 3. 実行権限確認
ls -la bin/noveler
# -rwxr-xr-x のように x（実行権限）があるか確認

# 4. PATH設定（一時的）
export PATH="$PWD/bin:$PATH"
noveler --help

# 5. PATH設定（永続化）
echo 'export PATH="/full/path/to/00_ガイド/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### ❌ 問題2: 「Permission denied」
**症状**: 実行権限がない

**解決方法**:
```bash
# 実行権限を付与
chmod +x bin/noveler
chmod +x bin/install.sh

# それでもダメな場合
sudo chmod +x bin/*
```

### ❌ 問題3: 「プロジェクトが見つからない」
**症状**: `noveler check 1` で「プロジェクトが見つかりません」

**解決方法**:
```bash
# 1. 正しいディレクトリにいるか確認
pwd
# /path/to/9_小説/05_作品名 であることを確認

# 2. プロジェクト設定ファイルがあるか確認
ls プロジェクト設定.yaml

# 3. 正しいディレクトリに移動
cd "05_あなたの作品名"
noveler check 1
```

### ❌ 問題4: YAML構文エラー
**症状**: 「YAMLの解析に失敗しました」

**解決方法**:
```bash
# システム診断で詳細を確認
noveler diagnose

# 自動修復を試す
noveler diagnose --repair

# 手動修正（よくあるミス）
# ❌ 間違い: name:"test"（スペースがない）
# ✅ 正しい: name: "test"（コロンの後にスペース）
```

## 💡 環境要件の詳細確認

### 必須要件チェックリスト
```bash
# ✅ Python 3.10以上
python3 --version
# Python 3.10.12 以上であることを確認

# ✅ Git
git --version
# git version 2.x.x であることを確認

# ✅ ディスク容量（最低 1GB）
df -h .
# Available 列で空き容量を確認
```

### 推奨環境
- **OS**: Ubuntu 20.04+, macOS 12+, Windows 11（WSL2）
- **メモリ**: 4GB以上（8GB推奨）
- **エディタ**: VS Code, nano, vim のいずれか

---

## 🎉 これで準備完了！

```bash
# 🎯 あなたの最初のステップ
cd 9_小説
noveler create "あなたの作品名"
cd "05_あなたの作品名"

# 📝 設定を編集（重要）
nano プロジェクト設定.yaml

# ✍️ 執筆開始！
noveler write 1
```

**🔥 小説執筆の新しい体験が始まります！**

> 💡 **ヒント**: 最初は短い話（1000-2000文字）で練習し、システムに慣れてから本格的な執筆を始めることをおすすめします。
### ⚙️ MCPクライアント設定の自動更新（Codex/Claude）

Codex と Claude Code 双方の設定を安全にバックアップしてから最新構成を反映します。

```bash
# 1) 一括更新（codex.mcp.json, .mcp/config.json, Claude設定）
./bin/setup_mcp_configs

# 2) 個別更新
./bin/setup_mcp_configs --codex     # codex.mcp.json のみ
./bin/setup_mcp_configs --project   # .mcp/config.json のみ
./bin/setup_mcp_configs --claude    # Claude Code 設定のみ

# 3) ドライラン（変更内容のみ表示）
./bin/setup_mcp_configs --dry-run

# 4) サーバーキー変更（既定: noveler）
./bin/setup_mcp_configs --server-key noveler
```

**SSOT管理**: 詳細は `docs/mcp/config_management.md` を参照
**サンプル**: `docs/.examples/codex.mcp.json`
