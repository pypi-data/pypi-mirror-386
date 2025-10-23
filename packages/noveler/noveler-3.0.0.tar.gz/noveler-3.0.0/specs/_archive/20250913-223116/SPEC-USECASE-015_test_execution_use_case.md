# テスト実行ユースケース仕様書

## 概要
`TestExecutionUseCase`は、品質保証システムのテスト実行を統合管理するユースケースです。ユニットテスト、統合テスト、E2Eテストの実行制御、カバレッジ測定、テスト結果の分析、レポート生成、CI/CD連携を包括的に提供し、TDD開発プロセスを支援します。

## クラス設計

### TestExecutionUseCase

**責務**
- テスト実行の統合制御
- テストスイート選択と実行順序管理
- カバレッジ測定と分析
- テスト結果の集計と評価
- 失敗テストの詳細分析
- テストレポートの生成
- CI/CD パイプラインとの連携

## データ構造

### TestSuite (Enum)
```python
class TestSuite(Enum):
    UNIT = "unit"                    # ユニットテスト
    INTEGRATION = "integration"      # 統合テスト
    E2E = "e2e"                      # E2Eテスト
    ALL = "all"                      # 全テストスイート
    SMOKE = "smoke"                  # スモークテスト
    REGRESSION = "regression"        # リグレッションテスト
```

### TestExecutionMode (Enum)
```python
class TestExecutionMode(Enum):
    NORMAL = "normal"                # 通常実行
    VERBOSE = "verbose"              # 詳細出力
    FAST = "fast"                    # 高速実行（並列・スキップ）
    DEBUG = "debug"                  # デバッグモード
    CI = "ci"                        # CI環境実行
```

### TestExecutionRequest (DataClass)
```python
@dataclass
class TestExecutionRequest:
    suites: list[TestSuite] = [TestSuite.ALL]     # 実行対象スイート
    mode: TestExecutionMode = TestExecutionMode.NORMAL  # 実行モード
    coverage_enabled: bool = True                 # カバレッジ測定フラグ
    coverage_threshold: float = 80.0             # カバレッジ閾値（%）
    parallel_execution: bool = False             # 並列実行フラグ
    stop_on_failure: bool = False                # 失敗時停止フラグ
    specific_tests: list[str] = []               # 特定テスト指定
    exclude_tests: list[str] = []                # 除外テスト指定
    generate_report: bool = True                 # レポート生成フラグ
    report_format: str = "html"                  # レポート形式
    output_directory: Path | None = None         # 出力ディレクトリ
```

### TestExecutionResponse (DataClass)
```python
@dataclass
class TestExecutionResponse:
    success: bool                                # 実行成功フラグ
    message: str                                 # 実行結果メッセージ
    executed_suites: list[TestSuite] = []        # 実行されたスイート
    total_tests: int = 0                        # 総テスト数
    passed_tests: int = 0                       # 成功テスト数
    failed_tests: int = 0                       # 失敗テスト数
    skipped_tests: int = 0                      # スキップテスト数
    execution_time: float = 0.0                 # 実行時間（秒）
    coverage_percentage: float = 0.0            # カバレッジ率
    coverage_passed: bool = False               # カバレッジ閾値クリア
    failed_test_details: list[FailedTestInfo] = []  # 失敗テスト詳細
    report_file_path: Path | None = None        # レポートファイルパス
    artifacts_directory: Path | None = None     # アーティファクト格納先
```

### FailedTestInfo (DataClass)
```python
@dataclass
class FailedTestInfo:
    test_name: str                              # テスト名
    test_file: str                              # テストファイル
    suite: TestSuite                            # テストスイート
    error_message: str                          # エラーメッセージ
    stack_trace: str                            # スタックトレース
    execution_time: float                       # 実行時間
    failure_reason: str                         # 失敗理由分類
```

