# 小説執筆支援システム

> **📚 [ナビゲーションマップ](00_マスターガイド/00_ナビゲーションマップ.md)** ← すべての文書を一元的に参照
> **🖊️ [A00: 総合実践ガイド（執筆ハブ）](docs/A00_総合実践ガイド.md)** / **🛠️ [B00: 情報システム開発ガイド（開発ハブ）](docs/B00_情報システム開発ガイド.md)**
> **⚡ [クイックスタート](00_マスターガイド/00_クイックスタート.md)** ← 5分で始めたい方はこちら

「小説家になろう」向けの総合的な執筆支援システムです。企画から連載管理まで、web小説執筆の全工程を統合的にサポートします。

重要: 旧レガシーCLIである `novel` コマンドは完全廃止しました。以後は `noveler`（統合CLI）および MCP ツールのみを使用してください。

## 🎯 システムの特徴

### 🚀 **Claude Code統合機能（v2.0）**
- **error_max_turns自動回復**: ターン数制限時の段階的拡張（10→15→20ターン）
- **タイムアウト延長**: 600秒（10分）まで自動延長
- **環境自動検出**: Claude Code内外で適切に動作分岐
- **プロンプト最適化**: エラー時の自動プロンプト最適化
- **統合設定管理**: `config/novel_config.yaml`による柔軟な制御

### ✨ **品質管理システム**
- **Smart Auto-Enhancement（デフォルト）**: 基本→A31→Claude分析の全段階統合実行
- **🎭 視点情報連動品質評価**: プロット視点情報に基づく動的評価基準調整
- **📊 適応的品質基準**: 執筆レベル・ジャンル別の自動品質基準調整
- **💡 具体的エラーメッセージ**: 改善前後の例付きフィードバック
- **🛡️ 固有名詞自動保護**: 設定集からの自動固有名詞抽出・除外
- **🧠 内面描写深度評価**: 5層構造による文学的表現分析

### 🔧 **システム基盤**
- **🌐 グローバル対応**: `/noveler`コマンドで任意の場所からアクセス（2025年9月1日追加）
- **🚀 統合CLI操作**: `noveler`コマンドですべての機能にアクセス
- **⚡ 高速並列処理**: GNU parallel対応による大規模プロジェクト品質チェック高速化
- **📊 適応的品質ゲート**: ファイル数・重要度に応じた動的処理切り替え
- **🏎️ Git高速化**: OneDriveから分離した.gitで10-1000倍の高速化（2025年9月21日実装）
- **🎯 SPEC-901 MessageBus/DDD**: 軽量MessageBus（P95<1ms）による非同期コマンド・イベント処理（2025年9月22日完成）
- **TDD+DDD準拠**: テスト駆動開発とドメイン駆動設計による高品質実装
- **📁 標準化構造**: Pythonプロジェクトの標準的な構造に準拠

## 🚀 5分で始めるクイックスタート

> **🔰 詳しい手順を知りたい方**: [01_クイックスタート.md](docs/guides/quick_start.md) で段階的ウォークスルーをご覧ください
> **ℹ️ CLI役割分離**: `noveler check` は品質評価（スコア/オートフィクス）。Stage2/Stage3 改稿や追加ツールは `noveler mcp call polish_manuscript '{...}'` などの MCP 呼び出しで利用します。内部では ProgressiveCheckManager がテンプレ探索順（checks→backup→writing）と I/O ログを共有します。

### ✨ **最新機能（2025年9月1日）**
- 🌐 **グローバルコマンド**: `/noveler` で任意の場所からアクセス
- 🚀 **Smart Auto-Enhancement**: MCPツール `run_quality_checks`（summary推奨）で全品質チェック
- 📊 **統合評価**: 82.5点等の定量的品質スコア表示
- ⚡ **一気通貫ワークフロー**: 基本→A31→Claude分析を完全自動化

### 品質チェック体系（ライトウェイト／12ステップ／推敲）
- ライトウェイト: `noveler check` → MCP `run_quality_checks`/`improve_quality_until`（12ステップではない）
- 12ステップ: MCP `progressive_check.get_tasks`（初回呼び出しでセッション生成）→ `execute_step` → `get_status` / `get_history` で段階実行・反復
- 推敲（A40/A41）: `noveler mcp call polish_manuscript '{...}'` / `noveler mcp call polish_manuscript_apply '{...}'`（改稿・レポート `.noveler/artifacts`）


### 🌐 **グローバルコマンド インストール**
```bash
# グローバル化（任意）
python scripts/install_global_command.py

# PATH 上の `noveler` を直接実行
noveler mcp-server --port 3000
noveler check 1 --auto-fix
noveler write 1 --dry-run
noveler mcp call run_quality_checks '{"episode_number":1,"additional_params":{"format":"summary"}}'
noveler mcp call polish_manuscript '{"episode_number":1,"additional_params":{"stages":["stage2","stage3"],"dry_run":true}}'
```
### Step 1: システムインストール
```bash
# Python3.10以上が必要
python3 --version

# インストール（推奨方法）
cd 00_ガイド
./bin/install.sh

# 動作確認
./bin/noveler --help
```

