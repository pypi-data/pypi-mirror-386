#!/usr/bin/env python3
"""エラーメッセージドメインエンティティのテスト

TDD+DDD原則に基づく包括的なテストスイート


仕様書: SPEC-DOMAIN-ENTITIES
"""

import pytest
pytestmark = pytest.mark.error_messages

from noveler.domain.error_messages.entities import (
    ConcreteErrorMessage,
    ErrorAnalysis,
    ErrorContext,
    ErrorSeverity,
    QualityError,
)
from noveler.domain.error_messages.value_objects import ErrorCode, ErrorLocation, ImprovementExample


class TestErrorContext:
    """ErrorContextのテスト"""

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-ERROR_CONTEXT_CREATI")
    def test_error_context_creation(self) -> None:
        """エラーコンテキストの作成"""
        # Arrange
        text = "これは長すぎる文章です。"
        surrounding_lines = ["前の行", "後の行"]

        # Act
        context = ErrorContext(text=text, surrounding_lines=surrounding_lines)

        # Assert
        assert context.text == text
        assert context.surrounding_lines == surrounding_lines

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-ERROR_CONTEXT_GET_CO")
    def test_error_context_get_context_window_default(self) -> None:
        """デフォルトのコンテキストウィンドウ取得"""
        # Arrange
        context = ErrorContext(text="現在の行", surrounding_lines=["前の行1", "前の行2", "後の行1", "後の行2"])

        # Act
        window = context.get_context_window()

        # Assert
        expected = "前の行1\n前の行2\n現在の行\n後の行1\n後の行2"
        assert window == expected

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-ERROR_CONTEXT_GET_CO")
    def test_error_context_get_context_window_custom(self) -> None:
        """カスタムのコンテキストウィンドウ取得"""
        # Arrange
        context = ErrorContext(
            text="現在の行",
            surrounding_lines=["前の行1", "前の行2", "後の行1", "後の行2", "後の行3"],
        )

        # Act
        window = context.get_context_window(lines_before=1, lines_after=3)

        # Assert
        # 簡易実装では lines_before で前の行を取得し、lines_before以降を後の行として使用
        expected = "前の行1\n現在の行\n前の行2\n後の行1\n後の行2\n後の行3"
        assert window == expected

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-ERROR_CONTEXT_EMPTY_")
    def test_error_context_empty_surrounding_lines(self) -> None:
        """空の周辺行でのコンテキストウィンドウ取得"""
        # Arrange
        context = ErrorContext(text="現在の行", surrounding_lines=[])

        # Act
        window = context.get_context_window()

        # Assert
        assert window == "現在の行"


class TestQualityError:
    """QualityErrorのテスト"""

    def create_sample_quality_error(self, severity=ErrorSeverity.ERROR) -> QualityError:
        """サンプル品質エラーを作成"""
        return QualityError(
            code=ErrorCode("E001"),
            severity=severity,
            message="文章が長すぎます",
            location=ErrorLocation(line=10, column=5),
            context=ErrorContext(text="これは非常に長い文章です。", surrounding_lines=["前の行", "後の行"]),
        )

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-QUALITY_ERROR_CREATI")
    def test_quality_error_creation(self) -> None:
        """品質エラーの作成"""
        # Arrange
        code = ErrorCode("E001")
        severity = ErrorSeverity.ERROR
        message = "文章が長すぎます"
        location = ErrorLocation(line=10, column=5)
        context = ErrorContext(text="これは非常に長い文章です。", surrounding_lines=["前の行", "後の行"])

        # Act
        error = QualityError(code=code, severity=severity, message=message, location=location, context=context)

        # Assert
        assert error.code == code
        assert error.severity == severity
        assert error.message == message
        assert error.location == location
        assert error.context == context

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-QUALITY_ERROR_IS_ERR")
    def test_quality_error_is_error_true(self) -> None:
        """エラーレベルの判定(真)"""
        # Arrange
        error = self.create_sample_quality_error(ErrorSeverity.ERROR)

        # Act & Assert
        assert error.is_error() is True
        assert error.is_warning() is False

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-QUALITY_ERROR_IS_WAR")
    def test_quality_error_is_warning_true(self) -> None:
        """警告レベルの判定(真)"""
        # Arrange
        error = self.create_sample_quality_error(ErrorSeverity.WARNING)

        # Act & Assert
        assert error.is_error() is False
        assert error.is_warning() is True

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-QUALITY_ERROR_IS_INF")
    def test_quality_error_is_info_level(self) -> None:
        """情報レベルの判定"""
        # Arrange
        error = self.create_sample_quality_error(ErrorSeverity.INFO)

        # Act & Assert
        assert error.is_error() is False
        assert error.is_warning() is False

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-QUALITY_ERROR_GET_LI")
    def test_quality_error_get_line_preview_short(self) -> None:
        """短いテキストの行プレビュー取得"""
        # Arrange
        error = self.create_sample_quality_error()

        # Act
        preview = error.get_line_preview()

        # Assert
        assert preview == "これは非常に長い文章です。"

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-QUALITY_ERROR_GET_LI")
    def test_quality_error_get_line_preview_long(self) -> None:
        """長いテキストの行プレビュー取得(切り詰め)"""
        # Arrange
        long_text = "これは非常に長い文章です。" * 10  # 80文字を超える
        error = QualityError(
            code=ErrorCode("E001"),
            severity=ErrorSeverity.ERROR,
            message="文章が長すぎます",
            location=ErrorLocation(line=10, column=5),
            context=ErrorContext(text=long_text, surrounding_lines=[]),
        )

        # Act
        preview = error.get_line_preview()

        # Assert
        assert len(preview) == 80
        assert preview.endswith("...")
        assert preview.startswith("これは非常に長い文章です。")


