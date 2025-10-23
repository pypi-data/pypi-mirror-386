# DEVELOPER GUIDE

> ℹ️ **CLI移行メモ**: 本ガイドには旧 `bin/novel` コマンドの例が残っています。実運用では `./bin/noveler` および MCP ツールを利用してください。最新手順は [docs/migration/novel_to_noveler.md](../migration/novel_to_noveler.md) を参照のうえ、必要に応じて記載コマンドを読み替えてください。

開発者向け技術ガイド統合版。Claude Code開発時に必要なコマンド・アーキテクチャ・テスト情報を統合。

## 📚 関連ドキュメント

### **システム開発**
- [docs/B20_Claude_Code開発作業指示書.md](docs/B20_Claude_Code開発作業指示書.md) - **📊 SPEC-901 MessageBus/DDD統合** 開発プロセス
- [docs/B21_DDD_TDD統合開発プロセス.md](docs/B21_DDD_TDD統合開発プロセス.md) - DDD/TDD開発プロセス
- [docs/B32_共通コンポーネント品質管理ガイド.md](docs/B32_共通コンポーネント品質管理ガイド.md) - 品質管理

### **執筆システム**
- [docs/A30_執筆ワークフロー.md](docs/A30_執筆ワークフロー.md) - 執筆総合ガイド（人間向け）
- [docs/A30_AI構造設計プロンプト集.md](docs/A30_AI構造設計プロンプト集.md) - Claude Code向け骨格設計
- [docs/A30_統合執筆ワークフロー.md](docs/A30_統合執筆ワークフロー.md) - AIと人間の協創ワークフロー
- [docs/A28_話別プロットプロンプト.md](docs/A28_話別プロットプロンプト.md) - **v3.0** 話別プロンプト・作成手順（統合版）
- [docs/A32_執筆コマンドガイド.md](docs/A32_執筆コマンドガイド.md) - CLIコマンド

## 🚀 クイックリファレンス

### 最頻用コマンド（MCP / 現行導線）
```bash
# 品質チェック（要約）
noveler mcp call run_quality_checks '{"episode_number": 1, "additional_params": {"format": "summary"}}'

# 原稿整形（ドライラン）
noveler mcp call polish_manuscript '{"episode_number": 1, "file_path": "40_原稿/第001話_サンプル.md", "stages": ["stage2"], "dry_run": true}'

# テスト（LLM要約は既定ON）
make test
make test-last
make test-changed

# 品質ゲート
python scripts/tools/quality_gate_check.py
```

<!-- Deprecated: 旧CLI codemap系コマンドは廃止。必要なら CODEMAP.yaml とCIジョブを参照。 -->

### Claude Code統合ヒント（v2.0）
```bash
# MCPサーバー起動
noveler mcp-server --port 3000

# 設定確認（環境変数 + .novelerrc.yaml を参照）
echo $CLAUDE_CODE_MAX_TURNS
```

### 環境構築
```bash
pip install .[dev]               # 開発環境一式
pre-commit install              # Git hooks設定（自動修正統合対応）

# ログ分析ユーティリティ（LogAnalyzer）を利用する場合は追加で NumPy をインストール
pip install numpy
```

### pre-commit自動修正システム（2025/8/15統合完了）
```bash
# 統合自動修正フロー（問題発見時に自動修正実行）
git commit -m "your changes"     # 自動修正が問題発見時に実行される

# 手動での品質チェック＆自動修正
pre-commit run --all-files       # 全ファイル対象の品質チェック＆自動修正
pre-commit run unified-auto-syntax-fix    # 統合構文エラー自動修正
pre-commit run b30-quality-auto-fix       # B30統合品質チェック＆自動修正

# 段階的品質レベルでの検証
python scripts/tools/quality_gate_check.py --level BASIC     # 基本レベル
python scripts/tools/quality_gate_check.py --level MODERATE  # B30基本準拠（推奨）
python scripts/tools/quality_gate_check.py --level STRICT    # B30完全準拠
```

## 📋 コマンドリファレンス