#### 💡 CLI実行メモ（dist優先/自動フォールバック）
- `./bin/noveler` は本番用 `dist/` を優先して実行します。`dist` が不在または `src` より古い場合は、自動で `src/` をフォールバック使用し、その旨を警告表示します。
- `noveler check <episode|file> [--auto-fix]` は互換ラッパーです。内部で MCP ツール `run_quality_checks`（必要に応じて `fix_quality_issues`）を呼び出します。既定ではスコア80点以上で終了コード0、未満で1になります。
- MCPツールを直接使う場合は `noveler mcp call <tool> '{...JSON}'` を推奨します（例は本書末尾の「品質ツールとCI連携」を参照）。
- dist ラッパー生成: CIは `scripts/ci/ensure_dist_wrapper.py` で `dist/mcp_servers/noveler/main.py` を用意、ローカルは `make build-dist-wrapper` で同等に生成可能。

### Step 2: プロジェクト作成と初期設定
```bash
# 1. サンプルプロジェクトを作成
cd 9_小説
./bin/create-project "転生したら最強の魔法使いだった件"

# 2. プロジェクトディレクトリへ移動
cd "05_転生したら最強の魔法使いだった件"

# 3. 主要設定ファイルを確認
ls .noveler
cat .novelerrc.yaml
```

### Step 3: 第1話の執筆と品質チェック
```bash
./bin/noveler write 1 --dry-run
./bin/noveler check 1 --auto-fix
./bin/noveler check 1 --exclude-dialogue
noveler mcp call run_quality_checks '{"episode_number":1,"additional_params":{"format":"summary","exclude_dialogue_lines":true}}'
noveler mcp call polish_manuscript '{"episode_number":1,"additional_params":{"stages":["stage2","stage3"],"dry_run":true}}'
```

### 💡 **よく使うコマンド（使用頻度順）**
```bash
noveler write 1 --dry-run                 # 18ステップの進行のみを確認
noveler write 1                         # 実際に原稿を生成
noveler check 1 --auto-fix              # 品質チェック+自動修正
noveler check README.md --exclude-dialogue  # ファイル単位チェック（会話除外）
noveler mcp call run_quality_checks '{"episode_number":1,"additional_params":{"format":"detail"}}'
noveler mcp call improve_quality_until '{"episode_number":1,"additional_params":{"target_score":85,"max_iterations":3}}'
```

## 📚 ガイド体系（A/Bカテゴリ別）

### 📋 00_マスターガイド
- [01_クイックスタート](docs/guides/quick_start.md) - 5分で始める
- [_index.yaml](docs/_index.yaml) - 全文書一覧

### 📚 A_執筆ガイド
- **A10_企画設計** - プロジェクトの基礎作り
- **A20_プロット作成** - ストーリー構成
- **A30_原稿執筆** - 毎話の執筆実務
- **A40_推敲品質** - 品質向上プロセス
- **A50_AI協創** - AI活用技法

### 🔧 B_技術ガイド
- **B10_品質チェック** - 自動チェックシステム
- **B20_YAML管理** - 設定ファイル管理
- **B30_離脱率分析** - 読者データ分析
- **B40_システム運用** - システム操作とトラブル対処
- **B50_開発プロセス** - TDD/DDD/API設計

## 🎨 主要機能

### 現行CLIコマンド一覧（2025年10月時点）
```bash
noveler mcp-server [--port 3000]
noveler mcp call <tool> '{...JSON}'
noveler check <episode|file> [--auto-fix] [--exclude-dialogue]
noveler write <episode> [--dry-run]
```

- `noveler mcp-server` : MCP サーバーを起動。Codex/Claude Code からの接続時は `MCP_STDIO_SAFE=1` で静音化。
- `noveler mcp call <tool>` : `run_quality_checks` や `polish_manuscript` など任意の MCP ツールを即時実行。
- `noveler check` : エピソード番号またはファイルパスを入力して品質ベンチを実行。`--exclude-dialogue` で会話行を除外。
- `noveler write` : 18 ステップの執筆フローを実行。`--dry-run` で成果物を書き込まずに進行を確認。

### よく使う MCP ツール呼び出し例
```bash
noveler mcp call run_quality_checks '{"episode_number":5,"additional_params":{"format":"summary"}}'
noveler mcp call polish_manuscript '{"episode_number":5,"additional_params":{"stages":["stage2","stage3"],"dry_run":false}}'
noveler mcp call improve_quality_until '{"episode_number":5,"additional_params":{"target_score":85,"max_iterations":3}}'
noveler mcp call enhanced_get_writing_tasks '{"episode_number":5}'
```
#### 🧩 エンハンスト執筆ユースケース（診断/復旧対応）
- MCPの補助ツールとして、診断付きタスクリスト／復旧対応ステップ実行が利用できます。
- 例（MCP直呼び）:
  - `noveler mcp call enhanced_get_writing_tasks '{"episode_number":1}'`
  - `noveler mcp call enhanced_execute_writing_step '{"episode_number":1,"step_id":1,"dry_run":false}'`
  - `noveler mcp call enhanced_resume_from_partial_failure '{"episode_number":1,"recovery_point":5}'`
  - 戻り値には `execution_method: enhanced_use_case` が含まれ、復旧が適用された場合は `recovery_applied: true` を返します。