### CoverageResult (DataClass)
```python
@dataclass
class CoverageResult:
    overall_percentage: float                   # 全体カバレッジ率
    line_coverage: float                        # 行カバレッジ
    branch_coverage: float                      # 分岐カバレッジ
    function_coverage: float                    # 関数カバレッジ
    uncovered_files: list[str] = []             # 未カバーファイル
    low_coverage_files: list[tuple[str, float]] = []  # 低カバレッジファイル
```

## パブリックメソッド

### execute_tests()

**シグネチャ**
```python
def execute_tests(self, request: TestExecutionRequest) -> TestExecutionResponse:
```

**目的**
指定されたテストスイートを実行し、結果を分析してレポートを生成する。

**引数**
- `request`: テスト実行リクエスト

**戻り値**
- `TestExecutionResponse`: テスト実行結果

**処理フロー**
1. **実行準備**: テスト環境の準備とスイート選択
2. **テスト実行**: 各スイートの順次または並列実行
3. **結果収集**: テスト結果とカバレッジデータの収集
4. **分析処理**: 失敗分析と品質評価
5. **レポート生成**: HTML/JSON形式でのレポート作成
6. **アーティファクト保存**: ログとカバレッジデータの保存
7. **結果統合**: レスポンスの構築

### analyze_test_trends()

**シグネチャ**
```python
def analyze_test_trends(self, history_days: int = 30) -> TestTrendAnalysis:
```

**目的**
過去のテスト実行履歴を分析し、品質トレンドを可視化する。

**分析項目**
- 成功率の推移
- カバレッジの変化
- 実行時間の変化
- 頻繁に失敗するテストの特定

## プライベートメソッド

### _execute_test_suite()

**シグネチャ**
```python
def _execute_test_suite(
    self,
    suite: TestSuite,
    request: TestExecutionRequest
) -> TestSuiteResult:
```

**目的**
個別のテストスイートを実行し、結果を収集する。

**スイート別実行コマンド**
```python
test_commands = {
    TestSuite.UNIT: "pytest tests/unit/ -v",
    TestSuite.INTEGRATION: "pytest tests/integration/ -v",
    TestSuite.E2E: "pytest tests/e2e/ -v --browser chrome",
    TestSuite.ALL: "pytest tests/ -v"
}
```

### _measure_coverage()

**シグネチャ**
```python
def _measure_coverage(
    self,
    request: TestExecutionRequest
) -> CoverageResult:
```

**目的**
コードカバレッジを測定し、詳細な分析結果を生成する。

**カバレッジ測定コマンド**
```python
coverage_cmd = [
    "pytest", "tests/",
    "--cov=scripts",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-report=json",
    f"--cov-fail-under={request.coverage_threshold}"
]
```

### _analyze_failed_tests()

**シグネチャ**
```python
def _analyze_failed_tests(
    self,
    test_output: str
) -> list[FailedTestInfo]:
```

**目的**
失敗したテストを解析し、失敗理由を分類する。

**失敗理由分類**
- `ASSERTION_ERROR`: アサーション失敗
- `TIMEOUT`: タイムアウト
- `SETUP_ERROR`: セットアップエラー
- `DEPENDENCY_ERROR`: 依存関係エラー
- `ENVIRONMENT_ERROR`: 環境問題
- `UNKNOWN`: 不明なエラー

### _generate_test_report()

**シグネチャ**
```python
def _generate_test_report(
    self,
    results: TestExecutionResult,
    coverage: CoverageResult,
    request: TestExecutionRequest
) -> Path:
```

**目的**
テスト実行結果の包括的なレポートを生成する。

**HTMLレポート構成**
```html
<!DOCTYPE html>
<html>
<head>
    <title>テスト実行レポート</title>
    <style>/* CSS styles */</style>
</head>
<body>
    <h1>テスト実行サマリー</h1>
    <div class="summary-cards">
        <div class="card success">成功: XX件</div>
        <div class="card failed">失敗: XX件</div>
        <div class="card coverage">カバレッジ: XX%</div>
    </div>

    <h2>スイート別結果</h2>
    <table class="results-table">
        <!-- 詳細結果テーブル -->
    </table>

    <h2>失敗テスト詳細</h2>
    <div class="failed-tests">
        <!-- 失敗テストの詳細 -->
    </div>

    <h2>カバレッジ詳細</h2>
    <div class="coverage-details">
        <!-- カバレッジレポート -->
    </div>
</body>
</html>
```

