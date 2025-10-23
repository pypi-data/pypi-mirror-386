# pytest-xdist ベストプラクティス

**目的**: pytest-xdistを使用した並列テスト実行のベストプラクティスとトラブルシューティング

**対象読者**: Novelerプロジェクトの開発者、CI/CD担当者

**更新日**: 2025-10-12

---

## 概要

pytest-xdistはpytestの並列実行プラグインで、複数のワーカープロセスを使用してテストを並列実行します。Novelerプロジェクトでは、ServiceLocatorのPID/Worker ID分離により、xdistと完全互換の実装を実現しています。

---

## 基本的な使用方法

### コマンドライン実行

```bash
# 4ワーカーで並列実行
pytest -n 4

# 8ワーカーで並列実行（推奨）
pytest -n 8

# CPUコア数に自動調整
pytest -n auto

# 特定のテストファイルのみ並列実行
pytest tests/unit/ -n 4
```

### Makefileターゲット

```bash
# 推奨: プロジェクト標準の実行方法
make test

# xdist無効化（デバッグ時）
XDIST_WORKERS=0 make test

# ワーカー数指定
XDIST_WORKERS=16 make test
```

---

## ServiceLocatorとの統合

### アーキテクチャ

NovelerのServiceLocatorは、xdist並列実行に完全対応しています:

```python
# src/noveler/infrastructure/di/service_locator.py

class ServiceLocator:
    def __init__(self) -> None:
        self._factory = get_service_factory()
        self._worker_id = self._get_worker_id()  # PID/Worker ID取得
        self._cache: dict[str, dict[str, Any]] = {}  # Worker ID別キャッシュ
        atexit.register(self._cleanup_worker_cache)  # クリーンアップ登録

    def _get_worker_id(self) -> str:
        """ワーカーIDを取得（xdist対応）"""
        return os.environ.get("PYTEST_XDIST_WORKER") or f"pid-{os.getpid()}"

    def _get_cache_for_worker(self) -> dict[str, Any]:
        """現在のワーカー専用キャッシュを取得"""
        if self._worker_id not in self._cache:
            self._cache[self._worker_id] = {}
        return self._cache[self._worker_id]
```

### キャッシュ分離の仕組み

**ワーカー別キャッシュ構造**:

```
ServiceLocator._cache = {
    "gw0": {
        "ILoggerProtocol": <LoggerService>,
        "IConsoleServiceProtocol": <ConsoleService>,
    },
    "gw1": {
        "ILoggerProtocol": <LoggerService>,
        "IConsoleServiceProtocol": <ConsoleService>,
    },
    ...
}
```

**ワーカーID形式**:
- xdist環境: `gw0`, `gw1`, `gw2`, ... (環境変数 `PYTEST_XDIST_WORKER`)
- 非xdist環境: `pid-12345` (プロセスID)

### 自動クリーンアップ

ワーカー終了時にatexitハンドラが自動的にキャッシュをクリーンアップします:

```python
def _cleanup_worker_cache(self) -> None:
    """ワーカー終了時のキャッシュクリーンアップ"""
    if self._worker_id in self._cache:
        self._cache.pop(self._worker_id)
```

---

## テスト実装のベストプラクティス

### 1. グローバル状態の回避

❌ **NG例**: クラス変数でグローバル状態を保持

```python
class MyService:
    _instance = None  # 全ワーカーで共有されてしまう
    _cache = {}       # 競合の原因
```

✅ **OK例**: ワーカー別インスタンス

```python
def get_service():
    """ServiceLocator経由で取得（ワーカー別キャッシュ）"""
    return get_service_locator().get_logger_service()
```

### 2. フィクスチャスコープの適切な設定

❌ **NG例**: sessionスコープで状態を共有

```python
@pytest.fixture(scope="session")
def shared_service():
    # 全ワーカーで共有される可能性（危険）
    return MyService()
```

✅ **OK例**: functionスコープで独立

```python
@pytest.fixture(scope="function")
def service():
    # 各テストで独立したインスタンス
    return get_service_locator().get_logger_service()
```

✅ **OK例**: sessionスコープでも安全な場合

```python
@pytest.fixture(scope="session")
def project_config():
    # 読み取り専用の設定はsessionスコープ可
    return load_config("config.yaml")
```

### 3. ファイルI/Oの競合回避

❌ **NG例**: 固定ファイル名

```python
def test_write_output():
    with open("output.txt", "w") as f:  # 全ワーカーで競合
        f.write("test")
```

