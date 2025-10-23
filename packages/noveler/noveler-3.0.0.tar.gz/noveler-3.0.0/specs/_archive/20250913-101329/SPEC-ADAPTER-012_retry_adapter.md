# リトライアダプター仕様書

## 概要
リトライアダプターは、システム内の様々な操作に対して統一的なリトライ機能を提供するアダプターです。ネットワーク通信、ファイルI/O、外部API呼び出し等の一時的な障害に対して、柔軟で設定可能なリトライメカニズムを実装します。

## クラス設計

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import asyncio
import functools

T = TypeVar('T')

class RetryStrategy(Enum):
    """リトライ戦略"""
    FIXED_INTERVAL = "fixed_interval"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIBONACCI_BACKOFF = "fibonacci_backoff"
    CUSTOM = "custom"

class StopCondition(Enum):
    """停止条件"""
    MAX_ATTEMPTS = "max_attempts"
    MAX_DURATION = "max_duration"
    SUCCESS = "success"
    CUSTOM_CONDITION = "custom_condition"

class RetryableError(Enum):
    """リトライ可能エラー"""
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    SERVICE_UNAVAILABLE = "service_unavailable"
    RATE_LIMITED = "rate_limited"
    TEMPORARY_FAILURE = "temporary_failure"

@dataclass
class RetryConfig:
    """リトライ設定"""
    strategy: RetryStrategy
    max_attempts: int
    max_duration: Optional[timedelta]
    base_delay: float
    max_delay: float
    backoff_multiplier: float
    jitter: bool
    retryable_exceptions: List[type]
    stop_conditions: List[StopCondition]
    custom_strategy: Optional[Callable[[int], float]] = None

@dataclass
class RetryAttempt:
    """リトライ試行"""
    attempt_number: int
    timestamp: datetime
    delay_before: float
    exception: Optional[Exception]
    duration: float
    success: bool

@dataclass
class RetryResult(Generic[T]):
    """リトライ結果"""
    success: bool
    result: Optional[T]
    attempts: List[RetryAttempt]
    total_duration: float
    final_exception: Optional[Exception]
    stop_reason: str

class IRetryableOperation(ABC, Generic[T]):
    """リトライ可能操作インターフェース"""

    @abstractmethod
    def execute(self) -> T:
        """操作を実行"""
        pass

    @abstractmethod
    def is_retryable_error(self, error: Exception) -> bool:
        """エラーがリトライ可能か判定"""
        pass

class RetryAdapter:
    """リトライアダプター"""

    def __init__(
        self,
        default_config: RetryConfig,
        error_classifier: IErrorClassifier,
        metrics_collector: IMetricsCollector,
        logger: IRetryLogger
    ):
        self._default_config = default_config
        self._error_classifier = error_classifier
        self._metrics_collector = metrics_collector
        self._logger = logger
```

## データ構造

### インターフェース定義

```python
class IErrorClassifier(ABC):
    """エラー分類インターフェース"""

    @abstractmethod
    def classify_error(self, error: Exception) -> RetryableError:
        """エラーを分類"""
        pass

    @abstractmethod
    def is_retryable(self, error: Exception) -> bool:
        """リトライ可能か判定"""
        pass

    @abstractmethod
    def get_recommended_delay(self, error: Exception, attempt: int) -> float:
        """推奨遅延時間を取得"""
        pass

class IMetricsCollector(ABC):
    """メトリクス収集インターフェース"""

    @abstractmethod
    def record_attempt(self, operation: str, attempt: RetryAttempt) -> None:
        """試行を記録"""
        pass

    @abstractmethod
    def record_result(self, operation: str, result: RetryResult) -> None:
        """結果を記録"""
        pass

    @abstractmethod
    def get_statistics(self, operation: str) -> Dict[str, Any]:
        """統計情報を取得"""
        pass

