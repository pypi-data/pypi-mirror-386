#!/usr/bin/env python3
# File: tests/unit/infrastructure/logging/test_structured_logger.py
# Purpose: Unit tests for structured logging functionality
# Context: Verifies PII masking, request context, and structured output

"""構造化ログヘルパーのユニットテスト"""

import json
import logging
import time
import uuid
from unittest.mock import MagicMock, patch

import pytest

from noveler.infrastructure.logging.structured_logger import (
    ErrorCategory,
    LogAggregator,
    RequestContext,
    StructuredLogger,
    get_structured_logger,
)


class TestRequestContext:
    """RequestContextのテスト"""

    def test_context_creation(self):
        """コンテキスト作成のテスト"""
        context = RequestContext(
            session_id="session123",
            user_id="user456",
            episode_number=1,
            operation="test_operation"
        )

        context_dict = context.to_dict()

        assert context_dict["session_id"] == "session123"
        assert context_dict["user_id"] == "user456"
        assert context_dict["episode_number"] == 1
        assert context_dict["operation"] == "test_operation"
        assert "request_id" in context_dict
        assert "elapsed_ms" in context_dict

    def test_auto_request_id_generation(self):
        """request_idの自動生成テスト"""
        context1 = RequestContext()
        context2 = RequestContext()

        # 各コンテキストで異なるrequest_idが生成される
        assert context1.request_id != context2.request_id
        # UUID形式であることを確認
        uuid.UUID(context1.request_id)  # 不正な形式ならエラーになる

    def test_context_manager(self):
        """コンテキストマネージャーとしての動作テスト"""
        # 初期状態ではコンテキストなし
        assert RequestContext.get_current() is None

        # withブロック内でコンテキストが設定される
        with RequestContext(operation="test") as ctx:
            current = RequestContext.get_current()
            assert current is not None
            assert current.operation == "test"
            assert current is ctx

        # withブロックを抜けるとコンテキストがリセットされる
        assert RequestContext.get_current() is None

    def test_nested_context(self):
        """ネストしたコンテキストのテスト"""
        with RequestContext(operation="outer") as outer:
            assert RequestContext.get_current().operation == "outer"

            with RequestContext(operation="inner") as inner:
                assert RequestContext.get_current().operation == "inner"

            # 内側を抜けると外側のコンテキストに戻る
            assert RequestContext.get_current().operation == "outer"