### _setup_test_environment()

**シグネチャ**
```python
def _setup_test_environment(self, request: TestExecutionRequest) -> bool:
```

**目的**
テスト実行前の環境準備を行う。

**セットアップ内容**
- 依存パッケージの確認
- テストデータベースの初期化
- 一時ディレクトリの作成
- 環境変数の設定
- モックサービスの起動

### _cleanup_test_environment()

**シグネチャ**
```python
def _cleanup_test_environment(self) -> None:
```

**目的**
テスト実行後のクリーンアップを行う。

## 依存関係

### インフラストラクチャ
- `TestRunner`: テスト実行エンジン
- `CoverageAnalyzer`: カバレッジ測定・分析
- `ReportGenerator`: レポート生成
- `ArtifactManager`: アーティファクト管理

### 外部ツール
- `pytest`: Pythonテストフレームワーク
- `coverage.py`: カバレッジ測定ツール
- `pytest-html`: HTMLレポート生成
- `pytest-xdist`: 並列実行サポート

## 設計原則遵守

### DDD準拠
- ✅ ドメインサービス（`TestRunner`）の適切な活用
- ✅ エンティティ（`FailedTestInfo`）の適切な管理
- ✅ 値オブジェクト（列挙型）の活用
- ✅ 外部システム（pytest）との適切な分離

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的なエラーハンドリング
- ✅ 型安全な実装
- ✅ 列挙型による型安全性
- ✅ テスト駆動開発の実践支援

## 使用例

```python
# 依存関係の準備
test_runner = PytestTestRunner()
coverage_analyzer = CoverageAnalyzer()
report_generator = HtmlReportGenerator()
artifact_manager = FileArtifactManager()

# ユースケース作成
use_case = TestExecutionUseCase(
    test_runner=test_runner,
    coverage_analyzer=coverage_analyzer,
    report_generator=report_generator,
    artifact_manager=artifact_manager
)

# 全テストスイートの実行（CI環境）
ci_request = TestExecutionRequest(
    suites=[TestSuite.ALL],
    mode=TestExecutionMode.CI,
    coverage_enabled=True,
    coverage_threshold=80.0,
    parallel_execution=True,
    stop_on_failure=True,
    generate_report=True,
    report_format="html",
    output_directory=Path("./test-results")
)

ci_response = use_case.execute_tests(ci_request)

if ci_response.success:
    print(f"テスト実行完了: {ci_response.passed_tests}/{ci_response.total_tests} 成功")
    print(f"カバレッジ: {ci_response.coverage_percentage:.1f}%")
    print(f"実行時間: {ci_response.execution_time:.2f}秒")

    if ci_response.coverage_passed:
        print("✅ カバレッジ閾値をクリアしました")
    else:
        print("❌ カバレッジが閾値を下回っています")

    if ci_response.failed_tests > 0:
        print(f"\n失敗テスト: {ci_response.failed_tests}件")
        for failure in ci_response.failed_test_details:
            print(f"  - {failure.test_name}: {failure.failure_reason}")

    print(f"\n詳細レポート: {ci_response.report_file_path}")
else:
    print(f"テスト実行失敗: {ci_response.message}")
    exit(1)

# ユニットテストのみの高速実行
unit_request = TestExecutionRequest(
    suites=[TestSuite.UNIT],
    mode=TestExecutionMode.FAST,
    coverage_enabled=False,
    parallel_execution=True,
    generate_report=False
)

unit_response = use_case.execute_tests(unit_request)

# 特定テストの詳細実行
specific_request = TestExecutionRequest(
    suites=[TestSuite.UNIT],
    mode=TestExecutionMode.DEBUG,
    specific_tests=[
        "tests/unit/test_episode.py::TestEpisode::test_create_episode",
        "tests/unit/test_quality.py::TestQualityChecker"
    ],
    coverage_enabled=True,
    generate_report=True
)

specific_response = use_case.execute_tests(specific_request)

# テストトレンド分析
trend_analysis = use_case.analyze_test_trends(history_days=30)
print(f"30日間の成功率トレンド: {trend_analysis.success_rate_trend}")
print(f"カバレッジ変化: {trend_analysis.coverage_trend}")
```

