"""エラーメッセージ具体化システムのテストケース

TDD原則に従い、まず失敗するテストを作成
具体的な改善例を含むエラーメッセージの生成をテスト


仕様書: SPEC-DOMAIN-SERVICES
"""

import sys
import unittest
from pathlib import Path

import pytest

# プロジェクトルートへのパスを追加
# PathManager統一パス管理システムを使用(事前にパスを設定)
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/を追加
from noveler.infrastructure.utils.path_manager import ensure_imports

ensure_imports()

# まだ存在しないモジュールをインポート(REDフェーズ)
from noveler.domain.error_messages.entities import ConcreteErrorMessage, ErrorContext, ErrorSeverity, QualityError
from noveler.domain.error_messages.services import ErrorContextAnalyzer, ImprovementExampleGenerator
from noveler.domain.error_messages.value_objects import ErrorCode, ErrorLocation, ImprovementExample


class TestQualityError(unittest.TestCase):
    """品質エラーエンティティのテスト"""

    @pytest.mark.spec("SPEC-CONCRETE_ERROR_MESSAGES-CREATE_QUALITY_ERROR")
    def test_create_quality_error(self) -> None:
        """品質エラーの作成"""
        error = QualityError(
            code=ErrorCode("E001"),
            severity=ErrorSeverity.ERROR,
            message="文章が長すぎます",
            location=ErrorLocation(line=10, column=0),
            context=ErrorContext(
                text="これは非常に長い文章で、読者にとって理解しにくい可能性があり、また文章のリズムも悪くなってしまうため、適切に分割することが推奨されます。",
                surrounding_lines=["前の文。", "次の文。"],
            ),
        )

        assert error.code.value == "E001"
        assert error.severity == ErrorSeverity.ERROR
        assert error.location.line == 10
        assert "長い文章" in error.context.text

    @pytest.mark.spec("SPEC-CONCRETE_ERROR_MESSAGES-ERROR_SEVERITY_LEVEL")
    def test_error_severity_levels(self) -> None:
        """エラー重要度レベル"""
        assert ErrorSeverity.ERROR.value == "error"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.INFO.value == "info"


class TestConcreteErrorMessage(unittest.TestCase):
    """具体的エラーメッセージのテスト"""

    @pytest.mark.spec("SPEC-CONCRETE_ERROR_MESSAGES-CREATE_CONCRETE_MESS")
    def test_create_concrete_message_with_examples(self) -> None:
        """改善例を含む具体的メッセージの作成"""
        error = QualityError(
            code=ErrorCode("E002"),
            severity=ErrorSeverity.WARNING,
            message="感情表現が抽象的です",
            location=ErrorLocation(line=15, column=20),
            context=ErrorContext(
                text="彼は悲しかった。",
                surrounding_lines=["状況説明の文。", "次の行動。"],
            ),
        )

        examples = [
            ImprovementExample(
                before="彼は悲しかった。",
                after="胸の奥が締め付けられ、視界が滲んだ。",
                explanation="感情を身体感覚で表現することで読者の共感を深める",
            ),
            ImprovementExample(
                before="彼は悲しかった。",
                after="唇を噛みしめ、拳を握りしめた。誰にも涙は見せまいと。",
                explanation="行動と内面の葛藤を描写して感情を表現",
            ),
        ]

        concrete_msg = ConcreteErrorMessage(
            error=error,
            improvement_examples=examples,
            general_advice="感情は『説明』ではなく『描写』で表現しましょう。",
        )

        assert len(concrete_msg.improvement_examples) == 2
        assert "身体感覚" in concrete_msg.improvement_examples[0].explanation
        assert "描写" in concrete_msg.general_advice

    @pytest.mark.spec("SPEC-CONCRETE_ERROR_MESSAGES-FORMAT_CONCRETE_MESS")
    def test_format_concrete_message(self) -> None:
        """具体的メッセージのフォーマット"""
        error = QualityError(
            code=ErrorCode("E003"),
            severity=ErrorSeverity.ERROR,
            message="会話文の文末に句点があります",
            location=ErrorLocation(line=20, column=15),
            context=ErrorContext(
                text="「こんにちは。」",
                surrounding_lines=[],
            ),
        )

        example = ImprovementExample(
            before="「こんにちは。」",
            after="「こんにちは」",
            explanation="会話文の文末に句点は不要です",
        )

        concrete_msg = ConcreteErrorMessage(
            error=error,
            improvement_examples=[example],
            general_advice="会話文は自然な話し言葉として表現しましょう。",
        )

        formatted = concrete_msg.format()

        assert "E003" in formatted
        assert "行20" in formatted
        assert "現在:" in formatted
        assert "改善例:" in formatted
        assert "理由:" in formatted


