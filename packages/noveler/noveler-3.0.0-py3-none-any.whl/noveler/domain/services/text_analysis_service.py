"""テキスト分析サービス

SPEC-COUNT-001: Unicode文字数詳細分析機能
Functional Core（純粋関数）として実装
"""

import hashlib
import re

from noveler.domain.value_objects.text_analysis_result import (
    CharacterBreakdown,
    LineInfo,
    ParagraphInfo,
    QualityWarning,
    SentenceInfo,
    TextAnalysisResult,
)
from noveler.domain.writing.value_objects.word_count import WordCount


class TextAnalysisService:
    """テキスト分析サービス

    Functional Core - すべて純粋関数として実装
    副作用なし、決定論的、完全にテスト可能
    """

    def analyze_text(
        self,
        text: str,
        warn_long_line: int = 40,
        warn_long_sentence: int = 100
    ) -> TextAnalysisResult:
        """テキストを分析（純粋関数）

        Args:
            text: 分析対象テキスト
            warn_long_line: 長い行の警告閾値
            warn_long_sentence: 長い文の警告閾値

        Returns:
            TextAnalysisResult: 分析結果
        """
        # 空文字列または空白のみの場合
        if not text or not text.strip():
            return self._create_empty_result()

        # 各構造要素を分析
        lines = self._analyze_lines(text)
        sentences = self._analyze_sentences(text)
        paragraphs = self._analyze_paragraphs(text, sentences)
        breakdown = self._count_character_types(text)
        warnings = self._check_quality(lines, sentences, warn_long_line, warn_long_sentence)

        # Unicode対応の正確な文字数を計算
        word_count = WordCount.from_japanese_text(text)

        return TextAnalysisResult(
            total_characters=word_count.value,
            total_lines=len(lines),
            total_sentences=len(sentences),
            total_paragraphs=len(paragraphs),
            breakdown=breakdown,
            lines=lines,
            sentences=sentences,
            paragraphs=paragraphs,
            quality_warnings=warnings
        )

    def _create_empty_result(self) -> TextAnalysisResult:
        """空テキスト用の結果を作成"""
        return TextAnalysisResult(
            total_characters=0,
            total_lines=0,
            total_sentences=0,
            total_paragraphs=0,
            breakdown=CharacterBreakdown(),
            lines=[],
            sentences=[],
            paragraphs=[],
            quality_warnings=[]
        )

    def _analyze_lines(self, text: str) -> list[LineInfo]:
        """行ごとの分析（純粋関数）"""
        lines = text.split("\n")
        result = []

        for idx, line in enumerate(lines):
            # 行ごとの正確な文字数を計算
            line_word_count = WordCount.from_display_length(line)

            line_info = LineInfo(
                id=self._generate_hash(line, idx),
                line_number=idx + 1,
                text=line,
                char_count=line_word_count.value,
                is_empty=len(line.strip()) == 0
            )
            result.append(line_info)

        return result

    def _analyze_sentences(self, text: str) -> list[SentenceInfo]:
        """文ごとの分析（純粋関数）"""
        # 句点で分割（。！？）
        sentence_pattern = r"([^。！？]*[。！？])"
        matches = re.findall(sentence_pattern, text)

        result = []
        sentence_number = 1

        for match in matches:
            if match.strip():  # 空でない文のみ
                # 終端記号を特定
                terminator = match[-1] if match and match[-1] in "。！？" else ""

                sentence_info = SentenceInfo(
                    id=self._generate_hash(match, sentence_number - 1),
                    sentence_number=sentence_number,
                    text=match,
                    char_count=len(match),
                    start_line=self._find_line_number(text, match, sentence_number),
                    end_line=self._find_line_number(text, match, sentence_number),
                    terminator=terminator
                )
                result.append(sentence_info)
                sentence_number += 1

        return result

    def _analyze_paragraphs(self, text: str, sentences: list[SentenceInfo]) -> list[ParagraphInfo]:
        """段落ごとの分析（純粋関数）"""
        if not text.strip():
            return []

        # 空行で分割して段落を特定
        paragraphs = text.split("\n\n")
        result = []

        for idx, paragraph_text in enumerate(paragraphs):
            if paragraph_text.strip():  # 空でない段落のみ
                # この段落に含まれる文の数を計算
                paragraph_sentences = [s for s in sentences if s.text in paragraph_text]

                # 段落の正確な文字数を計算
                paragraph_word_count = WordCount.from_japanese_text(paragraph_text)

                paragraph_info = ParagraphInfo(
                    id=self._generate_hash(paragraph_text, idx),
                    paragraph_number=len(result) + 1,  # 実際の段落番号
                    char_count=paragraph_word_count.value,
                    sentence_count=len(paragraph_sentences),
                    line_count=paragraph_text.count("\n") + 1
                )
                result.append(paragraph_info)

        return result

    def _count_character_types(self, text: str) -> CharacterBreakdown:
        """文字種別をカウント（純粋関数）"""
        hiragana = katakana = kanji = alphabet = numbers = punctuation = whitespace = other = 0

        for char in text:
            if self._is_hiragana(char):
                hiragana += 1
            elif self._is_katakana(char):
                katakana += 1
            elif self._is_kanji(char):
                kanji += 1
            elif char.isalpha():
                alphabet += 1
            elif char.isdigit():
                numbers += 1
            elif self._is_punctuation(char):
                punctuation += 1
            elif char.isspace():
                whitespace += 1
            else:
                other += 1

        return CharacterBreakdown(
            hiragana=hiragana,
            katakana=katakana,
            kanji=kanji,
            alphabet=alphabet,
            numbers=numbers,
            punctuation=punctuation,
            whitespace=whitespace,
            other=other
        )

    def _check_quality(
        self,
        lines: list[LineInfo],
        sentences: list[SentenceInfo],
        warn_long_line: int,
        warn_long_sentence: int
    ) -> list[QualityWarning]:
        """品質チェック（純粋関数）"""
        warnings = []

        # 長い行のチェック
        for line in lines:
            if line.char_count > warn_long_line and not line.is_empty:
                warning = QualityWarning(
                    type="long_line",
                    target_id=line.id,
                    message=f"行{line.line_number}: {line.char_count}文字（推奨: {warn_long_line}文字以内）",
                    severity="warning"
                )
                warnings.append(warning)

        # 長い文のチェック
        for sentence in sentences:
            if sentence.char_count > warn_long_sentence:
                warning = QualityWarning(
                    type="long_sentence",
                    target_id=sentence.id,
                    message=f"文が{sentence.char_count}文字です（推奨: {warn_long_sentence}文字以内）",
                    severity="warning"
                )
                warnings.append(warning)

        return warnings

    def _generate_hash(self, text: str, index: int) -> str:
        """ハッシュIDを生成（純粋関数）"""
        # テキスト内容とインデックスを組み合わせて一意性を保証
        source = f"{text}_{index}"
        # セキュリティ用途ではないため、sha1を使用（高速かつ十分）
        hash_obj = hashlib.sha1(source.encode("utf-8")).hexdigest()
        return hash_obj[:8]  # 先頭8文字

    def _find_line_number(self, text: str, sentence: str, sentence_number: int) -> int:
        """文が含まれる行番号を推定（純粋関数）"""
        # 簡易実装：文の位置から行番号を推定
        pos = text.find(sentence)
        if pos == -1:
            return sentence_number  # 見つからない場合は文番号と同じにする

        return text[:pos].count("\n") + 1

    def _is_hiragana(self, char: str) -> bool:
        """ひらがな判定（純粋関数）"""
        return "\u3040" <= char <= "\u309F"

    def _is_katakana(self, char: str) -> bool:
        """カタカナ判定（純粋関数）"""
        return "\u30A0" <= char <= "\u30FF"

    def _is_kanji(self, char: str) -> bool:
        """漢字判定（純粋関数）"""
        return "\u4E00" <= char <= "\u9FAF"

    def _is_punctuation(self, char: str) -> bool:
        """句読点・記号判定（純粋関数）"""
        punctuation_chars = "。！？、．，：；「」『』（）〔〕［］｛｝〈〉《》【】"
        return char in punctuation_chars or (not char.isalnum() and not char.isspace())
