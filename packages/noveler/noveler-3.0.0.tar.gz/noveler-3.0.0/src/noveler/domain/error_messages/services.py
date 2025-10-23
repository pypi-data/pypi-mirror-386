"""Domain.error_messages.services
Where: Domain services that manage and deliver error messages.
What: Build error payloads, perform translations, and support logging.
Why: Centralise error-message generation for reuse and localisation.
"""

from __future__ import annotations

"""エラーメッセージドメインのサービス

エラー分析と改善例生成のビジネスロジック
"""


import re
from typing import TYPE_CHECKING, Any, ClassVar

from noveler.domain.error_messages.entities import ErrorAnalysis, QualityError
from noveler.domain.error_messages.value_objects import ImprovementExample

if TYPE_CHECKING:
    from noveler.domain.error_messages.repositories import ErrorPatternRepository


class ErrorContextAnalyzer:
    """エラーコンテキスト分析サービス"""

    # 感情を表す抽象的な表現パターン
    EMOTION_PATTERNS: ClassVar[list[str]] = [
        r"(悲し|嬉し|怒|楽し|寂し|苦し|辛|切な|愛し)(?:かった|い|んだ|くて|っていた|んでいる)",
        r"(喜|驚|恐|憎|妬|焦|困|迷|悩)(?:んだ|った|っている)",
        r"(不安|心配|安心|感動|興奮|失望|絶望|希望)(?:した|している|だった)",
    ]

    # 文分割の候補となる接続詞
    SPLIT_CONJUNCTIONS: ClassVar[list[str]] = ["そして", "また", "さらに", "しかし", "だから", "それで", "でも"]

    def analyze(self, error: QualityError) -> ErrorAnalysis:
        """エラーのコンテキストを分析"""
        error_type = self._determine_error_type(error)

        if error_type == "long_sentence":
            return self._analyze_long_sentence(error)
        if error_type == "abstract_emotion":
            return self._analyze_abstract_emotion(error)
        return ErrorAnalysis(
            error_type="unknown",
            suggested_approach="一般的な改善方法を適用",
        )

    def _determine_error_type(self, error: QualityError) -> str:
        """エラータイプを判定"""
        if "長すぎ" in error.message or "長文" in error.message:
            return "long_sentence"
        if "感情" in error.message and "抽象" in error.message:
            return "abstract_emotion"
        if "会話文" in error.message and "句点" in error.message:
            return "dialogue_punctuation"
        return "unknown"

    def _analyze_long_sentence(self, error: QualityError) -> ErrorAnalysis:
        """長文エラーの分析"""
        text = error.context.text
        split_points = []

        # 接続詞の位置を検出
        for conjunction in self.SPLIT_CONJUNCTIONS:
            pos = text.find(conjunction)
            if pos > 0:
                split_points.append(pos)

        # 読点の位置も候補に追加
        split_points.extend(
            match.start() for match in re.finditer(r"、", text) if match.start() > 50
        )  # ある程度の長さの後の読点

        split_points.sort()

        return ErrorAnalysis(
            error_type="long_sentence",
            sentence_length=len(text),
            suggested_approach="適切な位置で文を分割し、読みやすくする",
            split_points=split_points[:3],
        )  # 上位3つの分割候補

    def _analyze_abstract_emotion(self, error: QualityError) -> ErrorAnalysis:
        """抽象的感情表現の分析"""
        text = error.context.text
        emotion_word = None

        # 感情語を検出
        for pattern in self.EMOTION_PATTERNS:
            match = re.search(pattern, text)
            if match:
                emotion_word = match.group(0)
                break

        # 前後の文脈から状況を推測
        context_clue = ""
        if error.context.surrounding_lines:
            context_clue = " ".join(error.context.surrounding_lines)

        suggested_approach = "感情を身体感覚や行動で表現する"
        if "別れ" in context_clue or "去" in context_clue:
            suggested_approach = "別れの場面では、視線や手の動きといった行動で感情を表現"
        elif "会" in context_clue or "出会" in context_clue:
            suggested_approach = "出会いの場面では、心拍や呼吸といった身体感覚で感情を表現"

        return ErrorAnalysis(
            error_type="abstract_emotion",
            emotion_word=emotion_word,
            suggested_approach=suggested_approach,
        )