class TestErrorContextAnalyzer(unittest.TestCase):
    """エラーコンテキスト分析サービスのテスト"""

    @pytest.mark.spec("SPEC-CONCRETE_ERROR_MESSAGES-ANALYZE_LONG_SENTENC")
    def test_analyze_long_sentence_error(self) -> None:
        """長文エラーの分析"""
        analyzer = ErrorContextAnalyzer()

        error = QualityError(
            code=ErrorCode("E001"),
            severity=ErrorSeverity.ERROR,
            message="文章が長すぎます(150文字以上)",
            location=ErrorLocation(line=5, column=0),
            context=ErrorContext(
                text="これは非常に長い文章で、読者にとって理解しにくい可能性があり、また文章のリズムも悪くなってしまうため、適切に分割することが推奨されますが、どのように分割すればよいかわからない場合もあるでしょう。",
                surrounding_lines=[],
            ),
        )

        analysis = analyzer.analyze(error)

        assert analysis.error_type == "long_sentence"
        assert analysis.sentence_length == 97  # 実際の文字数に合わせて修正
        assert "分割" in analysis.suggested_approach
        assert len(analysis.split_points) > 0

    @pytest.mark.spec("SPEC-CONCRETE_ERROR_MESSAGES-ANALYZE_ABSTRACT_EMO")
    def test_analyze_abstract_emotion_error(self) -> None:
        """抽象的感情表現エラーの分析"""
        analyzer = ErrorContextAnalyzer()

        error = QualityError(
            code=ErrorCode("E002"),
            severity=ErrorSeverity.WARNING,
            message="感情表現が抽象的です",
            location=ErrorLocation(line=10, column=0),
            context=ErrorContext(
                text="彼女は嬉しかった。",
                surrounding_lines=["プレゼントを受け取った。", "笑顔を見せた。"],
            ),
        )

        analysis = analyzer.analyze(error)

        assert analysis.error_type == "abstract_emotion"
        assert analysis.emotion_word == "嬉しかった"
        assert "身体感覚" in analysis.suggested_approach


class TestImprovementExampleGenerator(unittest.TestCase):
    """改善例生成サービスのテスト"""

    def setUp(self) -> None:
        """テスト用リポジトリのモック設定"""
        self.pattern_repo = MockErrorPatternRepository()
        self.example_repo = MockExampleRepository()
        self.generator = ImprovementExampleGenerator(
            self.pattern_repo,
            self.example_repo,
        )

    @pytest.mark.spec("SPEC-CONCRETE_ERROR_MESSAGES-GENERATE_EXAMPLES_FO")
    def test_generate_examples_for_long_sentence(self) -> None:
        """長文に対する改善例生成"""
        error = QualityError(
            code=ErrorCode("E001"),
            severity=ErrorSeverity.ERROR,
            message="文章が長すぎます",
            location=ErrorLocation(line=5, column=0),
            context=ErrorContext(
                text="彼は朝起きてから顔を洗い、朝食を食べ、着替えをして、鞄を持って、靴を履いて、ドアの鍵をかけて、駅に向かって歩き始めた。",
                surrounding_lines=[],
            ),
        )

        examples = self.generator.generate(error, max_examples=2)

        assert len(examples) == 2
        assert all(isinstance(ex, ImprovementExample) for ex in examples)

        # 最初の例は文を分割している
        assert "。" in examples[0].after
        assert len(examples[0].after.split("。")[0]) < len(error.context.text)

    @pytest.mark.spec("SPEC-CONCRETE_ERROR_MESSAGES-GENERATE_EXAMPLES_FO")
    def test_generate_examples_for_emotion(self) -> None:
        """感情表現に対する改善例生成"""
        error = QualityError(
            code=ErrorCode("E002"),
            severity=ErrorSeverity.WARNING,
            message="感情表現が抽象的です",
            location=ErrorLocation(line=10, column=0),
            context=ErrorContext(
                text="彼は怒っていた。",
                surrounding_lines=[],
            ),
        )

        examples = self.generator.generate(error, max_examples=3)

        assert len(examples) > 0

        # 生成された例が身体描写を含むか確認
        body_descriptions = ["顔", "拳", "歯", "眉", "肩"]
        for example in examples:
            has_body_description = any(word in example.after for word in body_descriptions)
            assert has_body_description, f"改善例に身体描写が含まれていません: {example.after}"