class IRetryLogger(ABC):
    """リトライログインターフェース"""

    @abstractmethod
    def log_attempt(
        self,
        operation: str,
        attempt: int,
        delay: float,
        error: Exception
    ) -> None:
        """試行をログ"""
        pass

    @abstractmethod
    def log_success(self, operation: str, attempts: int, duration: float) -> None:
        """成功をログ"""
        pass

    @abstractmethod
    def log_failure(
        self,
        operation: str,
        attempts: int,
        duration: float,
        final_error: Exception
    ) -> None:
        """失敗をログ"""
        pass

class IDelayCalculator(ABC):
    """遅延計算インターフェース"""

    @abstractmethod
    def calculate_delay(
        self,
        attempt: int,
        config: RetryConfig,
        error: Optional[Exception] = None
    ) -> float:
        """遅延時間を計算"""
        pass

    @abstractmethod
    def add_jitter(self, delay: float) -> float:
        """ジッターを追加"""
        pass
```

### アダプター実装

```python
@dataclass
class OperationContext:
    """操作コンテキスト"""
    operation_name: str
    operation_id: str
    config: RetryConfig
    metadata: Dict[str, Any]
    start_time: datetime

class DefaultErrorClassifier(IErrorClassifier):
    """デフォルトエラー分類器"""

    def __init__(self):
        self._error_mappings = {
            ConnectionError: RetryableError.NETWORK_ERROR,
            TimeoutError: RetryableError.TIMEOUT,
            ConnectionResetError: RetryableError.NETWORK_ERROR,
            BrokenPipeError: RetryableError.NETWORK_ERROR,
        }

    def classify_error(self, error: Exception) -> RetryableError:
        error_type = type(error)

        # 直接マッピング
        if error_type in self._error_mappings:
            return self._error_mappings[error_type]

        # エラーメッセージベースの分類
        error_message = str(error).lower()

        if any(keyword in error_message for keyword in ["timeout", "timed out"]):
            return RetryableError.TIMEOUT
        elif any(keyword in error_message for keyword in ["rate limit", "throttle"]):
            return RetryableError.RATE_LIMITED
        elif any(keyword in error_message for keyword in ["unavailable", "service"]):
            return RetryableError.SERVICE_UNAVAILABLE
        else:
            return RetryableError.TEMPORARY_FAILURE

    def is_retryable(self, error: Exception) -> bool:
        # 特定の例外タイプはリトライ不可
        non_retryable_types = {
            ValueError,
            TypeError,
            KeyError,
            AttributeError
        }

        return type(error) not in non_retryable_types

    def get_recommended_delay(self, error: Exception, attempt: int) -> float:
        error_type = self.classify_error(error)

        # エラータイプ別の推奨遅延
        delay_mappings = {
            RetryableError.NETWORK_ERROR: 2.0 ** attempt,
            RetryableError.TIMEOUT: 5.0 + attempt * 2,
            RetryableError.RATE_LIMITED: 60.0 + attempt * 30,
            RetryableError.SERVICE_UNAVAILABLE: 10.0 + attempt * 5,
            RetryableError.TEMPORARY_FAILURE: 1.0 + attempt
        }

        return delay_mappings.get(error_type, 1.0 + attempt)

class ExponentialBackoffCalculator(IDelayCalculator):
    """指数バックオフ遅延計算器"""

    def calculate_delay(
        self,
        attempt: int,
        config: RetryConfig,
        error: Optional[Exception] = None
    ) -> float:
        if config.strategy == RetryStrategy.FIXED_INTERVAL:
            delay = config.base_delay
        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_multiplier ** (attempt - 1))
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * attempt
        elif config.strategy == RetryStrategy.FIBONACCI_BACKOFF:
            delay = config.base_delay * self._fibonacci(attempt)
        elif config.strategy == RetryStrategy.CUSTOM and config.custom_strategy:
            delay = config.custom_strategy(attempt)
        else:
            delay = config.base_delay

        # 最大遅延制限
        delay = min(delay, config.max_delay)

        # ジッター適用
        if config.jitter:
            delay = self.add_jitter(delay)

        return delay

    def add_jitter(self, delay: float) -> float:
        import random
        # ±20%のランダムジッター
        jitter_range = delay * 0.2
        return delay + random.uniform(-jitter_range, jitter_range)

    def _fibonacci(self, n: int) -> int:
        if n <= 1:
            return 1
        a, b = 1, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
