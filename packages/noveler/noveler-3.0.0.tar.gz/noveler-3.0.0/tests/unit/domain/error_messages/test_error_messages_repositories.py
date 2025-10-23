"""エラーメッセージドメインのリポジトリインターフェーステスト

TDD準拠テスト:
- ErrorPatternRepository (ABC)
- ExampleRepository (ABC)


仕様書: SPEC-UNIT-TEST
"""

from abc import ABC

import pytest

from noveler.domain.error_messages.repositories import (
    ErrorPatternRepository,
    ExampleRepository,
)


class TestErrorPatternRepository:
    """ErrorPatternRepository抽象インターフェーステスト"""

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_REPOSITORIES-ERROR_PATTERN_REPOSI")
    def test_error_pattern_repository_is_abstract(self) -> None:
        """ErrorPatternRepositoryが抽象クラスであることを確認"""
        assert issubclass(ErrorPatternRepository, ABC)

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_REPOSITORIES-ERROR_PATTERN_REPOSI")
    def test_error_pattern_repository_abstract_methods(self) -> None:
        """ErrorPatternRepositoryの抽象メソッド確認"""
        abstract_methods = ErrorPatternRepository.__abstractmethods__
        expected_methods = {
            "get_pattern",
            "get_all_patterns",
        }
        assert abstract_methods == expected_methods

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_REPOSITORIES-ERROR_PATTERN_REPOSI")
    def test_error_pattern_repository_get_pattern_signature(self) -> None:
        """get_patternメソッドのシグネチャ確認"""

        class MockErrorPatternRepo(ErrorPatternRepository):
            def get_pattern(self, _error_code: str) -> dict:
                return {
                    "code": _error_code,
                    "pattern": r"test_pattern",
                    "message": "テストエラーメッセージ",
                    "severity": "error",
                }

            def get_all_patterns(self) -> dict[str, dict]:
                return {}

        repo = MockErrorPatternRepo()
        result = repo.get_pattern("E001")

        assert isinstance(result, dict)
        assert result["code"] == "E001"
        assert "pattern" in result
        assert "message" in result

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_REPOSITORIES-ERROR_PATTERN_REPOSI")
    def test_error_pattern_repository_get_all_patterns_signature(self) -> None:
        """get_all_patternsメソッドのシグネチャ確認"""

        class MockErrorPatternRepo(ErrorPatternRepository):
            def get_pattern(self, _error_code: str) -> dict:
                return {}

            def get_all_patterns(self) -> dict[str, dict]:
                return {
                    "E001": {"pattern": r"pattern1", "message": "エラー1", "severity": "error"},
                    "E002": {"pattern": r"pattern2", "message": "エラー2", "severity": "warning"},
                }

        repo = MockErrorPatternRepo()
        result = repo.get_all_patterns()

        assert isinstance(result, dict)
        assert len(result) == 2
        assert "E001" in result
        assert "E002" in result
        assert isinstance(result["E001"], dict)

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_REPOSITORIES-ERROR_PATTERN_REPOSI")
    def test_error_pattern_repository_implementation_example(self) -> None:
        """ErrorPatternRepository実装例のテスト"""

        class InMemoryErrorPatternRepo(ErrorPatternRepository):
            def __init__(self) -> None:
                self.patterns = {
                    "SHOW_DONT_TELL": {
                        "pattern": r"(悲しかった|嬉しかった|怒っていた)",
                        "message": "感情を直接的に説明しています。行動や描写で表現しましょう。",
                        "severity": "warning",
                        "category": "expression",
                    },
                    "REPETITIVE_EXPRESSION": {
                        "pattern": r"(.{2,})\1{2,}",
                        "message": "同じ表現が繰り返されています。",
                        "severity": "info",
                        "category": "style",
                    },
                }

            def get_pattern(self, error_code: str) -> dict:
                if error_code not in self.patterns:
                    return {}
                return {"code": error_code, **self.patterns[error_code]}

            def get_all_patterns(self) -> dict[str, dict]:
                return {code: {"code": code, **pattern} for code, pattern in self.patterns.items()}

        repo = InMemoryErrorPatternRepo()

        # 個別パターンの取得
        pattern = repo.get_pattern("SHOW_DONT_TELL")
        assert pattern["code"] == "SHOW_DONT_TELL"
        assert "悲しかった" in pattern["pattern"]
        assert pattern["severity"] == "warning"

        # 存在しないパターン
        empty_pattern = repo.get_pattern("NONEXISTENT")
        assert empty_pattern == {}

        # 全パターンの取得
        all_patterns = repo.get_all_patterns()
        assert len(all_patterns) == 2
        assert all("code" in p for p in all_patterns.values())


