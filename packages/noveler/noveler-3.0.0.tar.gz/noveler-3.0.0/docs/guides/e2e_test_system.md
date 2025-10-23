# E2Eテストシステム運用ガイド

## 概要

本プロジェクトに構築されたエンドツーエンド（E2E）テストシステムの運用ガイドです。実際のユーザーワークフローを想定した包括的なテストが可能です。

## システム構成

### 🏗️ アーキテクチャ

```
E2Eテストシステム/
├── テストファイル層/                   # 実際のテストケース
│   ├── test_workflow_integration_e2e.py    # 統合ワークフロー
│   ├── test_quality_workflow_e2e.py        # 品質保証ワークフロー
│   ├── test_scenario_integration_e2e.py    # 複雑シナリオ統合
│   └── test_performance_stress_e2e.py      # パフォーマンス・ストレス
├── 実行基盤層/                        # テスト実行インフラ
│   ├── conftest.py                         # pytest設定・フィクスチャ
│   ├── pytest_e2e.ini                     # E2E専用pytest設定
│   └── BaseE2ETestCase                     # 共通テストベース
├── 実行スクリプト層/                   # 実行・制御スクリプト
│   ├── run_e2e_tests.sh/.bat              # テスト実行スクリプト
│   ├── generate_e2e_report.sh             # レポート生成スクリプト
│   └── Makefile.e2e                       # Make統合
└── 分析・レポート層/                   # 結果分析・可視化
    ├── analyze_e2e_coverage.py            # カバレッジ分析
    ├── HTMLレポート生成                    # 視覚的なレポート
    └── JSON API出力                       # 機械可読な結果
```

### 🧪 テストカテゴリ

1. **統合ワークフローテスト** (`test_workflow_integration_e2e.py`)
   - 完全執筆ワークフロー：プロジェクト作成→プロット→執筆→バックアップ
   - 品質保証ワークフロー：執筆→品質チェック→修正→検証
   - プロジェクト管理ワークフロー：作成→ステータス→ヘルス→メンテナンス

2. **品質保証ワークフローテスト** (`test_quality_workflow_e2e.py`)
   - 品質チェック→問題検出→修正提案→再チェック
   - 適応的品質基準の段階的向上
   - 長期品質トレンド分析

3. **シナリオ統合テスト** (`test_scenario_integration_e2e.py`)
   - 新規小説執筆完全フロー
   - 継続執筆作業フロー
   - エラー回復ワークフロー

4. **パフォーマンス・ストレステスト** (`test_performance_stress_e2e.py`)
   - 大容量データ処理性能
   - 並行処理の競合状態
   - メモリ使用量とリーク検出
   - 長時間実行安定性

## 🚀 基本的な使用方法

### 環境セットアップ

```bash
# 1. 仮想環境の有効化
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate     # Windows

# 2. 依存関係のインストール
make -f Makefile.e2e e2e-setup

# 3. 環境確認
make -f Makefile.e2e e2e-env-check
```

### 基本的なテスト実行

```bash
# スモークテスト（基本機能確認）
make -f Makefile.e2e e2e-smoke

# ワークフロー統合テスト
make -f Makefile.e2e e2e-workflow

# 品質保証ワークフローテスト
make -f Makefile.e2e e2e-quality

# 全てのE2Eテスト実行
make -f Makefile.e2e e2e-all
```

### 直接実行（詳細制御）

```bash
# Linux/Mac
./bin/run_e2e_tests.sh --smoke --verbose
./bin/run_e2e_tests.sh --workflow --performance
./bin/run_e2e_tests.sh --all --report

# Windows
bin\run_e2e_tests.bat --smoke --verbose
bin\run_e2e_tests.bat --workflow --performance
```

## 📊 レポート生成

### 基本レポート生成

```bash
# カバレッジ分析のみ
make -f Makefile.e2e e2e-coverage

# テスト実行+レポート生成
make -f Makefile.e2e e2e-report

# フル機能レポート（テスト+カバレッジ+統合レポート）
make -f Makefile.e2e e2e-full-report
```

### 生成されるレポート

1. **HTMLレポート**
   - `temp/reports/e2e_*/integrated_e2e_report.html`
   - テスト結果、カバレッジ、統計情報を統合

2. **カバレッジレポート**
   - `temp/reports/e2e_*/e2e_coverage_report.html`
   - コマンドカバレッジ、シナリオカバレッジ、不足項目