#### 🆕 最新アップデート（2025年7月19日）
- **話数指定対応**：ファイル名の代わりに話数（1, 2, 3...）で指定可能
- **話数単位対応**：
oveler write / 
oveler check で 1, 2, 3 ... の話数指定が可能。
- **仕上げフロー統合**：仕上げは 
oveler mcp call polish_manuscript_apply（dry_run 併用可）で一括適用。
- **タイトル自動取得**：
oveler write でプロット情報からタイトルを自動推定。
- **品質設定の段階展開**：プロジェクト各フェーズで品質プリセット（.novelerrc.yaml）が段階的に更新。
- **ステータス可視化**：品質・執筆・レビューの 3 指標をダッシュボード形式で整備。
## 📎 Prompts（Codex/Claude連携・シンボリックリンク仕様）

両CLI（Codex/Claude Code）で同一のプロンプト群を使うため、リポジトリ管理の `prompts/` を参照させます。実体はこのリポジトリ配下に置き、各CLIの既定ディレクトリへシンボリックリンクで接続します。

- ソース（正）: `prompts/`（本リポジトリ）
  - フォーマット: Markdown のみ（`*.md`）
- Codex 側: `~/.codex/prompts` → ソースへのシンボリックリンク
- Claude Code 側: `~/.claude/commands`
  - 既定（推奨）: merge モード（`prompts/*.md` をファイル単位でリンクし、既存コマンドは保持）
  - 代替: link モード（`~/.claude/commands` 自体を `prompts/` へリンク）

### 導入コマンド

通常（Linux/macOS 等で $HOME に設定）
```bash
bash scripts/setup/setup_cli_prompts.sh --force            # 既存があればバックアップして置換
# Claude をディレクトリごとリンクにする場合
bash scripts/setup/setup_cli_prompts.sh --force --claude-mode link
```

WSL で Windows 側 HOME を明示したい場合（例: `/mnt/c/Users/bamboocity`）
```bash
bash scripts/setup/setup_cli_prompts.sh --force \
  --home-dir /mnt/c/Users/bamboocity \
  --claude-mode merge    # or link
```

ドライラン（変更なしで内容確認）
```bash
bash scripts/setup/setup_cli_prompts.sh --dry-run
```

### 動作確認
- Codex: `ls -l ~/.codex/prompts` が `prompts/` を指している
- Claude: `ls -l ~/.claude/commands/*.md` が `prompts/*.md` を指している
- 併せて、サンドボックス検証: `bash scripts/setup/test_setup_cli_prompts.sh`

### Windows のシンボリックリンク注意点
- 権限エラーが出る場合は Windows の「開発者モード」有効化、または管理者権限での実行を検討してください。
- WSL から Windows 側ユーザーディレクトリを使う場合は `--home-dir /mnt/c/Users/<name>` を指定してください。

詳細は `docs/guides/prompts_setup.md` を参照。

### シーン管理（MCP ツール経由）
```bash
noveler mcp call list_artifacts '{"episode_number":25,"additional_params":{"kind":"scene"}}'
noveler mcp call fetch_artifact '{"artifact_id":"artifact:SCENE-00025"}'
noveler mcp call write_file '{"episode_number":25,"additional_params":{"file_path":"40_本編/第025話.md","content":"..."}}'
```

#### 視点・リズム分析
```bash
noveler check 2 --auto-fix
noveler mcp call run_quality_checks '{"episode_number":2,"additional_params":{"format":"detail","include_diff":true}}'
noveler mcp call check_readability '{"episode_number":2,"additional_params":{"target_score":82}}'
```
# 出力例:
# ✅ 視点: 内省型 | 語り: 一人称 | 評価: 合格
# 📌 詳細は metadata.diff / metadata.suggestions を確認
```

#### 適応的品質基準
```bash
./bin/noveler check 1                  # 執筆レベル自動判定（初心者/中級者/上級者/エキスパート）
./bin/noveler check 15                 # 高話数エピソードで上級者基準適用

# 出力例:
# 📚 執筆レベル: 中級者 - 安定した品質を目指しましょう
# 📖 ジャンル: ファンタジー
# 🎯 調整後スコア: 72.5点 (良好)
```

#### 具体的改善提案
```bash
noveler check 1 --auto-fix
noveler mcp call run_quality_checks '{"episode_number":1,"additional_params":{"format":"summary"}}'
```
# 出力例:
# ・スコア: 82.5 / 目標 80
・コメント: 対話パートは良好。叙述部は metadata.suggestions で要改善箇所を確認
```

