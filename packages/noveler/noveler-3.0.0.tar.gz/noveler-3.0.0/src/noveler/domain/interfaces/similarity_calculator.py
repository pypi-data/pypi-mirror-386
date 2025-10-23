"""類似度計算インターフェース

ドメイン層での類似度計算抽象化
"""

from abc import ABC, abstractmethod


class ISimilarityCalculator(ABC):
    """類似度計算の抽象インターフェース"""

    @abstractmethod
    def calculate_vector_similarity(self, vector1: dict[str, float], vector2: dict[str, float]) -> float:
        """ベクトル類似度計算"""

    @abstractmethod
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """テキスト類似度計算"""

    @abstractmethod
    def calculate_tfidf_similarity(self, tokens1: list[str], tokens2: list[str], corpus: list[list[str]]) -> float:
        """TF-IDF類似度計算"""