3. **JSONレポート**
   - `temp/reports/e2e_*/e2e_coverage_report.json`
   - 機械可読な詳細データ

4. **JUnit XML**
   - `temp/reports/e2e_*/e2e_test_results.xml`
   - CI/CD統合用

## ⚡ 高度な使用方法

### 特定テストファイルの実行

```bash
# 特定テストファイルのみ実行
make -f Makefile.e2e e2e-workflow-integration
make -f Makefile.e2e e2e-quality-workflow
make -f Makefile.e2e e2e-scenario-integration
make -f Makefile.e2e e2e-performance-stress
```

### パフォーマンス分析

```bash
# プロファイリング付き実行
make -f Makefile.e2e e2e-profile

# パフォーマンス・ストレステストのみ
make -f Makefile.e2e e2e-performance
make -f Makefile.e2e e2e-stress
```

### 並列実行（注意: リソース競合の可能性）

```bash
# 並列実行
./bin/run_e2e_tests.sh --workflow --parallel

# または
make -f Makefile.e2e e2e-parallel
```

### デバッグ実行

```bash
# デバッグモード
./bin/run_e2e_tests.sh --smoke --debug

# または
make -f Makefile.e2e e2e-debug
```

## 🔧 高度な設定

### pytest設定のカスタマイズ

`tests/e2e/pytest_e2e.ini`を編集：

```ini
[tool:pytest]
# タイムアウト調整
timeout = 300

# 詳細出力レベル
addopts = [
    "--tb=long",              # 詳細トレースバック
    "--durations=20",         # 遅いテスト上位20個表示
    "--maxfail=3",           # 3個失敗で停止
]

# カスタムマーカー追加
markers = [
    "custom_scenario: カスタムシナリオテスト",
]
```

### GUIDE_ROOTでの実行とサンプルプロジェクト解決

GUIDE_ROOT（このリポジトリ直下）でテストを実行する場合、実在するサンプル小説プロジェクトを基点にE2Eを流します。プロジェクトルートの解決順は以下の通りです。

- 優先順（上ほど優先）
  1) 環境変数 `PROJECT_ROOT` または `NOVELER_TEST_PROJECT_ROOT`
  2) 設定ファイル `config/novel_config.yaml` の `paths.samples.root`
  3) 環境変数 `NOVELER_SAMPLES_ROOT`（サンプル親ディレクトリ）または既定サンプル
  4) 最終フォールバック: カレントディレクトリ（`cwd`）

- 既定（本リポジトリでは設定済み）
  - `config/novel_config.yaml` に以下を追記済みです。
    ```yaml
    paths:
      samples:
        root: "/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/10_Fランク魔法使いはDEBUGログを読む"
    ```

- 上書きしたい場合
  - 一時的に環境変数を利用:
    ```bash
    export PROJECT_ROOT="/path/to/your/sample-project"
    pytest -c tests/e2e/pytest_e2e.ini -q
    ```
  - 恒久的に設定ファイルを変更:
    ```yaml
    # config/novel_config.yaml
    paths:
      samples:
        root: "/absolute/path/to/sample-project"
    ```

- 実行例
  ```bash
  # GUIDE_ROOT直下で
  pytest -c tests/e2e/pytest_e2e.ini -m e2e -q
  # もしくはMakefile.e2eから
  make -f tests/e2e/Makefile.e2e e2e-workflow
  ```

### 環境変数による制御

```bash
# テストタイムアウト調整
export E2E_TIMEOUT=600

# 詳細出力制御
export E2E_VERBOSE=1

# レポート出力先変更
export E2E_REPORT_DIR=/path/to/custom/reports
```

### カスタムテストシナリオの追加

新しいE2Eテストファイルを作成：

```python
#!/usr/bin/env python3
"""カスタムE2Eテスト"""

import pytest
from scripts.tests.unit.infrastructure.test_base import BaseE2ETestCase

class TestCustomE2E(BaseE2ETestCase):
    """カスタムE2Eテスト"""

    @pytest.mark.e2e
    @pytest.mark.custom_scenario
    def test_custom_workflow(self):
        """カスタムワークフローテスト"""
        # カスタムテストロジック
        pass
```

## 🔍 トラブルシューティング

### よくある問題と対処法