### エピソード管理
```bash
novel write 1                           # 第1話の執筆
novel complete プロジェクト名 1          # 第1話の完成処理
novel check プロジェクト名 1             # 第1話の品質チェック
```

### プロット作成（A24 v3.0対応）
```bash
# A24データ分析手順統合版プロット作成
novel plot episode 12 --title "調査の深化"    # 段階的プロット作成（推奨）
novel plot episode 12 --quick              # 簡易版プロット作成
novel plot episode 12 --template-only      # テンプレートコピーのみ

# プロンプト生成（AI執筆支援）
novel prompt generate-plot 12              # A24 v3.0プロンプト生成
```

### テスト実行
```bash
novel test run                          # 高速テスト実行（推奨）
novel test run --unit                   # 単体テストのみ
novel test run --integration            # 統合テストのみ
novel test run --coverage               # カバレッジレポート生成
pytest                                  # 従来のpytest実行
pytest --cache-clear                    # キャッシュを捨てたうえでの再実行
```

> 💡 **テスト後クリーンアップの挙動を調整したい場合**
>
> - `NOVELER_TEST_CLEANUP_MODE`
>   - `full`（既定）: プロジェクト全体を走査してテスト生成物を削除。CI など従来の挙動を維持。
>   - `fast`: 既知のキャッシュディレクトリ（`.pytest_cache`/`.ruff_cache` など）のみを掃除し、走査時間を短縮。ローカル開発での高速テスト向け。
>   - 使用例: `NOVELER_TEST_CLEANUP_MODE=fast python3 scripts/run_pytest.py -n0 tests/unit/...`
>
> - `NOVELER_TEST_CLEANUP_TIMEOUT`
>   - クリーンアップ処理の最大実行時間（秒）を指定。超過すると処理を打ち切り、`result["aborted"] = True` と警告ログを出力。
>   - 使用例: `NOVELER_TEST_CLEANUP_TIMEOUT=30 novel test run`
>
> いずれも未指定の場合は `full` モード / 無制限で動作します。CI ではデフォルト値のまま運用し、ローカルで必要に応じて切り替えてください。

> 🔎 **Domain依存ガードを更新した場合**
>
> - `tests/unit/domain/test_domain_dependency_guards.py` は pytest のキャッシュにスキャン結果を保存します。Domain 配下のファイルを編集した直後は `pytest --cache-clear tests/unit/domain/test_domain_dependency_guards.py` でキャッシュを無効化してから再実行してください。
> - 並列実行時は `bin/test -n=2 -m "(not e2e) and (not integration_skip)" --maxfail=1` のようにマーカー条件を明示すると安定します。`integration_skip` を含める場合は個別にテストを確認してください。

> 🆔 **run_id と成果物出力のベストプラクティス**
>
> - 並列（xdist）時は `run_id=YYYYMMDD_HHMMSS_{worker}` を推奨し、`reports/{worker}/` のようにワーカー別ディレクトリへ出力を分離してください。
> - 既定は `bin/test --xdist-auto` の利用を推奨します。長時間化防止のため `--timeout=300` 等のタイムアウト設定を併用してください（pytest-timeout）。
> - 大量のアーティファクトを生成するタスクは 30日を目安にクリーンアップする運用を推奨します（CI ではビルドごとに清掃）。

### システム診断・修復
```bash
novel health check                      # 総合診断
novel health fix                        # 自動修復
novel error-monitor start --auto-fix   # エラー監視開始
novel claude-export                     # Claude向けエラー出力
```

### 品質チェック
```bash
python scripts/tools/check_import_style.py    # インポートスタイル
python scripts/tools/quality_gate_check.py    # 品質ゲート
python scripts/tools/verify_commands.py       # コマンド存在確認
```

## 🗺️ CODEMAP - プロジェクト構造と品質管理

### CODEMAPとは

プロジェクトの依存関係と品質メトリクスを自動追跡する中央管理ファイル（CODEMAP.yaml）。プロジェクト構造、モジュール間依存、品質指標を一元管理。

### 主要機能