# モッククラス(REDフェーズではこれらも仮実装)
class MockErrorPatternRepository:
    """エラーパターンリポジトリのモック"""

    def get_pattern(self, error_code: str) -> dict:
        patterns = {
            "E001": {
                "type": "long_sentence",
                "threshold": 150,
                "split_keywords": ["そして", "また", "さらに", "しかし"],
            },
            "E002": {
                "type": "abstract_emotion",
                "emotion_words": ["悲しい", "嬉しい", "怒って", "楽しい"],
                "approach": "show_dont_tell",
            },
        }
        return patterns.get(error_code, {})


class MockExampleRepository:
    """改善例リポジトリのモック"""

    def get_examples(self, error_type: str, emotion: str | None = None) -> list[dict]:
        examples = {
            "long_sentence": [
                {
                    "approach": "split_by_action",
                    "template": "動作ごとに文を分割",
                },
                {
                    "approach": "focus_important",
                    "template": "重要な動作に焦点を当てる",
                },
            ],
            "abstract_emotion": {
                "怒って": [
                    {
                        "template": "顔が真っ赤に染まり、拳を握りしめた。",
                        "focus": "身体反応",
                    },
                    {
                        "template": "歯を食いしばり、肩が小刻みに震えた。",
                        "focus": "緊張と震え",
                    },
                ],
            },
        }

        if error_type == "abstract_emotion" and emotion:
            # 基本感情を抽出
            base_emotions = ["悲しい", "嬉しい", "怒って", "楽しい"]
            for base in base_emotions:
                if base in emotion or emotion in base:
                    return examples.get(error_type, {}).get("怒って", [])
        return examples.get(error_type, [])


class TestErrorMessageIntegration(unittest.TestCase):
    """統合テスト"""

    @pytest.mark.spec("SPEC-CONCRETE_ERROR_MESSAGES-COMPLETE_ERROR_PROCE")
    def test_complete_error_processing_flow(self) -> None:
        """エラー処理の完全なフロー"""
        # エラーの作成
        error = QualityError(
            code=ErrorCode("E002"),
            severity=ErrorSeverity.WARNING,
            message="感情表現が抽象的です",
            location=ErrorLocation(line=25, column=0),
            context=ErrorContext(
                text="主人公は悲しかった。",
                surrounding_lines=["別れの言葉を聞いた後、", "部屋を出て行った。"],
            ),
        )

        # コンテキスト分析
        analyzer = ErrorContextAnalyzer()
        analysis = analyzer.analyze(error)

        # 改善例生成
        pattern_repo = MockErrorPatternRepository()
        example_repo = MockExampleRepository()
        generator = ImprovementExampleGenerator(pattern_repo, example_repo)
        examples = generator.generate(error, context_analysis=analysis)

        # 具体的メッセージ作成
        concrete_msg = ConcreteErrorMessage(
            error=error,
            improvement_examples=examples,
            general_advice="感情は読者に『感じさせる』ものです。説明ではなく描写で表現しましょう。",
        )

        # フォーマット出力
        output = concrete_msg.format()

        # 検証
        assert "E002" in output
        assert "行25" in output
        assert "現在: 主人公は悲しかった。" in output
        assert "改善例:" in output
        assert "理由:" in output
        assert "💡 ヒント:" in output


if __name__ == "__main__":
    unittest.main()
