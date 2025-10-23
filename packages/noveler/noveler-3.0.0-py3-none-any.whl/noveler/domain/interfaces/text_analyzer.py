"""テキスト分析のインターフェース"""

from abc import ABC, abstractmethod
from typing import Any


class ITextAnalyzer(ABC):
    """テキスト分析のインターフェース"""

    @abstractmethod
    def analyze_text(self, text: str) -> dict[str, Any]:
        """テキストを分析"""

    @abstractmethod
    def extract_violations(self, text: str) -> list[dict[str, Any]]:
        """品質違反を抽出"""