class TestExampleRepository:
    """ExampleRepository抽象インターフェーステスト"""

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_REPOSITORIES-EXAMPLE_REPOSITORY_I")
    def test_example_repository_is_abstract(self) -> None:
        """ExampleRepositoryが抽象クラスであることを確認"""
        assert issubclass(ExampleRepository, ABC)

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_REPOSITORIES-EXAMPLE_REPOSITORY_A")
    def test_example_repository_abstract_methods(self) -> None:
        """ExampleRepositoryの抽象メソッド確認"""
        abstract_methods = ExampleRepository.__abstractmethods__
        expected_methods = {
            "get_examples",
            "add_example",
            "get_popular_examples",
        }
        assert abstract_methods == expected_methods

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_REPOSITORIES-EXAMPLE_REPOSITORY_G")
    def test_example_repository_get_examples_signature(self) -> None:
        """get_examplesメソッドのシグネチャ確認"""

        class MockExampleRepo(ExampleRepository):
            def get_examples(self, _error_type: str, _sub_type: str | None = None) -> list[dict]:
                examples = [
                    {
                        "before": "彼は悲しかった。",
                        "after": "彼の目から涙がこぼれ落ちた。",
                        "explanation": "感情を行動で表現",
                    }
                ]
                return examples if _error_type == "SHOW_DONT_TELL" else []

            def add_example(self, _error_type: str, example: dict) -> None:
                pass

            def get_popular_examples(self, _error_type: str, _limit: int = 5) -> list[dict]:
                return []

        repo = MockExampleRepo()

        # error_typeのみ
        result = repo.get_examples("SHOW_DONT_TELL")
        assert isinstance(result, list)
        assert len(result) == 1
        assert "before" in result[0]
        assert "after" in result[0]

        # sub_typeも指定
        result_with_subtype = repo.get_examples("SHOW_DONT_TELL", "emotion")
        assert isinstance(result_with_subtype, list)

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_REPOSITORIES-EXAMPLE_REPOSITORY_A")
    def test_example_repository_add_example_signature(self) -> None:
        """add_exampleメソッドのシグネチャ確認"""

        class MockExampleRepo(ExampleRepository):
            def __init__(self) -> None:
                self.examples = {}

            def get_examples(self, error_type: str, _sub_type: str | None = None) -> list[dict]:
                return self.examples.get(error_type, [])

            def add_example(self, error_type: str, example: dict) -> None:
                if error_type not in self.examples:
                    self.examples[error_type] = []
                self.examples[error_type].append(example)

            def get_popular_examples(self, _error_type: str, _limit: int = 5) -> list[dict]:
                return []

        repo = MockExampleRepo()

        example = {
            "before": "彼女は怒っていた。",
            "after": "彼女の頬が紅潮し、拳を握りしめた。",
            "explanation": "怒りを身体的な反応で表現",
            "tags": ["emotion", "anger"],
        }

        # 例外が発生しないことを確認
        repo.add_example("SHOW_DONT_TELL", example)

        # 追加されたことを確認
        examples = repo.get_examples("SHOW_DONT_TELL")
        assert len(examples) == 1
        assert examples[0]["before"] == "彼女は怒っていた。"

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_REPOSITORIES-EXAMPLE_REPOSITORY_G")
    def test_example_repository_get_popular_examples_signature(self) -> None:
        """get_popular_examplesメソッドのシグネチャ確認"""

        class MockExampleRepo(ExampleRepository):
            def get_examples(self, _error_type: str, _sub_type: str | None = None) -> list[dict]:
                return []

            def add_example(self, error_type: str, example: dict) -> None:
                pass

            def get_popular_examples(self, _error_type: str, limit: int = 5) -> list[dict]:
                all_examples = [
                    {"before": "ex1", "after": "改善1", "usage_count": 10},
                    {"before": "ex2", "after": "改善2", "usage_count": 8},
                    {"before": "ex3", "after": "改善3", "usage_count": 15},
                    {"before": "ex4", "after": "改善4", "usage_count": 3},
                    {"before": "ex5", "after": "改善5", "usage_count": 12},
                    {"before": "ex6", "after": "改善6", "usage_count": 5},
                ]
                # usage_countでソートして上位を返す
                sorted_examples = sorted(all_examples, key=lambda x: x.get("usage_count", 0), reverse=True)
                return sorted_examples[:limit]

        repo = MockExampleRepo()

        # デフォルトのlimit
        result = repo.get_popular_examples("SHOW_DONT_TELL")
        assert isinstance(result, list)
        assert len(result) == 5
        assert result[0]["usage_count"] == 15  # 最も人気

        # カスタムlimit
        result_limited = repo.get_popular_examples("SHOW_DONT_TELL", limit=3)
        assert len(result_limited) == 3

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_REPOSITORIES-EXAMPLE_REPOSITORY_I")
    def test_example_repository_implementation_example(self) -> None:
        """ExampleRepository実装例のテスト"""

        class InMemoryExampleRepo(ExampleRepository):
            def __init__(self) -> None:
                self.examples = {
                    "SHOW_DONT_TELL": [
                        {
                            "sub_type": "emotion",
                            "before": "彼は悲しかった。",
                            "after": "彼の肩が震え、目を伏せた。",
                            "explanation": "悲しみを身体的な描写で表現",
                            "usage_count": 25,
                            "rating": 4.5,
                        },
                        {
                            "sub_type": "emotion",
                            "before": "彼女は嬉しかった。",
                            "after": "彼女の瞳が輝き、口元に笑みが浮かんだ。",
                            "explanation": "喜びを表情で表現",
                            "usage_count": 30,
                            "rating": 4.8,
                        },
                        {
                            "sub_type": "state",
                            "before": "部屋は暗かった。",
                            "after": "窓から差し込む月明かりが、かろうじて家具の輪郭を浮かび上がらせていた。",
                            "explanation": "状態を具体的な描写で表現",
                            "usage_count": 15,
                            "rating": 4.2,
                        },
                    ],
                    "REPETITIVE_EXPRESSION": [
                        {
                            "sub_type": None,
                            "before": "とてもとても大きかった。",
                            "after": "途方もなく大きかった。",
                            "explanation": "重複を別の強調表現に置き換え",
                            "usage_count": 10,
                            "rating": 3.8,
                        }
                    ],
                }

            def get_examples(self, error_type: str, _sub_type: str | None = None) -> list[dict]:
                if error_type not in self.examples:
                    return []

                examples = self.examples[error_type]
                if _sub_type is not None:
                    examples = [e for e in examples if e.get("sub_type") == _sub_type]

                return examples

            def add_example(self, error_type: str, example: dict) -> None:
                if error_type not in self.examples:
                    self.examples[error_type] = []

                # デフォルト値を設定
                example.setdefault("usage_count", 0)
                example.setdefault("rating", 0.0)
                example.setdefault("sub_type", None)

                self.examples[error_type].append(example)

            def get_popular_examples(self, error_type: str, limit: int = 5) -> list[dict]:
                if error_type not in self.examples:
                    return []

                examples = self.examples[error_type]
                sorted_examples = sorted(
                    examples, key=lambda x: (x.get("usage_count", 0), x.get("rating", 0)), reverse=True
                )

                return sorted_examples[:limit]

        repo = InMemoryExampleRepo()

        # 全ての例を取得
        all_examples = repo.get_examples("SHOW_DONT_TELL")
        assert len(all_examples) == 3

        # サブタイプでフィルタ
        emotion_examples = repo.get_examples("SHOW_DONT_TELL", "emotion")
        assert len(emotion_examples) == 2
        assert all(e["sub_type"] == "emotion" for e in emotion_examples)

        # 人気の例を取得
        popular = repo.get_popular_examples("SHOW_DONT_TELL", limit=2)
        assert len(popular) == 2
        assert popular[0]["usage_count"] == 30  # 最も使用回数が多い

        # 新しい例を追加
        new_example = {
            "before": "天気が良かった。",
            "after": "雲一つない青空が広がり、暖かな日差しが降り注いでいた。",
            "explanation": "天気を具体的な描写で表現",
            "sub_type": "state",
        }
        repo.add_example("SHOW_DONT_TELL", new_example)

        # 追加確認
        state_examples = repo.get_examples("SHOW_DONT_TELL", "state")
        assert len(state_examples) == 2
        assert any(e["before"] == "天気が良かった。" for e in state_examples)


