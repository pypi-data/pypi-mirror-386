# MessageBus アーキテクチャドキュメント

**作成日**: 2025-09-22
**対象**: SPEC-901 MessageBus 技術実装
**読者**: 開発者、アーキテクト

## 🏗️ アーキテクチャ概要

noveler MessageBusは段階的なDDD移行を支援する二層構造を採用しています。

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐      ┌─────────────────────────────────┐ │
│  │  SimpleBus      │      │     TypedBus (legacy)          │ │
│  │ (文字列名ベース) │◄────►│     (型ベース)                  │ │
│  │ - 軽量・実用的   │      │     - 既存コード互換             │ │
│  │ - DLQ/メトリクス │      │     - フル DDD                  │ │
│  └─────────────────┘      └─────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Outbox        │  │  Idempotency    │  │    Metrics      │ │
│  │ FileRepository  │  │     Store       │  │   Collection    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 SimpleBus vs TypedBus

### SimpleBus（推奨・本実装）
**用途**: 新機能開発、MCP統合、運用重視

**特徴**:
- 文字列名ベースのコマンド/イベント（`"create_episode"`, `"episode_created"`）
- 軽量で高速（<1ms 処理時間）
- 完全な運用機能（DLQ、メトリクス、CLI）
- JSON シリアライゼーション対応

**実装場所**: `src/noveler/application/simple_message_bus.py`

```python
# SimpleBus 使用例
bus = MessageBus(config=BusConfig(), outbox_repo=outbox_repo)

# コマンド実行
result = await bus.handle_command("create_episode", {
    "title": "新しいエピソード",
    "episode_number": 1
})

# イベント発行
await bus.emit("episode_created", {"episode_id": "ep-1"})
```

### TypedBus（レガシー保持）
**用途**: 既存コード保守、フルDDD準拠が必要な場合

**特徴**:
- 型安全なコマンド/イベントクラス
- フルDDDパターン準拠
- 複雑だが表現力が高い
- 段階的にSimpleBusに移行予定

**実装場所**: `src/noveler/application/message_bus.py`

## 🗂️ データフロー

### 1. コマンド処理フロー
```
CLI/MCP → SimpleBus.handle_command()
    ↓
UnitOfWork.begin()
    ↓
CommandHandler 実行
    ↓
UnitOfWork.commit()
    ↓
イベント収集 → Outbox保存 → BackgroundFlush
```

### 2. イベント処理フロー
```
Outbox → SimpleBus.flush_outbox()
    ↓
GenericEvent再構築
    ↓
Idempotency チェック
    ↓
EventHandler 実行（リトライ付き）
    ↓
成功: mark_dispatched | 失敗: increment_attempts
    ↓
失敗5回: move_to_dlq()
```

### 3. 監視データフロー
```
各処理 → BusMetrics.record()
    ↓
統計計算（P50/P95/失敗率）
    ↓
CLI/監視システム → get_metrics_summary()
```

## 🔧 コア実装

### BusConfig（設定）
```python
@dataclass
class BusConfig:
    max_retries: int = 3              # リトライ回数
    backoff_base_sec: float = 0.05    # 初期バックオフ
    backoff_max_sec: float = 0.5      # 最大バックオフ
    jitter_sec: float = 0.05          # ジッタ
    dlq_max_attempts: int = 5         # DLQ移行しきい値
```

### BusMetrics（計測）
```python
@dataclass
class BusMetrics:
    command_count: int = 0
    event_count: int = 0
    failed_commands: int = 0
    failed_events: int = 0
    command_durations: list[float] = field(default_factory=list)
    event_durations: list[float] = field(default_factory=list)

    def get_command_stats(self) -> dict[str, float]:
        # P50/P95パーセンタイル計算
        # 失敗率計算
```

### OutboxEntry（永続化）
```python
@dataclass
class OutboxEntry:
    id: str                           # イベントID
    name: str                         # イベント名
    payload: dict[str, Any]           # イベントデータ
    created_at: datetime              # 作成日時
    attempts: int = 0                 # 試行回数
    dispatched_at: datetime | None = None    # 配信日時
    last_error: str | None = None     # 最終エラー
    failed_at: datetime | None = None # 失敗日時
```

## 🎯 パフォーマンス設計

### 計測精度
- `time.perf_counter()` による高精度時間計測
- 処理開始/終了での確実な記録
- メモリ効率を考慮した履歴管理（最新100件）

### スケーラビリティ
- ファイルベース実装（単一インスタンス想定）
- 将来的なDB移行に備えたRepository抽象化
- 並列処理時の競合回避（ワークスペース分離）

### レスポンス時間最適化
```python
# 同期処理（小規模）
async def handle_command(self, name: str, data: dict) -> dict:
    start_time = time.perf_counter()
    try:
        # 高速処理（<1ms目標）
        result = await handler(data)
        return result
    finally:
        # メトリクス記録
        duration = time.perf_counter() - start_time
        self.metrics.command_durations.append(duration)
```