```

## パブリックメソッド

### RetryAdapter

```python
def retry(
    self,
    operation: IRetryableOperation[T],
    config: Optional[RetryConfig] = None,
    operation_name: Optional[str] = None
) -> RetryResult[T]:
    """
    操作をリトライ実行

    Args:
        operation: リトライ可能操作
        config: リトライ設定（Noneの場合デフォルト使用）
        operation_name: 操作名（ログ・メトリクス用）

    Returns:
        RetryResult[T]: リトライ結果
    """
    effective_config = config or self._default_config
    operation_name = operation_name or operation.__class__.__name__

    context = OperationContext(
        operation_name=operation_name,
        operation_id=self._generate_operation_id(),
        config=effective_config,
        metadata={},
        start_time=datetime.now()
    )

    attempts = []
    calculator = ExponentialBackoffCalculator()

    for attempt_num in range(1, effective_config.max_attempts + 1):
        attempt_start = datetime.now()

        try:
            # 操作実行
            result = operation.execute()

            # 成功記録
            attempt = RetryAttempt(
                attempt_number=attempt_num,
                timestamp=attempt_start,
                delay_before=0.0,
                exception=None,
                duration=(datetime.now() - attempt_start).total_seconds(),
                success=True
            )
            attempts.append(attempt)

            # メトリクス・ログ記録
            self._metrics_collector.record_attempt(operation_name, attempt)
            total_duration = (datetime.now() - context.start_time).total_seconds()
            self._logger.log_success(operation_name, attempt_num, total_duration)

            # 成功結果返却
            retry_result = RetryResult(
                success=True,
                result=result,
                attempts=attempts,
                total_duration=total_duration,
                final_exception=None,
                stop_reason="success"
            )

            self._metrics_collector.record_result(operation_name, retry_result)
            return retry_result

        except Exception as error:
            # 失敗記録
            attempt = RetryAttempt(
                attempt_number=attempt_num,
                timestamp=attempt_start,
                delay_before=0.0,
                exception=error,
                duration=(datetime.now() - attempt_start).total_seconds(),
                success=False
            )
            attempts.append(attempt)
            self._metrics_collector.record_attempt(operation_name, attempt)

            # リトライ可能性判定
            if not self._should_retry(error, attempt_num, effective_config, context):
                # 最終失敗
                total_duration = (datetime.now() - context.start_time).total_seconds()
                self._logger.log_failure(
                    operation_name,
                    attempt_num,
                    total_duration,
                    error
                )

                retry_result = RetryResult(
                    success=False,
                    result=None,
                    attempts=attempts,
                    total_duration=total_duration,
                    final_exception=error,
                    stop_reason=self._determine_stop_reason(error, attempt_num, effective_config)
                )

                self._metrics_collector.record_result(operation_name, retry_result)
                return retry_result

            # リトライ実行
            if attempt_num < effective_config.max_attempts:
                delay = calculator.calculate_delay(attempt_num, effective_config, error)

                self._logger.log_attempt(operation_name, attempt_num, delay, error)

                # 遅延実行
                time.sleep(delay)

                # 次の試行のために遅延を記録
                if attempts:
                    attempts[-1] = attempts[-1]._replace(delay_before=delay)

    # 最大試行数到達
    total_duration = (datetime.now() - context.start_time).total_seconds()
    final_error = attempts[-1].exception if attempts else None

    retry_result = RetryResult(
        success=False,
        result=None,
        attempts=attempts,
        total_duration=total_duration,
        final_exception=final_error,
        stop_reason="max_attempts_reached"
    )

    self._metrics_collector.record_result(operation_name, retry_result)
    return retry_result