class TestRepositoryIntegration:
    """エラーメッセージリポジトリ間の統合テスト"""

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_REPOSITORIES-ERROR_PATTERN_AND_EX")
    def test_error_pattern_and_example_repository_integration(self) -> None:
        """ErrorPatternRepositoryとExampleRepositoryの連携確認"""

        class MockErrorPatternRepo(ErrorPatternRepository):
            def __init__(self) -> None:
                self.patterns = {
                    "SHOW_DONT_TELL": {
                        "pattern": r"(悲しかった|嬉しかった|怒っていた|楽しかった)",
                        "message": "感情を直接的に説明しています。",
                        "severity": "warning",
                        "category": "expression",
                        "sub_types": ["emotion"],
                    },
                    "PASSIVE_VOICE": {
                        "pattern": r"られた|された",
                        "message": "受動態が使用されています。",
                        "severity": "info",
                        "category": "style",
                        "sub_types": None,
                    },
                }

            def get_pattern(self, error_code: str) -> dict:
                if error_code not in self.patterns:
                    return {}
                return {"code": error_code, **self.patterns[error_code]}

            def get_all_patterns(self) -> dict[str, dict]:
                return {code: {"code": code, **pattern} for code, pattern in self.patterns.items()}

        class MockExampleRepo(ExampleRepository):
            def __init__(self) -> None:
                self.examples = {
                    "SHOW_DONT_TELL": [
                        {
                            "sub_type": "emotion",
                            "before": "悲しかった",
                            "after": "胸が締め付けられるような感覚に襲われた",
                            "usage_count": 20,
                        }
                    ],
                    "PASSIVE_VOICE": [
                        {
                            "sub_type": None,
                            "before": "手紙が彼に送られた",
                            "after": "彼は手紙を受け取った",
                            "usage_count": 15,
                        }
                    ],
                }

            def get_examples(self, error_type: str, _sub_type: str | None = None) -> list[dict]:
                if error_type not in self.examples:
                    return []

                examples = self.examples[error_type]
                if _sub_type is not None:
                    examples = [e for e in examples if e.get("sub_type") == _sub_type]

                return examples

            def add_example(self, error_type: str, example: dict) -> None:
                if error_type not in self.examples:
                    self.examples[error_type] = []
                self.examples[error_type].append(example)

            def get_popular_examples(self, error_type: str, limit: int = 5) -> list[dict]:
                if error_type not in self.examples:
                    return []

                return sorted(self.examples[error_type], key=lambda x: x.get("usage_count", 0), reverse=True)[:limit]

        # リポジトリの作成
        pattern_repo = MockErrorPatternRepo()
        example_repo = MockExampleRepo()

        # エラーパターンを取得
        pattern = pattern_repo.get_pattern("SHOW_DONT_TELL")
        assert pattern["code"] == "SHOW_DONT_TELL"

        # パターンに対応する例を取得
        examples = example_repo.get_examples(
            pattern["code"], pattern.get("sub_types", [None])[0] if pattern.get("sub_types") else None
        )

        assert len(examples) == 1
        assert examples[0]["before"] in pattern["pattern"]

        # 全パターンに対して例が存在することを確認
        all_patterns = pattern_repo.get_all_patterns()
        for code in all_patterns:
            examples = example_repo.get_examples(code)
            assert len(examples) > 0, f"No examples found for {code}"

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_REPOSITORIES-ERROR_HANDLING_WORKF")
    def test_error_handling_workflow(self) -> None:
        """エラー処理の完全なワークフローテスト"""

        class CompleteErrorPatternRepo(ErrorPatternRepository):
            def __init__(self) -> None:
                self.patterns = {
                    "CLICHE_EXPRESSION": {
                        "pattern": r"(真っ白な雪|漆黒の闇|血のように赤い)",
                        "message": "使い古された表現です。オリジナリティのある表現を心がけましょう。",
                        "severity": "info",
                        "category": "originality",
                        "replaceable": True,
                    }
                }

            def get_pattern(self, error_code: str) -> dict:
                if error_code not in self.patterns:
                    return {}
                return {"code": error_code, **self.patterns[error_code]}

            def get_all_patterns(self) -> dict[str, dict]:
                return {code: {"code": code, **pattern} for code, pattern in self.patterns.items()}

        class CompleteExampleRepo(ExampleRepository):
            def __init__(self) -> None:
                self.examples = {}
                self.usage_stats = {}

            def get_examples(self, error_type: str, _sub_type: str | None = None) -> list[dict]:
                return self.examples.get(error_type, [])

            def add_example(self, error_type: str, example: dict) -> None:
                if error_type not in self.examples:
                    self.examples[error_type] = []

                example["id"] = f"{error_type}_{len(self.examples[error_type])}"
                example["usage_count"] = 0
                example["created_at"] = "2025-01-23"

                self.examples[error_type].append(example)

            def get_popular_examples(self, error_type: str, limit: int = 5) -> list[dict]:
                if error_type not in self.examples:
                    return []

                # 使用統計を更新
                for example in self.examples[error_type]:
                    example_id = example["id"]
                    if example_id in self.usage_stats:
                        example["usage_count"] = self.usage_stats[example_id]

                return sorted(self.examples[error_type], key=lambda x: x.get("usage_count", 0), reverse=True)[:limit]

            def record_usage(self, example_id: str) -> None:
                """使用統計を記録(テスト用メソッド)"""
                self.usage_stats[example_id] = self.usage_stats.get(example_id, 0) + 1

        # ワークフローの実行
        pattern_repo = CompleteErrorPatternRepo()
        example_repo = CompleteExampleRepo()

        # 1. エラーパターンの検出
        pattern = pattern_repo.get_pattern("CLICHE_EXPRESSION")
        assert pattern["replaceable"] is True

        # 2. 改善例の追加(初回は例がないので追加)
        example_repo.add_example(
            "CLICHE_EXPRESSION",
            {"before": "真っ白な雪", "after": "音もなく舞い降りる雪", "explanation": "視覚以外の感覚も含めた表現"},
        )

        example_repo.add_example(
            "CLICHE_EXPRESSION",
            {"before": "真っ白な雪", "after": "綿毛のような雪", "explanation": "具体的な比喩を使用"},
        )

        # 3. 改善例の取得
        examples = example_repo.get_examples("CLICHE_EXPRESSION")
        assert len(examples) == 2

        # 4. 使用統計の記録
        example_repo.record_usage("CLICHE_EXPRESSION_1")  # 2番目の例を3回使用
        example_repo.record_usage("CLICHE_EXPRESSION_1")
        example_repo.record_usage("CLICHE_EXPRESSION_1")
        example_repo.record_usage("CLICHE_EXPRESSION_0")  # 1番目の例を1回使用

        # 5. 人気の例を取得
        popular = example_repo.get_popular_examples("CLICHE_EXPRESSION")
        assert popular[0]["id"] == "CLICHE_EXPRESSION_1"  # 最も使用された例
        assert popular[0]["usage_count"] == 3

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_REPOSITORIES-REPOSITORY_ERROR_CAS")
    def test_repository_error_cases(self) -> None:
        """リポジトリのエラーケーステスト"""

        class StrictErrorPatternRepo(ErrorPatternRepository):
            def __init__(self) -> None:
                self.patterns = {}

            def get_pattern(self, error_code: str) -> dict:
                if not error_code:
                    msg = "error_code cannot be empty"
                    raise ValueError(msg)

                if error_code not in self.patterns:
                    return {}  # 空の辞書を返す(例外は投げない)
                return self.patterns[error_code]

            def get_all_patterns(self) -> dict[str, dict]:
                return self.patterns.copy()

        class StrictExampleRepo(ExampleRepository):
            def __init__(self) -> None:
                self.examples = {}
                self.max_examples_per_type = 100

            def get_examples(self, error_type: str, _sub_type: str | None = None) -> list[dict]:
                if not error_type:
                    return []  # 空のリストを返す

                return self.examples.get(error_type, [])

            def add_example(self, error_type: str, example: dict) -> None:
                if not error_type:
                    msg = "error_type cannot be empty"
                    raise ValueError(msg)

                if not example:
                    msg = "example cannot be empty"
                    raise ValueError(msg)

                if "before" not in example or "after" not in example:
                    msg = "example must have 'before' and 'after' fields"
                    raise ValueError(msg)

                if error_type not in self.examples:
                    self.examples[error_type] = []

                if len(self.examples[error_type]) >= self.max_examples_per_type:
                    msg = f"Maximum examples ({self.max_examples_per_type}) reached for {error_type}"
                    raise ValueError(msg)

                self.examples[error_type].append(example)

            def get_popular_examples(self, error_type: str, limit: int = 5) -> list[dict]:
                if limit < 0:
                    msg = "limit must be non-negative"
                    raise ValueError(msg)

                if limit == 0:
                    return []

                return self.get_examples(error_type)[:limit]

        # エラーパターンリポジトリのテスト
        pattern_repo = StrictErrorPatternRepo()

        # 空のerror_codeでエラー
        with pytest.raises(ValueError, match="error_code cannot be empty"):
            pattern_repo.get_pattern("")

        # 存在しないパターンは空の辞書
        result = pattern_repo.get_pattern("NONEXISTENT")
        assert result == {}

        # 例リポジトリのテスト
        example_repo = StrictExampleRepo()

        # 空のerror_typeは空リストを返す
        result = example_repo.get_examples("")
        assert result == []

        # 不正な例の追加
        with pytest.raises(ValueError, match="error_type cannot be empty"):
            example_repo.add_example("", {"before": "test", "after": "test"})

        with pytest.raises(ValueError, match="example cannot be empty"):
            example_repo.add_example("TEST", {})

        with pytest.raises(ValueError, match="example must have"):
            example_repo.add_example("TEST", {"before": "test"})  # afterがない

        # 負のlimit
        with pytest.raises(ValueError, match="limit must be non-negative"):
            example_repo.get_popular_examples("TEST", limit=-1)

        # limit=0は空リスト
        result = example_repo.get_popular_examples("TEST", limit=0)
        assert result == []
