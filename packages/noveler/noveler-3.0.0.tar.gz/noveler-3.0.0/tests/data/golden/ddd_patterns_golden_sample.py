#!/usr/bin/env python3
"""
DDD実装パターン ゴールデンサンプル

../___code-master/ から抽出した実装上非常に参考になる設計パターン集
Domain-Driven Design (DDD) の実装パターンとベストプラクティスを包含

主要パターン:
1. Unit of Work - トランザクション管理
2. Repository - データアクセス抽象化
3. Message Bus - CQRS & イベント駆動
4. Domain Events - ドメインイベント
5. Dependency Injection - 依存関係注入
6. Aggregate Root - 集約ルート
7. Clean Architecture - クリーンアーキテクチャ

作成日: 2025-09-07
参考: code-master (Pythonアーキテクチャ本実装)
"""

import abc
import inspect
from collections.abc import Callable

# 統一ロガー使用
from noveler.infrastructure.logging.unified_logger import get_logger
from dataclasses import dataclass
from datetime import date
from typing import Any, Union

# ===================================
# 1. DOMAIN LAYER - ドメイン層
# ===================================

# ドメインイベント定義
class DomainEvent:
    """ドメインイベント基底クラス"""


@dataclass
class ProductAllocated(DomainEvent):
    """在庫割当イベント"""
    order_id: str
    sku: str
    quantity: int
    batch_ref: str


@dataclass
class ProductDeallocated(DomainEvent):
    """在庫割当解除イベント"""
    order_id: str
    sku: str
    quantity: int


@dataclass
class OutOfStock(DomainEvent):
    """在庫切れイベント"""
    sku: str


# ドメインコマンド定義
class DomainCommand:
    """ドメインコマンド基底クラス"""


@dataclass
class AllocateProduct(DomainCommand):
    """在庫割当コマンド"""
    order_id: str
    sku: str
    quantity: int


@dataclass
class CreateBatch(DomainCommand):
    """バッチ作成コマンド"""
    reference: str
    sku: str
    quantity: int
    eta: date | None = None


@dataclass
class ChangeBatchQuantity(DomainCommand):
    """バッチ数量変更コマンド"""
    reference: str
    quantity: int


# 値オブジェクト
@dataclass(frozen=True)
class OrderLine:
    """注文明細値オブジェクト"""
    order_id: str
    sku: str
    quantity: int


# エンティティ
class Batch:
    """バッチエンティティ"""

    def __init__(self, reference: str, sku: str, quantity: int, eta: date | None):
        self.reference = reference
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = quantity
        self._allocations: set[OrderLine] = set()

    def __repr__(self):
        return f"<Batch {self.reference}>"

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __hash__(self):
        return hash(self.reference)

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    @property
    def available_quantity(self) -> int:
        """利用可能数量"""
        return self._purchased_quantity - sum(line.quantity for line in self._allocations)

    def can_allocate(self, line: OrderLine) -> bool:
        """割当可能性チェック"""
        return self.sku == line.sku and self.available_quantity >= line.quantity

    def allocate(self, line: OrderLine):
        """割当実行"""
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate_one(self) -> OrderLine:
        """一つの割当を解除"""
        return self._allocations.pop()


