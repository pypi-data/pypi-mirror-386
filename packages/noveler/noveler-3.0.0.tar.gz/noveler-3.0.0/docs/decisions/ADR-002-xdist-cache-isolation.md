# ADR-002: pytest-xdist キャッシュ隔離戦略

**ステータス**: Draft
**日付**: 2025-10-12
**決定者**: Development Team
**関連**: [xdist キャッシュ隔離 (P1)](../../TODO.md#xdist-キャッシュ隔離-pidキー実装計画)

---

## Context

### 問題の背景

pytest-xdist を使用した並列テスト実行時に、`ServiceLocator` と `CommonPathService` のグローバルキャッシュがワーカー間で共有され、特定のユニットテストが**並列時のみ失敗**する事象を継続的に観測している。

**現状の回避策**:
- テスト個別フィクスチャでのキャッシュリセット（`ServiceLocatorManager().reset()`）
- `autouse=True` フィクスチャによる強制クリーンアップ

**問題点**:
- 類似テストの追加時に再発するリスクが高い
- テスト作成者がキャッシュ問題を意識する必要がある
- 構造的な解決ではなく、対症療法に過ぎない

### 技術的詳細

**ServiceLocator の現状** ([src/noveler/infrastructure/di/service_locator.py](../../src/noveler/infrastructure/di/service_locator.py)):
```python
class ServiceLocatorManager:
    _instance: "ServiceLocatorManager | None" = None  # クラス変数（グローバル）
    _locator: ServiceLocator | None = None            # クラス変数（グローバル）

class ServiceLocator(IServiceLocator):
    def __init__(self) -> None:
        self._cache: dict[type, Any] = {}  # インスタンス変数（理論上は隔離）
```

**問題の本質**:
1. `ServiceLocatorManager` はシングルトンパターンを使用
2. クラス変数 `_instance` と `_locator` はPythonプロセス内でグローバル
3. pytest-xdist の各ワーカーは**同じPythonインタープリタプロセス**内で動作（マルチスレッド）
4. ワーカーA が初期化した `ServiceLocator._cache` をワーカーB が参照可能

---

## Decision

### 選択した解決策: **PID/Worker ID ベースのキャッシュキー**

`ServiceLocator._cache` を **プロセスID（PID）** または **pytest-xdist Worker ID** でキー分割し、ワーカー間の完全な隔離を実現する。

**実装方針**:
```python
import atexit
import os
from typing import Any, TYPE_CHECKING, TypeVar, cast

if TYPE_CHECKING:
    from noveler.domain.protocols import ILoggerProtocol

class ServiceLocator(IServiceLocator):
    def __init__(self) -> None:
        self._factory = get_service_factory()
        self._worker_id = self._get_worker_id()  # PID or xdist worker ID
        self._cache: dict[str, dict[str, Any]] = {}  # {worker_id: {service_type: instance}}

        # ワーカー終了時のクリーンアップ登録
        atexit.register(self._cleanup_worker_cache)

    def _get_worker_id(self) -> str:
        """ワーカーIDを取得（PIDまたはPYTEST_XDIST_WORKER）"""
        return os.environ.get("PYTEST_XDIST_WORKER") or f"pid-{os.getpid()}"

    def _get_cache_for_worker(self) -> dict[str, Any]:
        """現在のワーカー専用のキャッシュを取得"""
        if self._worker_id not in self._cache:
            self._cache[self._worker_id] = {}
        return self._cache[self._worker_id]

    def _cleanup_worker_cache(self) -> None:
        """ワーカー終了時にキャッシュをクリーンアップ"""
        if self._worker_id in self._cache:
            self._cache.pop(self._worker_id)

    def get_logger_service(self) -> "ILoggerProtocol":
        """ロガーサービス取得（Lazy Proxy、Worker ID分離対応）"""
        service_type = "ILoggerProtocol"
        cache = self._get_cache_for_worker()  # Worker ID別キャッシュ取得
        if service_type not in cache:
            cache[service_type] = LazyProxy(self._factory.create_logger_service)
        return cast("ILoggerProtocol", cache[service_type])

    # 他のget_*_service()メソッドも同様にWorker ID分離対応
```

**クリーンアップ戦略**:
- `atexit` ハンドラでワーカー終了時にキャッシュを削除（`__init__`で自動登録）
- pytest hook (`pytest_runtest_teardown`) での定期クリーンアップ（オプション）

---

## Alternatives

### Option A: マルチプロセス化（`pytest-xdist -n auto --dist loadscope`）

**概要**: ワーカーを完全に独立したプロセスとして起動し、メモリ空間を物理的に分離。

**利点**:
- ✅ 完全なメモリ隔離が保証される
- ✅ グローバル変数の競合が構造的に発生しない

**欠点**:
- ❌ プロセス起動オーバーヘッドが大きい（+30%以上の実行時間増加）
- ❌ 各ワーカーが独立したPython インタープリタを持つため、メモリ使用量が増大（ワーカー数 × ベースメモリ）
- ❌ 既存のテストインフラ（shared fixtures）との互換性問題

**判断**: ❌ **却下** - パフォーマンスとメモリのトレードオフが大きすぎる

---

### Option B: Thread-Local Storage（`threading.local()`）

**概要**: `ServiceLocator._cache` を `threading.local()` で管理し、スレッド単位で隔離。

**利点**:
- ✅ Python標準ライブラリで実装可能
- ✅ スレッド間の自動隔離

**欠点**:
- ❌ pytest-xdist がマルチスレッドではなく**マルチプロセス**で動作する場合に無効
- ❌ asyncio/gevent などの非同期環境では不適切
- ❌ スレッドプールの再利用でキャッシュが意図せず残留する可能性

**判断**: ❌ **却下** - pytest-xdist の実装モデルと不一致

---

### Option C: Context Manager ベースのスコープ管理

**概要**: テストごとに `with service_locator_scope():` で明示的にスコープを管理。

```python
@pytest.fixture
def isolated_service_locator():
    with service_locator_scope():
        yield get_service_locator()
```

**利点**:
- ✅ 明示的で理解しやすい
- ✅ テストごとの完全な制御が可能

**欠点**:
- ❌ 全テストにフィクスチャ適用が必要（数千件のテスト修正）
- ❌ テスト作成者が常にキャッシュ問題を意識する必要がある
- ❌ 既存テストとの互換性が低い

**判断**: ⚠️ **部分採用** - PID隔離と組み合わせてテスト側の明示的制御オプションとして提供

---

### Option D: ServiceLocator の完全削除（DI Container への移行）

**概要**: ServiceLocator パターンを廃止し、`dependency-injector` などの DI Container に移行。

**利点**:
- ✅ グローバルステートの完全な排除
- ✅ 依存注入の明示化による保守性向上
- ✅ テスト時の mock 注入が容易

**欠点**:
- ❌ 大規模なリファクタリングが必要（数百ファイル）
- ❌ 移行期間中の混在状態による不安定化リスク
- ❌ 学習コストとチーム全体への影響が大きい

**判断**: 🔮 **長期計画** - Phase 5で Issue 化し、段階的移行を検討

---

## Consequences

### 期待される効果

**テスト安定性**:
- ✅ xdist 並列実行での失敗率を < 5% に抑制
- ✅ テスト作成者がキャッシュ問題を意識不要に

**パフォーマンス**:
- ✅ 初期化オーバーヘッド +10% 以内に抑制（Lazy initialization維持）
- ✅ メモリ使用量はワーカー数に比例するが、LRU退避で上限制御

**保守性**:
- ✅ 構造的な解決により、類似テストでの再発を防止
- ✅ Feature flag による段階的ロールアウトでリスク最小化

### 潜在的リスク

**メモリ増大**:
- ⚠️ ワーカーごとのキャッシュ保持により、メモリ使用量が増加
- **軽減策**: ワーカーごとのキャッシュ上限（50エントリ）+ LRU 退避

**既存テスト互換性**:
- ⚠️ キャッシュキーの変更により、一部テストが影響を受ける可能性
- **軽減策**: Feature flag `ENABLE_PID_CACHE_ISOLATION` で段階導入

**初期化オーバーヘッド**:
- ⚠️ ワーカーごとの初期化により、テスト実行時間がわずかに増加
- **軽減策**: Lazy initialization を維持し、+10% 以内を許容ライン

---

## Implementation Plan

### Phase 0: 診断・準備 (1-2日) ✅
- [x] `scripts/diagnostics/service_locator_xdist_diagnosis.py` 実装済み（既存）
- [x] `tests/unit/scripts/test_service_locator_diagnosis.py` 実装済み（既存）
- [x] ADR-002 起草（本ドキュメント）
- [x] 冗長ファイル削除 (`scripts/diagnosis/` 削除)

### Phase 1: PID分離実装 (3-5日)
- [ ] 先行テスト: `tests/unit/infrastructure/di/test_service_locator_xdist.py`
  - `test_cache_isolation_between_workers`
  - `test_pid_based_key_generation`
  - `test_memory_cleanup_on_worker_exit`
  - `test_cache_size_limit_per_worker`
- [ ] `ServiceLocator._get_worker_id()` 実装
- [ ] `ServiceLocator._get_cache_for_worker()` 実装
- [ ] ワーカー終了時のクリーンアップ（`atexit` または pytest hook）

### Phase 2: テスト・検証 (2-3日)
- [ ] `tests/integration/test_xdist_parallel_execution.py` 新設
- [ ] `bin/test` 全体を xdist 有効/無効で実行し失敗率比較
- [ ] tracemalloc / pytest-benchmark でメモリ＆オーバーヘッド計測

### Phase 3: ドキュメント整備 (1-2日)
- [ ] `docs/guides/xdist_best_practices.md` 作成
- [ ] `docs/architecture/service_locator.md` 更新
- [ ] CHANGELOG / Migration Guide 更新

### Phase 4: 段階的ロールアウト (2-3週間)
- [ ] Feature flag `ENABLE_PID_CACHE_ISOLATION` で段階導入
- [ ] ロールバック基準: メモリ > 4GB または失敗率 > 5%
- [ ] 全面展開後 2 週間経過時点で旧実装の削除判断

---

## References

- TODO.md: [xdist キャッシュ隔離 (PIDキー実装計画)](../../TODO.md#xdist-キャッシュ隔離-pidキー実装計画)
- 診断スクリプト: [scripts/diagnostics/service_locator_xdist_diagnosis.py](../../scripts/diagnostics/service_locator_xdist_diagnosis.py)
- テスト: [tests/unit/scripts/test_service_locator_diagnosis.py](../../tests/unit/scripts/test_service_locator_diagnosis.py)
- ServiceLocator実装: [src/noveler/infrastructure/di/service_locator.py](../../src/noveler/infrastructure/di/service_locator.py)

---

## Revision History

| 日付 | 著者 | 変更内容 |
|------|------|----------|
| 2025-10-12 | Claude Code | 初版作成（代替案比較、実装計画） |