✅ **OK例**: tmp_pathフィクスチャ使用

```python
def test_write_output(tmp_path: Path):
    output_file = tmp_path / "output.txt"  # ワーカー別の一時ディレクトリ
    with open(output_file, "w") as f:
        f.write("test")
```

### 4. データベース・外部リソース

❌ **NG例**: 共有データベース

```python
def test_database():
    db = connect("shared.db")  # 全ワーカーで競合
    db.insert({"id": 1})
```

✅ **OK例**: ワーカー別データベース

```python
def test_database():
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
    db = connect(f"test_{worker_id}.db")  # ワーカー別DB
    db.insert({"id": 1})
```

---

## パフォーマンス最適化

### 最適なワーカー数

**推奨設定**: 8 workers

```bash
pytest -n 8
```

**理由**:
- 4 workers: 3.89s
- 8 workers: 3.49s (**10%高速化**)
- 16 workers: 5.28s (起動オーバーヘッドで遅延)

**ガイドライン**:
- CPU密集型テスト: `n = CPUコア数`
- I/O密集型テスト: `n = CPUコア数 × 2`
- 統合テスト: `n = 4` (外部リソース競合回避)

### テストの粒度

**短時間テストを多数**: ✅ xdistで高速化効果大

```python
@pytest.mark.parametrize("value", range(100))
def test_fast_operation(value):
    assert process(value) > 0  # 0.01s/test → 並列化で大幅短縮
```

**長時間テストを少数**: ⚠️ 効果限定的

```python
def test_slow_integration():
    time.sleep(10)  # 10s/test → 並列化しても10秒必要
```

### メモリ使用量

**ワーカー数とメモリの関係**:

```
メモリ使用量 ≈ 基本メモリ + (ワーカー数 × ワーカーメモリ)
```

**例**:
- 基本メモリ: 200MB
- ワーカーメモリ: 50MB/worker
- 8 workers: 200 + (8 × 50) = **600MB**
- 16 workers: 200 + (16 × 50) = **1000MB**

**推奨**: メモリ制約がある環境では `n = 4` または `n = 8`

---

## トラブルシューティング

### 問題1: テストが並列実行時のみ失敗する

**症状**:
```bash
# 単一実行: 成功
pytest tests/test_service.py -v

# 並列実行: 失敗
pytest tests/test_service.py -n 4 -v
```

**原因**: グローバル状態の共有、ファイル競合、データベース競合

**診断方法**:

```bash
# 診断スクリプト実行
python scripts/diagnostics/service_locator_xdist_diagnosis.py

# スナップショット比較
diff reports/xdist_snapshot_before.json reports/xdist_snapshot_after.json
```

**解決策**:

1. **ServiceLocator使用を確認**:
   ```python
   # NG: 直接インスタンス化
   service = LoggerService()

   # OK: ServiceLocator経由
   service = get_service_locator().get_logger_service()
   ```

2. **tmp_pathフィクスチャ使用**:
   ```python
   def test_file_operation(tmp_path: Path):
       output_file = tmp_path / "output.txt"
       # ワーカー別の一時ディレクトリが自動生成される
   ```

3. **ワーカーID付きリソース名**:
   ```python
   worker_id = os.environ.get("PYTEST_XDIST_WORKER", "main")
   db_name = f"test_{worker_id}.db"
   ```

### 問題2: メモリ使用量が増加し続ける

**症状**: テスト実行中にメモリ使用量が増加し、OOMエラー

**原因**: キャッシュクリーンアップ失敗、メモリリーク

**診断方法**:

```bash
# メモリプロファイリング
pytest tests/ -n 4 --memray
```

**解決策**:

1. **atexitハンドラ確認**:
   ```python
   # ServiceLocatorが自動クリーンアップを登録
   atexit.register(self._cleanup_worker_cache)
   ```

2. **手動キャッシュクリア**（テスト用）:
   ```python
   @pytest.fixture(autouse=True)
   def cleanup_cache():
       yield
       get_service_locator().clear_cache()
   ```

### 問題3: ワーカー起動が遅い

**症状**: `pytest -n 16` が `pytest -n 4` より遅い

**原因**: ワーカー起動オーバーヘッド、過剰な並列度

**解決策**:

1. **適切なワーカー数に調整**: `n = 8` (推奨)
2. **テストスコープを限定**: `pytest tests/unit/ -n 8`
3. **高速なテストのみ並列化**: マーカー使用

