---
spec_id: SPEC-901
status: canonical
owner: bamboocity
last_reviewed: 2025-09-15
category: ARCH
sources: [REQ]
tags: [ddd, architecture, refactoring, async, message_bus]
---
# SPEC-901-DDD-REFACTORING: DDDパターンによるアーキテクチャリファクタリング

**作成日**: 2025-09-07
**更新日**: 2025-09-21
**ステータス**: 実装中（現用/canonical）
**優先度**: 高
**参照**: goldensamples/ddd_patterns_golden_sample.py, goldensamples/hexagonal_architecture_golden_sample.py, archive/demo_servers/mcp_server*.py (アーカイブ)

## 1. 概要

### 目的
ゴールデンサンプル（DDD patterns, Hexagonal Architecture）を参考に、novelerプロジェクトのアーキテクチャをDDD/ヘキサゴナルアーキテクチャパターンに完全準拠させる。

### 背景
現在のnovelerプロジェクトは部分的にDDDパターンを適用しているが、以下の重要な要素が不完全または未実装：
- Message Bus パターン（CQRS実装の中核）
- Domain Events の完全な管理
- Port & Adapter の明確な分離
- 依存関係注入の完全適用

### 期待効果
- 保守性: 30%向上（責任分離による）
- テスタビリティ: 50%向上（依存性注入による）
- 拡張性: 40%向上（イベント駆動による）
- パフォーマンス: 20%向上（非同期最適化による）

## 2. 機能要件

### 2.1 Message Bus パターンの実装
- 要件: CQRS（Command Query Responsibility Segregation）の実装
- 機能: コマンドとイベントの統一処理システム
- 参照: `goldensamples/ddd_patterns_golden_sample.py` の MessageBus クラス

```python
class MessageBus:
    """メッセージバス - CQRS実装の中核"""
    def handle(self, message: Message) -> Any
    def handle_event(self, event: DomainEvent) -> None
    def handle_command(self, command: DomainCommand) -> Any
```

### 2.2 Domain Events 管理システム
- 要件: 集約ルート内でのイベント収集・発行機能
- 機能: ビジネスロジック実行時の自動イベント生成
- 参照: `goldensamples/ddd_patterns_golden_sample.py` の Product.events

```python
class AggregateRoot:
    """集約ルート基底クラス"""
    def __init__(self):
        self.events: List[DomainEvent] = []

    def collect_events(self) -> List[DomainEvent]
    def clear_events(self) -> None
```

### 2.3 Port & Adapter 分離
- 要件: インフラストラクチャ層の責任明確化
- 機能: プラグイン可能なアダプター実装
- 参照: `goldensamples/hexagonal_architecture_golden_sample.py` の Port/Adapter

```python
# ポート（インターフェース）
class EpisodeRepository(abc.ABC):
    @abc.abstractmethod
    async def save(self, episode: Episode) -> None

    @abc.abstractmethod
    async def find_by_id(self, episode_id: str) -> Optional[Episode]

# アダプター（実装）
class FileSystemEpisodeRepository(EpisodeRepository):
    async def save(self, episode: Episode) -> None: ...
    async def find_by_id(self, episode_id: str) -> Optional[Episode]: ...
```

### 2.4 MCPサーバー非同期最適化
- 要件: FastMCPの非同期機能完全活用
- 機能: タイムアウト制御とエラーハンドリング改善
- 対象: `src/mcp_servers/noveler/json_conversion_server.py`

## 3. 非機能要件

### 3.1 パフォーマンス要件
- Message Bus のメッセージ処理: 1ms以内
- Domain Events の収集・発行: 5ms以内
- MCPサーバーのレスポンス時間: 100ms以内（95%tile）

### 3.2 品質要件
- テストカバレッジ: 80%以上を維持
- 循環依存: 0件（import-linterでチェック）
- CODEMAP準拠: 100%