class TestConcreteErrorMessage:
    """ConcreteErrorMessageのテスト"""

    def create_sample_concrete_error_message(self) -> ConcreteErrorMessage:
        """サンプル具体的エラーメッセージを作成"""
        error = QualityError(
            code=ErrorCode("E002"),
            severity=ErrorSeverity.WARNING,
            message="感情表現が抽象的です",
            location=ErrorLocation(line=5, column=10),
            context=ErrorContext(text="彼は悲しかった。", surrounding_lines=["前の行", "後の行"]),
        )

        examples = [
            ImprovementExample(
                before="彼は悲しかった。",
                after="目頭が熱くなり、視界が滲んだ。",
                explanation="感情を身体的な描写で表現",
            ),
            ImprovementExample(
                before="彼は悲しかった。",
                after="喉の奥が締め付けられ、言葉が出なかった。",
                explanation="感情を身体的な苦痛で表現",
            ),
        ]

        return ConcreteErrorMessage(
            error=error,
            improvement_examples=examples,
            general_advice="感情は『説明』ではなく『描写』で表現しましょう。",
        )

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-CONCRETE_ERROR_MESSA")
    def test_concrete_error_message_creation(self) -> None:
        """具体的エラーメッセージの作成"""
        # Act
        message = self.create_sample_concrete_error_message()

        # Assert
        assert message.error.code.value == "E002"
        assert len(message.improvement_examples) == 2
        assert message.general_advice == "感情は『説明』ではなく『描写』で表現しましょう。"

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-CONCRETE_ERROR_MESSA")
    def test_concrete_error_message_has_examples_true(self) -> None:
        """改善例の有無判定(真)"""
        # Arrange
        message = self.create_sample_concrete_error_message()

        # Act & Assert
        assert message.has_examples() is True

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-CONCRETE_ERROR_MESSA")
    def test_concrete_error_message_has_examples_false(self) -> None:
        """改善例の有無判定(偽)"""
        # Arrange
        message = self.create_sample_concrete_error_message()
        message.improvement_examples = []

        # Act & Assert
        assert message.has_examples() is False

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-CONCRETE_ERROR_MESSA")
    def test_concrete_error_message_get_primary_example(self) -> None:
        """主要な改善例の取得"""
        # Arrange
        message = self.create_sample_concrete_error_message()

        # Act
        primary = message.get_primary_example()

        # Assert
        assert primary is not None
        assert primary.before == "彼は悲しかった。"
        assert primary.after == "目頭が熱くなり、視界が滲んだ。"

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-CONCRETE_ERROR_MESSA")
    def test_concrete_error_message_get_primary_example_none(self) -> None:
        """改善例がない場合の主要な改善例取得"""
        # Arrange
        message = self.create_sample_concrete_error_message()
        message.improvement_examples = []

        # Act
        primary = message.get_primary_example()

        # Assert
        assert primary is None

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-CONCRETE_ERROR_MESSA")
    def test_concrete_error_message_format_error_level(self) -> None:
        """エラーレベルのフォーマット"""
        # Arrange
        message = self.create_sample_concrete_error_message()
        message.error.severity = ErrorSeverity.ERROR

        # Act
        formatted = message.format()

        # Assert
        assert "❌ E002: 感情表現が抽象的です" in formatted
        assert "行5: 彼は悲しかった。" in formatted
        assert "📝 改善例:" in formatted
        assert "例1:" in formatted
        assert "例2:" in formatted
        assert "💡 ヒント:" in formatted

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-CONCRETE_ERROR_MESSA")
    def test_concrete_error_message_format_warning_level(self) -> None:
        """警告レベルのフォーマット"""
        # Arrange
        message = self.create_sample_concrete_error_message()
        message.error.severity = ErrorSeverity.WARNING

        # Act
        formatted = message.format()

        # Assert
        assert "⚠️ E002: 感情表現が抽象的です" in formatted
        assert "行5: 彼は悲しかった。" in formatted

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-CONCRETE_ERROR_MESSA")
    def test_concrete_error_message_format_info_level(self) -> None:
        """情報レベルのフォーマット"""
        # Arrange
        message = self.create_sample_concrete_error_message()
        message.error.severity = ErrorSeverity.INFO

        # Act
        formatted = message.format()

        # Assert
        assert "ℹ️ E002: 感情表現が抽象的です" in formatted
        assert "行5: 彼は悲しかった。" in formatted

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-CONCRETE_ERROR_MESSA")
    def test_concrete_error_message_format_no_examples(self) -> None:
        """改善例がない場合のフォーマット"""
        # Arrange
        message = self.create_sample_concrete_error_message()
        message.improvement_examples = []

        # Act
        formatted = message.format()

        # Assert
        assert "⚠️ E002: 感情表現が抽象的です" in formatted  # WARNING level
        assert "行5: 彼は悲しかった。" in formatted
        assert "📝 改善例:" not in formatted
        assert "💡 ヒント:" in formatted

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-CONCRETE_ERROR_MESSA")
    def test_concrete_error_message_format_structure(self) -> None:
        """フォーマットの構造確認"""
        # Arrange
        message = self.create_sample_concrete_error_message()

        # Act
        formatted = message.format()
        lines = formatted.split("\n")

        # Assert
        # エラーヘッダー
        assert lines[0].startswith("⚠️ E002:")
        assert lines[1].startswith("   行5:")
        assert lines[2] == ""

        # 改善例セクション
        assert "📝 改善例:" in lines[3]

        # 一般的なアドバイス(最後の方にある)
        advice_found = False
        for line in lines:
            if line.startswith("💡 ヒント:"):
                advice_found = True
                break
        assert advice_found