## テスト実行パターン

### 開発時の高速テスト
```python
# TDD Red-Green-Refactor サイクル用
development_request = TestExecutionRequest(
    suites=[TestSuite.UNIT],
    mode=TestExecutionMode.FAST,
    coverage_enabled=False,
    parallel_execution=True,
    stop_on_failure=True,
    generate_report=False
)
```

### プリコミットテスト
```python
# コミット前の品質チェック
precommit_request = TestExecutionRequest(
    suites=[TestSuite.UNIT, TestSuite.INTEGRATION],
    mode=TestExecutionMode.NORMAL,
    coverage_enabled=True,
    coverage_threshold=75.0,
    stop_on_failure=True
)
```

### リリース前テスト
```python
# 包括的なテスト実行
release_request = TestExecutionRequest(
    suites=[TestSuite.ALL],
    mode=TestExecutionMode.VERBOSE,
    coverage_enabled=True,
    coverage_threshold=90.0,
    parallel_execution=False,  # 安定性重視
    generate_report=True,
    report_format="html"
)
```

## CI/CD 統合

### GitHub Actions 連携
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Setup Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: pip install -r requirements-dev.txt
    - name: Execute Tests
      run: |
        python -c "
        from scripts.application.use_cases.test_execution_use_case import *
        request = TestExecutionRequest(
            suites=[TestSuite.ALL],
            mode=TestExecutionMode.CI,
            coverage_enabled=True,
            coverage_threshold=80.0
        )
        use_case = TestExecutionUseCase(...)
        result = use_case.execute_tests(request)
        exit(0 if result.success and result.coverage_passed else 1)
        "
    - name: Upload Test Results
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: test-results/
```

## エラーハンドリング

### テスト実行失敗
```python
try:
    result = self.test_runner.execute_suite(suite, config)
except TestExecutionError as e:
    failed_suites.append({
        "suite": suite,
        "error": str(e),
        "recoverable": e.recoverable
    })
    if request.stop_on_failure:
        break
except Exception as e:
    logger.error(f"予期しないテスト実行エラー: {e}")
    # 他のスイートの実行を継続
```

### カバレッジ測定失敗
```python
try:
    coverage_result = self.coverage_analyzer.measure()
except CoverageError as e:
    logger.warning(f"カバレッジ測定失敗: {e}")
    coverage_result = CoverageResult(
        overall_percentage=0.0,
        error_message=str(e)
    )
```

### 環境セットアップ失敗
```python
if not self._setup_test_environment(request):
    return TestExecutionResponse(
        success=False,
        message="テスト環境のセットアップに失敗しました。依存関係を確認してください。"
    )
```

## テスト観点

### 単体テスト
- 各テストスイートの正常実行
- カバレッジ測定の正確性
- 失敗テスト解析の精度
- レポート生成機能の動作
- エラー条件での処理

### 統合テスト
- 実際のテストスイートでの動作
- CI/CD環境での実行
- 並列実行の安定性
- アーティファクト生成の確認

## 品質基準

- **信頼性**: テスト実行の安定性と再現性
- **効率性**: 並列実行による高速化
- **可視性**: 詳細で分かりやすいレポート
- **拡張性**: 新しいテストスイートへの対応
- **統合性**: CI/CDパイプラインとのシームレス連携
