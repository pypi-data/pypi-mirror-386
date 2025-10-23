"""Infrastructure.adapters.similarity_calculation_adapter
Where: Infrastructure adapter providing similarity calculations to the domain.
What: Delegates similarity scoring to configured engines and normalises responses.
Why: Integrates external similarity services without coupling domain logic to implementations.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""類似度計算アダプタ

仕様書: SPEC-NIH-PREVENTION-CODEMAP-001
"""


import math
import re
from collections import Counter

from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)


class BasicSimilarityCalculationAdapter:
    """基本類似度計算アダプタ"""

    def __init__(self) -> None:
        """初期化"""
        # ストップワード（類似度計算で無視する単語）
        self.stopwords = {
            "the",
            "and",
            "for",
            "are",
            "but",
            "not",
            "you",
            "all",
            "can",
            "had",
            "was",
            "one",
            "our",
            "out",
            "day",
            "get",
            "has",
            "him",
            "his",
            "how",
            "man",
            "new",
            "now",
            "old",
            "see",
            "two",
            "way",
            "who",
            "boy",
            "did",
            "its",
            "let",
            "put",
            "say",
            "she",
            "too",
            "use",
        }

    def calculate_vector_similarity(self, vector1: dict[str, float], vector2: dict[str, float]) -> float:
        """ベクトル類似度計算（コサイン類似度）"""

        if not vector1 or not vector2:
            return 0.0

        # 共通の次元を取得
        common_dimensions = set(vector1.keys()) & set(vector2.keys())

        if not common_dimensions:
            return 0.0

        # 内積の計算
        dot_product = sum(vector1[dim] * vector2[dim] for dim in common_dimensions)

        # ベクトルの大きさ計算
        magnitude1 = math.sqrt(sum(value**2 for value in vector1.values()))
        magnitude2 = math.sqrt(sum(value**2 for value in vector2.values()))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        # コサイン類似度
        similarity = dot_product / (magnitude1 * magnitude2)
        return max(0.0, min(1.0, similarity))

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """テキスト類似度計算"""

        if not text1 or not text2:
            return 0.0

        # テキストの前処理
        tokens1 = self._preprocess_text(text1)
        tokens2 = self._preprocess_text(text2)

        if not tokens1 or not tokens2:
            return 0.0

        # Jaccard類似度を計算
        set1 = set(tokens1)
        set2 = set(tokens2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        jaccard_similarity = intersection / union if union > 0 else 0.0

        # 重み付きオーバーラップも考慮
        counter1 = Counter(tokens1)
        counter2 = Counter(tokens2)

        weighted_overlap = self._calculate_weighted_overlap(counter1, counter2)

        # 最終的な類似度（Jaccard + 重み付きオーバーラップの平均）
        return (jaccard_similarity + weighted_overlap) / 2.0

    def calculate_tfidf_similarity(self, tokens1: list[str], tokens2: list[str], corpus: list[list[str]]) -> float:
        """TF-IDF類似度計算"""

        if not tokens1 or not tokens2:
            return 0.0

        # TF-IDFベクトルの計算
        tfidf1 = self._calculate_tfidf_vector(tokens1, corpus)
        tfidf2 = self._calculate_tfidf_vector(tokens2, corpus)

        # コサイン類似度でTF-IDFベクトルを比較
        return self.calculate_vector_similarity(tfidf1, tfidf2)

    def calculate_structural_similarity(self, structure1: dict[str, any], structure2: dict[str, any]) -> float:
        """構造的類似度計算"""

        if not structure1 or not structure2:
            return 0.0

        # 構造的特徴を数値ベクトルに変換
        vector1 = self._extract_structural_features(structure1)
        vector2 = self._extract_structural_features(structure2)

        # 正規化ユークリッド距離を類似度に変換
        euclidean_distance = self._calculate_euclidean_distance(vector1, vector2)
        max_distance = math.sqrt(len(vector1))  # 最大可能距離

        normalized_distance = euclidean_distance / max_distance if max_distance > 0 else 0.0
        similarity = 1.0 - normalized_distance

        return max(0.0, min(1.0, similarity))

    def calculate_semantic_distance(self, word1: str, word2: str, use_levenshtein: bool = True) -> float:
        """意味的距離計算（簡易版）"""

        if not word1 or not word2:
            return 1.0  # 最大距離

        if word1 == word2:
            return 0.0  # 同じ単語

        # 編集距離ベースの類似度
        if use_levenshtein:
            edit_distance = self._calculate_levenshtein_distance(word1, word2)
            max_length = max(len(word1), len(word2))
            return edit_distance / max_length if max_length > 0 else 1.0

        # 単純な文字レベル類似度
        char_similarity = self._calculate_character_similarity(word1, word2)
        return 1.0 - char_similarity

    def calculate_fuzzy_match_score(self, query: str, candidate: str, threshold: float = 0.7) -> float:
        """ファジーマッチスコア計算"""

        if not query or not candidate:
            return 0.0

        # 複数の類似度指標を組み合わせ
        scores = []

        # 1. レーベンシュタイン距離ベース
        edit_distance = self._calculate_levenshtein_distance(query.lower(), candidate.lower())
        max_length = max(len(query), len(candidate))
        edit_score = 1.0 - (edit_distance / max_length) if max_length > 0 else 0.0
        scores.append(edit_score)

        # 2. 共通部分文字列スコア
        substring_score = self._calculate_longest_common_substring_ratio(query, candidate)
        scores.append(substring_score)

        # 3. トークンレベル類似度
        tokens_query = query.lower().split()
        tokens_candidate = candidate.lower().split()
        token_score = self._calculate_token_level_similarity(tokens_query, tokens_candidate)
        scores.append(token_score)

        # 重み付き平均
        weighted_score = edit_score * 0.4 + substring_score * 0.3 + token_score * 0.3

        return weighted_score if weighted_score >= threshold else 0.0

    def _preprocess_text(self, text: str) -> list[str]:
        """テキストの前処理"""
        if not text:
            return []

        # 小文字化
        text = text.lower()

        # 英数字以外を削除
        text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)

        # トークン化
        tokens = text.split()

        # ストップワード除去
        tokens = [token for token in tokens if token not in self.stopwords]

        # 短すぎるトークンを除去
        return [token for token in tokens if len(token) >= 2]


    def _calculate_weighted_overlap(self, counter1: Counter, counter2: Counter) -> float:
        """重み付きオーバーラップ計算"""

        # 共通する要素の重み付き重複度を計算
        common_elements = set(counter1.keys()) & set(counter2.keys())

        if not common_elements:
            return 0.0

        weighted_intersection = sum(min(counter1[element], counter2[element]) for element in common_elements)

        total_elements = sum(counter1.values()) + sum(counter2.values())

        return (2 * weighted_intersection) / total_elements if total_elements > 0 else 0.0

    def _calculate_tfidf_vector(self, tokens: list[str], corpus: list[list[str]]) -> dict[str, float]:
        """TF-IDFベクトルの計算"""

        if not tokens or not corpus:
            return {}

        # TF（Term Frequency）計算
        token_counts = Counter(tokens)
        total_tokens = len(tokens)
        tf_scores = {token: count / total_tokens for token, count in token_counts.items()}

        # IDF（Inverse Document Frequency）計算
        corpus_size = len(corpus)
        idf_scores = {}

        for token in set(tokens):
            # トークンを含む文書数をカウント
            docs_with_token = sum(1 for doc in corpus if token in doc)

            # IDF計算（ゼロ除算を防ぐ）
            if docs_with_token > 0:
                idf = math.log(corpus_size / docs_with_token)
            else:
                idf = math.log(corpus_size)  # 文書に含まれない場合

            idf_scores[token] = idf

        # TF-IDF計算
        return {token: tf_scores[token] * idf_scores[token] for token in tf_scores}


    def _extract_structural_features(self, structure: dict[str, any]) -> list[float]:
        """構造的特徴の抽出"""

        features = []

        # 基本的な数値特徴を抽出
        for value in structure.values():
            if isinstance(value, int | float):
                features.append(float(value))
            elif isinstance(value, bool):
                features.append(1.0 if value else 0.0)
            elif isinstance(value, list | tuple | set | dict):
                features.append(float(len(value)))
            else:
                # 文字列など、その他の型
                features.append(0.0)

        # 最小限の特徴数を保証
        while len(features) < 5:
            features.append(0.0)

        # 正規化（0-1範囲）
        if features:
            max_feature = max(features)
            if max_feature > 0:
                features = [f / max_feature for f in features]

        return features

    def _calculate_euclidean_distance(self, vector1: list[float], vector2: list[float]) -> float:
        """ユークリッド距離計算"""

        # ベクトルの長さを揃える
        max_length = max(len(vector1), len(vector2))
        v1 = vector1 + [0.0] * (max_length - len(vector1))
        v2 = vector2 + [0.0] * (max_length - len(vector2))

        # ユークリッド距離計算
        squared_diffs = [(a - b) ** 2 for a, b in zip(v1, v2, strict=False)]
        return math.sqrt(sum(squared_diffs))

    def _calculate_levenshtein_distance(self, s1: str, s2: str) -> int:
        """レーベンシュタイン距離（編集距離）計算"""

        if not s1:
            return len(s2)
        if not s2:
            return len(s1)

        # 動的プログラミングによる計算
        rows = len(s1) + 1
        cols = len(s2) + 1

        # 初期化
        dp = [[0] * cols for _ in range(rows)]

        for i in range(rows):
            dp[i][0] = i
        for j in range(cols):
            dp[0][j] = j

        # DP計算
        for i in range(1, rows):
            for j in range(1, cols):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i - 1][j],  # 削除
                        dp[i][j - 1],  # 挿入
                        dp[i - 1][j - 1],  # 置換
                    )

        return dp[rows - 1][cols - 1]

    def _calculate_character_similarity(self, s1: str, s2: str) -> float:
        """文字レベル類似度計算"""

        if not s1 or not s2:
            return 0.0

        # 文字の出現頻度を比較
        counter1 = Counter(s1.lower())
        counter2 = Counter(s2.lower())

        # 共通文字の重複度
        common_chars = set(counter1.keys()) & set(counter2.keys())

        if not common_chars:
            return 0.0

        common_count = sum(min(counter1[char], counter2[char]) for char in common_chars)

        total_chars = len(s1) + len(s2)

        return (2 * common_count) / total_chars if total_chars > 0 else 0.0

    def _calculate_longest_common_substring_ratio(self, s1: str, s2: str) -> float:
        """最長共通部分文字列比率計算"""

        if not s1 or not s2:
            return 0.0

        # 最長共通部分文字列を発見
        lcs_length = self._longest_common_substring_length(s1.lower(), s2.lower())

        # より短い文字列の長さで正規化
        shorter_length = min(len(s1), len(s2))

        return lcs_length / shorter_length if shorter_length > 0 else 0.0

    def _longest_common_substring_length(self, s1: str, s2: str) -> int:
        """最長共通部分文字列の長さ"""

        if not s1 or not s2:
            return 0

        # 動的プログラミングによる計算
        rows = len(s1) + 1
        cols = len(s2) + 1

        dp = [[0] * cols for _ in range(rows)]
        max_length = 0

        for i in range(1, rows):
            for j in range(1, cols):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                    max_length = max(max_length, dp[i][j])
                else:
                    dp[i][j] = 0

        return max_length

    def _calculate_token_level_similarity(self, tokens1: list[str], tokens2: list[str]) -> float:
        """トークンレベル類似度計算"""

        if not tokens1 or not tokens2:
            return 0.0

        # トークン集合のJaccard類似度
        set1 = set(tokens1)
        set2 = set(tokens2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0