### 3.3 互換性要件
- 既存API: 完全な後方互換性維持
- CLI コマンド: 変更なし
- MCP インターフェース: レスポンス形式統一

## 4. 実装詳細

### 4.1 Message Bus 実装

ファイル: `src/noveler/application/message_bus.py`

```python
from typing import Dict, List, Type, Callable, Union
from noveler.domain.events.base import DomainEvent
from noveler.domain.commands.base import DomainCommand

Message = Union[DomainCommand, DomainEvent]

class MessageBus:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        event_handlers: Dict[Type[DomainEvent], List[Callable]],
        command_handlers: Dict[Type[DomainCommand], Callable],
    ):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers
        self.queue: List[Message] = []

    def handle(self, message: Message) -> Any:
        """メッセージ処理のエントリーポイント"""
        self.queue = [message]

        while self.queue:
            message = self.queue.pop(0)

            if isinstance(message, DomainEvent):
                self.handle_event(message)
            elif isinstance(message, DomainCommand):
                return self.handle_command(message)
            else:
                raise ValueError(f"未対応メッセージタイプ: {message}")
```

#### 4.1a Simple Message Bus（最小・文字列名ベース／実装完了）

ファイル: `src/noveler/application/simple_message_bus.py`

- 目的: SPEC-901 の段階導入として、文字列名ベースの軽量Busを提供（既存の型ベース Bus は温存）
- 機能: UoW（commit 後イベント発行）、Outbox（同期/遅延ディスパッチ）、べき等性、イベントハンドラのリトライ、DLQ、メトリクス収集
- 主なAPI:
  - `await bus.handle_command(name: str, data: dict)`
  - `await bus.emit(event_name: str, payload: dict)`
  - `await bus.flush_outbox(limit=100)`
  - `await bus.start_background_flusher(interval_seconds=30.0)`
  - `await bus.get_dlq_stats()`
  - `bus.get_metrics_summary()`

関連モジュール:
- `src/noveler/application/uow.py`（InMemoryUnitOfWork）
- `src/noveler/application/outbox.py`（OutboxEntry, OutboxRepository）
- `src/noveler/infrastructure/adapters/file_outbox_repository.py`（ファイルベース実装）
- `src/noveler/application/idempotency.py`（べき等性管理）

### 4.2 Outbox / Idempotency 基盤（2025-09-22完全実装）

イベントの確実な配送、コマンド重複防止、運用監視を目的とした完全な基盤を実装完了。

#### 4.2.1 コア実装

- **Outbox Repository**: `src/noveler/application/outbox.py`, `src/noveler/infrastructure/adapters/file_outbox_repository.py`
  - ファイルベース (`<project>/temp/bus_outbox/`) でイベント管理
  - `OutboxEntry` に `last_error`, `failed_at` フィールド追加（DLQ対応）
  - DLQディレクトリ (`dlq/`) で失敗イベント分離
  - `increment_attempts()`, `move_to_dlq()`, `load_dlq_entries()` メソッド実装
- **Idempotency Store**: `src/noveler/application/idempotency.py`
  - `event_id` ベースの重複イベント検知（InMemory実装）
- **BusConfig**: 設定拡張
  - `dlq_max_attempts: int = 5` - DLQ移行しきい値
  - リトライ設定（`max_retries`, `backoff_base_sec`, `backoff_max_sec`, `jitter_sec`）
- **BusMetrics**: `src/noveler/application/simple_message_bus.py`
  - 処理数、処理時間、失敗率の統計収集
  - P50/P95パーセンタイル計算
  - `get_command_stats()`, `get_event_stats()` メソッド

#### 4.2.2 運用・信頼性機能（完全実装済み）

