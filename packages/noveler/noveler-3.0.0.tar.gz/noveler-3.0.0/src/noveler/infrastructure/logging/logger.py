#!/usr/bin/env python3
"""レガシー互換ログAPI（統一ロガー委譲版）

過去の `setup_logger` をはじめとするAPIを維持しつつ、
実体は `noveler.infrastructure.logging.unified_logger` に完全委譲します。
MCP/Claude Code環境におけるSTDIO安全性（stdout汚染の防止）も
統一ロガー側のポリシーに一本化します。
"""

from __future__ import annotations
from typing import Any
from pathlib import Path

from noveler.infrastructure.logging.unified_logger import get_logger as _get_unified_logger


def setup_logger(
    name: str,
    log_dir: Path | None = None,  # 互換維持（未使用）
    max_bytes: int = 10 * 1024 * 1024,  # 互換維持（未使用）
    backup_count: int = 5,  # 互換維持（未使用）
) -> Any:
    """レガシー互換のロガー取得（統一ロガー委譲）

    既存コードはそのまま、実体は統一ロガーに委譲します。
    個別ファイル出力などのレガシー機能は廃止し、
    ファイル出力は統一ログ（logs/novel_system.log）へ集約します。
    """
    return _get_unified_logger(name)


def log_step(logger: Any, step_name: str, message: str | None = None) -> None:
    """ステップ実行のログを記録する便利関数

    Args:
        logger: ロガーインスタンス
        step_name: ステップ名
        message: 追加メッセージ(オプション)
    """
    log_message = f"[STEP] {step_name}"
    if message:
        log_message += f" - {message}"
    logger.info(log_message)


def log_error(logger: Any, step_name: str, error: Exception) -> None:
    """エラーログを記録する便利関数

    Args:
        logger: ロガーインスタンス
        step_name: エラーが発生したステップ名
        error: 例外オブジェクト
    """
    logger.error("[ERROR] %s - %s: %s", step_name, type(error).__name__, str(error))


def log_result(logger: Any, step_name: str, result: object) -> None:
    """処理結果のログを記録する便利関数

    Args:
        logger: ロガーインスタンス
        step_name: ステップ名
        result: 処理結果
    """
    logger.info("[RESULT] %s - %s", step_name, result)