# 集約ルート
class Product:
    """
    製品集約ルート

    集約ルートパターンの実装例:
    - ドメインイベントの収集と管理
    - ビジネスルールの一元管理
    - 一貫性境界の設定
    """

    def __init__(self, sku: str, batches: list[Batch], version_number: int = 0):
        self.sku = sku
        self.batches = batches
        self.version_number = version_number
        self.events: list[DomainEvent] = []  # ドメインイベント収集

    def allocate(self, line: OrderLine) -> str | None:
        """
        在庫割当ビジネスロジック

        Returns:
            割当されたバッチ参照 or None (在庫不足時)
        """
        try:
            # 最適なバッチを選択（ETA順でソート）
            batch = next(
                b for b in sorted(self.batches)
                if b.can_allocate(line)
            )

            # 割当実行
            batch.allocate(line)
            self.version_number += 1

            # ドメインイベント発火
            self.events.append(
                ProductAllocated(
                    order_id=line.order_id,
                    sku=line.sku,
                    quantity=line.quantity,
                    batch_ref=batch.reference,
                )
            )

            return batch.reference

        except StopIteration:
            # 在庫不足時のイベント
            self.events.append(OutOfStock(line.sku))
            return None

    def change_batch_quantity(self, reference: str, quantity: int):
        """バッチ数量変更"""
        batch = next(b for b in self.batches if b.reference == reference)
        batch._purchased_quantity = quantity

        # 利用可能数量がマイナスになった場合の調整
        while batch.available_quantity < 0:
            line = batch.deallocate_one()
            self.events.append(
                ProductDeallocated(
                    order_id=line.order_id,
                    sku=line.sku,
                    quantity=line.quantity
                )
            )


# ===================================
# 2. INFRASTRUCTURE LAYER - インフラ層
# ===================================

# リポジトリパターン
class AbstractRepository(abc.ABC):
    """
    リポジトリパターン抽象基底クラス

    特徴:
    - seenセットによる追跡機能
    - テンプレートメソッドパターン
    - 具象実装の責任分離
    """

    def __init__(self):
        self.seen: set[Product] = set()  # 変更追跡用セット

    def add(self, product: Product):
        """製品追加"""
        self._add(product)
        self.seen.add(product)

    def get(self, sku: str) -> Product | None:
        """SKU指定取得"""
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    def get_by_batch_ref(self, batch_ref: str) -> Product | None:
        """バッチ参照指定取得"""
        product = self._get_by_batch_ref(batch_ref)
        if product:
            self.seen.add(product)
        return product

    @abc.abstractmethod
    def _add(self, product: Product):
        """具象実装用の追加メソッド"""
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, sku: str) -> Product | None:
        """具象実装用の取得メソッド"""
        raise NotImplementedError

    @abc.abstractmethod
    def _get_by_batch_ref(self, batch_ref: str) -> Product | None:
        """具象実装用のバッチ参照取得メソッド"""
        raise NotImplementedError


class InMemoryRepository(AbstractRepository):
    """インメモリリポジトリ実装（テスト用）"""

    def __init__(self):
        super().__init__()
        self._products: dict[str, Product] = {}

    def _add(self, product: Product):
        self._products[product.sku] = product

    def _get(self, sku: str) -> Product | None:
        return self._products.get(sku)

    def _get_by_batch_ref(self, batch_ref: str) -> Product | None:
        for product in self._products.values():
            for batch in product.batches:
                if batch.reference == batch_ref:
                    return product
        return None


# Unit of Workパターン
class AbstractUnitOfWork(abc.ABC):
    """
    Unit of Workパターン抽象基底クラス

    特徴:
    - コンテキストマネージャーによるトランザクション管理
    - ドメインイベント収集機能
    - 自動ロールバック機能
    """

    products: AbstractRepository

    def __enter__(self) -> "AbstractUnitOfWork":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()

    def commit(self):
        """コミット実行"""
        self._commit()

    def collect_new_events(self) -> list[DomainEvent]:
        """新しいドメインイベント収集"""
        events = []
        for product in self.products.seen:
            while product.events:
                events.append(product.events.pop(0))
        return events

    @abc.abstractmethod
    def _commit(self):
        """具象実装用コミット"""
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        """具象実装用ロールバック"""
        raise NotImplementedError


class InMemoryUnitOfWork(AbstractUnitOfWork):
    """インメモリUnit of Work実装"""

    def __init__(self):
        self.products = InMemoryRepository()
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass  # インメモリなのでロールバック不要


# ===================================
# 3. APPLICATION LAYER - アプリケーション層
# ===================================

# メッセージ（コマンド・イベント）の統合型
Message = Union[DomainCommand, DomainEvent]


