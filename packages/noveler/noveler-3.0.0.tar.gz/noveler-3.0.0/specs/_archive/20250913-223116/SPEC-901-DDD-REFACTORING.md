# SPEC-901-DDD-REFACTORING: DDDパターンによるアーキテクチャリファクタリング

**作成日**: 2025-09-07
**更新日**: 2025-09-07
**ステータス**: 実装中
**優先度**: 高
**参照**: goldensamples/ddd_patterns_golden_sample.py, goldensamples/hexagonal_architecture_golden_sample.py

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
- **保守性**: 30%向上（責任分離による）
- **テスタビリティ**: 50%向上（依存性注入による）
- **拡張性**: 40%向上（イベント駆動による）
- **パフォーマンス**: 20%向上（非同期最適化による）

## 2. 機能要件

### 2.1 Message Bus パターンの実装
- **要件**: CQRS（Command Query Responsibility Segregation）の実装
- **機能**: コマンドとイベントの統一処理システム
- **参照**: `goldensamples/ddd_patterns_golden_sample.py` の MessageBus クラス

```python
class MessageBus:
    """メッセージバス - CQRS実装の中核"""
    def handle(self, message: Message) -> Any
    def handle_event(self, event: DomainEvent) -> None
    def handle_command(self, command: DomainCommand) -> Any
```

### 2.2 Domain Events 管理システム
- **要件**: 集約ルート内でのイベント収集・発行機能
- **機能**: ビジネスロジック実行時の自動イベント生成
- **参照**: `goldensamples/ddd_patterns_golden_sample.py` の Product.events

```python
class AggregateRoot:
    """集約ルート基底クラス"""
    def __init__(self):
        self.events: List[DomainEvent] = []

    def collect_events(self) -> List[DomainEvent]
    def clear_events(self) -> None
```

### 2.3 Port & Adapter 分離
- **要件**: インフラストラクチャ層の責任明確化
- **機能**: プラグイン可能なアダプター実装
- **参照**: `goldensamples/hexagonal_architecture_golden_sample.py` の Port/Adapter

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
- **要件**: FastMCPの非同期機能完全活用
- **機能**: タイムアウト制御とエラーハンドリング改善
- **対象**: `src/mcp_servers/noveler/json_conversion_server.py`

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

**ファイル**: `src/noveler/application/message_bus.py`

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

### 4.2 Domain Events システム

**ファイル**: `src/noveler/domain/events/base.py`

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

**ファイル**: `src/noveler/domain/events/episode_events.py`

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

### 4.3 集約ルート強化

**ファイル**: `src/noveler/domain/entities/base.py`

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

### 4.4 Port & Adapter 実装

**ディレクトリ構造**:
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

### 4.5 依存関係注入の完全適用

**ファイル**: `src/noveler/application/bootstrap.py`

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

## 5. テスト戦略

### 5.1 Unit Tests

**Message Bus テスト** (`tests/unit/application/test_message_bus.py`):
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

    def test_should_handle_event_chain_correctly(self):
        # Given
        bus = create_test_message_bus()

        # When
        bus.handle(EpisodeCreated("ep-1", "Title", 1))

        # Then
        # イベントチェーンが正しく処理されることを確認
        assert len(bus.processed_events) >= 1
```

**Domain Events テスト** (`tests/unit/domain/test_domain_events.py`):
```python
@pytest.mark.spec("SPEC-901-DDD-REFACTORING")
class TestDomainEvents:
    def test_aggregate_should_collect_events(self):
        # Given
        episode = Episode.create("Test Title", 1)

        # When
        episode.update_content("New content")
        events = episode.collect_events()

        # Then
        assert len(events) == 2  # Created + Updated
        assert isinstance(events[0], EpisodeCreated)
        assert isinstance(events[1], EpisodeContentUpdated)
```

### 5.2 Integration Tests

**MCPサーバー統合テスト** (`tests/integration/test_mcp_ddd_integration.py`):
```python
@pytest.mark.spec("SPEC-901-DDD-REFACTORING")
@pytest.mark.integration
async def test_mcp_server_with_message_bus():
    # Given
    server = create_test_mcp_server_with_message_bus()

    # When
    response = await server.handle_write_command(1, {"fresh-start": True})

    # Then
    assert response["success"] is True
    assert "エピソード1を正常に作成しました" in response["stdout"]
```

## 6. 受け入れ基準

### 6.1 機能面
- [ ] Message Bus でコマンド処理が正常に動作する
- [ ] Domain Events が集約ルートで正しく収集される
- [ ] Port & Adapter が正しく分離され、実装交換が可能
- [ ] MCPサーバーが非同期で最適化される
- [ ] 既存のCLIコマンドが変更なく動作する

### 6.2 品質面
- [ ] テストカバレッジ80%以上
- [ ] 全てのユニットテストがパス
- [ ] 統合テストがパス
- [ ] CODEMAP準拠チェックがパス
- [ ] Import-linter チェックがパス

### 6.3 パフォーマンス面
- [ ] Message Bus レスポンス時間 < 1ms
- [ ] MCPサーバーレスポンス時間 < 100ms (95%tile)
- [ ] メモリ使用量が20%以内の増加

## 7. 実装計画

### Phase 1: 基盤実装（第1コミット: 仕様書+失敗テスト）
- [x] SPEC-901-DDD-REFACTORING.md 作成
- [ ] 失敗するテストケース作成
  - `tests/unit/application/test_message_bus.py`
  - `tests/unit/domain/test_domain_events.py`
  - `tests/integration/test_mcp_ddd_integration.py`

### Phase 2: 最小実装（第2コミット: 最小実装）
- [ ] Message Bus 基本実装
- [ ] Domain Events 基本実装
- [ ] Port & Adapter 基本分離
- [ ] テストがGREENになる最小限の実装

### Phase 3: 統合・リファクタリング（第3コミット）
- [ ] 既存ユースケースへのMessage Bus統合
- [ ] MCPサーバーの非同期処理最適化
- [ ] 依存関係注入の完全適用
- [ ] CODEMAP更新と品質ゲート実行

## 8. リスク管理

### 高リスク
- **既存システムとの統合複雑性**: 段階的移行によるリスク軽減
- **パフォーマンス劣化**: 継続的なベンチマーク測定で対策

### 中リスク
- **学習コストの増加**: ゴールデンサンプルとドキュメントで軽減
- **テスト複雑化**: 従来のテストは維持、新機能は独立テスト

### 軽減策
- B20準拠の3コミット開発サイクルで段階的実装
- ゴールデンサンプルを参照実装として活用
- 既存APIの完全後方互換性維持

## 9. 参考資料

- **goldensamples/ddd_patterns_golden_sample.py**: DDD実装パターン集
- **goldensamples/hexagonal_architecture_golden_sample.py**: Port & Adapter実装例
- **docs/B20_Claude_Code開発作業指示書.md**: 開発プロセス指針
- **docs/B30_Claude_Code品質作業指示書.md**: 品質基準
- **CODEMAP.yaml**: 現在のアーキテクチャ定義