class TestStructuredLogger:
    """StructuredLoggerのテスト"""

    @patch('noveler.infrastructure.logging.structured_logger.get_logger')
    def test_pii_masking(self, mock_get_logger):
        """PII（個人情報）マスキングのテスト"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = StructuredLogger("test")

        # PII情報を含むデータ
        sensitive_data = {
            "email": "user@example.com",
            "phone": "123-456-7890",
            "ip": "192.168.1.1",
            "card": "1234 5678 9012 3456",
            "safe_data": "これは安全なデータ"
        }

        masked = logger._mask_pii(sensitive_data)

        assert masked["email"] == "[EMAIL]"
        assert masked["phone"] == "[PHONE]"
        assert masked["ip"] == "[IP]"
        assert masked["card"] == "[CARD]"
        assert masked["safe_data"] == "これは安全なデータ"

    @patch('noveler.infrastructure.logging.structured_logger.get_logger')
    def test_log_with_context(self, mock_get_logger):
        """リクエストコンテキスト付きログのテスト"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = StructuredLogger("test")

        with RequestContext(operation="test_op", episode_number=1):
            logger.info("テストメッセージ", custom_field="value")

            # ログが呼び出されたことを確認
            mock_logger.info.assert_called_once()

            # extra構造を確認
            call_args = mock_logger.info.call_args
            extra = call_args.kwargs.get("extra", {})
            extra_data = extra.get("extra_data", {})

            assert extra_data["operation"] == "test_op"
            assert extra_data["episode_number"] == 1
            assert extra_data["custom_field"] == "value"
            assert "request_id" in extra_data
            assert "timestamp" in extra_data

    @patch('noveler.infrastructure.logging.structured_logger.get_logger')
    def test_error_logging_with_category(self, mock_get_logger):
        """エラーカテゴリ付きエラーログのテスト"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = StructuredLogger("test")

        error = ValueError("テストエラー")
        logger.error(
            "エラーが発生しました",
            error=error,
            category=ErrorCategory.VALIDATION,
            user_input="invalid_data"
        )

        mock_logger.error.assert_called_once()

        call_args = mock_logger.error.call_args
        extra = call_args.kwargs.get("extra", {})
        extra_data = extra.get("extra_data", {})

        assert extra_data["error_type"] == "ValueError"
        assert extra_data["error_message"] == "テストエラー"
        assert extra_data["error_category"] == "validation"
        assert extra_data["user_input"] == "invalid_data"
        assert call_args.kwargs.get("exc_info") is True

    @patch('noveler.infrastructure.logging.structured_logger.get_logger')
    def test_performance_logging(self, mock_get_logger):
        """パフォーマンスログのテスト"""
        mock_logger = MagicMock()
        mock_logger.isEnabledFor.return_value = True
        mock_get_logger.return_value = mock_logger

        logger = StructuredLogger("test")

        logger.log_performance(
            operation="データ処理",
            elapsed_ms=150.5,
            success=True,
            records_processed=1000,
            memory_usage_mb=256
        )

        mock_logger.log.assert_called_once()

        call_args = mock_logger.log.call_args
        level = call_args.args[0]
        message = call_args.args[1]
        extra = call_args.kwargs.get("extra", {})
        extra_data = extra.get("extra_data", {})

        assert level == logging.INFO
        assert "完了" in message
        assert extra_data["operation"] == "データ処理"
        assert extra_data["elapsed_ms"] == 150.5
        assert extra_data["success"] is True
        assert extra_data["records_processed"] == 1000

    @patch('noveler.infrastructure.logging.structured_logger.get_logger')
    def test_llm_call_logging(self, mock_get_logger):
        """LLM呼び出しログのテスト"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = StructuredLogger("test")

        logger.log_llm_call(
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            total_cost=0.015,
            elapsed_ms=2500,
            success=True,
            temperature=0.7
        )

        mock_logger.log.assert_called_once()

        call_args = mock_logger.log.call_args
        extra = call_args.kwargs.get("extra", {})
        extra_data = extra.get("extra_data", {})

        assert extra_data["llm_model"] == "gpt-4"
        assert extra_data["prompt_tokens"] == 100
        assert extra_data["completion_tokens"] == 50
        assert extra_data["total_tokens"] == 150
        assert extra_data["total_cost_usd"] == 0.015
        assert extra_data["temperature"] == 0.7

    @patch('noveler.infrastructure.logging.structured_logger.get_logger')
    def test_debug_lazy_evaluation(self, mock_get_logger):
        """DEBUG レベルの遅延評価テスト"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = StructuredLogger("test")

        # DEBUG無効の場合
        mock_logger.isEnabledFor.return_value = False
        logger.debug("デバッグメッセージ", expensive_data="計算コストが高いデータ")

        # debugメソッドが呼ばれないことを確認
        mock_logger.debug.assert_not_called()

        # DEBUG有効の場合
        mock_logger.isEnabledFor.return_value = True
        logger.debug("デバッグメッセージ", expensive_data="計算コストが高いデータ")

        # debugメソッドが呼ばれることを確認
        mock_logger.debug.assert_called_once()


class TestLogAggregator:
    """LogAggregatorのテスト"""

    @patch('noveler.infrastructure.logging.structured_logger.get_logger')
    def test_event_aggregation(self, mock_get_logger):
        """イベント集約のテスト"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = StructuredLogger("test")
        aggregator = LogAggregator(logger)

        # イベントを追加
        aggregator.add_event("process_start", item_id=1)
        aggregator.add_event("process_complete", item_id=1, duration_ms=100)
        aggregator.add_event("process_start", item_id=2)
        aggregator.add_event("process_complete", item_id=2, duration_ms=150)

        # フラッシュ
        aggregator.flush("バッチ処理")

        # ログが出力されたことを確認
        mock_logger.info.assert_called_once()

        call_args = mock_logger.info.call_args
        message = call_args.args[0]

        # extra構造を確認
        extra = call_args.kwargs.get("extra", {})
        extra_data = extra.get("extra_data", {})

        assert "バッチ処理完了" in message
        assert extra_data["event_count"] == 4
        assert extra_data["event_summary"]["process_start"] == 2
        assert extra_data["event_summary"]["process_complete"] == 2

    @patch('noveler.infrastructure.logging.structured_logger.get_logger')
    def test_auto_flush_on_max_events(self, mock_get_logger):
        """最大イベント数での自動フラッシュテスト"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = StructuredLogger("test")
        aggregator = LogAggregator(logger, max_events=3)

        # 3つ目のイベントで自動フラッシュされる
        aggregator.add_event("event1")
        aggregator.add_event("event2")

        # まだフラッシュされない
        mock_logger.info.assert_not_called()

        aggregator.add_event("event3")

        # 自動フラッシュされる
        mock_logger.info.assert_called_once()

    @patch('noveler.infrastructure.logging.structured_logger.get_logger')
    def test_context_manager(self, mock_get_logger):
        """コンテキストマネージャーとしての動作テスト"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = StructuredLogger("test")

        with LogAggregator(logger) as aggregator:
            aggregator.add_event("event1")
            aggregator.add_event("event2")
            # withブロックを抜ける際に自動フラッシュ

        # フラッシュされたことを確認
        mock_logger.info.assert_called_once()


def test_get_structured_logger():
    """get_structured_logger関数のテスト"""
    logger1 = get_structured_logger("test1")
    logger2 = get_structured_logger("test2")

    assert isinstance(logger1, StructuredLogger)
    assert isinstance(logger2, StructuredLogger)
    assert logger1.name == "test1"
    assert logger2.name == "test2"