#### 1. dependency_map - モジュール間依存グラフ
- **core_dependencies**: 主要モジュールの詳細な依存関係
- **dependency_statistics**: 統計情報（最も参照されるモジュール、循環依存の検出）
- **dependency_issues**: 潜在的な問題（高結合度、レイヤー違反）

#### 2. quality_metrics - 品質メトリクス情報
- **test_coverage**: テストカバレッジ（全体/レイヤー別）
- **lint_scores**: コード品質スコア（ruff使用）
- **type_checking**: 型チェック結果（mypy使用）
- **complexity_metrics**: コード複雑度（radon使用）

### 使用方法

```bash
# 手動更新
python scripts/tools/dependency_analyzer.py

# 循環依存検出付き実行
python scripts/tools/dependency_analyzer.py --detect-circular

# GraphViz形式で依存グラフ出力
python scripts/tools/dependency_analyzer.py --export-graphviz
dot -Tpng dependency_graph.dot -o dependency_graph.png

# CLIコマンド経由
novel codemap overview              # 全体構造確認
novel codemap update                # CODEMAP更新
novel codemap check-circular        # 循環依存チェック
```

### CI/CD自動更新

GitHub Actionsで自動更新が設定済み：
- `scripts/`配下のPythonファイル変更時
- 毎日0時（UTC）に定期実行
- 手動実行も可能

### 品質基準

推奨される品質閾値：
- テストカバレッジ: 80%以上
- リントスコア: 90点以上
- 循環依存: 0個
- 高結合度モジュール: 全体の10%以下

## 🏗️ アーキテクチャ

### Claude Code統合システム（v2.0）

**概要**: `novel write`コマンドのClaude Code実行において、error_max_turns等のエラーを自動回復するシステム。段階的ターン数拡張（10→15→20）とプロンプト最適化により安定した実行を実現。

**DDD準拠設計**:
```
Domain Layer:
├── ClaudeCodeExecutionRequest (Value Object)
├── ClaudeCodeExecutionResponse (Value Object)
└── ClaudeCodeExecutionService (Domain Service)

Application Layer:
└── EnhancedIntegratedWritingUseCase
    └── _attempt_max_turns_recovery()  # 自動回復メソッド

Infrastructure Layer:
├── ClaudeCodeIntegrationService    # Claude Code実行
├── NovelConfiguration             # 設定管理システム
└── UnifiedLogger                  # 統一ログシステム
```

**自動回復フロー**:
1. **エラー検出**: error_max_turns判定
2. **プロンプト最適化**: トークン削減・構造最適化
3. **段階的拡張**: 10→15→20ターンまで自動増加
4. **フォールバック**: 全失敗時の代替ワークフロー

### Smart Auto-Enhancement システム（デフォルト品質チェック）

**概要**: `novel check` コマンドのデフォルト動作として、基本→A31→Claude分析の全段階を統合実行するシステム。

**DDD準拠設計**:
```
Domain Layer:
├── SmartAutoEnhancement (Entity)
│   ├── EnhancementRequest (Value Object)
│   ├── EnhancementResult (Value Object)
│   └── EnhancementStage (Enum)
└── SmartAutoEnhancementService (Domain Service)

Application Layer:
└── SmartAutoEnhancementUseCase

Infrastructure Layer:
├── BasicQualityCheckerAdapter  # 改善された基本品質チェック
├── A31EvaluatorAdapter        # 既存A31評価システム連携
└── ClaudeAnalyzerAdapter      # Claude分析システム連携
```

**主要改善点**:
- ✅ 平均値文字数チェック廃止（構造的品質重視）
- ✅ Protocol-based依存注入による疎結合
- ✅ 三段階統合実行による情報統合表示
- ✅ `--standard` フラグによるレガシーモード提供

### B20事前確認義務化システム（2025/8/9導入）

**概要**: 実装着手前のCODEMAP参照を義務化し、循環インポート・NIH症候群を根本的に防止するシステム。3コミット開発サイクルと統合したGit Hooks自動化を実現。