#### 自動修正・固有名詞保護
```bash
./bin/noveler check 1 --auto-fix   # 固有名詞を保護しながら自動修正
# 「A-137」「BUG.CHURCH」「綾瀬カノン」等の固有名詞は除外対象
```

#### 包括的品質チェック項目
- **🎭 視点情報連動評価**: プロット視点情報による動的基準調整
- **📊 適応的品質基準**: 執筆レベル・ジャンル別評価
- **🧠 内面描写深度評価**: 5層構造（感覚/感情/思考/記憶/象徴）
- **🛡️ 固有名詞自動保護**: 設定集からの自動抽出・除外
- **💡 具体的改善提案**: 改善前後の例付きフィードバック
- **🔧 基礎文章作法**: 句読点・記号・段落構成チェック
- **📝 構成・展開分析**: 文章バランス・展開テンポ
- **👥 キャラクター一貫性**: 名前・設定の整合性
- **📈 離脱率予測**: 読者離脱リスク分析・改善提案

## 📁 プロジェクト構成

```
[プロジェクト名]/
├── プロジェクト設定.yaml   # プロジェクト基本設定
├── 10_企画/              # 企画・設定（YAML主体）
├── 20_プロット/          # プロジェクト資材（プロット）
├── 30_設定集/            # 設定集（YAML主体）
├── 40_原稿/              # プロジェクト資材（本文）
├── 50_管理資料/          # プロジェクト資材（管理資料）
│   ├── 話数管理.yaml
│   ├── 重要シーン.yaml    # 重要シーン詳細設計
│   ├── 品質記録.yaml
│   └── アクセス分析.yaml
└── 90_アーカイブ/        # アーカイブ
```

## 🧪 ローカルCI（push不要）

Makefile のターゲットでローカルでもCI相当を実行できます。

```bash
make help              # 利用可能なターゲットを表示
make build             # distビルド（scripts/build.py 呼び）
make lint              # ruff / mypy（インストール済みなら）
make test              # pytest（全体）
make validate-templates # 品質テンプレートのスキーマ検証
make test-fast         # slowマーカー除外で高速レーン
make test-slow         # slowマーカーのみ（遅い統合/E2E）
make test-suite        # pytest（フルスイートの別名）
make test-last         # 直近失敗テストを優先実行（-x）
make test-changed      # git差分のテストのみ（なければ last-failed）
make pre-commit        # pre-commit（インストール済みなら）
make ci-mcp-dry-run    # MCP設定のドライラン検証（codex/.mcp/Claude）
make ci-smoke          # MCPツールの簡易スモーク（run_quality_checks, enhanced_*）
make ci                # lint + test + dry-run + smoke の一括実行
```

推奨フロー: 日常開発では `make test-fast` でフィードバックを得て、マージ前に `make test-slow`→`make test` を順に確認してください。

Tips:
- 個別実行や絞り込み（LLM要約は常に自動出力）
  - `make test FILE=tests/test_api.py::TestUser::test_create`
  - `make test K='user and not slow'`
  - `make test M='unit'`
  - `make test VV=1`（冗長度）
- 出力: `reports/llm_summary.{jsonl,txt}` と STDOUT の `LLM:BEGIN ... LLM:END`

## ⚙️ MCPクライアント設定の自動更新（Codex/Claude）

既存設定をバックアップした上で、安全にマージ更新します。Noveler MCPサーバーのみが対象です。

```bash
./bin/setup_mcp_configs                 # 一括（codex/.mcp/Claude）
./bin/setup_mcp_configs --codex         # codex.mcp.json のみ
./bin/setup_mcp_configs --project       # .mcp/config.json のみ
./bin/setup_mcp_configs --claude        # Claude Code 設定のみ
./bin/setup_mcp_configs --dry-run       # 変更の表示のみ
```

**SSOT管理**: 詳細は `docs/mcp/config_management.md` を参照
**最小サンプル**: `docs/.examples/codex.mcp.json`


## 🎯 対象ユーザー

- **なろう新人作家**: 基本的な執筆技法とシステム化されたワークフローを習得したい
- **経験者**: 執筆効率化と品質向上を図りたい
- **AI協創執筆者**: 構造化されたAI協働プロセスを活用したい
- **データ分析重視**: 読者反応を数値で把握し改善したい

## 📈 期待効果

### 🎭 革新的機能による効果
- **視点情報連動評価**: エピソード特性に最適化された品質評価
- **適応的品質基準**: 執筆レベルに応じた段階的成長支援
- **具体的改善提案**: 学習効果95%向上（具体例による理解促進）
- **固有名詞保護**: 誤修正リスク100%削減（自動除外）
- **内面描写深度評価**: 文学的表現力30%向上

### 📊 従来効果（改善済み）
- **執筆効率**: 50%向上（システム化によるタスク削減）
- **品質スコア**: 85%以上維持（視点連動評価による精度向上）
- **離脱率**: 30%削減（内面描写評価とエラー具体化）
- **学習コスト**: 75%削減（TDD+DDD統合ガイド）