def retry_with_decorator(
    self,
    config: Optional[RetryConfig] = None,
    operation_name: Optional[str] = None
) -> Callable:
    """
    デコレーター形式でリトライ機能を提供

    Args:
        config: リトライ設定
        operation_name: 操作名

    Returns:
        Callable: デコレーター関数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # 関数をリトライ可能操作に変換
            operation = FunctionOperation(func, args, kwargs)

            # リトライ実行
            result = self.retry(
                operation=operation,
                config=config,
                operation_name=operation_name or func.__name__
            )

            if result.success:
                return result.result
            else:
                raise result.final_exception

        return wrapper
    return decorator

async def async_retry(
    self,
    operation: Callable[[], T],
    config: Optional[RetryConfig] = None,
    operation_name: Optional[str] = None
) -> RetryResult[T]:
    """
    非同期操作のリトライ実行

    Args:
        operation: 非同期操作
        config: リトライ設定
        operation_name: 操作名

    Returns:
        RetryResult[T]: リトライ結果
    """
    effective_config = config or self._default_config
    operation_name = operation_name or "async_operation"

    attempts = []
    calculator = ExponentialBackoffCalculator()
    start_time = datetime.now()

    for attempt_num in range(1, effective_config.max_attempts + 1):
        attempt_start = datetime.now()

        try:
            # 非同期操作実行
            result = await operation()

            # 成功処理
            attempt = RetryAttempt(
                attempt_number=attempt_num,
                timestamp=attempt_start,
                delay_before=0.0,
                exception=None,
                duration=(datetime.now() - attempt_start).total_seconds(),
                success=True
            )
            attempts.append(attempt)

            total_duration = (datetime.now() - start_time).total_seconds()

            return RetryResult(
                success=True,
                result=result,
                attempts=attempts,
                total_duration=total_duration,
                final_exception=None,
                stop_reason="success"
            )

        except Exception as error:
            # 失敗処理
            attempt = RetryAttempt(
                attempt_number=attempt_num,
                timestamp=attempt_start,
                delay_before=0.0,
                exception=error,
                duration=(datetime.now() - attempt_start).total_seconds(),
                success=False
            )
            attempts.append(attempt)

            # リトライ判定
            if not self._error_classifier.is_retryable(error) or attempt_num >= effective_config.max_attempts:
                total_duration = (datetime.now() - start_time).total_seconds()

                return RetryResult(
                    success=False,
                    result=None,
                    attempts=attempts,
                    total_duration=total_duration,
                    final_exception=error,
                    stop_reason="max_attempts_reached" if attempt_num >= effective_config.max_attempts else "non_retryable_error"
                )

            # 非同期遅延
            if attempt_num < effective_config.max_attempts:
                delay = calculator.calculate_delay(attempt_num, effective_config, error)
                await asyncio.sleep(delay)

def create_config(
    self,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_multiplier: float = 2.0,
    **kwargs
) -> RetryConfig:
    """
    リトライ設定を作成

    Args:
        strategy: リトライ戦略
        max_attempts: 最大試行回数
        base_delay: 基本遅延時間
        max_delay: 最大遅延時間
        backoff_multiplier: バックオフ乗数
        **kwargs: その他の設定

    Returns:
        RetryConfig: リトライ設定
    """
    return RetryConfig(
        strategy=strategy,
        max_attempts=max_attempts,
        max_duration=kwargs.get('max_duration'),
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_multiplier=backoff_multiplier,
        jitter=kwargs.get('jitter', True),
        retryable_exceptions=kwargs.get('retryable_exceptions', []),
        stop_conditions=kwargs.get('stop_conditions', [StopCondition.MAX_ATTEMPTS]),
        custom_strategy=kwargs.get('custom_strategy')
    )
```

## プライベートメソッド

```python
def _should_retry(
    self,
    error: Exception,
    attempt_num: int,
    config: RetryConfig,
    context: OperationContext
) -> bool:
    """リトライすべきか判定"""
    # 最大試行回数チェック
    if attempt_num >= config.max_attempts:
        return False

    # 最大実行時間チェック
    if config.max_duration:
        elapsed = datetime.now() - context.start_time
        if elapsed >= config.max_duration:
            return False

    # エラーのリトライ可能性チェック
    if not self._error_classifier.is_retryable(error):
        return False

    # 設定された例外タイプチェック
    if config.retryable_exceptions:
        if not any(isinstance(error, exc_type) for exc_type in config.retryable_exceptions):
            return False

    return True

def _determine_stop_reason(
    self,
    error: Exception,
    attempt_num: int,
    config: RetryConfig
) -> str:
    """停止理由を決定"""
    if attempt_num >= config.max_attempts:
        return "max_attempts_reached"
    elif not self._error_classifier.is_retryable(error):
        return "non_retryable_error"
    elif config.max_duration:
        return "max_duration_exceeded"
    else:
        return "unknown"

def _generate_operation_id(self) -> str:
    """操作IDを生成"""
    import uuid
    return f"op_{uuid.uuid4().hex[:8]}"

class FunctionOperation(IRetryableOperation[T]):
    """関数操作ラッパー"""

    def __init__(self, func: Callable[..., T], args: tuple, kwargs: dict):
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def execute(self) -> T:
        return self._func(*self._args, **self._kwargs)

    def is_retryable_error(self, error: Exception) -> bool:
        # デフォルト分類器に委譲
        return True  # 分類器で判定
```

## アダプターパターン実装

### 具体的リトライ操作

```python
class NetworkOperation(IRetryableOperation[Dict[str, Any]]):
    """ネットワーク操作"""

    def __init__(self, url: str, method: str = "GET", **kwargs):
        self._url = url
        self._method = method
        self._kwargs = kwargs

    def execute(self) -> Dict[str, Any]:
        import requests

        response = requests.request(
            method=self._method,
            url=self._url,
            timeout=30,
            **self._kwargs
        )
        response.raise_for_status()

        return response.json()

    def is_retryable_error(self, error: Exception) -> bool:
        retryable_types = {
            requests.ConnectionError,
            requests.Timeout,
            requests.HTTPError
        }

        if isinstance(error, requests.HTTPError):
            # 5xxエラーのみリトライ可能
            return 500 <= error.response.status_code < 600

        return type(error) in retryable_types

class FileOperation(IRetryableOperation[str]):
    """ファイル操作"""

    def __init__(self, file_path: str, operation: str, content: str = None):
        self._file_path = file_path
        self._operation = operation
        self._content = content

    def execute(self) -> str:
        if self._operation == "read":
            with open(self._file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif self._operation == "write":
            with open(self._file_path, 'w', encoding='utf-8') as f:
                f.write(self._content)
                return f"Wrote {len(self._content)} characters"
        else:
            raise ValueError(f"Unknown operation: {self._operation}")

    def is_retryable_error(self, error: Exception) -> bool:
        retryable_types = {
            OSError,
            IOError,
            PermissionError  # 一時的な権限問題
        }

        return type(error) in retryable_types

class DatabaseOperation(IRetryableOperation[List[Dict[str, Any]]]):
    """データベース操作"""

    def __init__(self, connection, query: str, params: Optional[tuple] = None):
        self._connection = connection
        self._query = query
        self._params = params or ()

    def execute(self) -> List[Dict[str, Any]]:
        cursor = self._connection.cursor()

        try:
            cursor.execute(self._query, self._params)

            if self._query.strip().upper().startswith('SELECT'):
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            else:
                self._connection.commit()
                return [{"affected_rows": cursor.rowcount}]

        except Exception:
            self._connection.rollback()
            raise
        finally:
            cursor.close()

    def is_retryable_error(self, error: Exception) -> bool:
        # データベース固有のリトライ可能エラー
        retryable_messages = [
            "connection lost",
            "deadlock detected",
            "timeout",
            "temporary failure"
        ]

        error_message = str(error).lower()
        return any(msg in error_message for msg in retryable_messages)
```

## 依存関係

```python
from domain.services import ErrorHandlingService
from infrastructure.services import (
    NetworkService,
    FileSystemService,
    DatabaseService,
    LoggingService
)
from application.use_cases import RetryableUseCase
```

## 設計原則遵守

### アダプターパターン
- **統一インターフェース**: 様々な操作に対する統一的なリトライ機能
- **戦略パターン**: 複数のリトライ戦略を選択可能
- **テンプレートメソッド**: 共通のリトライフローを提供

### 責任の分離
- **エラー分類**: エラー分類器が担当
- **遅延計算**: 遅延計算器が担当
- **メトリクス収集**: メトリクス収集器が担当
- **ログ記録**: リトライログが担当

## 使用例

### 基本的な使用

```python
# リトライアダプター設定
retry_config = RetryConfig(
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    max_attempts=5,
    base_delay=1.0,
    max_delay=30.0,
    backoff_multiplier=2.0,
    jitter=True,
    retryable_exceptions=[ConnectionError, TimeoutError],
    stop_conditions=[StopCondition.MAX_ATTEMPTS]
)

retry_adapter = RetryAdapter(
    default_config=retry_config,
    error_classifier=DefaultErrorClassifier(),
    metrics_collector=PrometheusMetricsCollector(),
    logger=StructuredRetryLogger()
)

# ネットワーク操作のリトライ
network_op = NetworkOperation(
    url="https://api.example.com/data",
    method="GET"
)

result = retry_adapter.retry(
    operation=network_op,
    operation_name="fetch_api_data"
)

if result.success:
    print(f"成功: {result.result}")
else:
    print(f"失敗: {result.final_exception}")
```

### デコレーター使用

```python
# 関数デコレーター
@retry_adapter.retry_with_decorator(
    config=RetryConfig(
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        max_attempts=3,
        base_delay=2.0
    ),
    operation_name="process_file"
)
def process_file(file_path: str) -> str:
    # ファイル処理ロジック
    with open(file_path, 'r') as f:
        content = f.read()

    # 何らかの処理
    processed = content.upper()

    return processed

# 使用
try:
    result = process_file("/path/to/file.txt")
    print(f"処理結果: {result}")
except Exception as e:
    print(f"最終的な失敗: {e}")
```

### 非同期操作使用

```python
async def fetch_data_async(url: str) -> dict:
    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()

# 非同期リトライ
async def main():
    result = await retry_adapter.async_retry(
        operation=lambda: fetch_data_async("https://api.example.com/data"),
        config=retry_config,
        operation_name="async_api_fetch"
    )

    if result.success:
        print(f"データ取得成功: {result.result}")
```

## エラーハンドリング

```python
try:
    result = retry_adapter.retry(operation, config)

    if not result.success:
        # リトライ失敗の詳細分析
        print(f"停止理由: {result.stop_reason}")
        print(f"試行回数: {len(result.attempts)}")
        print(f"総実行時間: {result.total_duration}秒")

        # 最後のエラーを処理
        if result.final_exception:
            error_type = retry_adapter._error_classifier.classify_error(
                result.final_exception
            )
            print(f"エラータイプ: {error_type}")

        # 各試行の分析
        for attempt in result.attempts:
            if not attempt.success:
                print(f"試行{attempt.attempt_number}: {attempt.exception}")

except Exception as e:
    print(f"リトライアダプター自体のエラー: {e}")
```

## テスト観点

### ユニットテスト
- リトライ戦略の動作検証
- エラー分類の正確性
- 遅延計算の精度
- 停止条件の判定

### 統合テスト
- 実際の外部サービスとの連携
- 各種操作タイプでのリトライ
- 非同期操作のリトライ
- メトリクス収集の動作

### 負荷テスト
- 高頻度リトライ処理
- 複数操作の並行リトライ
- リソース使用量の測定

## 品質基準

### コード品質
- 循環的複雑度: 8以下
- テストカバレッジ: 90%以上
- 型ヒント: 100%実装

### 設計品質
- 戦略パターンの適用
- インターフェース分離の徹底
- 設定可能性の確保

### 運用品質
- リトライ処理の信頼性
- メトリクス収集の完全性
- ログ記録の適切性