**DDD準拠設計**:
```
Domain Layer:
├── B20DevelopmentStage (Value Object)
│   ├── DevelopmentStage (Enum) - 6段階管理
│   └── StageRequirement (Enum) - 必要作業項目
├── ThreeCommitCycle (Entity)
└── B20PreImplementationCheckService (Domain Service)

Application Layer:
└── B20PreImplementationCheckUseCase
    ├── execute() - 事前チェック実行
    └── get_development_stage_guidance() - ガイダンス提供

Infrastructure Layer:
├── B20PreCommitHook - Git統合自動チェック
├── B20PostCommitHook - CODEMAP自動更新
└── B20HooksInstaller - 一括統合管理
```

**6段階開発プロセス**:
1. **SPECIFICATION_REQUIRED**: 仕様書作成必須
2. **CODEMAP_CHECK_REQUIRED**: CODEMAP確認必須
3. **IMPLEMENTATION_ALLOWED**: 実装許可状態
4. **COMMIT_ALLOWED**: コミット許可状態
5. **INTEGRATION_COMPLETE**: 統合完了
6. **DEPLOYMENT_READY**: デプロイ準備完了

**主要効果**:
- ✅ **実装前CODEMAP参照100%義務化**
- ✅ **循環インポート事前検出・防止**
- ✅ **NIH症候群防止（類似機能自動発見）**
- ✅ **Git統合による自動プロセス管理**
- ✅ **仕様書先行開発強制化**

### DDD準拠レイヤー構造
```
scripts/
├── domain/          # ビジネスロジック層（外部依存なし）
├── application/     # ユースケース層（ビジネスフロー制御）
├── infrastructure/  # 技術詳細層（外部システム連携）
├── presentation/    # プレゼンテーション層（CLI・UI）
└── tests/           # テストピラミッド
    ├── unit/        # 単体テスト（75%）
    ├── integration/ # 統合テスト（20%）
    └── e2e/         # E2Eテスト（5%）
```

### SPEC-901 MessageBus 完全実装ダイジェスト（2025-09-22）
- **主要ファイル**
  - Simple MessageBus: `src/noveler/application/simple_message_bus.py`（完全実装）
  - Outbox Repository: `src/noveler/application/outbox.py`, `src/noveler/infrastructure/adapters/file_outbox_repository.py`
  - Idempotency Store: `src/noveler/application/idempotency.py`
  - 運用CLI: `src/noveler/presentation/cli/commands/bus_commands.py`
  - Unit of Work: `src/noveler/application/uow.py`
- **出力先ディレクトリ**: `<project>/temp/bus_outbox/`
  - `pending/` に配信待ちイベント JSON を保管
  - `dlq/` に配信失敗イベント（5回試行後）を退避
  - べき等性は InMemory 管理（プロセス終了でリセット）
- **初期化手順**: テスト後にリセットする場合は `rm -rf temp/bus_outbox` を実行（次回 self-heal）。CI ではワークスペースごとに分離してコンフリクトを回避。
- **運用機能（完全実装済み）**:
  - 背景フラッシュタスク（30秒間隔、`NOVELER_DISABLE_BACKGROUND_FLUSH=1` で無効化）
  - Dead Letter Queue（DLQ、5回失敗で移行、エラー情報保持）
  - メトリクス収集（処理時間P50/P95、失敗率）
  - 運用CLI（`noveler bus flush|list|replay|health|metrics`）
- **検証用テスト**: `pytest tests/unit/application/test_message_bus_outbox.py`

### 依存方向の原則
- **Domain層**: 他の層に依存しない（純粋なビジネスロジック）
- **Application層**: Domain層のみに依存
- **Infrastructure層**: Domain層のインターフェースを実装
- **Presentation層**: Application層とInfrastructure層を統合

### CommonPathService統合アーキテクチャ
```
CommonPathService (shared_utilities.py)
├── YAML設定駆動パス管理
├── ハードコーディング排除実装
├── プロジェクトルート自動検出
└── フォールバック機能付き

影響範囲:
├── Infrastructure層: 全リポジトリ実装
├── Application層: 各種ユースケース
└── Presentation層: CLIコマンド実装
```