class TestErrorAnalysis:
    """ErrorAnalysisのテスト"""

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-ERROR_ANALYSIS_CREAT")
    def test_error_analysis_creation_with_defaults(self) -> None:
        """デフォルト値でのエラー分析作成"""
        # Arrange & Act
        analysis = ErrorAnalysis(error_type="long_sentence")

        # Assert
        assert analysis.error_type == "long_sentence"
        assert analysis.sentence_length == 0
        assert analysis.emotion_word is None
        assert analysis.suggested_approach == ""
        assert analysis.split_points == []

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-ERROR_ANALYSIS_CREAT")
    def test_error_analysis_creation_with_values(self) -> None:
        """値指定でのエラー分析作成"""
        # Arrange & Act
        analysis = ErrorAnalysis(
            error_type="emotion_abstract",
            sentence_length=25,
            emotion_word="悲しい",
            suggested_approach="身体的描写に変更",
            split_points=[10, 20],
        )

        # Assert
        assert analysis.error_type == "emotion_abstract"
        assert analysis.sentence_length == 25
        assert analysis.emotion_word == "悲しい"
        assert analysis.suggested_approach == "身体的描写に変更"
        assert analysis.split_points == [10, 20]

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-ERROR_ANALYSIS_POST_")
    def test_error_analysis_post_init_default_split_points(self) -> None:
        """__post_init__でのsplit_pointsデフォルト値設定"""
        # Arrange & Act
        analysis = ErrorAnalysis(error_type="test", split_points=None)

        # Assert
        assert analysis.split_points == []

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-ERROR_ANALYSIS_COMPL")
    def test_error_analysis_complex_scenario(self) -> None:
        """複雑なエラー分析シナリオ"""
        # Arrange & Act
        analysis = ErrorAnalysis(
            error_type="complex_emotion",
            sentence_length=120,
            emotion_word="複雑な気持ち",
            suggested_approach="具体的な身体感覚と内面描写の組み合わせ",
            split_points=[30, 60, 90],
        )

        # Assert
        assert analysis.error_type == "complex_emotion"
        assert analysis.sentence_length == 120
        assert analysis.emotion_word == "複雑な気持ち"
        assert len(analysis.split_points) == 3
        assert analysis.split_points == [30, 60, 90]
        assert "具体的な身体感覚" in analysis.suggested_approach

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-ERROR_ANALYSIS_EMPTY")
    def test_error_analysis_empty_split_points(self) -> None:
        """空のsplit_pointsでのエラー分析"""
        # Arrange & Act
        analysis = ErrorAnalysis(error_type="simple_error", split_points=[])

        # Assert
        assert analysis.split_points == []

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-ERROR_ANALYSIS_MULTI")
    def test_error_analysis_multiple_emotion_words(self) -> None:
        """複数の感情語を含むエラー分析"""
        # Arrange & Act
        analysis = ErrorAnalysis(
            error_type="multiple_emotions",
            sentence_length=80,
            emotion_word="悲しく、怒り、困惑",
            suggested_approach="感情を段階的に描写",
            split_points=[20, 40, 60],
        )

        # Assert
        assert analysis.error_type == "multiple_emotions"
        assert "悲しく、怒り、困惑" in analysis.emotion_word
        assert len(analysis.split_points) == 3


