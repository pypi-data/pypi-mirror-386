#!/usr/bin/env python3
"""NLP分析インターフェース

DDD準拠: Domain層の抽象インターフェース
外部NLP分析サービスへの抽象化層
"""

from abc import ABC, abstractmethod
from typing import Any


class INLPAnalysisAdapter(ABC):
    """NLP分析アダプターインターフェース

    Domain層の抽象インターフェース。
    Infrastructure層で具体実装（OpenAI API、spaCy、BERT等）を提供。
    """

    @abstractmethod
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """意味的類似度計算

        Args:
            text1: 比較対象テキスト1
            text2: 比較対象テキスト2

        Returns:
            float: 意味的類似度（0.0-1.0）
        """

    @abstractmethod
    def extract_intent_features(self, text: str) -> dict[str, float]:
        """意図特徴量抽出

        Args:
            text: 分析対象テキスト

        Returns:
            Dict[str, float]: 意図特徴量マップ
        """

    @abstractmethod
    def analyze_structural_complexity(self, code: str) -> dict[str, Any]:
        """構造複雑度分析

        Args:
            code: 分析対象コード

        Returns:
            Dict[str, Any]: 複雑度分析結果
        """

    @abstractmethod
    def compute_embedding_similarity(self, embeddings1: list[float], embeddings2: list[float]) -> float:
        """埋め込みベクトル類似度計算

        Args:
            embeddings1: 埋め込みベクトル1
            embeddings2: 埋め込みベクトル2

        Returns:
            float: コサイン類似度（-1.0 to 1.0）
        """

    @abstractmethod
    def generate_text_embeddings(self, text: str) -> list[float]:
        """テキスト埋め込み生成

        Args:
            text: 埋め込み対象テキスト

        Returns:
            List[float]: 埋め込みベクトル
        """

    @abstractmethod
    def is_available(self) -> bool:
        """分析サービス利用可能性確認

        Returns:
            bool: 利用可能な場合True
        """