## 🧪 テスト戦略

### 推奨テスト実行
```bash
novel test run                   # 日常開発（最推奨）
novel test run --unit --fast    # 高速単体テスト
novel test run --lf             # 前回失敗分のみ
```

### テストピラミッド
- **Unit Tests (75%)**: Domain/Application層の高速テスト
- **Integration Tests (20%)**: Repository/外部API統合
- **E2E Tests (5%)**: CLI全体ワークフロー

### カバレッジ目標
- **全体**: 80%以上
- **Domain層**: 90%以上（ビジネスロジック重要）

## 🔧 開発フロー

### B20準拠開発フロー（2025/8/9準拠）

**事前準備（実装着手前必須）**:
```bash
# 1. システム理解・競合チェック
novel codemap overview                           # アーキテクチャ全体把握
novel codemap discover-existing <機能概要>       # 類似機能発見（NIH症候群防止）

# 2. 事前実装チェック（必須）
novel codemap pre-check <機能名> --target-layer domain --create-missing-spec

# 3. Git Hooks統合（初回のみ）
novel codemap install-hooks --git-root <プロジェクトパス> --guide-root <ガイドパス>
```

**3コミット開発サイクル（B20準拠）**:
```bash
# 第1コミット: 仕様書+失敗テスト
git checkout -b feature/SPEC-XXX-YYY-機能名
novel codemap validate-spec <機能名>             # 仕様書・CODEMAP整合性確認
git add specs/ tests/
git commit -m "docs+test: SPEC-XXX-YYY 仕様書作成 + 失敗テスト作成"

# 第2コミット: 最小実装
novel codemap track-implementation <機能名>      # 実装進捗追跡
git add scripts/domain/
git commit -m "feat: SPEC-XXX-YYY 最小実装 - 全テストパス"

# 第3コミット: 統合+リファクタリング
novel codemap integration-check <機能名>         # 全層統合確認
novel codemap finalize-implementation           # CODEMAP完成状態更新
git add -A
git commit -m "refactor: SPEC-XXX-YYY DDD適用 + CLI統合完了"
```

**Git Hooks自動化プロセス**:
- **Pre-commit**: 3コミットサイクル進行チェック + アーキテクチャ違反検出
- **Post-commit**: CODEMAP自動更新 + サイクル進行記録

## 🔧 開発フロー（従来版）

### TDD仕様駆動開発
```bash
# 1. 仕様書ID生成
python scripts/tools/spec_id_generator.py generate DOMAIN

# 2. テスト作成（@pytest.mark.spec("SPEC-XXX-YYY") 付き）
# 3. 実装（GREEN）→ リファクタリング（REFACTOR）
```

### 品質ゲート
```bash
# 開発完了前の必須チェック
python scripts/tools/quality_gate_check.py
novel test run --coverage
python scripts/tools/check_import_style.py
```

## 📁 重要ファイル

- `CLAUDE.md` - 必須コーディング規約
- `pyproject.toml` - プロジェクト設定
- `scripts/` - メインコードベース
- `temp/` - 一時ファイル・キャッシュ

## ⚡ 開発Tips

### 一般開発
- エピソード番号は常に整数指定（例: `1`, `2`, `10`）
- Pythonファイルは英語命名、原稿ファイルは日本語OK
- すべてのインポートは `scripts.` プレフィックス必須
- テスト失敗時は `--lf` オプションで効率的デバッグ

### Claude Code統合開発
- **設定管理**: `config/novel_config.yaml`の`claude_code`セクションで制御
- **エラーハンドリング**: `ClaudeCodeExecutionResponse.is_claude_code_error()`で判定
- **自動回復テスト**: `error_max_turns`をモックして自動回復フローを検証
- **ログ確認**: `get_logger(__name__)`で統一ログシステムを使用

### 設定例
```yaml
# config/novel_config.yaml - 開発用設定
claude_code:
  max_turns: 12  # 開発時はやや高めに設定
  error_handling:
    auto_retry_on_max_turns: true
    max_total_turns: 25  # テスト用に高い値
```