class TestErrorDomainIntegration:
    """エラードメイン統合テスト"""

    @pytest.mark.spec("SPEC-ERROR_MESSAGES_ENTITIES-COMPLETE_ERROR_FLOW")
    def test_complete_error_flow(self) -> None:
        """完全なエラーフロー"""
        # Arrange: エラーコンテキスト作成
        context = ErrorContext(
            text="彼は非常に悲しかったが、それを表現する言葉が見つからなかった。",
            surrounding_lines=["前の段落の最後の行", "次の段落の最初の行"],
        )

        # Arrange: 品質エラー作成
        error = QualityError(
            code=ErrorCode("E002"),
            severity=ErrorSeverity.WARNING,
            message="感情表現が抽象的で、文章が長すぎます",
            location=ErrorLocation(line=15, column=1),
            context=context,
        )

        # Arrange: 改善例作成
        examples = [
            ImprovementExample(
                before="彼は非常に悲しかった",
                after="胸が締め付けられ、呼吸が浅くなった",
                explanation="感情を身体的な感覚で表現",
            ),
            ImprovementExample(
                before="それを表現する言葉が見つからなかった",
                after="口を開こうとしたが、喉が詰まったように声が出なかった",
                explanation="抽象的な状況を具体的な行動で表現",
            ),
        ]

        # Arrange: 具体的エラーメッセージ作成
        concrete_message = ConcreteErrorMessage(
            error=error,
            improvement_examples=examples,
            general_advice="感情は読者が感じられる具体的な描写で表現し、長い文は適切な位置で分割しましょう。",
        )

        # Act: フォーマット
        formatted = concrete_message.format()

        # Assert: 全体的な構造確認
        assert "⚠️ E002:" in formatted
        assert "感情表現が抽象的で、文章が長すぎます" in formatted
        assert "行15:" in formatted
        assert "彼は非常に悲しかったが、それを表現する言葉が見つからなかった。" in formatted
        assert "📝 改善例:" in formatted
        assert "例1:" in formatted
        assert "例2:" in formatted
        assert "💡 ヒント:" in formatted
        assert "感情は読者が感じられる具体的な描写で表現し" in formatted

        # Assert: エラー判定
        assert error.is_warning() is True
        assert error.is_error() is False

        # Assert: 改善例の有無
        assert concrete_message.has_examples() is True
        assert concrete_message.get_primary_example() is not None

        # Assert: エラー分析との連携
        analysis = ErrorAnalysis(
            error_type="emotion_and_length",
            sentence_length=len(context.text),
            emotion_word="悲しかった",
            suggested_approach="感情の具体的描写と文の分割",
            split_points=[20, 40],
        )

        assert analysis.error_type == "emotion_and_length"
        assert analysis.sentence_length > 30
        assert analysis.emotion_word == "悲しかった"
        assert len(analysis.split_points) == 2