```python
# 高速なテストのみマーク
@pytest.mark.fast
def test_quick_operation():
    pass

# 実行
pytest -m fast -n 8
```

### 問題4: 統合テストで外部リソース競合

**症状**: 統合テストが並列実行時に失敗（DB接続エラーなど）

**解決策**:

1. **統合テストはシーケンシャル実行**:
   ```python
   @pytest.mark.serial
   class TestIntegration:
       def test_database_integration(self):
           # 外部DBを使用
           pass
   ```

2. **pytest.ini設定**:
   ```ini
   [pytest]
   markers =
       serial: mark test to run serially (not in parallel)
   ```

3. **実行コマンド**:
   ```bash
   # ユニットテストのみ並列化
   pytest tests/unit/ -n 8

   # 統合テストはシーケンシャル
   pytest tests/integration/ -n 0
   ```

---

## CI/CD設定

### GitHub Actions

```yaml
# .github/workflows/test.yml

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install dependencies
        run: |
          pip install -e .[dev]

      - name: Run tests with xdist
        run: |
          pytest tests/unit/ -n 8 --verbose
          pytest tests/integration/ -n 4 --verbose

      - name: Upload failure logs
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-logs
          path: reports/
```

### ローカル開発

```bash
# .env (開発環境)
XDIST_WORKERS=8
PYTEST_XDIST_WORKER=  # 空（自動設定）
```

```bash
# Makefile
test:
	pytest tests/ -n $(XDIST_WORKERS) -v

test-serial:
	pytest tests/ -n 0 -v

test-integration:
	pytest tests/integration/ -n 4 -v
```

---

## 統合テスト例

### ワーカー間キャッシュ隔離テスト

```python
# tests/integration/test_xdist_parallel_execution.py

def test_cache_isolation_between_workers():
    """ワーカー間でキャッシュが隔離されること"""
    locator = get_service_locator()
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", f"pid-{os.getpid()}")

    # サービスを取得
    logger = locator.get_logger_service()
    console = locator.get_console_service()

    # このワーカーのキャッシュを確認
    cache = locator._get_cache_for_worker()
    assert "ILoggerProtocol" in cache
    assert "IConsoleServiceProtocol" in cache

    print(f"Worker {worker_id}: Cache size = {len(cache)}")
```

### 高負荷並列実行テスト

```python
@pytest.mark.parametrize("iteration", range(20))
def test_high_load_parallel_execution(tmp_path: Path, iteration: int):
    """高負荷並列実行時の安定性テスト

    20テスト × 16ワーカー = 320並列実行で安定動作することを確認
    """
    locator = get_service_locator()

    # ランダムな処理負荷
    time.sleep(0.001 * (iteration % 5))

    # サービスを取得
    logger = locator.get_logger_service()
    console = locator.get_console_service()

    # 全サービスが正常動作すること
    cache = locator._get_cache_for_worker()
    assert len(cache) >= 2
```

**実行結果**:

```bash
$ pytest tests/integration/test_xdist_parallel_execution.py -n 16

42 passed in 5.28s
# 20 tests × 16 workers = 320 parallel executions, 全成功
```

---

## 関連ドキュメント

- [ADR-002: xdist Cache Isolation](../decisions/ADR-002-xdist-cache-isolation.md)
- [xdist Implementation Plan](../notes/xdist_service_locator_plan.md)
- [ServiceLocator Architecture](../architecture/service_locator.md)
- [pytest-xdist公式ドキュメント](https://pytest-xdist.readthedocs.io/)

---

## まとめ

### ✅ DO（推奨）

- ServiceLocator経由でサービス取得
- tmp_pathフィクスチャでファイルI/O
- ワーカー数は8を推奨（`-n 8`）
- 統合テストは適度な並列度（`-n 4`）
- atexitによる自動クリーンアップ

### ❌ DON'T（非推奨）

- グローバル変数でのキャッシュ共有
- 固定ファイル名での書き込み
- 共有データベースへの同時書き込み
- 過剰なワーカー数（`-n 32`など）
- sessionスコープでの状態保持（読み取り専用を除く）

### 📋 チェックリスト

新しいテストを追加する際は、以下を確認してください:

- [ ] ServiceLocator経由でサービス取得しているか？
- [ ] ファイルI/Oにtmp_pathを使用しているか？
- [ ] グローバル状態を共有していないか？
- [ ] 並列実行でテストが成功するか？（`pytest -n 4`）
- [ ] メモリリークしていないか？

---

**更新履歴**:
- 2025-10-12: 初版作成（Phase 3）