## 🔧 環境要件

### 必須環境
- Python 3.10+
- Git
- テキストエディタ（VS Code推奨）

### オプション（推奨）
- **GNU parallel**: 大規模プロジェクトでの並列処理による品質チェック高速化
  - Ubuntu/Debian: `sudo apt install parallel`
  - macOS: `brew install parallel`
  - Windows WSL: `sudo apt install parallel`
- 小説家になろうアカウント（分析機能用）

## 🚀 初回セットアップ

```bash
# 1. 依存関係インストール（pyproject.toml統合版）
cd 00_ガイド
pip install .[dev]  # 開発環境一式をインストール

# または用途別インストール:
# pip install .        # 基本依存関係のみ
# pip install .[test]  # テスト依存関係のみ
# pip install .[lint]  # リント依存関係のみ

# 1-2. 並列処理最適化（推奨）
# Ubuntu/Debian/WSL:
sudo apt update && sudo apt install parallel

# macOS:
# brew install parallel

# 2. プロジェクトショートカットの設置（推奨）
python3 setup/setup_project_shortcuts.py

# 3. グローバルコマンドの設定（任意）
# bashの場合
# bin/novelへのパスを追加
export PATH="$PATH:/path/to/00_ガイド/bin"
source ~/.bashrc

# 2. 環境設定（プロジェクト内で実行）
source setup/setup_env.sh /path/to/your/project

# 3. グローバル設定
python setup/novel_config.py init

# 4. 動作確認
python main/diagnose.py
```

### 📦 現代的な依存関係管理（2025年8月3日統合完了）

本システムは**pyproject.toml**による現代的なPython依存関係管理を採用しています：

**主な変更点：**
- ✅ `requirements.txt` → pyproject.toml に統合完了
- ✅ `requirements-dev.txt` → pyproject.toml に統合完了
- ✅ PEP 621準拠のproject設定セクション実装
- ✅ 用途別依存関係グループ（dev, test, lint）

**利点：**
- 🎯 依存関係の一元管理
- 🔧 他ツールとの互換性向上
- 📈 現代的なPythonプロジェクト標準準拠
- 🧹 ルートディレクトリの簡素化

## 🧪 TDD（テスト駆動開発）

このシステムは包括的なTDD環境を提供します：

### テスト実行
```bash
make test              # 全テスト実行（LLM要約は既定で有効）
make validate-templates # 品質テンプレートのスキーマ検証
make test-fast         # slowマーカー除外で高速確認
make test-slow         # 遅い統合/E2Eのみ
make test-last         # 直近失敗の再実行（-x）
make test-changed      # 差分ファイルのテスト（なければ last-failed）
make coverage          # カバレッジ付きテスト
make pre-commit        # コミット前チェック

# 個別/絞り込み（LLM要約は自動）
make test FILE=tests/test_api.py::TestUser::test_create
make test K='user and not slow'
make test M='unit' VV=1

# JSON要約のみ（/test-json 相当）
/bin/test-json -q

# ラッパ直呼び（/test 対応の薄い入口）
bin/test -q
bin/test-failed
RANGE='origin/master...HEAD' bin/test-changed -q

# 依存プラグイン: bin/test 系コマンドは `pytest-timeout` を利用します。未導入環境では
#   pip install pytest-timeout
# を実行してから再試行してください。

# 推奨: テストは scripts/run_pytest.py または `make test` を利用してください（環境/出力を統一）
# 直pytestでLLM要約を有効化したい場合
pytest -q --llm-report
# または
LLM_REPORT=1 pytest -q

# 生成物（レポート）
# - reports/llm_summary.jsonl
# - reports/llm_summary.txt
# - reports/llm_summary.attachments.jsonl（テスト実行時の添付ログマニフェスト）
# - reports/artifacts/<run_id>/pytest*.log（pytest 実行ログ、xdist 時はワーカー別）
```

#### sandbox/xdist環境での回避例
テスト環境によっては pyproject.toml の `addopts` 設定が使用できない場合があります:

```bash
# xdist/並列実行が利用できない環境での回避例
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTEST_ADDOPTS='' pytest -q -c /dev/null tests/unit/

# 収集ルート逸脱防止と一時ディレクトリ制御
pytest --rootdir . --basetemp temp/pytest tests/unit/specific_test.py

# strictモード時のCI推奨設定（fallback検出で失敗）
pytest -q --fail-on-path-fallback tests/integration/
```

### TDD関連文書
- **[TDD改善提案.md](TDD改善提案.md)** - 導入計画・実装戦略
- **[テストガイドライン.md](テストガイドライン.md)** - 日常的な開発指針
- **[scripts/TDD継続的改善プロセス.md](scripts/TDD継続的改善プロセス.md)** - 継続的改善サイクル
- **[scripts/README_TDD.md](scripts/README_TDD.md)** - TDD統合ガイド