- ✅ **背景フラッシュタスク**: 30秒間隔でOutbox自動フラッシュ、`NOVELER_DISABLE_BACKGROUND_FLUSH=1` で無効化
- ✅ **Dead Letter Queue**: 5回失敗でDLQ移行、エラー情報保持、監視ログ出力
- ✅ **メトリクス/トレース**: 処理時間計測（`time.perf_counter()`）、統計情報可視化
- ✅ **運用CLI**: `src/noveler/presentation/cli/commands/bus_commands.py`
  - `noveler bus flush [--limit] [--dry-run]` - 手動Outboxフラッシュ
  - `noveler bus list [--type pending|dlq|all] [--format table|json]` - エントリ一覧
  - `noveler bus replay <entry_id> [--force]` - DLQエントリ再実行
  - `noveler bus health [--detailed]` - ヘルス状況表示
  - `noveler bus metrics [--reset]` - パフォーマンス指標表示

#### 4.2.3 次期拡張候補

- コマンド/イベントのスキーマ（pydantic）定義と入力バリデーション
- 互換層（既存型ベースBus ↔ SimpleBus）のブリッジ実装
- Busコマンド拡充（`check_quality`, `publish_episode`, `update_plot`）
- イベント体系化（`episode.*`, `quality.*`, `plot.*` 名前空間）
- データストア差し替え（ファイル → DB）のRepository抽象化拡張

これにより SPEC-901 の非機能要件（高信頼配送・再送制御・監視・運用）が完全に満たされた。


### 4.3 Domain Events システム

ファイル: `src/noveler/domain/events/base.py`

```python
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

@dataclass
class DomainEvent(ABC):
    """ドメインイベント基底クラス"""
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
```

ファイル: `src/noveler/domain/events/episode_events.py`

```python
@dataclass
class EpisodeCreated(DomainEvent):
    """エピソード作成完了イベント"""
    episode_id: str
    title: str
    episode_number: int

@dataclass
class EpisodeContentUpdated(DomainEvent):
    """エピソード内容更新イベント"""
    episode_id: str
    word_count: int
    previous_word_count: int
```

### 4.4 集約ルート強化

ファイル: `src/noveler/domain/entities/base.py`

```python
class AggregateRoot(ABC):
    """集約ルート基底クラス - イベント管理機能付き"""

    def __init__(self):
        self._events: List[DomainEvent] = []
        self._version: int = 0

    def add_event(self, event: DomainEvent) -> None:
        """ドメインイベント追加"""
        self._events.append(event)

    def collect_events(self) -> List[DomainEvent]:
        """イベント収集（クリア付き）"""
        events = self._events.copy()
        self._events.clear()
        return events

    def increment_version(self) -> None:
        """バージョン増加（楽観的ロック用）"""
        self._version += 1
```

### 4.5 Port & Adapter 実装

ディレクトリ構造:
```
src/noveler/infrastructure/
├── adapters/
│   ├── repositories/
│   │   ├── file_episode_repository.py
│   │   ├── database_episode_repository.py
│   │   └── in_memory_episode_repository.py
│   ├── external_services/
│   │   ├── ai_service_adapter.py
│   │   └── notification_service_adapter.py
│   └── mcp/
│       ├── mcp_command_adapter.py
│       └── mcp_response_adapter.py
└── ports/
    ├── repositories/
    │   ├── episode_repository.py
    │   └── plot_repository.py
    └── external_services/
        ├── ai_service_port.py
        └── notification_service_port.py
```

### 4.6 依存関係注入の完全適用

ファイル: `src/noveler/application/bootstrap.py`

```python
def bootstrap_message_bus(
    uow: AbstractUnitOfWork = None,
    notifications: NotificationService = None,
    ai_service: AIService = None,
) -> MessageBus:
    """アプリケーション依存関係注入とブートストラップ"""

    if uow is None:
        uow = create_default_unit_of_work()

    dependencies = {
        "uow": uow,
        "notifications": notifications or create_default_notifications(),
        "ai_service": ai_service or create_default_ai_service(),
    }

    # 動的依存関係注入
    injected_event_handlers = inject_dependencies_to_handlers(
        EVENT_HANDLERS, dependencies
    )
    injected_command_handlers = inject_dependencies_to_handlers(
        COMMAND_HANDLERS, dependencies
    )

    return MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )
```

