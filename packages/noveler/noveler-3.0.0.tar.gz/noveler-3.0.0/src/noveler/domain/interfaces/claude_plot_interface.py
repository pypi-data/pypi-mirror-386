#!/usr/bin/env python3
"""Claude Plot インターフェース

DDD準拠: Domain層の抽象インターフェース
Claude Codeとのプロット生成連携の抽象化
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class PlotGenerationRequest:
    """プロット生成リクエスト"""

    episode_number: int
    chapter_number: int | None = None
    context: dict[str, Any] | None = None
    quality_settings: dict[str, Any] | None = None
    regenerate: bool = False


@dataclass
class ClaudeResponse:
    """Claude レスポンス"""

    success: bool
    content: str
    metadata: dict[str, Any] | None = None
    error_message: str | None = None
    confidence_score: float = 0.0


class ClaudePlotInterface(ABC):
    """Claude Plot インターフェース

    DDD準拠のClaude Code連携抽象化
    Application層からDomain層への依存を定義
    """

    @abstractmethod
    async def generate_plot(self, request: PlotGenerationRequest) -> ClaudeResponse:
        """プロット生成

        Args:
            request: プロット生成リクエスト

        Returns:
            ClaudeResponse: Claude生成レスポンス
        """

    @abstractmethod
    async def validate_plot(self, plot_content: str) -> ClaudeResponse:
        """プロット検証

        Args:
            plot_content: 検証するプロット内容

        Returns:
            ClaudeResponse: 検証結果レスポンス
        """

    @abstractmethod
    async def enhance_plot(self, plot_content: str, enhancement_type: str) -> ClaudeResponse:
        """プロット強化

        Args:
            plot_content: 強化するプロット内容
            enhancement_type: 強化タイプ

        Returns:
            ClaudeResponse: 強化結果レスポンス
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Claude Code連携可能状態確認

        Returns:
            bool: 利用可能な場合True
        """