class MessageBus:
    """
    メッセージバス - CQRS実装の中核

    特徴:
    - コマンドとイベントの分離処理
    - メッセージキュー機能
    - エラーハンドリング戦略
    - 新しいイベントの自動処理
    """

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        event_handlers: dict[type[DomainEvent], list[Callable]],
        command_handlers: dict[type[DomainCommand], Callable],
    ):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers
        self.queue: list[Message] = []

    def handle(self, message: Message):
        """メッセージ処理エントリーポイント"""
        self.queue = [message]

        while self.queue:
            message = self.queue.pop(0)

            if isinstance(message, DomainEvent):
                self.handle_event(message)
            elif isinstance(message, DomainCommand):
                self.handle_command(message)
            else:
                raise ValueError(f"未知のメッセージタイプ: {message}")

    def handle_event(self, event: DomainEvent):
        """イベント処理"""
        handlers = self.event_handlers.get(type(event), [])

        for handler in handlers:
            try:
                logging.debug(f"イベント処理: {event} with {handler}")
                handler(event)
                # 新しいイベントをキューに追加
                self.queue.extend(self.uow.collect_new_events())
            except Exception:
                logging.exception(f"イベント処理エラー: {event}")
                continue  # 他のハンドラーは継続実行

    def handle_command(self, command: DomainCommand):
        """コマンド処理"""
        try:
            handler = self.command_handlers[type(command)]
            logging.debug(f"コマンド処理: {command}")
            handler(command)
            # 新しいイベントをキューに追加
            self.queue.extend(self.uow.collect_new_events())
        except Exception:
            logging.exception(f"コマンド処理エラー: {command}")
            raise  # コマンドエラーは再発生


# ===================================
# 4. SERVICE LAYER - サービス層
# ===================================

def allocate_product_handler(
    command: AllocateProduct,
    uow: AbstractUnitOfWork
) -> str | None:
    """製品割当ハンドラー"""
    with uow:
        product = uow.products.get(command.sku)
        if product is None:
            raise ValueError(f"無効なSKU: {command.sku}")

        line = OrderLine(command.order_id, command.sku, command.quantity)
        batch_ref = product.allocate(line)
        uow.commit()
        return batch_ref


def create_batch_handler(
    command: CreateBatch,
    uow: AbstractUnitOfWork
):
    """バッチ作成ハンドラー"""
    with uow:
        product = uow.products.get(command.sku)
        if product is None:
            # 新規製品作成
            product = Product(command.sku, [])
            uow.products.add(product)

        batch = Batch(command.reference, command.sku, command.quantity, command.eta)
        product.batches.append(batch)
        uow.commit()


def change_batch_quantity_handler(
    command: ChangeBatchQuantity,
    uow: AbstractUnitOfWork
):
    """バッチ数量変更ハンドラー"""
    with uow:
        product = uow.products.get_by_batch_ref(command.reference)
        if product is None:
            raise ValueError(f"無効なバッチ参照: {command.reference}")

        product.change_batch_quantity(command.reference, command.quantity)
        uow.commit()


# イベントハンドラー例
def send_out_of_stock_notification(event: OutOfStock):
    """在庫切れ通知ハンドラー"""
    logging.info(f"在庫切れ通知送信: SKU={event.sku}")
    # 実際の通知処理（メール、Slack等）をここに実装


def update_inventory_view(event: ProductAllocated):
    """在庫ビュー更新ハンドラー（CQRS Read側更新）"""
    logging.info(f"在庫ビュー更新: SKU={event.sku}, 割当数量={event.quantity}")
    # Read側データベース更新処理をここに実装


# ===================================
# 5. BOOTSTRAP & DEPENDENCY INJECTION
# ===================================

# ハンドラー登録辞書
EVENT_HANDLERS = {
    OutOfStock: [send_out_of_stock_notification],
    ProductAllocated: [update_inventory_view],
}

COMMAND_HANDLERS = {
    AllocateProduct: allocate_product_handler,
    CreateBatch: create_batch_handler,
    ChangeBatchQuantity: change_batch_quantity_handler,
}


