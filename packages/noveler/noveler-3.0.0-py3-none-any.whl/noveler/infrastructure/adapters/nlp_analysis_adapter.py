#!/usr/bin/env python3
"""NLP分析アダプター - NIH症候群防止システム Phase2

SPEC: SPEC-NIH-PREVENTION-CODEMAP-001
責務: Word2Vec・Doc2Vec統合による機械学習ベース意味類似度分析
"""


import math
import re
from collections import Counter

from noveler.infrastructure.utils.numpy_compat import get_numpy

# logger_service経由で注入

np = get_numpy()


class NLPAnalysisAdapter:
    """自然言語処理による類似度分析アダプター"""

    def __init__(self, enable_advanced_features: bool = True) -> None:
        """初期化"""
        self.enable_advanced_features = enable_advanced_features

        # 意味的重要度辞書（プログラミング関連）
        self.semantic_weights = {
            # 高重要度動詞
            "create": 1.0,
            "generate": 1.0,
            "build": 1.0,
            "construct": 1.0,
            "process": 0.9,
            "handle": 0.9,
            "manage": 0.9,
            "execute": 0.9,
            "validate": 0.8,
            "check": 0.8,
            "verify": 0.8,
            "analyze": 0.8,
            "update": 0.7,
            "modify": 0.7,
            "change": 0.7,
            "transform": 0.7,
            # 重要度名詞
            "data": 1.0,
            "information": 1.0,
            "content": 1.0,
            "result": 1.0,
            "service": 0.9,
            "manager": 0.9,
            "handler": 0.9,
            "processor": 0.9,
            "validator": 0.8,
            "checker": 0.8,
            "analyzer": 0.8,
            "parser": 0.8,
            "adapter": 0.7,
            "wrapper": 0.7,
            "helper": 0.7,
            "utility": 0.7,
            # ドメイン固有用語
            "user": 1.0,
            "episode": 1.0,
            "plot": 1.0,
            "quality": 1.0,
            "authentication": 0.9,
            "authorization": 0.9,
            "session": 0.9,
            "repository": 0.8,
            "entity": 0.8,
            "value": 0.8,
            "object": 0.8,
        }

        # 同義語辞書
        self.synonym_groups = {
            "create_group": {"create", "generate", "build", "construct", "produce"},
            "process_group": {"process", "handle", "manage", "execute", "perform"},
            "validate_group": {"validate", "check", "verify", "confirm", "ensure"},
            "data_group": {"data", "information", "content", "payload", "input"},
            "user_group": {"user", "customer", "client", "account", "person"},
            "auth_group": {"authentication", "authorization", "login", "access", "permission"},
        }

        # ストップワード（プログラミング特化版）
        self.programming_stopwords = {
            "get",
            "set",
            "is",
            "has",
            "do",
            "can",
            "will",
            "should",
            "would",
            "the",
            "and",
            "or",
            "not",
            "but",
            "for",
            "in",
            "on",
            "at",
            "by",
            "to",
            "from",
            "with",
            "of",
            "a",
            "an",
            "as",
            "if",
            "when",
            "where",
        }

    def calculate_semantic_similarity_with_word2vec(
        self, text1: str, text2: str, use_custom_weights: bool = True
    ) -> float:
        """Word2Vec風の意味的類似度計算（簡易版）"""

        if not text1 or not text2:
            return 0.0

        # テキストの前処理とトークン化
        tokens1 = self._preprocess_programming_text(text1)
        tokens2 = self._preprocess_programming_text(text2)

        if not tokens1 or not tokens2:
            return 0.0

        # 意味ベクトル作成
        vector1 = self._create_semantic_vector(tokens1, use_custom_weights)
        vector2 = self._create_semantic_vector(tokens2, use_custom_weights)

        # コサイン類似度計算
        return self._calculate_cosine_similarity(vector1, vector2)

    def calculate_doc2vec_similarity(
        self, doc1_tokens: list[str], doc2_tokens: list[str], context_corpus: list[list[str]] | None = None
    ) -> float:
        """Doc2Vec風のドキュメント類似度計算"""

        if not doc1_tokens or not doc2_tokens:
            return 0.0

        # ドキュメント特徴量の抽出
        doc1_features = self._extract_document_features(doc1_tokens, context_corpus)
        doc2_features = self._extract_document_features(doc2_tokens, context_corpus)

        # 特徴量ベクトルの類似度計算
        return self._calculate_feature_similarity(doc1_features, doc2_features)

    def analyze_function_semantic_similarity(
        self,
        func1_name: str,
        func1_params: list[str],
        func1_docstring: str,
        func2_name: str,
        func2_params: list[str],
        func2_docstring: str,
    ) -> dict[str, float]:
        """関数間の包括的意味類似度分析"""

        similarities = {}

        # 関数名類似度（最重要）
        similarities["name_similarity"] = self.calculate_semantic_similarity_with_word2vec(
            func1_name, func2_name, use_custom_weights=True
        )

        # パラメータ名類似度
        param1_text = " ".join(func1_params) if func1_params else ""
        param2_text = " ".join(func2_params) if func2_params else ""
        similarities["parameter_similarity"] = self.calculate_semantic_similarity_with_word2vec(
            param1_text, param2_text
        )

        # ドキュメント文字列類似度
        similarities["docstring_similarity"] = self.calculate_semantic_similarity_with_word2vec(
            func1_docstring or "", func2_docstring or ""
        )

        # 構造的類似度（パラメータ数等）
        similarities["structural_similarity"] = self._calculate_parameter_structural_similarity(
            func1_params, func2_params
        )

        # 総合類似度（重み付け平均）
        weights = {
            "name_similarity": 0.4,
            "parameter_similarity": 0.25,
            "docstring_similarity": 0.25,
            "structural_similarity": 0.1,
        }

        similarities["overall_semantic_similarity"] = sum(
            similarities[key] * weights[key] for key in weights if key in similarities
        )

        return similarities

    def extract_programming_intent_features(
        self, function_name: str, parameters: list[str], docstring: str | None = None
    ) -> dict[str, float]:
        """プログラミング意図特徴量の抽出"""

        features = {}

        # 関数名からの意図抽出
        name_features = self._extract_name_intent_features(function_name)
        features.update(name_features)

        # パラメータからの意図抽出
        param_features = self._extract_parameter_intent_features(parameters)
        features.update(param_features)

        # ドキュメント文字列からの意図抽出
        if docstring:
            doc_features = self._extract_docstring_intent_features(docstring)
            features.update(doc_features)

        return features

    def calculate_semantic_distance_matrix(self, text_pairs: list[tuple[str, str]]) -> list[list[float]]:
        """複数テキストペアの意味距離行列計算"""

        if not text_pairs:
            return []

        n = len(text_pairs)
        # numpy配列の代わりにネストしたリストを使用
        distance_matrix = [[0.0 for _ in range(n)] for _ in range(n)]

        for i in range(n):
            for j in range(i + 1, n):
                # 非対称距離も考慮
                sim_ij = self.calculate_semantic_similarity_with_word2vec(text_pairs[i][0], text_pairs[j][0])

                sim_ji = self.calculate_semantic_similarity_with_word2vec(text_pairs[i][1], text_pairs[j][1])

                # 対称化
                avg_similarity = (sim_ij + sim_ji) / 2.0
                distance = 1.0 - avg_similarity

                distance_matrix[i][j] = distance
                distance_matrix[j][i] = distance

        return distance_matrix

    def _preprocess_programming_text(self, text: str) -> list[str]:
        """プログラミング向けテキスト前処理"""

        if not text:
            return []

        # キャメルケース・スネークケースの分割
        text = self._split_camel_snake_case(text)

        # 小文字化
        text = text.lower()

        # 記号除去（アンダースコアは保持）
        text = re.sub(r"[^\w\s_]", " ", text)

        # トークン化
        tokens = text.split()

        # ストップワード除去
        tokens = [token for token in tokens if token not in self.programming_stopwords]

        # 短すぎるトークンの除去
        return [token for token in tokens if len(token) >= 2]


    def _split_camel_snake_case(self, text: str) -> str:
        """キャメルケース・スネークケースの分割"""

        # キャメルケース分割 (camelCase -> camel Case)
        text = re.sub("([a-z0-9])([A-Z])", r"\1 \2", text)

        # スネークケース分割 (snake_case -> snake case)
        return text.replace("_", " ")


    def _create_semantic_vector(self, tokens: list[str], use_custom_weights: bool = True) -> dict[str, float]:
        """意味ベクトルの作成"""

        vector = {}
        token_counts = Counter(tokens)

        for token, count in token_counts.items():
            # 基本のTF値
            tf = count / len(tokens)

            # 意味的重要度の適用
            if use_custom_weights and token in self.semantic_weights:
                semantic_weight = self.semantic_weights[token]
            else:
                semantic_weight = 1.0

            # 同義語グループの考慮
            synonym_boost = self._get_synonym_group_boost(token)

            # 最終重み計算
            final_weight = tf * semantic_weight * synonym_boost
            vector[token] = final_weight

        # ベクトル正規化
        return self._normalize_vector(vector)

    def _get_synonym_group_boost(self, token: str) -> float:
        """同義語グループによるブースト値計算"""

        boost = 1.0

        for synonyms in self.synonym_groups.values():
            if token in synonyms:
                boost = 1.2  # 同義語グループに属する場合はブースト
                break

        return boost

    def _normalize_vector(self, vector: dict[str, float]) -> dict[str, float]:
        """ベクトル正規化（L2ノルム）"""

        if not vector:
            return {}

        # L2ノルム計算
        norm = math.sqrt(sum(value**2 for value in vector.values()))

        if norm == 0:
            return vector

        # 正規化
        return {key: value / norm for key, value in vector.items()}

    def _calculate_cosine_similarity(self, vector1: dict[str, float], vector2: dict[str, float]) -> float:
        """コサイン類似度計算"""

        if not vector1 or not vector2:
            return 0.0

        # 共通次元の取得
        common_dims = set(vector1.keys()) & set(vector2.keys())

        if not common_dims:
            return 0.0

        # 内積計算
        dot_product = sum(vector1[dim] * vector2[dim] for dim in common_dims)

        return max(0.0, min(1.0, dot_product))

    def _extract_document_features(self, tokens: list[str], context_corpus: list[list[str]] | None = None) -> dict[str, float]:
        """ドキュメント特徴量の抽出"""

        features = {}

        if not tokens:
            return features

        # 基本統計特徴量
        features["doc_length"] = len(tokens)
        features["unique_tokens"] = len(set(tokens))
        features["token_diversity"] = features["unique_tokens"] / features["doc_length"]

        # 意味的密度
        semantic_token_count = sum(1 for token in tokens if token in self.semantic_weights)

        features["semantic_density"] = semantic_token_count / len(tokens)

        # TF-IDF特徴量（簡易版）
        if context_corpus:
            tfidf_features = self._calculate_simple_tfidf_features(tokens, context_corpus)
            features.update(tfidf_features)

        return features

    def _calculate_simple_tfidf_features(self, tokens: list[str], corpus: list[list[str]]) -> dict[str, float]:
        """簡易TF-IDF特徴量計算"""

        features = {}
        token_counts = Counter(tokens)
        total_tokens = len(tokens)
        corpus_size = len(corpus)

        # 重要トークンのTF-IDF計算
        for token, count in token_counts.items():
            if token in self.semantic_weights:
                # TF計算
                tf = count / total_tokens

                # DF計算（そのトークンを含む文書数）
                df = sum(1 for doc in corpus if token in doc)

                # IDF計算
                idf = math.log(corpus_size / df) if df > 0 else math.log(corpus_size)

                # TF-IDF
                tfidf = tf * idf
                features[f"tfidf_{token}"] = tfidf

        return features

    def _calculate_feature_similarity(self, features1: dict[str, float], features2: dict[str, float]) -> float:
        """特徴量ベクトル間類似度計算"""

        if not features1 or not features2:
            return 0.0

        # 共通特徴量の取得
        common_features = set(features1.keys()) & set(features2.keys())

        if not common_features:
            return 0.0

        # 正規化ユークリッド距離による類似度
        distances = []
        for feature in common_features:
            val1 = features1[feature]
            val2 = features2[feature]

            # 正規化（最大値で割る）
            max_val = max(abs(val1), abs(val2), 1.0)
            normalized_distance = abs(val1 - val2) / max_val
            distances.append(normalized_distance)

        # 平均距離から類似度に変換
        if distances:
            avg_distance = sum(distances) / len(distances)
            similarity = 1.0 - avg_distance
            return max(0.0, min(1.0, similarity))

        return 0.0

    def _extract_name_intent_features(self, function_name: str) -> dict[str, float]:
        """関数名からの意図特徴量抽出"""

        features = {}

        if not function_name:
            return features

        # 名前の前処理
        tokens = self._preprocess_programming_text(function_name)

        # 動作タイプの特定
        action_types = {
            "create": ["create", "generate", "build", "construct", "make"],
            "read": ["get", "read", "fetch", "retrieve", "find"],
            "update": ["update", "modify", "change", "set", "edit"],
            "delete": ["delete", "remove", "clear", "destroy"],
            "validate": ["validate", "check", "verify", "ensure"],
            "process": ["process", "handle", "execute", "run"],
        }

        for action_type, keywords in action_types.items():
            has_action = any(keyword in tokens for keyword in keywords)
            features[f"intent_{action_type}"] = 1.0 if has_action else 0.0

        return features

    def _extract_parameter_intent_features(self, parameters: list[str]) -> dict[str, float]:
        """パラメータからの意図特徴量抽出"""

        features = {}

        if not parameters:
            features["param_count"] = 0.0
            return features

        features["param_count"] = float(len(parameters))

        # パラメータタイプの分析
        param_types = {
            "id": ["id", "identifier", "key"],
            "data": ["data", "content", "info", "payload"],
            "config": ["config", "settings", "options", "params"],
            "callback": ["callback", "handler", "function", "func"],
        }

        param_text = " ".join(parameters).lower()

        for param_type, keywords in param_types.items():
            has_type = any(keyword in param_text for keyword in keywords)
            features[f"param_{param_type}"] = 1.0 if has_type else 0.0

        return features

    def _extract_docstring_intent_features(self, docstring: str) -> dict[str, float]:
        """ドキュメント文字列からの意図特徴量抽出"""

        features = {}

        if not docstring:
            return features

        # ドキュメント文字列の前処理
        tokens = self._preprocess_programming_text(docstring)
        features["docstring_length"] = float(len(tokens))

        # 意図キーワードの検出
        intent_keywords = {
            "creation": ["作成", "生成", "create", "generate"],
            "processing": ["処理", "加工", "process", "handle"],
            "validation": ["検証", "チェック", "validate", "check"],
            "retrieval": ["取得", "検索", "get", "fetch", "find"],
            "analysis": ["分析", "解析", "analyze", "parse"],
        }

        docstring_lower = docstring.lower()

        for intent, keywords in intent_keywords.items():
            has_intent = any(keyword in docstring_lower for keyword in keywords)
            features[f"docstring_{intent}"] = 1.0 if has_intent else 0.0

        return features

    def _calculate_parameter_structural_similarity(self, params1: list[str], params2: list[str]) -> float:
        """パラメータ構造類似度計算"""

        if not params1 and not params2:
            return 1.0

        if not params1 or not params2:
            return 0.0

        # パラメータ数の類似度
        count_similarity = 1.0 - abs(len(params1) - len(params2)) / max(len(params1), len(params2))

        # パラメータ名の類似度（順序考慮）
        name_similarities = []
        max_len = max(len(params1), len(params2))

        for i in range(max_len):
            param1 = params1[i] if i < len(params1) else ""
            param2 = params2[i] if i < len(params2) else ""

            if param1 and param2:
                sim = self.calculate_semantic_similarity_with_word2vec(param1, param2)
                name_similarities.append(sim)

        name_similarity = sum(name_similarities) / len(name_similarities) if name_similarities else 0.0

        # 重み付け平均
        return count_similarity * 0.3 + name_similarity * 0.7
