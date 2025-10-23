#!/usr/bin/env python3
"""Adapter that implements retry logic with exponential backoff for infrastructure services."""

import functools
import random
import time
from collections.abc import Callable
from datetime import timedelta
from typing import Any

import requests

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)


# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class RetryExhaustedError(Exception):
    """Raised when retry attempts are exhausted."""


class CircuitBreakerOpenError(Exception):
    """Raised when the circuit breaker is open."""


class RetryConfig:
    """Configuration for retry behaviour."""

    def __init__(
        self,
        max_retries: int,
        initial_delay: float,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        exceptions: tuple[type[Exception], ...] | None = None,
    ) -> None:
        """Initialize retry configuration settings.

        Args:
            max_retries: Maximum number of retry attempts.
            initial_delay: Initial delay before the first retry in seconds.
            max_delay: Maximum delay ceiling in seconds.
            exponential_base: Base for exponential backoff.
            jitter: Whether to add jitter to the delay.
            exceptions: Tuple of exceptions that trigger retries.
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.exceptions = exceptions or (Exception,)

    def calculate_delay(self, attempt: int) -> float:
        """Calculate the delay for a given retry attempt."""
        # エクスポネンシャルバックオフ計算
        delay = self.initial_delay * (self.exponential_base**attempt)

        # 最大遅延時間でキャップ
        delay = min(delay, self.max_delay)

        # ジッターを追加(0.5〜1.5倍のランダムな係数)
        if self.jitter:
            delay *= 0.5 + random.random()

        return delay


def retry_with_backoff(config: RetryConfig | None, on_retry: Callable[[int, Exception], None] | None) -> Callable:
    """Decorator that applies exponential backoff retry behaviour."""
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> object:
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    # 関数実行
                    return func(*args, **kwargs)

                except config.exceptions as e:
                    last_exception = e

                    # 最後の試行の場合はリトライしない
                    if attempt >= config.max_retries:
                        break

                    # 待機時間を計算
                    delay = config.calculate_delay(attempt)

                    # リトライコールバック
                    if on_retry:
                        on_retry(attempt + 1, e)

                    # ログ出力
                    logger.warning(
                        f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                        f"after {delay}s due to {type(e).__name__}: {e!s}"
                    )

                    # 待機
                    time.sleep(delay)

            # すべてのリトライが失敗した場合
            msg = f"Failed after {config.max_retries} retries: {last_exception}"
            raise RetryExhaustedError(
                msg,
            ) from last_exception

        return wrapper

    return decorator


class APIRetryHandler:
    """Retry handler tailored for HTTP API interactions."""

    def __init__(self, config: RetryConfig | None) -> None:
        """Initialize the handler with retry settings."""
        if config is None:
            # API用のデフォルト設定
            config = RetryConfig(
                max_retries=3,
                initial_delay=1.0,
                max_delay=30.0,
                exceptions=(
                    requests.exceptions.RequestException,
                    requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.HTTPError,
                ),
            )

        self.config = config
        self.session = requests.Session()

    def request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """Issue an HTTP request with retry behaviour applied."""

        @retry_with_backoff(
            config=self.config,
            on_retry=self._on_retry_callback,
        )
        def _make_request() -> None:
            response = self.session.request(method, url, **kwargs)

            # HTTPステータスコードによるリトライ判定
            if response.status_code in [429, 500, 502, 503, 504]:
                # レート制限や一時的なサーバーエラー
                if response.status_code == 429:
                    # Retry-Afterヘッダーを確認
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait_time = int(retry_after)
                            self.logger_service.info("Rate limited. Waiting %ss as requested by server", wait_time)
                            time.sleep(wait_time)
                        except ValueError:
                            pass

                response.raise_for_status()

            return response

        return _make_request()

    def _on_retry_callback(self, exception: Exception, attempt: int) -> None:
        """Callback invoked whenever a retry attempt occurs."""
        if isinstance(exception, requests.exceptions.HTTPError):
            response = exception.response
            if response is not None:
                self.logger_service.warning(
                    f"HTTP {response.status_code} error on attempt {attempt}: {response.text[:200]}",
                )

    def get(self, url: str, **kwargs) -> requests.Response:
        """Perform a GET request with retry behaviour."""
        return self.request_with_retry("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """Perform a POST request with retry behaviour."""
        return self.request_with_retry("POST", url, **kwargs)


class CircuitBreaker:
    """Circuit breaker implementation for guarding failing operations."""

    def __init__(
        self, failure_threshold: int, recovery_timeout: float, expected_exception: type[Exception] = Exception
    ) -> None:
        """Initialize the circuit breaker settings.

        Args:
            failure_threshold: Consecutive failures required to open the circuit.
            recovery_timeout: Time in seconds before attempting to close the circuit.
            expected_exception: Exception types that contribute to failure counts.
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self._failure_count = 0
        self._last_failure_time = None
        self._state = "closed"  # closed, open, half_open

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if self._state == "open":
                # オープン状態の場合、回復時間をチェック
                if self._last_failure_time and project_now().datetime - self._last_failure_time > timedelta(
                    seconds=self.recovery_timeout,
                ):
                    self._state = "half_open"
                    self.logger_service.info("Circuit breaker for %s entering half-open state", func.__name__)
                else:
                    msg = f"Circuit breaker is OPEN for {func.__name__}"
                    raise CircuitBreakerOpenError(msg)

            try:
                result = func(*args, **kwargs)

                # 成功した場合
                if self._state == "half_open":
                    self._state = "closed"
                    self._failure_count = 0
                    self.logger_service.info("Circuit breaker for %s is now CLOSED", func.__name__)

                return result

            except self.expected_exception:
                self._failure_count += 1
                self._last_failure_time = project_now().datetime

                if self._failure_count >= self.failure_threshold:
                    self._state = "open"
                    logger.exception(
                        f"Circuit breaker for {func.__name__} is now OPEN after {self._failure_count} failures",
                    )

                raise

        return wrapper


# 便利な事前定義設定
SLOW_API_CONFIG = RetryConfig(
    max_retries=5,
    initial_delay=2.0,
    max_delay=120.0,
)


FAST_API_CONFIG = RetryConfig(
    max_retries=3,
    initial_delay=0.5,
    max_delay=10.0,
)


CRITICAL_API_CONFIG = RetryConfig(
    max_retries=10,
    initial_delay=1.0,
    max_delay=300.0,
)


def create_retry_session(config: RetryConfig | None) -> APIRetryHandler:
    """Create an API retry handler configured with the provided settings."""
    return APIRetryHandler(config)
