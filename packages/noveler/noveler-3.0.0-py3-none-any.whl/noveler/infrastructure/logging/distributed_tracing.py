# File: src/noveler/infrastructure/logging/distributed_tracing.py
# Purpose: Distributed tracing support for tracking requests across services
# Context: Phase 3 implementation for end-to-end request tracing

"""分散トレーシングサポート

リクエストを複数のサービス/コンポーネント間で追跡し、
エンドツーエンドのパフォーマンス分析を可能にする。
"""

import json
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from noveler.infrastructure.logging.structured_logger import get_structured_logger

# トレースコンテキスト（スレッド/非同期タスク間で共有）
trace_context: ContextVar[Optional['TraceContext']] = ContextVar('trace_context', default=None)


@dataclass
class Span:
    """トレーシングスパン

    分散トレーシングの基本単位。
    一つの操作や処理を表現する。
    """
    span_id: str
    parent_id: Optional[str]
    trace_id: str
    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "in_progress"  # in_progress, success, error
    error_message: Optional[str] = None

    def finish(self, status: str = "success", error: Optional[Exception] = None) -> None:
        """スパンを終了

        Args:
            status: 終了ステータス
            error: エラー情報（あれば）
        """
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status

        if error:
            self.status = "error"
            self.error_message = str(error)
            self.tags["error.type"] = type(error).__name__
            self.tags["error.message"] = str(error)

    def add_tag(self, key: str, value: Any) -> None:
        """タグを追加

        Args:
            key: タグのキー
            value: タグの値
        """
        self.tags[key] = value

    def add_log(self, message: str, **fields: Any) -> None:
        """ログエントリを追加

        Args:
            message: ログメッセージ
            **fields: 追加フィールド
        """
        log_entry = {
            "timestamp": time.time(),
            "message": message,
            **fields
        }
        self.logs.append(log_entry)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "trace_id": self.trace_id,
            "operation": self.operation,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "tags": self.tags,
            "logs": self.logs,
            "status": self.status,
            "error_message": self.error_message
        }


@dataclass
class TraceContext:
    """トレースコンテキスト

    現在のトレーシング情報を保持し、
    スパン間の親子関係を管理する。
    """
    trace_id: str
    spans: List[Span] = field(default_factory=list)
    current_span: Optional[Span] = None
    baggage: Dict[str, Any] = field(default_factory=dict)

    def create_span(self, operation: str, **tags: Any) -> Span:
        """新しいスパンを作成

        Args:
            operation: 操作名
            **tags: スパンタグ

        Returns:
            作成されたスパン
        """
        span_id = str(uuid.uuid4())[:8]
        parent_id = self.current_span.span_id if self.current_span else None

        span = Span(
            span_id=span_id,
            parent_id=parent_id,
            trace_id=self.trace_id,
            operation=operation,
            start_time=time.time(),
            tags=tags
        )

        self.spans.append(span)
        return span