def inject_dependencies(handler: Callable, dependencies: dict[str, Any]) -> Callable:
    """
    依存関係注入関数

    inspect.signatureを使用して関数の引数を動的に解析し、
    必要な依存関係のみを注入する高度なDIパターン
    """
    params = inspect.signature(handler).parameters
    deps = {
        name: dependency
        for name, dependency in dependencies.items()
        if name in params
    }
    return lambda message: handler(message, **deps)


def bootstrap(
    start_orm: bool = False,
    uow: AbstractUnitOfWork | None = None,
    notifications: Any | None = None,
    publish: Callable | None = None,
) -> MessageBus:
    """
    アプリケーションブートストラップ関数

    システム全体の依存関係を解決し、MessageBusを構築する。
    テスト時と本番時で異なる実装を注入可能。
    """

    # デフォルト依存関係
    if uow is None:
        uow = InMemoryUnitOfWork()

    if notifications is None:
        notifications = get_logger("notifications")

    if publish is None:
        logger = get_logger(__name__)
        publish = lambda msg: logger.info(f"Published: {msg}")

    # 依存関係辞書
    dependencies = {
        "uow": uow,
        "notifications": notifications,
        "publish": publish,
    }

    # イベントハンドラーに依存関係注入
    injected_event_handlers = {
        event_type: [
            inject_dependencies(handler, dependencies)
            for handler in event_handlers
        ]
        for event_type, event_handlers in EVENT_HANDLERS.items()
    }

    # コマンドハンドラーに依存関係注入
    injected_command_handlers = {
        command_type: inject_dependencies(handler, dependencies)
        for command_type, handler in COMMAND_HANDLERS.items()
    }

    return MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )


# ===================================
# 6. USAGE EXAMPLES - 使用例
# ===================================

def example_basic_usage():
    """基本的な使用例"""
    print("=== DDD パターン基本使用例 ===")

    # 1. アプリケーションブートストラップ
    bus = bootstrap()

    # 2. バッチ作成
    create_command = CreateBatch("BATCH-001", "WIDGET", 100, date.today())
    bus.handle(create_command)
    print("バッチ作成完了")

    # 3. 製品割当
    allocate_command = AllocateProduct("ORDER-001", "WIDGET", 10)
    batch_ref = bus.handle(allocate_command)
    print(f"割当完了: バッチ={batch_ref}")

    # 4. 在庫不足シナリオ
    allocate_large = AllocateProduct("ORDER-002", "WIDGET", 200)
    try:
        bus.handle(allocate_large)
    except Exception as e:
        print(f"在庫不足エラー: {e}")


def example_unit_of_work_pattern():
    """Unit of Work パターン使用例"""
    print("\n=== Unit of Work パターン使用例 ===")

    uow = InMemoryUnitOfWork()

    # コンテキストマネージャーでの使用
    with uow:
        # 製品作成
        product = Product("TEST-SKU", [])
        batch = Batch("BATCH-TEST", "TEST-SKU", 50)
        product.batches.append(batch)

        uow.products.add(product)

        # 割当実行
        line = OrderLine("ORDER-TEST", "TEST-SKU", 5)
        result = product.allocate(line)
        print(f"割当結果: {result}")

        # イベント確認
        events = uow.collect_new_events()
        print(f"発生イベント: {len(events)}件")
        for event in events:
            print(f"  - {type(event).__name__}: {event}")

        # 自動コミット（__exit__で実行）

    print(f"コミット状態: {uow.committed}")


def example_repository_pattern():
    """Repository パターン使用例"""
    print("\n=== Repository パターン使用例 ===")

    repo = InMemoryRepository()

    # 製品登録
    product1 = Product("SKU-001", [Batch("B1", "SKU-001", 100)])
    product2 = Product("SKU-002", [Batch("B2", "SKU-002", 50)])

    repo.add(product1)
    repo.add(product2)

    print(f"追跡対象製品数: {len(repo.seen)}")

    # 取得テスト
    retrieved = repo.get("SKU-001")
    print(f"取得結果: {retrieved.sku if retrieved else 'None'}")

    # バッチ参照での取得
    by_batch = repo.get_by_batch_ref("B2")
    print(f"バッチ参照取得: {by_batch.sku if by_batch else 'None'}")