### 品質メトリクス（2025年7月28日更新）
- **ruffリンター適合**: 主要エラー248件自動修正済み（残り4950件改善進行中）
- **TDD+DDD準拠**: 100% (新機能は完全TDD準拠実装)
- **統合インポート管理**: 統合インポートパターン準拠・統一化完了
- **型安全性向上**: 主要ドメインエンティティの型注釈追加完了
- **品質ゲート**: 5/5チェック合格（構文エラー0件達成）
- **複雑度改善**: 高複雑度関数111件のリファクタリング完了
- **パフォーマンス**: 単一話3秒、複数話1秒
- **視点情報連動評価**: 100%動作確認済み
- **適応的品質基準**: 19テストケース全通過

## 📁 プロジェクト構造

**標準化されたPythonプロジェクト構造** (2025年8月更新)

```
00_ガイド/
├── src/noveler/              # アプリケーションコード
│   ├── domain/              # ドメインロジック
│   ├── application/         # アプリケーションサービス
│   ├── infrastructure/      # インフラストラクチャ
│   └── presentation/        # プレゼンテーション層
├── tests/                   # テストコード（標準化移行完了）
│   ├── unit/               # ユニットテスト
│   ├── integration/        # 統合テスト
│   └── e2e/               # E2Eテスト
├── scripts/                 # プロジェクト管理スクリプト
│   ├── setup/              # 環境設定スクリプト
│   └── project_novel_shortcut.sh  # プロジェクト用ショートカット
├── templates/              # テンプレートファイル
│   ├── claude_quality/     # 品質チェック設定
│   └── plot_requests/      # プロット生成テンプレート
├── bin/                    # 実行可能ファイル
└── docs/                   # ドキュメント
```

### 📋 主な変更点（2025年8月29日）
- ✅ **テスト構造標準化**: `src/noveler/tests/` → `tests/` 移行完了
- ✅ **スクリプト整理**: 環境設定・プロジェクト管理スクリプトを`scripts/`に統合
- ✅ **テンプレート統合**: 全テンプレートを`templates/`に一元化
- ✅ **DDD準拠**: Domain/Application/Infrastructure層の明確な分離
- ✅ **標準構造**: Pythonプロジェクトの標準的な構造に準拠

## 🧰 品質ツールとCI連携（MCP / NDJSON）

- MCPツール: `run_quality_checks`, `check_rhythm`, `check_style`, `check_grammar`, `fix_quality_issues`, `export_quality_report`, `improve_quality_until`, `polish_manuscript`, `polish_manuscript_apply`, `polish`
  - ロールバック: `restore_manuscript_from_artifact`（artifact_idの本文を原稿へ適用）
- 設定: ルートに `.novelerrc.yaml`、および `.noveler/quality_ignore.json`

### 統合チェック（B20準拠強化点）

- 出力軽量化・同一箇所の重複検出は統合側で自動集約（severityは最大値、`details.aspects` に検出元アスペクトを記録）。
- 総合スコアは既定「最小値」。`weights` を指定すると重み付き平均で計算し、`metadata.score_method` に `weighted_average` を記録。
- サブツールは `content` を優先受理し、統合から本文を渡すことで重複I/Oを削減。
- 既存の `format: summary|ndjson`、ページング、`fail_on` はそのまま利用可能。

例: 重み付き平均で実行（CIの段階ゲートと相性良）

```bash
noveler mcp call run_quality_checks '{
  "episode_number": 1,
  "additional_params": {
    "format": "summary",
    "weights": {"rhythm":0.35,"readability":0.35,"grammar":0.2,"style":0.1}
  }
}'
```

### CIでのNDJSON出力と失敗条件

```bash
python scripts/ci/run_quality_checks_ndjson.py \
  --file-path path/to/manuscript.txt \
  --severity-threshold medium \
  --fail-on-score-below 80 \
  --fail-on-severity-at-least high \
  --out reports/quality.ndjson
```

- 標準出力にNDJSONが流れ、`should_fail` が真のとき終了コード2で終了します。
- `.novelerrc.yaml` で `sentence_split`/`sentence_merge`/`morphology`/`stage1` を調整できます（行幅/自動改行の設定は撤廃）。
  - `stage1.*` で技術推敲（字下げ・？！後スペース等）の自動修正も制御可能
 - `defaults.weights` を指定すると重み付き平均で総合スコアを計算します（既定は最小値）。
 - 同一箇所の多重検出は統合側で自動集約されます（`details.aspects` に検出元の観点を付記）。
 - `format: ndjson` を指定した場合、ページング適用後の範囲のみが `metadata.ndjson` に同梱されます（先頭は `SUMMARY`）。
 - ページングは `page_size` 優先。未指定かつ多数ヒット時は既定200件に切り詰め、`metadata.pagination` と `truncated: true` を付与します。

追加の失敗条件（パスフォールバック可視化）:

```bash
# PathServiceのフォールバック（旧配置/命名への依存）が検出されたらCI失敗
python scripts/ci/run_quality_checks_ndjson.py \
  --project-root /path/to/project \
  --episode 1 \
  --fail-on-path-fallback
```

- NDJSON各行に `path_fallback_used` と `path_fallback_events_count` を付与しています。
- 00_ガイド配下で `--project-root` を省略して実行した場合、隣接のサンプル「10_Fランク魔法使いはDEBUGログを読む」を自動対象化（存在時のみ）。

### CIスモーク: A40 polish_manuscript_apply（dry-run）

GitHub Actionsの `cli-smoke.yml` にて、`polish_manuscript_apply` を `dry_run: true` で実行し、
差分/レポート/改稿本文の参照IDが返ることをスモーク検証します。

```yaml
- name: MCP A40 polish_manuscript_apply dry-run smoke
  env:
    MCP_STDIO_SAFE: '1'
    NOVEL_PRODUCTION_MODE: '1'
  run: |
    python bin/noveler mcp call polish_manuscript_apply '{
      "episode_number": 1,
      "file_path": "README.md",
      "stages": ["stage2","stage3"],
      "dry_run": true,
      "save_report": false
    }' | tee polish_apply_smoke.json || echo "Non-zero exit tolerated"
```

追加の失敗条件（パスフォールバック可視化）:

```bash
# PathServiceのフォールバック（旧配置/命名への依存）が検出されたらCI失敗
python scripts/ci/run_quality_checks_ndjson.py \
  --project-root /path/to/project \
  --episode 1 \
  --fail-on-path-fallback
```

- NDJSON各行に `path_fallback_used` と `path_fallback_events_count` を付与しています。
- 00_ガイド配下で `--project-root` を省略して実行した場合、隣接のサンプル「10_Fランク魔法使いはDEBUGログを読む」を自動対象化（存在時のみ）。

### Writeツールのスモーク実行（CI/ローカル）

LLM不要のオフライン・スモークとして、writeツールの基本動作（出力先解決・プロンプト雛形生成）を検証できます。

```bash
# JSONを標準出力 + ファイル保存（フォールバックは検出のみ）
python scripts/ci/run_write_smoke.py \
  --project-root . \
  --episode 1 \
  --out reports/write_smoke.json

# フォールバックをCI失敗条件に含める場合
python scripts/ci/run_write_smoke.py \
  --project-root . \
  --episode 1 \
  --fail-on-path-fallback
```

- 出力: `{ success, episode, manuscript_path, prompt, plot_artifact_id?, path_fallback_used, path_fallback_events }`
- CI: `.github/workflows/quality-ndjson-check.yml` でスモーク実行済み（アーティファクト `write-smoke`）。

### パス管理のstrictモード（推奨）

- 目的: 旧仕様の命名・配置にフォールバックせず、逸脱を早期検出するためのモード
- 有効化方法:
  - 環境変数: `NOVELER_STRICT_PATHS=1`（`true`/`yes`/`on` も可）
  - 設定ファイル: `config/novel_config.yaml` の `paths.strict: true`
  - または `.novelerrc.yaml` に以下を追加:
    ```yaml
    paths:
      strict: true
    ```
- 挙動:
  - `PathService.get_episode_plot_path`/`get_episode_title` で旧仕様フォールバックが必要になった場合、strict時は `PathResolutionError` を送出
  - 非strict時は警告ログを出力しつつ動作継続
- 推奨運用:
  - 開発中は非strictで警告を見える化→修正
  - CI/本番は strict を有効化して逸脱を遮断

### パス移行ツール（旧命名→新命名）

旧仕様の命名・配置（例: 20_プロット直下の話別プロット、原稿の無題命名など）を検出・移行するツールを提供します。

```bash
# 検出のみ
python scripts/tools/paths_validate_migrate.py validate \
  --project-root /path/to/project \
  --json-out reports/paths_validate.json

# 自動移行（ドライラン）
python scripts/tools/paths_validate_migrate.py migrate \
  --project-root /path/to/project \
  --fix-manuscripts --fix-plots --dry-run \
  --json-out reports/paths_migrate_plan.json

# 実行移行（慎重に）
python scripts/tools/paths_validate_migrate.py migrate \
  --project-root /path/to/project \
  --fix-manuscripts --fix-plots
```

詳細は `docs/references/config_paths.md` を参照してください。

### 個別ツールの直接実行（LLM裁量用）

- `check_rhythm` / `check_readability` / `check_grammar` / `check_style` は個別に呼び出し可能です。統合で概要を掴んだ後、必要なアスペクトのみ深掘りする用途を想定しています。
- `fix_quality_issues` は安全な理由コード（約物統一・短文/長文の安全分割/連結・句読点の基本正規化など）に限定して自動修正を行います（行幅に関する自動改行・警告は提供しません）。
- `improve_quality_until` は各アスペクトごとに「自動修正→再評価」を反復し、合格スコア（既定80点）まで改善します（本文は既定で同梱せず、ハッシュ/ID中心）。

 例: `improve_quality_until` の実行