#### 1. テスト実行時のタイムアウト

```bash
# タイムアウト値を増加
./bin/run_e2e_tests.sh --smoke --timeout 600
```

#### 2. メモリ不足エラー

```bash
# 軽量テストのみ実行
make -f Makefile.e2e e2e-fast

# ストレステストを除外
./bin/run_e2e_tests.sh --workflow --fast
```

#### 3. 並行実行での競合エラー

```bash
# シーケンシャル実行に変更
./bin/run_e2e_tests.sh --workflow  # --parallel オプションを除去
```

#### 4. 権限エラー（Linux/Mac）

```bash
# スクリプトに実行権限を付与
chmod +x bin/run_e2e_tests.sh
chmod +x bin/generate_e2e_report.sh
chmod +x bin/analyze_e2e_coverage.py
```

### 環境診断

```bash
# 包括的な環境診断
make -f Makefile.e2e e2e-troubleshoot

# 統計情報確認
make -f Makefile.e2e e2e-stats
```

### ログの確認

```bash
# 最新のE2Eテストログ
ls -la temp/logs/e2e_test_*

# エラーログの内容確認
tail -n 50 temp/logs/e2e_test_*.log
```

## 📈 CI/CD統合

### GitHub Actions統合例

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: make -f Makefile.e2e e2e-setup

      - name: Run E2E tests
        run: make -f Makefile.e2e e2e-ci

      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: e2e-reports
          path: temp/reports/
```

### Jenkins統合例

```groovy
pipeline {
    agent any
    stages {
        stage('E2E Tests') {
            steps {
                sh 'make -f Makefile.e2e e2e-setup'
                sh 'make -f Makefile.e2e e2e-ci'
            }
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'temp/reports/',
                        reportFiles: 'integrated_e2e_report.html',
                        reportName: 'E2E Test Report'
                    ])
                }
            }
        }
    }
}
```

## 🎯 ベストプラクティス

### テスト作成のガイドライン

1. **テスト分離の確保**
   - 各テストは独立して実行可能であること
   - テスト間でのデータ共有を避ける
   - 専用のテンポラリディレクトリを使用

2. **適切なタイムアウト設定**
   - 軽量テスト: 30秒以内
   - 統合テスト: 2分以内
   - ストレステスト: 10分以内

3. **リソース使用量の管理**
   - メモリ使用量の監視
   - CPU使用率の制限
   - 並行実行時の競合回避

4. **エラーハンドリング**
   - 予想されるエラーのテスト
   - 適切なエラーメッセージの検証
   - 復旧処理のテスト

### パフォーマンス最適化

1. **テスト実行順序**
   - スモークテスト→統合テスト→ストレステスト
   - 失敗しやすいテストを早期に実行
   - 重いテストは最後に実行

2. **リソース管理**
   - ガベージコレクションの適切な実行
   - 一時ファイルの適切なクリーンアップ
   - メモリリークの監視

3. **並列実行の制御**
   - リソース競合の回避
   - 適切なワーカー数の設定
   - ファイルロックの適切な使用

## 🚦 運用監視

### メトリクス収集

- テスト実行時間の追跡
- メモリ使用量の監視
- 成功率の追跡
- カバレッジの推移

### アラート設定

- テスト成功率の低下（80%を下回る）
- 実行時間の異常な増加（前回の1.5倍以上）
- メモリ使用量の異常な増加（500MB以上）

### 定期的なメンテナンス

- 古いレポートファイルの削除
- テンポラリファイルのクリーンアップ
- テストケースの見直しと更新

---

このE2Eテストシステムにより、実際のユーザーワークフローに近い包括的なテストが可能になり、システムの品質と安定性を確保できます。


### Fail-only NDJSON（CI既定ON）

- CIでは `LLM_REPORT_STREAM_FAIL=1` を既定有効化し、失敗フェーズのみをNDJSONで逐次記録します。
  - ワーカー別: `reports/stream/llm_fail_<worker>.ndjson`
  - 集約: セッション終了時に `reports/llm_fail.ndjson` へ統合し、末尾に `session_summary` を1行追記します。
  - レコード: `{ts,event,test_id,phase,outcome,duration_s,worker_id}`（summaryには failed/error/crashed 件数を含みます）
- ローカルで無効化したい場合は `LLM_REPORT_STREAM_FAIL=0` を設定してください。
