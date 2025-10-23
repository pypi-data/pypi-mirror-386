# pytest-xdist ServiceLocator キャッシュ隔離計画

**最終更新**: 2025-10-12
**ステータス**: Phase 0 完了、Phase 1 準備完了
**優先度**: P1 (Critical - Test Infrastructure Stability)

---

## 概要

pytest-xdist 併用時に `ServiceLocator` と `CommonPathService` のグローバルキャッシュがワーカー間で共有され、特定のユニットテストが**並列時のみ失敗**する事象を構造的に解決する。

---

## 問題の詳細

### 現象

- 単一ワーカーでのテスト実行: ✅ 全パス
- 並列実行（`-n 4`）: ❌ 特定テストが間欠的に失敗
- 失敗パターン: キャッシュの不整合、予期しない初期化順序

### 根本原因

**ServiceLocatorManager** がシングルトンパターンを使用し、クラス変数 `_locator` をグローバルに保持:

```python
class ServiceLocatorManager:
    _instance: "ServiceLocatorManager | None" = None  # グローバル
    _locator: ServiceLocator | None = None            # グローバル
```

pytest-xdist の各ワーカーは同じPython プロセス内で動作するため、`ServiceLocator._cache` が共有される。

---

## 解決策: PID/Worker ID ベースのキャッシュキー

**ADR-002** で決定した実装方針:

```python
class ServiceLocator(IServiceLocator):
    def __init__(self) -> None:
        self._worker_id = self._get_worker_id()  # PID or xdist worker ID
        self._cache: dict[str, dict[type, Any]] = {}  # {worker_id: {service_type: instance}}

    def _get_worker_id(self) -> str:
        """ワーカーIDを取得（PIDまたはPYTEST_XDIST_WORKER）"""
        return os.environ.get("PYTEST_XDIST_WORKER") or f"pid-{os.getpid()}"

    def _get_cache_for_worker(self) -> dict[type, Any]:
        """現在のワーカー専用のキャッシュを取得"""
        if self._worker_id not in self._cache:
            self._cache[self._worker_id] = {}
        return self._cache[self._worker_id]
```

---

## Phase 別実装計画

### ✅ Phase 0: 診断・準備 (1-2日) - **完了**

**目標**: 現状把握とADR作成

**成果物**:
- ✅ `scripts/diagnostics/service_locator_xdist_diagnosis.py`
  - スナップショット収集: `collect_snapshot()`
  - 競合検出: `detect_conflicts()`
  - JSON出力: `write_snapshot()`
- ✅ `tests/unit/scripts/test_service_locator_diagnosis.py`
  - 3つのテストケース（スナップショット、競合検出、シリアライゼーション）
- ✅ `docs/decisions/ADR-002-xdist-cache-isolation.md`
  - 4つの代替案比較（マルチプロセス、Thread-Local、Context Manager、DI Container）
  - PID/Worker ID ベース選択の根拠
  - 実装計画（Phase 0-4）

**診断コマンド**:
```bash
# 現在のキャッシュ状態をダンプ
python scripts/diagnostics/service_locator_xdist_diagnosis.py --dump-dir reports/xdist_diagnostics

# xdist並列実行中にスナップショット収集
pytest -n 4 --tb=short -v -k test_service_locator 2>&1 | tee reports/xdist_run.log
```

---

### 🔄 Phase 1: PID分離実装 (3-5日) - **次のステップ**

**目標**: ServiceLocator にPID/Worker ID キー分離を実装

**タスク**:
1. **先行テスト作成** (`tests/unit/infrastructure/di/test_service_locator_xdist.py`):
   ```python
   def test_cache_isolation_between_workers():
       """ワーカー間でキャッシュが隔離されること"""

   def test_pid_based_key_generation():
       """PID/Worker IDベースのキー生成が正しいこと"""

   def test_memory_cleanup_on_worker_exit():
       """ワーカー終了時にキャッシュがクリーンアップされること"""

   def test_cache_size_limit_per_worker():
       """ワーカーごとのキャッシュ上限が機能すること"""
   ```

2. **ServiceLocator 改修**:
   - `_get_worker_id()` メソッド追加
   - `_get_cache_for_worker()` メソッド追加
   - 既存の `get_*_service()` メソッドを Worker ID キー対応に変更

3. **クリーンアップ実装**:
   ```python
   import atexit

   def _cleanup_worker_cache():
       """ワーカー終了時にキャッシュをクリーンアップ"""
       worker_id = self._get_worker_id()
       if worker_id in self._cache:
           self._cache.pop(worker_id)

   atexit.register(_cleanup_worker_cache)
   ```

**完了条件 (DoD)**:
- [ ] 先行テスト全パス（4件）
- [ ] 既存テストの互換性維持（後方互換フラグ導入）
- [ ] メモリ使用量 ≤ 基準値 + 20%