### 4.7 Unit of Work（実装済み）

ファイル: `src/noveler/application/uow.py`

```python
class UnitOfWork(Protocol):
    def begin(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def add_event(self, name: str, payload: dict[str, Any] | None = None) -> None: ...
```

`InMemoryUnitOfWork` は `episode_repo` を抱え、`add_event()` したイベントは commit 後に Bus 側で発行される。

### 4.8 Outbox + べき等性 + リトライ（実装済み）

- Outbox リポジトリ: `src/noveler/application/outbox.py`, `src/noveler/infrastructure/adapters/file_outbox_repository.py`
  - 1イベント=1JSON、`./temp/bus_outbox/` に pending 保存→配信後 `dispatched` に更新
- べき等性ストア: `src/noveler/application/idempotency.py`
  - `event_id` を記録し二重配信回避（InMemory 実装）
- リトライ戦略（BusConfig）: `max_retries`, `backoff_base_sec`, `backoff_max_sec`, `jitter_sec`
  - イベントハンドラ実行を指数バックオフ＋ジッタで再試行

### 4.9 MCP サーバー統合（実装済み）

ファイル: `src/mcp_servers/noveler/json_conversion_server.py`

```python
server = JSONConversionServer(use_message_bus=True)
await server.handle_write_command(episode_number=1, opts={})
# => {"success": True, "episode_id": "ep-1", "events_processed": ["episode_written"]}
```

`noveler_write` ツールも Bus 有効時は Bus 経由で実行される。

## 5. テスト戦略

### 5.1 Unit Tests

Message Bus テスト（例）:
```python
@pytest.mark.spec("SPEC-901-DDD-REFACTORING")
class TestMessageBus:
    def test_should_handle_command_successfully(self):
        # Given
        bus = create_test_message_bus()
        command = CreateEpisodeCommand(title="Test", episode_number=1)

        # When
        result = bus.handle(command)

        # Then
        assert result.success is True
        assert "Test" in result.episode.title
```

### 5.2 Integration Tests（現用テスト）

以下の統合テストでSPEC-901の受け入れを担保：
- `tests/integration/test_spec_901_async_mcp_integration.py`
  - 非同期Subprocessアダプタ/並列実行/タイムアウト要件
  - Async/Synchronous MessageBus性能要件（<1ms）の確認
- `tests/integration/test_mcp_ddd_integration.py`
  - MCP-MessageBus 統合、イベント収集、後方互換性、Port&Adapter 切替の最小確認

SPEC-901のテストはデフォルトでスキップされ、以下の環境変数で有効化する：

```
ENABLE_SPEC_901_TESTS=1 pytest -k mcp_ddd_integration
```

## 6. 受け入れ基準（抜粋）

### 機能面
- Message Bus でコマンド処理が正常に動作する
- Domain Events が集約ルートで正しく収集される
- Port & Adapter が正しく分離され、実装交換が可能
- MCPサーバーが非同期で最適化される
- 既存のCLIコマンドが変更なく動作する

### 品質面
- テストカバレッジ80%以上
- 循環依存0件、CODEMAP準拠

### パフォーマンス面
- Message Bus レスポンス時間 < 1ms
- MCPサーバーレスポンス時間 < 100ms (95%tile)

## 7. 実装計画（概要）

Phase 1: 仕様書＋失敗テスト
Phase 2: 最小実装
Phase 3: 統合・リファクタリング

## 8. リスク管理（抜粋）
- 統合複雑性: 段階移行で軽減
- 性能劣化: ベンチマーク継続
- 学習コスト: ゴールデンサンプル提示

## 9. 参考資料
- goldensamples/ddd_patterns_golden_sample.py
- goldensamples/hexagonal_architecture_golden_sample.py
- docs/B20_Claude_Code開発作業指示書.md
- docs/B30_Claude_Code品質作業指示書.md
- CODEMAP.yaml