class DistributedTracer:
    """分散トレーサー

    分散トレーシング機能を提供し、
    リクエストの追跡と分析を可能にする。
    """

    def __init__(self, service_name: str = "noveler"):
        """初期化

        Args:
            service_name: サービス名
        """
        self.service_name = service_name
        self.logger = get_structured_logger(__name__)
        self.traces: Dict[str, TraceContext] = {}

    def start_trace(
        self,
        operation: str,
        trace_id: Optional[str] = None,
        **tags: Any
    ) -> TraceContext:
        """トレースを開始

        Args:
            operation: 操作名
            trace_id: トレースID（省略時は自動生成）
            **tags: トレースタグ

        Returns:
            トレースコンテキスト
        """
        if not trace_id:
            trace_id = str(uuid.uuid4())

        context = TraceContext(trace_id=trace_id)
        span = context.create_span(operation, service=self.service_name, **tags)
        context.current_span = span

        self.traces[trace_id] = context
        trace_context.set(context)

        self.logger.info(
            f"トレース開始: {operation}",
            extra_data={
                "trace_id": trace_id,
                "span_id": span.span_id,
                "operation": operation,
                "tags": tags
            }
        )

        return context

    def start_span(self, operation: str, **tags: Any) -> Span:
        """スパンを開始

        Args:
            operation: 操作名
            **tags: スパンタグ

        Returns:
            作成されたスパン
        """
        context = trace_context.get()
        if not context:
            # トレースコンテキストがない場合は新規作成
            context = self.start_trace(operation, **tags)
            return context.current_span

        span = context.create_span(operation, service=self.service_name, **tags)

        self.logger.debug(
            f"スパン開始: {operation}",
            extra_data={
                "trace_id": context.trace_id,
                "span_id": span.span_id,
                "parent_id": span.parent_id,
                "operation": operation
            }
        )

        return span

    def finish_span(self, span: Span, status: str = "success", error: Optional[Exception] = None) -> None:
        """スパンを終了

        Args:
            span: 終了するスパン
            status: 終了ステータス
            error: エラー情報（あれば）
        """
        span.finish(status, error)

        log_level = "error" if status == "error" else "info"
        log_method = getattr(self.logger, log_level)

        log_method(
            f"スパン終了: {span.operation}",
            extra_data={
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "parent_id": span.parent_id,
                "operation": span.operation,
                "duration_ms": span.duration_ms,
                "status": status,
                "error_message": span.error_message
            }
        )

    def get_trace(self, trace_id: str) -> Optional[TraceContext]:
        """トレース情報を取得

        Args:
            trace_id: トレースID

        Returns:
            トレースコンテキスト（存在しない場合はNone）
        """
        return self.traces.get(trace_id)

    def inject_context(self, headers: Dict[str, str]) -> Dict[str, str]:
        """コンテキストをHTTPヘッダに注入

        Args:
            headers: HTTPヘッダ辞書

        Returns:
            コンテキストが注入されたヘッダ
        """
        context = trace_context.get()
        if context and context.current_span:
            headers["X-Trace-Id"] = context.trace_id
            headers["X-Span-Id"] = context.current_span.span_id
            headers["X-Parent-Span-Id"] = context.current_span.parent_id or ""

            # バゲージ情報も伝搬
            if context.baggage:
                headers["X-Trace-Baggage"] = json.dumps(context.baggage)

        return headers

    def extract_context(self, headers: Dict[str, str]) -> Optional[TraceContext]:
        """HTTPヘッダからコンテキストを抽出

        Args:
            headers: HTTPヘッダ辞書

        Returns:
            抽出されたトレースコンテキスト
        """
        trace_id = headers.get("X-Trace-Id")
        if not trace_id:
            return None

        parent_span_id = headers.get("X-Span-Id")

        # バゲージ情報の復元
        baggage = {}
        baggage_header = headers.get("X-Trace-Baggage")
        if baggage_header:
            try:
                baggage = json.loads(baggage_header)
            except json.JSONDecodeError:
                pass

        # 新しいコンテキストを作成（親スパンIDを保持）
        context = TraceContext(trace_id=trace_id, baggage=baggage)

        # 仮の親スパンを作成（参照用）
        if parent_span_id:
            parent_span = Span(
                span_id=parent_span_id,
                parent_id=None,
                trace_id=trace_id,
                operation="external",
                start_time=0
            )
            context.current_span = parent_span

        trace_context.set(context)
        return context

    def create_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """トレースサマリーを作成

        Args:
            trace_id: トレースID

        Returns:
            トレースサマリー辞書
        """
        context = self.traces.get(trace_id)
        if not context:
            return {"error": "Trace not found"}

        # スパンを親子関係でグループ化
        span_tree = self._build_span_tree(context.spans)

        # 統計を計算
        total_duration = 0
        error_count = 0
        span_count = len(context.spans)

        for span in context.spans:
            if span.duration_ms:
                total_duration += span.duration_ms
            if span.status == "error":
                error_count += 1

        # クリティカルパスを特定
        critical_path = self._find_critical_path(context.spans)

        return {
            "trace_id": trace_id,
            "span_count": span_count,
            "total_duration_ms": total_duration,
            "error_count": error_count,
            "spans": [span.to_dict() for span in context.spans],
            "span_tree": span_tree,
            "critical_path": critical_path,
            "baggage": context.baggage
        }

    def _build_span_tree(self, spans: List[Span]) -> Dict[str, Any]:
        """スパンツリーを構築

        Args:
            spans: スパンリスト

        Returns:
            スパンツリー
        """
        # スパンIDでインデックス化
        span_map = {span.span_id: span for span in spans}

        # ルートスパンを特定
        roots = [span for span in spans if span.parent_id is None]

        def build_node(span: Span) -> Dict[str, Any]:
            children = [
                build_node(child)
                for child in spans
                if child.parent_id == span.span_id
            ]

            node = {
                "span_id": span.span_id,
                "operation": span.operation,
                "duration_ms": span.duration_ms,
                "status": span.status
            }

            if children:
                node["children"] = children

            return node

        return {
            "roots": [build_node(root) for root in roots]
        }

    def _find_critical_path(self, spans: List[Span]) -> List[str]:
        """クリティカルパスを特定

        Args:
            spans: スパンリスト

        Returns:
            クリティカルパス上のスパンIDリスト
        """
        if not spans:
            return []

        # 最も時間のかかったルートからリーフまでのパスを見つける
        span_map = {span.span_id: span for span in spans}

        def find_longest_path(span_id: str, visited: set) -> Tuple[float, List[str]]:
            if span_id in visited:
                return 0, []

            visited.add(span_id)
            span = span_map.get(span_id)
            if not span:
                return 0, []

            # 子スパンの最長パスを再帰的に探索
            child_spans = [s for s in spans if s.parent_id == span_id]

            if not child_spans:
                return span.duration_ms or 0, [span_id]

            max_duration = 0
            max_path = []

            for child in child_spans:
                duration, path = find_longest_path(child.span_id, visited.copy())
                if duration > max_duration:
                    max_duration = duration
                    max_path = path

            total_duration = (span.duration_ms or 0) + max_duration
            return total_duration, [span_id] + max_path

        # 各ルートスパンから最長パスを探索
        root_spans = [s for s in spans if s.parent_id is None]
        longest_duration = 0
        critical_path = []

        for root in root_spans:
            duration, path = find_longest_path(root.span_id, set())
            if duration > longest_duration:
                longest_duration = duration
                critical_path = path

        return critical_path


# グローバルトレーサーインスタンス
global_tracer = DistributedTracer()


class traced:
    """トレーシングデコレータ

    関数やメソッドに分散トレーシングを追加する。
    """

    def __init__(self, operation: Optional[str] = None, **tags: Any):
        """初期化

        Args:
            operation: 操作名（省略時は関数名）
            **tags: スパンタグ
        """
        self.operation = operation
        self.tags = tags

    def __call__(self, func):
        """デコレート実行"""
        import asyncio
        import functools

        operation = self.operation or func.__name__

        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                span = global_tracer.start_span(operation, **self.tags)
                try:
                    result = await func(*args, **kwargs)
                    global_tracer.finish_span(span, status="success")
                    return result
                except Exception as e:
                    global_tracer.finish_span(span, status="error", error=e)
                    raise

            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                span = global_tracer.start_span(operation, **self.tags)
                try:
                    result = func(*args, **kwargs)
                    global_tracer.finish_span(span, status="success")
                    return result
                except Exception as e:
                    global_tracer.finish_span(span, status="error", error=e)
                    raise

            return sync_wrapper