"""エラーメッセージドメインサービスのテスト

TDD準拠テスト:
    - ErrorContextAnalyzer
- ImprovementExampleGenerator


仕様書: SPEC-UNIT-TEST
"""

import re
from unittest.mock import Mock

import pytest

from noveler.domain.error_messages.entities import (
    ErrorAnalysis,
    ErrorContext,
    ErrorSeverity,
    QualityError,
)
from noveler.domain.error_messages.services import (
    ErrorContextAnalyzer,
    ImprovementExampleGenerator,
)
from noveler.domain.error_messages.value_objects import (
    ErrorCode,
    ErrorLocation,
    ImprovementExample,
)


class TestErrorContextAnalyzer:
    """ErrorContextAnalyzerのテストクラス"""

    @pytest.fixture
    def analyzer(self) -> ErrorContextAnalyzer:
        """アナライザーのインスタンス"""
        return ErrorContextAnalyzer()

    @pytest.fixture
    def long_sentence_error(self) -> QualityError:
        """長文エラーのサンプル"""
        return QualityError(
            code=ErrorCode("LONG_SENTENCE"),
            severity=ErrorSeverity.WARNING,
            message="文が長すぎます",
            location=ErrorLocation(line=1),
            context=ErrorContext(
                text="彼は朝早くから準備をして、そして駅まで急いで向かい、また電車を待ち、さらに目的地に到着してから会議室を探した。",
                surrounding_lines=["前の行", "次の行"],
            ),
        )

    @pytest.fixture
    def abstract_emotion_error(self) -> QualityError:
        """抽象的感情表現エラーのサンプル"""
        return QualityError(
            code=ErrorCode("ABSTRACT_EMOTION"),
            severity=ErrorSeverity.WARNING,
            message="感情表現が抽象的です",
            location=ErrorLocation(line=1),
            context=ErrorContext(text="彼女は悲しかった。", surrounding_lines=["別れの場面だった", "雨が降っていた"]),
        )

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-ANALYZE_LONG_SENTENC")
    def test_analyze_long_sentence(self, analyzer: ErrorContextAnalyzer, long_sentence_error: QualityError) -> None:
        """長文エラーの分析テスト"""
        analysis = analyzer.analyze(long_sentence_error)

        assert analysis.error_type == "long_sentence"
        assert analysis.sentence_length > 0
        assert "読みやすくする" in analysis.suggested_approach
        assert isinstance(analysis.split_points, list)

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-ANALYZE_ABSTRACT_EMO")
    def test_analyze_abstract_emotion(
        self, analyzer: ErrorContextAnalyzer, abstract_emotion_error: QualityError
    ) -> None:
        """抽象的感情表現の分析テスト"""
        analysis = analyzer.analyze(abstract_emotion_error)

        assert analysis.error_type == "abstract_emotion"
        assert analysis.emotion_word is not None
        assert "身体感覚" in analysis.suggested_approach or "行動" in analysis.suggested_approach

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-ANALYZE_UNKNOWN_ERRO")
    def test_analyze_unknown_error_type(self, analyzer: ErrorContextAnalyzer) -> None:
        """未知のエラータイプの分析テスト"""
        unknown_error = QualityError(
            code=ErrorCode("UNKNOWN"),
            severity=ErrorSeverity.INFO,
            message="未知のエラー",
            location=ErrorLocation(line=1),
            context=ErrorContext(text="普通の文です。", surrounding_lines=[]),
        )

        analysis = analyzer.analyze(unknown_error)

        assert analysis.error_type == "unknown"
        assert "一般的な改善方法" in analysis.suggested_approach

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-DETERMINE_ERROR_TYPE")
    def test_determine_error_type_long_sentence(self, analyzer: ErrorContextAnalyzer) -> None:
        """長文エラータイプの判定テスト"""
        error = QualityError(
            code=ErrorCode("TEST"),
            severity=ErrorSeverity.WARNING,
            message="文が長すぎます",
            location=ErrorLocation(line=1),
            context=ErrorContext(text="テスト文", surrounding_lines=[]),
        )

        error_type = analyzer._determine_error_type(error)
        assert error_type == "long_sentence"

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-DETERMINE_ERROR_TYPE")
    def test_determine_error_type_abstract_emotion(self, analyzer: ErrorContextAnalyzer) -> None:
        """抽象的感情エラータイプの判定テスト"""
        error = QualityError(
            code=ErrorCode("TEST"),
            severity=ErrorSeverity.WARNING,
            message="感情表現が抽象的です",
            location=ErrorLocation(line=1),
            context=ErrorContext(text="テスト文", surrounding_lines=[]),
        )

        error_type = analyzer._determine_error_type(error)
        assert error_type == "abstract_emotion"

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-DETERMINE_ERROR_TYPE")
    def test_determine_error_type_dialogue_punctuation(self, analyzer: ErrorContextAnalyzer) -> None:
        """会話文句点エラータイプの判定テスト"""
        error = QualityError(
            code=ErrorCode("TEST"),
            severity=ErrorSeverity.WARNING,
            message="会話文の句点が不適切です",
            location=ErrorLocation(line=1),
            context=ErrorContext(text="テスト文", surrounding_lines=[]),
        )

        error_type = analyzer._determine_error_type(error)
        assert error_type == "dialogue_punctuation"

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-ANALYZE_LONG_SENTENC")
    def test_analyze_long_sentence_with_conjunctions(self, analyzer: ErrorContextAnalyzer) -> None:
        """接続詞を含む長文の分析テスト"""
        error = QualityError(
            code=ErrorCode("LONG_SENTENCE"),
            severity=ErrorSeverity.WARNING,
            message="文が長すぎます",
            location=ErrorLocation(line=1),
            context=ErrorContext(
                text="彼は家を出た。そして駅に向かった。しかし電車が遅れていた。", surrounding_lines=[]
            ),
        )

        analysis = analyzer._analyze_long_sentence(error)

        assert analysis.error_type == "long_sentence"
        assert len(analysis.split_points) > 0
        # 「そして」の位置が含まれているはず
        text = error.context.text
        so_pos = text.find("そして")
        assert so_pos in analysis.split_points

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-ANALYZE_LONG_SENTENC")
    def test_analyze_long_sentence_with_commas(self, analyzer: ErrorContextAnalyzer) -> None:
        """読点を含む長文の分析テスト"""
        long_text = "a" * 60 + "、" + "b" * 20  # 60文字後に読点
        error = QualityError(
            code=ErrorCode("LONG_SENTENCE"),
            severity=ErrorSeverity.WARNING,
            message="文が長すぎます",
            location=ErrorLocation(line=1),
            context=ErrorContext(text=long_text, surrounding_lines=[]),
        )

        analysis = analyzer._analyze_long_sentence(error)

        # 50文字以降の読点が検出されるはず
        comma_pos = long_text.find("、")
        assert comma_pos in analysis.split_points

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-ANALYZE_ABSTRACT_EMO")
    def test_analyze_abstract_emotion_with_context_clues(self, analyzer: ErrorContextAnalyzer) -> None:
        """コンテキスト手がかりを含む感情表現の分析テスト"""
        error = QualityError(
            code=ErrorCode("ABSTRACT_EMOTION"),
            severity=ErrorSeverity.WARNING,
            message="感情表現が抽象的です",
            location=ErrorLocation(line=1),
            context=ErrorContext(
                text="彼は嬉しかった。", surrounding_lines=["彼女との出会いは偶然だった", "運命を感じた"]
            ),
        )

        analysis = analyzer._analyze_abstract_emotion(error)

        assert analysis.error_type == "abstract_emotion"
        assert analysis.emotion_word == "嬉しかった"
        # 出会いの場面のため、心拍や呼吸での表現を提案
        assert "心拍" in analysis.suggested_approach or "呼吸" in analysis.suggested_approach

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-ANALYZE_ABSTRACT_EMO")
    def test_analyze_abstract_emotion_separation_context(self, analyzer: ErrorContextAnalyzer) -> None:
        """別れの場面での感情表現分析テスト"""
        error = QualityError(
            code=ErrorCode("ABSTRACT_EMOTION"),
            severity=ErrorSeverity.WARNING,
            message="感情表現が抽象的です",
            location=ErrorLocation(line=1),
            context=ErrorContext(text="彼女は寂しかった。", surrounding_lines=["別れの時が来た", "彼は去っていった"]),
        )

        analysis = analyzer._analyze_abstract_emotion(error)

        # 別れの場面のため、視線や手の動きでの表現を提案
        assert "視線" in analysis.suggested_approach or "手の動き" in analysis.suggested_approach

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-EMOTION_PATTERNS_DET")
    def test_emotion_patterns_detection(self, analyzer: ErrorContextAnalyzer) -> None:
        """感情パターンの検出テスト"""
        test_cases = [
            ("彼は悲しかった", True),
            ("嬉しい気持ちになった", True),
            ("怒っていた", True),
            ("楽しんでいる", True),
            ("普通の文章です", False),
        ]

        for text, should_match in test_cases:
            found_match = False
            for pattern in analyzer.EMOTION_PATTERNS:
                if re.search(pattern, text):
                    found_match = True
                    break

            assert found_match == should_match, f"Text: {text}, Expected: {should_match}, Got: {found_match}"