## 🛡️ 信頼性機能

### Outboxパターン
- イベント配信の確実性保証
- トランザクション境界での安全な永続化
- 配信失敗時の自動リトライ

### Dead Letter Queue
- 重大な配信失敗の分離
- エラー情報の詳細保持
- 手動復旧操作の支援

### べき等性保証
- InMemory実装（軽量・高速）
- event_id による重複検知
- プロセスライフサイクルでの管理

### リトライ戦略
```python
async def _run_with_retry(coro_factory, cfg: BusConfig):
    attempt = 0
    while attempt <= cfg.max_retries:
        try:
            return await coro_factory()
        except Exception:
            if attempt == cfg.max_retries:
                raise  # 最終的にDLQへ
            # 指数バックオフ + ジッタ
            delay = min(cfg.backoff_base_sec * (2 ** attempt), cfg.backoff_max_sec)
            delay += random.uniform(0, cfg.jitter_sec)
            await asyncio.sleep(delay)
            attempt += 1
```

## 🔌 拡張ポイント

### 新しいコマンド/イベントの追加

1. **コマンドハンドラー登録**
```python
async def handle_new_command(data: dict, uow: UnitOfWork) -> dict:
    # ビジネスロジック実装
    result = perform_business_logic(data)
    # イベント追加
    uow.add_event("new_event_occurred", {"result_id": result.id})
    return {"success": True, "result_id": result.id}

# 登録
bus.command_handlers["new_command"] = handle_new_command
```

2. **イベントハンドラー登録**
```python
async def handle_new_event(event: DomainEvent) -> None:
    # 副作用処理（通知、ログ、連携等）
    await notify_external_system(event.payload)

# 登録
bus.event_handlers["new_event_occurred"] = [handle_new_event]
```

### カスタムRepository実装
```python
class DatabaseOutboxRepository(OutboxRepository):
    """DB実装例"""
    async def add(self, entry: OutboxEntry) -> None:
        # DB INSERT

    async def load_pending(self, limit: int) -> list[OutboxEntry]:
        # DB SELECT WHERE status='pending'

    async def move_to_dlq(self, entry_id: str) -> None:
        # DB UPDATE SET status='dlq'
```

### メトリクス拡張
```python
# カスタムメトリクス追加
class ExtendedBusMetrics(BusMetrics):
    custom_counter: int = 0
    custom_timing: list[float] = field(default_factory=list)

    def record_custom_event(self, duration: float):
        self.custom_counter += 1
        self.custom_timing.append(duration)
```

## 🧪 テスト戦略

### Unit Tests
```python
@pytest.mark.spec("SPEC-901")
async def test_command_handling_with_metrics():
    bus = MessageBus(config=BusConfig())

    result = await bus.handle_command("test_command", {"data": "test"})

    assert result["success"] is True
    assert bus.metrics.command_count == 1
    assert len(bus.metrics.command_durations) == 1
```

### Integration Tests
```python
@pytest.mark.integration
async def test_outbox_dlq_integration():
    # Outbox → DLQ フロー検証
    # 背景フラッシュタスク検証
    # CLI コマンド検証
```

### Performance Tests
```python
@pytest.mark.performance
async def test_bus_performance_under_load():
    # 1000コマンド/秒での性能測定
    # メモリ使用量測定
    # P95 < 100ms 検証
```

## 📈 監視とメトリクス

### 主要KPI
- **スループット**: コマンド/イベント処理数/秒
- **レイテンシ**: P50/P95/P99処理時間
- **信頼性**: 成功率、DLQ移行率
- **リソース**: メモリ使用量、ディスク使用量

### アラート基準
- コマンド失敗率 > 5%
- P95レイテンシ > 100ms
- DLQエントリ > 20件
- ディスク使用量 > 1GB

## 🔮 将来的な拡張

### Phase 1: スキーマ定義
```python
from pydantic import BaseModel

class CreateEpisodeCommand(BaseModel):
    title: str
    episode_number: int
    content: str = ""

# バリデーション付きハンドリング
async def handle_command_with_schema(name: str, data: dict):
    schema = COMMAND_SCHEMAS[name]
    validated_data = schema.parse_obj(data)
    # ...
```

### Phase 2: イベント名前空間
```python
# ドメイン別名前空間
await bus.emit("episode.created", payload)
await bus.emit("quality.checked", payload)
await bus.emit("plot.updated", payload)
```

### Phase 3: 分散展開
```python
# Redis/RabbitMQ バックエンド
class RedisOutboxRepository(OutboxRepository):
    # 分散環境対応
    # 複数インスタンス間でのワーカー分散
```

---

**設計原則**: Simple, Reliable, Observable
**品質目標**: <1ms レスポンス, >99.9% 信頼性, 完全可観測性
