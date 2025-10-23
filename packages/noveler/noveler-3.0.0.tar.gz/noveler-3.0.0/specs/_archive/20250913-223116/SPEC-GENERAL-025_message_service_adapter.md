# SPEC-GENERAL-025: メッセージサービスアダプター仕様書

## 概要
メッセージサービスアダプターは、システム内外への通知・メッセージ配信機能を統一的に提供するアダプターです。複数の通知チャネル（メール、Slack、Discord、システム内通知等）を抽象化し、一貫したメッセージングインターフェースを提供します。

## クラス設計

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class MessageType(Enum):
    """メッセージタイプ"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    NOTIFICATION = "notification"
    ALERT = "alert"

class MessagePriority(Enum):
    """メッセージ優先度"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class DeliveryChannel(Enum):
    """配信チャネル"""
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    SYSTEM = "system"
    WEBHOOK = "webhook"
    SMS = "sms"

@dataclass
class Message:
    """メッセージ"""
    id: str
    type: MessageType
    priority: MessagePriority
    title: str
    content: str
    recipient: str
    channel: DeliveryChannel
    metadata: Dict[str, Any]
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    attachments: List[Dict[str, Any]] = None

@dataclass
class DeliveryResult:
    """配信結果"""
    message_id: str
    channel: DeliveryChannel
    success: bool
    delivered_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    metadata: Dict[str, Any]

class IMessageChannelProvider(ABC):
    """メッセージチャネルプロバイダーインターフェース"""

    @abstractmethod
    def send(self, message: Message) -> DeliveryResult:
        """メッセージを送信"""
        pass

    @abstractmethod
    def supports_channel(self, channel: DeliveryChannel) -> bool:
        """チャネルをサポートするか判定"""
        pass

    @abstractmethod
    def get_channel_status(self) -> Dict[str, Any]:
        """チャネル状態を取得"""
        pass

class MessageServiceAdapter:
    """メッセージサービスアダプター"""

    def __init__(
        self,
        channel_providers: Dict[DeliveryChannel, IMessageChannelProvider],
        message_formatter: IMessageFormatter,
        delivery_tracker: IDeliveryTracker,
        retry_handler: IRetryHandler,
        template_engine: ITemplateEngine
    ):
        self._providers = channel_providers
        self._formatter = message_formatter
        self._tracker = delivery_tracker
        self._retry_handler = retry_handler
        self._template_engine = template_engine
```

## データ構造

### インターフェース定義

```python
class IMessageFormatter(ABC):
    """メッセージフォーマッターインターフェース"""

    @abstractmethod
    def format_for_channel(
        self,
        message: Message,
        channel: DeliveryChannel
    ) -> Dict[str, Any]:
        """チャネル固有の形式でメッセージをフォーマット"""
        pass

    @abstractmethod
    def validate_message(self, message: Message) -> List[str]:
        """メッセージを検証"""
        pass

class IDeliveryTracker(ABC):
    """配信追跡インターフェース"""

    @abstractmethod
    def track_delivery(self, result: DeliveryResult) -> None:
        """配信を追跡"""
        pass

    @abstractmethod
    def get_delivery_status(self, message_id: str) -> List[DeliveryResult]:
        """配信状態を取得"""
        pass

    @abstractmethod
    def get_delivery_statistics(self, period: Dict[str, Any]) -> Dict[str, Any]:
        """配信統計を取得"""
        pass

class IRetryHandler(ABC):
    """リトライハンドラーインターフェース"""

    @abstractmethod
    def should_retry(self, result: DeliveryResult) -> bool:
        """リトライすべきか判定"""
        pass

    @abstractmethod
    def calculate_retry_delay(self, retry_count: int) -> int:
        """リトライ遅延を計算"""
        pass

    @abstractmethod
    def get_max_retries(self, channel: DeliveryChannel) -> int:
        """最大リトライ回数を取得"""
        pass

class ITemplateEngine(ABC):
    """テンプレートエンジンインターフェース"""

    @abstractmethod
    def render_template(
        self,
        template_name: str,
        data: Dict[str, Any]
    ) -> str:
        """テンプレートをレンダリング"""
        pass

    @abstractmethod
    def register_template(self, name: str, template: str) -> None:
        """テンプレートを登録"""
        pass
```

### アダプター実装

```python
@dataclass
class MessageDeliveryRequest:
    """メッセージ配信要求"""
    recipient: str
    channels: List[DeliveryChannel]
    template_name: Optional[str]
    template_data: Dict[str, Any]
    message_type: MessageType
    priority: MessagePriority
    scheduled_at: Optional[datetime]
    options: Dict[str, Any]