class TestImprovementExampleGenerator:
    """ImprovementExampleGeneratorのテストクラス"""

    @pytest.fixture
    def mock_pattern_repo(self) -> Mock:
        """パターンリポジトリのモック"""
        return Mock()

    @pytest.fixture
    def mock_example_repo(self) -> Mock:
        """例リポジトリのモック"""
        mock = Mock()
        mock.get_examples.return_value = []
        return mock

    @pytest.fixture
    def generator(self, mock_pattern_repo: Mock, mock_example_repo: Mock) -> ImprovementExampleGenerator:
        """ジェネレーターのインスタンス"""
        return ImprovementExampleGenerator(mock_pattern_repo, mock_example_repo)

    @pytest.fixture
    def long_sentence_error(self) -> QualityError:
        """長文エラーのサンプル"""
        return QualityError(
            code=ErrorCode("LONG_SENTENCE"),
            severity=ErrorSeverity.WARNING,
            message="文が長すぎます",
            location=ErrorLocation(line=1),
            context=ErrorContext(
                text="彼は朝早くから準備をして、そして駅に向かい、電車に乗って目的地に到着した。", surrounding_lines=[]
            ),
        )

    @pytest.fixture
    def abstract_emotion_error(self) -> QualityError:
        """抽象的感情表現エラーのサンプル"""
        return QualityError(
            code=ErrorCode("ABSTRACT_EMOTION"),
            severity=ErrorSeverity.WARNING,
            message="感情表現が抽象的です",
            location=ErrorLocation(line=1),
            context=ErrorContext(text="彼女は悲しかった。", surrounding_lines=[]),
        )

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-GENERATE_WITH_CONTEX")
    def test_generate_with_context_analysis(
        self, generator: ImprovementExampleGenerator, long_sentence_error: QualityError
    ) -> None:
        """コンテキスト分析付きの例生成テスト"""
        analysis = ErrorAnalysis(
            error_type="long_sentence", sentence_length=50, suggested_approach="文を分割する", split_points=[20, 35]
        )

        examples = generator.generate(long_sentence_error, max_examples=2, context_analysis=analysis)

        assert len(examples) > 0
        assert all(isinstance(ex, ImprovementExample) for ex in examples)
        assert examples[0].before == long_sentence_error.context.text

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-GENERATE_WITHOUT_CON")
    def test_generate_without_context_analysis(
        self, generator: ImprovementExampleGenerator, long_sentence_error: QualityError
    ) -> None:
        """コンテキスト分析なしの例生成テスト(自動分析)"""
        examples = generator.generate(long_sentence_error, max_examples=1)

        assert len(examples) > 0
        assert isinstance(examples[0], ImprovementExample)

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-GENERATE_LONG_SENTEN")
    def test_generate_long_sentence_examples_with_split_points(
        self, generator: ImprovementExampleGenerator, long_sentence_error: QualityError
    ) -> None:
        """分割点付き長文例の生成テスト"""
        analysis = ErrorAnalysis(error_type="long_sentence", sentence_length=50, split_points=[20])

        examples = generator._generate_long_sentence_examples(long_sentence_error, analysis, 2)

        assert len(examples) > 0
        # 分割された文に「。」が追加されているはず
        assert examples[0].after.count("。") > examples[0].before.count("。")
        assert "読みやすさを向上" in examples[0].explanation

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-GENERATE_LONG_SENTEN")
    def test_generate_long_sentence_examples_without_split_points(
        self, generator: ImprovementExampleGenerator, long_sentence_error: QualityError
    ) -> None:
        """分割点なし長文例の生成テスト"""
        analysis = ErrorAnalysis(error_type="long_sentence", sentence_length=50, split_points=[])

        examples = generator._generate_long_sentence_examples(long_sentence_error, analysis, 1)

        assert len(examples) > 0
        # 中央で分割されているはず
        assert "。" in examples[0].after

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-GENERATE_LONG_SENTEN")
    def test_generate_long_sentence_examples_with_conjunction_removal(
        self, generator: ImprovementExampleGenerator
    ) -> None:
        """接続詞除去を含む長文例の生成テスト"""
        text_with_conjunction = "彼は家を出た、そして駅に向かった、また電車に乗った。"
        error = QualityError(
            code=ErrorCode("LONG_SENTENCE"),
            severity=ErrorSeverity.WARNING,
            message="文が長すぎます",
            location=ErrorLocation(line=1),
            context=ErrorContext(text=text_with_conjunction, surrounding_lines=[]),
        )

        so_pos = text_with_conjunction.find("そして")
        analysis = ErrorAnalysis(
            error_type="long_sentence", sentence_length=len(text_with_conjunction), split_points=[so_pos]
        )

        examples = generator._generate_long_sentence_examples(error, analysis, 1)

        # 「そして」が除去され、適切に分割されているはず
        assert len(examples) > 0
        improved_text = examples[0].after
        assert improved_text.count("。") > text_with_conjunction.count("。")

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-GENERATE_EMOTION_EXA")
    def test_generate_emotion_examples_with_stored_examples(
        self, generator: ImprovementExampleGenerator, mock_example_repo: Mock, abstract_emotion_error: QualityError
    ) -> None:
        """保存済み例を使用した感情表現例の生成テスト"""
        # リポジトリに例を設定
        mock_example_repo.get_examples.return_value = [
            {"template": "目頭が熱くなり、喉の奥が締め付けられた。", "focus": "身体感覚で悲しみを表現"}
        ]

        analysis = ErrorAnalysis(error_type="abstract_emotion", emotion_word="悲しかった")

        examples = generator._generate_emotion_examples(abstract_emotion_error, analysis, 1)

        assert len(examples) > 0
        assert "目頭が熱くなり" in examples[0].after
        assert "身体感覚" in examples[0].explanation

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-GENERATE_EMOTION_EXA")
    def test_generate_emotion_examples_fallback_to_generic(
        self, generator: ImprovementExampleGenerator, abstract_emotion_error: QualityError
    ) -> None:
        """汎用例へのフォールバックテスト"""
        analysis = ErrorAnalysis(error_type="abstract_emotion", emotion_word="悲しかった")

        examples = generator._generate_emotion_examples(abstract_emotion_error, analysis, 1)

        # 少なくとも1つの例が生成される
        assert len(examples) > 0
        assert isinstance(examples[0], ImprovementExample)

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-GENERATE_GENERIC_EXA")
    def test_generate_generic_examples(
        self, generator: ImprovementExampleGenerator, long_sentence_error: QualityError
    ) -> None:
        """汎用例の生成テスト"""
        examples = generator._generate_generic_examples(long_sentence_error, 1)

        assert len(examples) == 1
        assert isinstance(examples[0], ImprovementExample)
        assert "一般的な表記規則" in examples[0].explanation

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-EXTRACT_BASE_EMOTION")
    def test_extract_base_emotion(self, generator: ImprovementExampleGenerator) -> None:
        """基本感情の抽出テスト"""
        test_cases = [
            ("悲しかった", "悲しい"),
            ("嬉しい", "嬉しい"),
            ("怒っている", "怒って"),
            ("楽しんだ", "楽しい"),
            ("寂しかった", "寂しい"),
            ("不明な感情", "不明な感情"),  # マッピングなし
        ]

        for emotion_word, expected in test_cases:
            result = generator._extract_base_emotion(emotion_word)
            assert result == expected

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-ADJUST_TO_CONTEXT_FI")
    def test_adjust_to_context_first_person(self, generator: ImprovementExampleGenerator) -> None:
        """一人称コンテキストへの調整テスト"""
        template = "彼は立ち上がった。"
        context = ErrorContext(text="私は疲れていた。", surrounding_lines=[])

        adjusted = generator._adjust_to_context(template, context)

        assert adjusted == "私は立ち上がった。"

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-ADJUST_TO_CONTEXT_FE")
    def test_adjust_to_context_female_third_person(self, generator: ImprovementExampleGenerator) -> None:
        """三人称女性コンテキストへの調整テスト"""
        template = "彼は立ち上がった。"
        context = ErrorContext(text="彼女は座っていた。", surrounding_lines=[])

        adjusted = generator._adjust_to_context(template, context)

        assert adjusted == "彼女は立ち上がった。"

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-CREATE_GENERIC_EMOTI")
    def test_create_generic_emotion_example(self, generator: ImprovementExampleGenerator) -> None:
        """汎用感情例の作成テスト"""
        test_cases = [
            ("悲しかった", "目頭が熱くなり"),
            ("嬉しかった", "心臓が軽く跳ね"),
            ("怒っていた", "こめかみに血管が浮き"),
            ("楽しかった", "胸の奥から温かい"),
            ("不明な感情", None),  # パターンなし
        ]

        for emotion_word, expected_phrase in test_cases:
            result = generator._create_generic_emotion_example("テスト文", emotion_word)

            if expected_phrase:
                assert result is not None
                assert expected_phrase in result.after
                assert "身体の反応として描写" in result.explanation
            else:
                assert result is None

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_SERVICES-CREATE_GENERIC_EMOTI")
    def test_create_generic_emotion_example_none_emotion(self, generator: ImprovementExampleGenerator) -> None:
        """感情語なしでの汎用例作成テスト"""
        result = generator._create_generic_emotion_example("テスト文", None)
        assert result is None