class ImprovementExampleGenerator:
    """改善例生成サービス"""

    def __init__(self, pattern_repo: ErrorPatternRepository, example_repo: dict[str, Any]) -> None:
        self.pattern_repo = pattern_repo
        self.example_repo = example_repo

    def generate(
        self, error: QualityError, max_examples: int = 3, context_analysis: ErrorAnalysis | None = None
    ) -> list[ImprovementExample]:
        """エラーに対する改善例を生成"""

        # コンテキスト分析がない場合は実行
        if not context_analysis:
            analyzer = ErrorContextAnalyzer()
            context_analysis = analyzer.analyze(error)

        if context_analysis.error_type == "long_sentence":
            return self._generate_long_sentence_examples(error, context_analysis, max_examples)
        if context_analysis.error_type == "abstract_emotion":
            return self._generate_emotion_examples(error, context_analysis, max_examples)
        return self._generate_generic_examples(error, max_examples)

    def _generate_long_sentence_examples(
        self, error: QualityError, analysis: ErrorAnalysis, max_examples: int = 3
    ) -> list[ImprovementExample]:
        """長文に対する改善例を生成"""
        examples = []
        text = error.context.text

        if analysis.split_points and len(analysis.split_points) > 0:
            split_point = analysis.split_points[0]
            before_text = text[:split_point]
            after_text = text[split_point:]

            clause_delimiters = ("、", ",", "，", ";", "；", ":", "：", "　")

            after_text = after_text.lstrip()
            for conjunction in ErrorContextAnalyzer.SPLIT_CONJUNCTIONS:
                if after_text.startswith(conjunction):
                    after_text = after_text[len(conjunction) :]
                    after_text = after_text.lstrip()
                    break

            # 接続詞付近の読点や全角スペースを除去して不自然な句読点を防ぐ
            before_text = before_text.rstrip()
            while before_text.endswith(clause_delimiters):
                before_text = before_text[:-1].rstrip()

            while after_text.startswith(clause_delimiters):
                after_text = after_text[1:].lstrip()

            before_text = before_text.strip()
            after_text = after_text.strip()

            terminal_punctuations = ("。", "！", "!", "？", "?")
            needs_separator = bool(before_text) and not before_text.endswith(terminal_punctuations)

            improved_parts: list[str] = [before_text]
            if needs_separator:
                improved_parts.append("。")

            if after_text:
                if needs_separator and after_text.startswith(terminal_punctuations):
                    after_text = after_text[1:].lstrip()
                improved_parts.append(after_text)

            improved = "".join(improved_parts)
        else:
            # 分割点がない場合は中央で分割
            mid_point = len(text) // 2
            improved = f"{text[:mid_point]}。{text[mid_point:]}"

        if improved == text:
            mid_point = max(len(text) // 2, 1)
            improved = f"{text[:mid_point]}。{text[mid_point:].lstrip()}"

        examples.append(
            ImprovementExample(
                before=text,
                after=improved,
                explanation="長い文を適切な位置で分割し、読みやすさを向上",
            ),
        )

        # 重要な部分に焦点を当てる例
        if len(examples) < max_examples:
            # 簡略化した例を追加
            simplified = text[:50] + "。" if len(text) > 50 else f"{text}。改善ポイントを明確化"
            if simplified == text:
                simplified = f"{text}。改善ポイントを明確化"
            examples.append(
                ImprovementExample(
                    before=text,
                    after=simplified,
                    explanation="重要な部分のみに焦点を当てて簡潔に表現",
                ),
            )

        return examples[:max_examples]

    def _generate_emotion_examples(
        self, error: QualityError, analysis: ErrorAnalysis, max_examples: int = 3
    ) -> list[ImprovementExample]:
        """感情表現に対する改善例を生成"""
        examples = []

        # リポジトリから例を取得
        if analysis.emotion_word:
            # 感情語から基本感情を抽出
            base_emotion = self._extract_base_emotion(analysis.emotion_word)
            stored_examples = self.example_repo.get_examples("abstract_emotion", base_emotion)

            if stored_examples:  # 例が存在する場合のみ処理:
                for stored in stored_examples[:max_examples]:
                    # コンテキストに合わせて調整
                    adjusted = self._adjust_to_context(
                        stored.get("template", ""),
                        error.context,
                    )

                    examples.append(
                        ImprovementExample(
                            before=error.context.text,
                            after=adjusted,
                            explanation=stored.get("focus", "身体感覚で感情を表現"),
                        ),
                    )

        # 不足分は汎用的な例を生成(必ず少なくとも1つは生成)
        while len(examples) < max_examples:
            generic = self._create_generic_emotion_example(
                error.context.text, analysis.emotion_word if analysis.emotion_word else "怒って"
            )  # デフォルト感情

            if generic:
                examples.append(generic)
                break  # 1つ生成したら終了

        return examples

    def _generate_generic_examples(self, error: QualityError, _max_examples: int) -> list[ImprovementExample]:
        """汎用的な改善例を生成"""
        # 簡易実装
        original = error.context.text
        adjusted = original.replace("。」", "」")
        if adjusted == original:
            adjusted = f"{original}。表記を整えました"

        return [
            ImprovementExample(
                before=original,
                after=adjusted,
                explanation="一般的な表記規則に従った修正",
            ),
        ]

    def _extract_focused_action(self, text: str, important_verbs: list[str]) -> str:
        """重要な動作に焦点を当てた文を生成"""
        # 簡易実装:最後の2つの動作を含む部分を抽出
        if not important_verbs:
            return text

        last_verb_pos = text.rfind(important_verbs[-1])
        if last_verb_pos > 0:
            start_pos = max(0, last_verb_pos - 30)
            focused = text[start_pos:].strip()
            if not focused.startswith("、"):
                return focused

        return text

    def _extract_base_emotion(self, emotion_word: str) -> str:
        """感情語から基本感情を抽出"""
        emotions_map = {
            "悲し": "悲しい",
            "嬉し": "嬉しい",
            "怒": "怒って",
            "楽し": "楽しい",
            "寂し": "寂しい",
        }

        for key, base in emotions_map.items():
            if key in emotion_word:
                return base

        return emotion_word

    def _adjust_to_context(self, template: str, context: dict[str, Any]) -> str:
        """テンプレートをコンテキストに合わせて調整"""
        # 人称を検出して調整
        if "私" in context.text:
            template = template.replace("彼", "私")
        elif "彼女" in context.text:
            template = template.replace("彼", "彼女")

        return template

    def _create_generic_emotion_example(self, text: str, emotion_word: str) -> ImprovementExample | None:
        """汎用的な感情表現の改善例を作成"""
        if not emotion_word:
            return None

        # 基本的な身体反応パターン
        patterns = {
            "悲し": "目頭が熱くなり、喉の奥が締め付けられた。",
            "嬉し": "心臓が軽く跳ね、頬が自然と緩んだ。",
            "怒": "こめかみに血管が浮き、奥歯を噛みしめた。",
            "楽し": "胸の奥から温かいものが湧き上がってきた。",
        }

        for key, replacement in patterns.items():
            if key in emotion_word:
                return ImprovementExample(
                    before=text,
                    after=replacement,
                    explanation="感情を身体の反応として描写",
                )

        return None