```bash
noveler mcp call improve_quality_until '{
  "episode_number": 1,
  "additional_params": {
    "file_path": "40_原稿/第001話_サンプル.md",
    "aspects": ["rhythm", "readability", "grammar"],
    "target_score": 80,
    "max_iterations": 3,
    "include_diff": false
  }
}'
```

注意（reason_codesの指定形式）:
- `fix_quality_issues` は `reason_codes: string[]`（配列）。
- `improve_quality_until` は `{ aspect: string[] }`（オブジェクト）推奨ですが、後方互換で配列も受理します。
  - 配列で渡した場合は、指定した全アスペクトに同一セットを適用します。
  - 例（オブジェクト）: `reason_codes: { "rhythm": ["CONSECUTIVE_LONG_SENTENCES","ELLIPSIS_STYLE","DASH_STYLE"] }`
  - 例（配列・後方互換）: `reason_codes: ["DASH","CONSECUTIVE_LONG_SENTENCES"]`（実行時に正規化: `DASH`→`DASH_STYLE`。非対応コードは `metadata.ignored_reason_codes` に記録）

例: `fix_quality_issues` の実行（安全自動修正）

```bash
noveler mcp call fix_quality_issues '{
  "episode_number": 1,
  "additional_params": {
    "file_path": "40_原稿/第001話_サンプル.md",
    "reason_codes": ["ELLIPSIS_STYLE","DASH_STYLE","COMMA_OVERUSE"],
    "dry_run": false,
    "include_diff": false
  }
}'
```

例: `check_style` の実行（体裁・スタイル）

```bash
noveler mcp call check_style '{
  "episode_number": 1,
  "additional_params": { "file_path": "40_原稿/第001話_サンプル.md" }
}'
```

例: `export_quality_report` の実行（Markdownレポート出力）

```bash
noveler mcp call export_quality_report '{
  "episode_number": 1,
  "additional_params": {
    "file_path": "40_原稿/第001話_サンプル.md",
    "format": "md",
    "destination": "reports/quality/quality_episode001.md",
    "template": "compact",
    "include_details": false
  }
}'
```

- CLIレスポンスの `metadata` には `output_path` や `file_hash` に加えて `aspect_scores` と `score_method` が含まれます。JSON/CSV/NDJSON 形式でもこの情報を参照できるため、Markdown以外の保存でも各アスペクトの評価指標を後処理に利用できます。

## 📞 サポート

- **ガイド**: 各機能の詳細は対応するガイドファイルを参照
- **トラブル**: [B40_トラブルシューティング](B_技術ガイド/B40_システム運用/B40_トラブルシューティング.md)
- **アーカイブ**: 旧ガイドは `90_アーカイブ/` フォルダ内

---

**開始方法**: まず [01_クイックスタート](docs/guides/quick_start.md) をお読みください。
### A40 Stage2/Stage3（内容推敲・読者体験）プロンプト生成（導線）

```bash
# ステージ別の統合プロンプトを生成（LLMに渡して改稿する導線）
noveler mcp call polish_manuscript '{
  "episode_number": 1,
  "file_path": "40_原稿/第001話_タイトル.md",
  "stages": ["stage2", "stage3"],
  "dry_run": true
}'

# 出力: metadata.prompts.stage2 / stage3 をLLMへ渡す
```

#### 便利エイリアス（polish）

```bash
# mode: apply（一気通貫）| prompt（プロンプト生成のみ）
noveler mcp call polish '{
  "episode_number": 1,
  "file_path": "40_原稿/第001話_タイトル.md",
  "mode": "apply",
  "stages": ["stage2", "stage3"],
  "dry_run": true
}'
```

### A40 Stage2/Stage3 一気通貫適用（LLM実行→適用→レポート）

```bash
noveler mcp call polish_manuscript_apply '{
  "episode_number": 1,
  "file_path": "40_原稿/第001話_タイトル.md",
  "stages": ["stage2","stage3"],
  "dry_run": false,
  "save_report": true
}'

# 出力:
# - metadata.diff_artifact / report_artifact に参照ID
# - 50_管理資料/品質記録 に A41レポートを保存（既定）
```

### 改稿ロールバック/適用（artifact_id指定）

```bash
noveler mcp call restore_manuscript_from_artifact '{
  "episode_number": 1,
  "file_path": "40_原稿/第001話_タイトル.md",
  "artifact_id": "artifact:xxxxxxxxxxxx",
  "dry_run": false,
  "create_backup": true
}'

# 出力: metadata.diff_artifact に差分、backup_path/written_to を返却
```


CLI Tip
- `noveler check <episode|file> [--auto-fix] [--exclude-dialogue]`
  - `--exclude-dialogue` excludes dialogue lines (「…」/『…』) from sentence-length checks.
  - Alternatively set `NOVELER_EXCLUDE_DIALOGUE=1` to default this behaviour.