---

### Phase 2: テスト・検証 (2-3日)

**目標**: 並列実行での安定性とパフォーマンス検証

**タスク**:
1. **統合テスト作成** (`tests/integration/test_xdist_parallel_execution.py`):
   - 4/8/16 ワーカーでの負荷試験
   - 失敗率測定（目標: < 5%）

2. **パフォーマンス計測**:
   ```bash
   # メモリプロファイリング
   python -m tracemalloc tests/unit/

   # 実行時間ベンチマーク
   pytest --benchmark-only -n 8
   ```

3. **比較実験**:
   - xdist無効: `pytest tests/`
   - xdist有効（PID隔離前）: `pytest -n 4 tests/`
   - xdist有効（PID隔離後）: `pytest -n 4 tests/` with `ENABLE_PID_CACHE_ISOLATION=1`

**完了条件 (DoD)**:
- [ ] xdist 並列実行でテスト成功率 > 95%
- [ ] 8 ワーカー時メモリ使用量 ≤ 8GB
- [ ] テスト実行時間の増加 ≤ 10%

---

### Phase 3: ドキュメント整備 (1-2日)

**目標**: 運用ガイドと設計ドキュメントの整備

**タスク**:
1. **ベストプラクティスガイド作成** (`docs/guides/xdist_best_practices.md`):
   - xdist 並列実行の推奨設定
   - キャッシュ隔離のトラブルシューティング
   - パフォーマンスチューニング

2. **アーキテクチャドキュメント更新** (`docs/architecture/service_locator.md`):
   - PID隔離の設計思想
   - キャッシュライフサイクル
   - クリーンアップ戦略

3. **CHANGELOG更新**:
   - Breaking Changes（あれば）
   - 移行ガイド

**完了条件 (DoD)**:
- [ ] 運用ガイド作成完了
- [ ] ADR-002 を Accepted にステータス更新
- [ ] CHANGELOG に変更履歴記載

---

### Phase 4: 段階的ロールアウト (2-3週間)

**目標**: Feature flag による段階的な本番導入

**タスク**:
1. **開発環境での試験** (Week 1):
   ```bash
   export ENABLE_PID_CACHE_ISOLATION=1
   pytest -n 4 tests/
   ```

2. **CI 部分適用** (Week 2):
   - CI の一部ジョブで PID隔離を有効化
   - 失敗率とメモリ使用量を監視

3. **全面展開** (Week 3):
   - CI 全ジョブで PID隔離を有効化
   - 2 週間安定稼働を確認

**ロールバック基準**:
- ❌ メモリ使用量 > 4GB
- ❌ テスト失敗率 > 5%
- ❌ 実行時間増加 > 15%

**完了条件 (DoD)**:
- [ ] CI で 2 週間連続安定稼働
- [ ] コードレビュー & セキュリティレビュー承認
- [ ] Feature flag 削除（完全移行）

---

### Phase 5: 長期的改善 (Future Work)

**目標**: ServiceLocator から DI Container への移行計画

**タスク**:
- [ ] Issue 化: ServiceLocator → DI Container 移行計画
- [ ] メトリクス収集（Prometheus/Grafana）
- [ ] アラート整備

---

## リスクと軽減策

| リスク | 影響 | 確率 | 軽減策 |
|--------|------|------|--------|
| メモリ増大 | Medium | High | ワーカーごとのキャッシュ上限（50エントリ） + LRU 退避 |
| 既存テスト互換性 | High | Medium | Feature flag での段階移行・ロールバック手順明記 |
| 初期化オーバーヘッド | Low | High | Lazy initialization 維持、+10% 以内を許容 |
| 並列実行での新規バグ | Medium | Low | Phase 2 で徹底的な負荷試験を実施 |

---

## 参照

- **ADR**: [docs/decisions/ADR-002-xdist-cache-isolation.md](../decisions/ADR-002-xdist-cache-isolation.md)
- **診断ツール**: [scripts/diagnostics/service_locator_xdist_diagnosis.py](../../scripts/diagnostics/service_locator_xdist_diagnosis.py)
- **TODO.md**: [xdist キャッシュ隔離 (PIDキー実装計画)](../../TODO.md#xdist-キャッシュ隔離-pidキー実装計画)
- **ServiceLocator実装**: [src/noveler/infrastructure/di/service_locator.py](../../src/noveler/infrastructure/di/service_locator.py)

---

## 更新履歴

| 日付 | 著者 | 変更内容 |
|------|------|----------|
| 2025-10-12 | Claude Code | Phase 0 完了、詳細計画を整備 |
| 2025-10-11 | Claude Code | 初版作成（TODO.mdから参照） |
