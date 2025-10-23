#!/usr/bin/env python3
"""プレゼンテーション層共有コンポーネント

Typer CLI削除後の共有ユーティリティモジュール配置。
MCPサーバー専用アーキテクチャに対応した構造に再編成。
"""

from .shared_utilities import (
    CommonPathService,
    console,
    get_app_state,
    get_common_path_service,
    get_logger,
    # get_project_handler,  # Typer CLI削除により無効化
    # get_quality_handler,  # Typer CLI削除により無効化
    handle_command_error,
    show_success_summary,
)

__all__ = [
    "CommonPathService",
    "console",
    "get_app_state",
    "get_common_path_service",
    "get_logger",
    # "get_project_handler",  # Typer CLI削除により無効化
    # "get_quality_handler",  # Typer CLI削除により無効化
    "handle_command_error",
    "show_success_summary",
]