def example_message_bus_pattern():
    """Message Bus パターン使用例"""
    print("\n=== Message Bus パターン使用例 ===")

    # カスタムイベントハンドラー
    def custom_handler(event: ProductAllocated):
        print(f"カスタムハンドラー: {event.sku}を{event.quantity}個割当")

    # カスタムハンドラー登録
    custom_event_handlers = {
        ProductAllocated: [custom_handler, update_inventory_view],
        OutOfStock: [send_out_of_stock_notification],
    }

    uow = InMemoryUnitOfWork()
    bus = MessageBus(uow, custom_event_handlers, COMMAND_HANDLERS)

    # バッチ作成とテスト実行
    with uow:
        product = Product("MSG-TEST", [Batch("BATCH-MSG", "MSG-TEST", 20)])
        uow.products.add(product)
        uow.commit()

    # 割当実行（複数ハンドラーが実行される）
    allocate_cmd = AllocateProduct("ORDER-MSG", "MSG-TEST", 15)
    bus.handle(allocate_cmd)

    # 在庫切れテスト
    out_of_stock_cmd = AllocateProduct("ORDER-MSG-2", "MSG-TEST", 100)
    bus.handle(out_of_stock_cmd)


# ===================================
# 7. TESTING UTILITIES - テストユーティリティ
# ===================================

class FakeRepository(AbstractRepository):
    """テスト用フェイクリポジトリ"""

    def __init__(self, products: list[Product]):
        super().__init__()
        self._products = {p.sku: p for p in products}

    def _add(self, product: Product):
        self._products[product.sku] = product

    def _get(self, sku: str) -> Product | None:
        return self._products.get(sku)

    def _get_by_batch_ref(self, batch_ref: str) -> Product | None:
        for product in self._products.values():
            for batch in product.batches:
                if batch.reference == batch_ref:
                    return product
        return None


class FakeUnitOfWork(AbstractUnitOfWork):
    """テスト用フェイクUnit of Work"""

    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_golden_sample():
    """ゴールデンサンプルのテスト"""
    print("\n=== ゴールデンサンプル統合テスト ===")

    # テスト用システム構築
    uow = FakeUnitOfWork()
    bus = bootstrap(uow=uow)

    # シナリオテスト
    try:
        # 1. バッチ作成
        bus.handle(CreateBatch("TEST-BATCH", "TEST-SKU", 100))

        # 2. 割当実行
        bus.handle(AllocateProduct("ORDER-001", "TEST-SKU", 10))

        # 3. バッチ数量変更
        bus.handle(ChangeBatchQuantity("TEST-BATCH", 50))

        # 4. 大量割当（在庫切れ発生）
        bus.handle(AllocateProduct("ORDER-002", "TEST-SKU", 100))

        print("✅ 全シナリオテスト完了")

    except Exception as e:
        print(f"❌ テストエラー: {e}")


# ===================================
# 8. MAIN EXECUTION
# ===================================

if __name__ == "__main__":
    """実行例"""
    logging.basicConfig(level=logging.INFO)

    print("DDD実装パターン ゴールデンサンプル実行")
    print("=" * 50)

    # 各パターンの実行例
    example_basic_usage()
    example_unit_of_work_pattern()
    example_repository_pattern()
    example_message_bus_pattern()

    # 統合テスト
    test_golden_sample()

    print("\n" + "=" * 50)
    print("ゴールデンサンプル実行完了")
    print("\n主要パターンの説明:")
    print("1. Unit of Work - トランザクション境界とイベント収集")
    print("2. Repository - データアクセス抽象化と変更追跡")
    print("3. Message Bus - CQRS実装とイベント駆動処理")
    print("4. Aggregate Root - ビジネスルールとイベント管理")
    print("5. Dependency Injection - 動的依存関係解決")
    print("6. Clean Architecture - レイヤー分離と依存関係逆転")