@dataclass
class BulkDeliveryRequest:
    """一括配信要求"""
    recipients: List[str]
    channels: List[DeliveryChannel]
    template_name: str
    template_data: Dict[str, Any]
    message_type: MessageType
    priority: MessagePriority
    batch_size: int
    delay_between_batches: int

@dataclass
class MessageStats:
    """メッセージ統計"""
    total_sent: int
    successful_deliveries: int
    failed_deliveries: int
    retry_attempts: int
    channel_breakdown: Dict[str, int]
    error_breakdown: Dict[str, int]

class DefaultMessageFormatter(IMessageFormatter):
    """デフォルトメッセージフォーマッター"""

    def format_for_channel(
        self,
        message: Message,
        channel: DeliveryChannel
    ) -> Dict[str, Any]:
        """チャネル固有フォーマット"""
        base_format = {
            "title": message.title,
            "content": message.content,
            "priority": message.priority.value,
            "timestamp": message.created_at.isoformat()
        }

        if channel == DeliveryChannel.SLACK:
            return self._format_for_slack(message, base_format)
        elif channel == DeliveryChannel.DISCORD:
            return self._format_for_discord(message, base_format)
        elif channel == DeliveryChannel.EMAIL:
            return self._format_for_email(message, base_format)
        else:
            return base_format

    def _format_for_slack(
        self,
        message: Message,
        base_format: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Slack形式でフォーマット"""
        slack_format = {
            "text": f"*{message.title}*",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message.content
                    }
                }
            ],
            "priority": self._get_slack_priority_color(message.priority)
        }

        # 添付ファイルがある場合
        if message.attachments:
            slack_format["attachments"] = self._format_slack_attachments(
                message.attachments
            )

        return slack_format
```

## パブリックメソッド

### MessageServiceAdapter

```python
def send_message(self, request: MessageDeliveryRequest) -> Dict[str, DeliveryResult]:
    """
    メッセージを送信

    Args:
        request: 配信要求

    Returns:
        Dict[str, DeliveryResult]: チャネル別配信結果
    """
    # テンプレートレンダリング
    content = self._render_content(request)

    # メッセージ作成
    message = Message(
        id=self._generate_message_id(),
        type=request.message_type,
        priority=request.priority,
        title=self._extract_title(content, request),
        content=content,
        recipient=request.recipient,
        channel=DeliveryChannel.SYSTEM,  # デフォルト、実際は各チャネルで上書き
        metadata=request.options,
        created_at=datetime.now(),
        scheduled_at=request.scheduled_at
    )

    # 複数チャネルへの配信
    results = {}

    for channel in request.channels:
        channel_message = self._adapt_message_for_channel(message, channel)

        # スケジュール配信チェック
        if request.scheduled_at and request.scheduled_at > datetime.now():
            result = self._schedule_delivery(channel_message)
        else:
            result = self._deliver_immediately(channel_message)

        results[channel.value] = result

        # 配信追跡
        self._tracker.track_delivery(result)

    return results

def send_bulk_messages(
    self,
    request: BulkDeliveryRequest
) -> Dict[str, List[DeliveryResult]]:
    """
    一括メッセージ送信

    Args:
        request: 一括配信要求

    Returns:
        Dict[str, List[DeliveryResult]]: チャネル別配信結果リスト
    """
    results = {}

    # 受信者をバッチに分割
    batches = self._split_into_batches(request.recipients, request.batch_size)

    for channel in request.channels:
        channel_results = []

        for batch in batches:
            # バッチ内の各受信者に配信
            for recipient in batch:
                delivery_request = MessageDeliveryRequest(
                    recipient=recipient,
                    channels=[channel],
                    template_name=request.template_name,
                    template_data=request.template_data,
                    message_type=request.message_type,
                    priority=request.priority,
                    scheduled_at=None,
                    options={}
                )

                batch_results = self.send_message(delivery_request)
                channel_results.extend(batch_results.values())

            # バッチ間遅延
            if request.delay_between_batches > 0:
                time.sleep(request.delay_between_batches)

        results[channel.value] = channel_results

    return results

def retry_failed_deliveries(self, time_window: int = 3600) -> List[DeliveryResult]:
    """
    失敗した配信をリトライ

    Args:
        time_window: リトライ対象の時間窓（秒）

    Returns:
        List[DeliveryResult]: リトライ結果
    """
    # 失敗した配信を取得
    failed_deliveries = self._tracker.get_failed_deliveries_in_window(time_window)

    retry_results = []

    for failed_result in failed_deliveries:
        # リトライ可否判定
        if not self._retry_handler.should_retry(failed_result):
            continue

        # 最大リトライ回数チェック
        max_retries = self._retry_handler.get_max_retries(failed_result.channel)
        if failed_result.retry_count >= max_retries:
            continue

        # リトライ実行
        try:
            # 元のメッセージを復元
            original_message = self._restore_message_from_result(failed_result)

            # リトライ
            retry_result = self._deliver_immediately(original_message)
            retry_result.retry_count = failed_result.retry_count + 1

            retry_results.append(retry_result)
            self._tracker.track_delivery(retry_result)

        except Exception as e:
            logger.error(f"リトライ失敗: {e}")

    return retry_results

def get_delivery_statistics(
    self,
    start_date: datetime,
    end_date: datetime
) -> MessageStats:
    """
    配信統計を取得

    Args:
        start_date: 開始日時
        end_date: 終了日時

    Returns:
        MessageStats: 配信統計
    """
    period = {"start": start_date, "end": end_date}
    raw_stats = self._tracker.get_delivery_statistics(period)

    return MessageStats(
        total_sent=raw_stats.get("total_sent", 0),
        successful_deliveries=raw_stats.get("successful", 0),
        failed_deliveries=raw_stats.get("failed", 0),
        retry_attempts=raw_stats.get("retries", 0),
        channel_breakdown=raw_stats.get("by_channel", {}),
        error_breakdown=raw_stats.get("by_error", {})
    )

def check_channel_health(self) -> Dict[str, Dict[str, Any]]:
    """
    チャネル健全性をチェック

    Returns:
        Dict[str, Dict[str, Any]]: チャネル別健全性情報
    """
    health_status = {}

    for channel, provider in self._providers.items():
        try:
            status = provider.get_channel_status()
            health_status[channel.value] = {
                "healthy": status.get("healthy", False),
                "response_time": status.get("response_time"),
                "error_rate": status.get("error_rate", 0.0),
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            health_status[channel.value] = {
                "healthy": False,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }

    return health_status
```

## プライベートメソッド

```python
def _render_content(self, request: MessageDeliveryRequest) -> str:
    """コンテンツをレンダリング"""
    if request.template_name:
        return self._template_engine.render_template(
            request.template_name,
            request.template_data
        )
    else:
        # テンプレートデータから直接コンテンツ作成
        return request.template_data.get("content", "")

def _adapt_message_for_channel(
    self,
    message: Message,
    channel: DeliveryChannel
) -> Message:
    """チャネル用にメッセージを適応"""
    adapted_message = Message(
        id=message.id,
        type=message.type,
        priority=message.priority,
        title=message.title,
        content=message.content,
        recipient=message.recipient,
        channel=channel,
        metadata=message.metadata,
        created_at=message.created_at,
        scheduled_at=message.scheduled_at,
        attachments=message.attachments
    )

    # チャネル固有のフォーマット適用
    formatted_data = self._formatter.format_for_channel(adapted_message, channel)
    adapted_message.content = formatted_data.get("content", message.content)
    adapted_message.title = formatted_data.get("title", message.title)

    return adapted_message

def _deliver_immediately(self, message: Message) -> DeliveryResult:
    """即座にメッセージを配信"""
    provider = self._providers.get(message.channel)

    if not provider:
        return DeliveryResult(
            message_id=message.id,
            channel=message.channel,
            success=False,
            delivered_at=None,
            error_message=f"チャネル {message.channel.value} のプロバイダーが見つかりません",
            retry_count=0,
            metadata={}
        )

    try:
        # メッセージ検証
        validation_errors = self._formatter.validate_message(message)
        if validation_errors:
            return DeliveryResult(
                message_id=message.id,
                channel=message.channel,
                success=False,
                delivered_at=None,
                error_message=f"検証エラー: {', '.join(validation_errors)}",
                retry_count=0,
                metadata={"validation_errors": validation_errors}
            )

        # 配信実行
        result = provider.send(message)
        return result

    except Exception as e:
        return DeliveryResult(
            message_id=message.id,
            channel=message.channel,
            success=False,
            delivered_at=None,
            error_message=str(e),
            retry_count=0,
            metadata={"exception": type(e).__name__}
        )

def _schedule_delivery(self, message: Message) -> DeliveryResult:
    """配信をスケジュール"""
    # 実装では、スケジュールシステム（Celery、Redis等）を使用
    scheduler_id = self._schedule_message_delivery(message)

    return DeliveryResult(
        message_id=message.id,
        channel=message.channel,
        success=True,
        delivered_at=None,  # スケジュール済み
        error_message=None,
        retry_count=0,
        metadata={
            "scheduled": True,
            "scheduler_id": scheduler_id,
            "scheduled_at": message.scheduled_at.isoformat()
        }
    )

def _split_into_batches(
    self,
    items: List[str],
    batch_size: int
) -> List[List[str]]:
    """リストをバッチに分割"""
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i:i + batch_size])
    return batches

def _generate_message_id(self) -> str:
    """メッセージIDを生成"""
    import uuid
    return f"msg_{uuid.uuid4().hex[:8]}"

def _extract_title(
    self,
    content: str,
    request: MessageDeliveryRequest
) -> str:
    """コンテンツからタイトルを抽出"""
    # タイトルがテンプレートデータに含まれている場合
    if "title" in request.template_data:
        return request.template_data["title"]

    # コンテンツの最初の行をタイトルとして使用
    lines = content.split('\n', 1)
    if lines:
        return lines[0][:100]  # 最大100文字

    return "通知"
```

## アダプターパターン実装

### チャネルプロバイダー実装

```python
class SlackChannelProvider(IMessageChannelProvider):
    """Slackチャネルプロバイダー"""

    def __init__(self, webhook_url: str, token: str):
        self._webhook_url = webhook_url
        self._token = token

    def send(self, message: Message) -> DeliveryResult:
        import requests

        try:
            formatted_message = self._format_slack_message(message)

            response = requests.post(
                self._webhook_url,
                json=formatted_message,
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=30
            )

            success = response.status_code == 200

            return DeliveryResult(
                message_id=message.id,
                channel=DeliveryChannel.SLACK,
                success=success,
                delivered_at=datetime.now() if success else None,
                error_message=response.text if not success else None,
                retry_count=0,
                metadata={"status_code": response.status_code}
            )

        except Exception as e:
            return DeliveryResult(
                message_id=message.id,
                channel=DeliveryChannel.SLACK,
                success=False,
                delivered_at=None,
                error_message=str(e),
                retry_count=0,
                metadata={"exception": type(e).__name__}
            )

    def supports_channel(self, channel: DeliveryChannel) -> bool:
        return channel == DeliveryChannel.SLACK

    def get_channel_status(self) -> Dict[str, Any]:
        # Slack APIの状態をチェック
        try:
            import requests
            response = requests.get(
                "https://slack.com/api/api.test",
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=10
            )

            return {
                "healthy": response.status_code == 200,
                "response_time": response.elapsed.total_seconds(),
                "error_rate": 0.0 if response.status_code == 200 else 1.0
            }
        except Exception:
            return {"healthy": False, "error_rate": 1.0}

class EmailChannelProvider(IMessageChannelProvider):
    """メールチャネルプロバイダー"""

    def __init__(self, smtp_config: Dict[str, Any]):
        self._smtp_config = smtp_config

    def send(self, message: Message) -> DeliveryResult:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        try:
            # メール作成
            msg = MIMEMultipart()
            msg['From'] = self._smtp_config['sender']
            msg['To'] = message.recipient
            msg['Subject'] = message.title

            # HTML/テキストコンテンツ
            msg.attach(MIMEText(message.content, 'html'))

            # SMTP送信
            with smtplib.SMTP(
                self._smtp_config['host'],
                self._smtp_config['port']
            ) as server:
                server.starttls()
                server.login(
                    self._smtp_config['username'],
                    self._smtp_config['password']
                )
                server.send_message(msg)

            return DeliveryResult(
                message_id=message.id,
                channel=DeliveryChannel.EMAIL,
                success=True,
                delivered_at=datetime.now(),
                error_message=None,
                retry_count=0,
                metadata={}
            )

        except Exception as e:
            return DeliveryResult(
                message_id=message.id,
                channel=DeliveryChannel.EMAIL,
                success=False,
                delivered_at=None,
                error_message=str(e),
                retry_count=0,
                metadata={"exception": type(e).__name__}
            )

    def supports_channel(self, channel: DeliveryChannel) -> bool:
        return channel == DeliveryChannel.EMAIL

    def get_channel_status(self) -> Dict[str, Any]:
        # SMTP接続テスト
        try:
            import smtplib
            with smtplib.SMTP(
                self._smtp_config['host'],
                self._smtp_config['port'],
                timeout=10
            ) as server:
                server.starttls()
                return {"healthy": True, "error_rate": 0.0}
        except Exception:
            return {"healthy": False, "error_rate": 1.0}
```

## 依存関係

```python
from domain.events import DomainEvent
from domain.services import NotificationService
from application.use_cases import SendNotificationUseCase
from infrastructure.services import (
    TemplateService,
    SchedulerService,
    EmailService,
    SlackService
)
```

## 設計原則遵守

### アダプターパターン
- **プロバイダー抽象化**: 複数の通知チャネルを統一インターフェースで提供
- **メッセージフォーマット**: チャネル固有のメッセージ形式を抽象化
- **配信戦略**: 即座配信・スケジュール配信・バッチ配信を統一

### 責任の分離
- **メッセージ配信**: チャネルプロバイダーが担当
- **フォーマット**: メッセージフォーマッターが担当
- **追跡**: 配信追跡サービスが担当
- **リトライ**: リトライハンドラーが担当

## 使用例

### 基本的な使用

```python
# チャネルプロバイダー設定
providers = {
    DeliveryChannel.SLACK: SlackChannelProvider(webhook_url, token),
    DeliveryChannel.EMAIL: EmailChannelProvider(smtp_config),
    DeliveryChannel.DISCORD: DiscordChannelProvider(webhook_url)
}

# アダプター初期化
message_service = MessageServiceAdapter(
    channel_providers=providers,
    message_formatter=DefaultMessageFormatter(),
    delivery_tracker=DatabaseDeliveryTracker(),
    retry_handler=ExponentialBackoffRetryHandler(),
    template_engine=JinjaTemplateEngine()
)

# メッセージ送信
request = MessageDeliveryRequest(
    recipient="user@example.com",
    channels=[DeliveryChannel.EMAIL, DeliveryChannel.SLACK],
    template_name="episode_published",
    template_data={
        "title": "新エピソード公開",
        "episode_title": "第1話: 始まり",
        "project_name": "異世界転生物語"
    },
    message_type=MessageType.NOTIFICATION,
    priority=MessagePriority.NORMAL,
    scheduled_at=None,
    options={}
)

results = message_service.send_message(request)
for channel, result in results.items():
    print(f"{channel}: {'成功' if result.success else '失敗'}")
```

### バッチ配信使用

```python
# 購読者リスト
subscribers = ["user1@example.com", "user2@example.com", "user3@example.com"]

bulk_request = BulkDeliveryRequest(
    recipients=subscribers,
    channels=[DeliveryChannel.EMAIL],
    template_name="weekly_update",
    template_data={"week": "2024年第1週", "updates": updates_list},
    message_type=MessageType.NOTIFICATION,
    priority=MessagePriority.LOW,
    batch_size=10,
    delay_between_batches=5  # 5秒間隔
)

bulk_results = message_service.send_bulk_messages(bulk_request)
```

## エラーハンドリング

```python
try:
    results = message_service.send_message(request)

    for channel, result in results.items():
        if not result.success:
            logger.error(f"配信失敗 {channel}: {result.error_message}")

            # 自動リトライ対象外エラーの場合の処理
            if "invalid_recipient" in result.error_message:
                # 受信者情報の修正
                fix_recipient_info(result.message_id)

except Exception as e:
    logger.error(f"メッセージサービスエラー: {e}")
    # フォールバック通知
    send_fallback_notification(request)
```

## テスト観点

### ユニットテスト
- メッセージフォーマットの正確性
- チャネルプロバイダーの動作検証
- リトライロジックの動作確認
- テンプレートレンダリングの検証

### 統合テスト
- 実際の通知サービスとの連携
- エンドツーエンドの配信フロー
- エラーハンドリングの実動作
- パフォーマンス測定

### 負荷テスト
- 大量メッセージの一括配信
- 同時配信要求の処理
- チャネル障害時の動作

## 品質基準

### コード品質
- 循環的複雑度: 10以下
- テストカバレッジ: 85%以上
- 型ヒント: 100%実装

### 設計品質
- チャネル独立性の確保
- メッセージ形式の統一
- 配信追跡の完全性

### 運用品質
- 配信信頼性の保証
- エラー処理の適切性
- 監視・アラートの完備
