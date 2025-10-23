"""テキスト分析結果の値オブジェクト

SPEC-COUNT-001: Unicode文字数詳細分析機能
Functional Coreで使用するデータクラス群
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CharacterBreakdown:
    """文字種別内訳"""
    hiragana: int = 0      # ひらがな文字数
    katakana: int = 0      # カタカナ文字数
    kanji: int = 0         # 漢字文字数
    alphabet: int = 0      # アルファベット文字数
    numbers: int = 0       # 数字文字数
    punctuation: int = 0   # 句読点・記号文字数
    whitespace: int = 0    # 空白文字数
    other: int = 0         # その他文字数

@dataclass(frozen=True)
class LineInfo:
    """行情報"""
    id: str                # ハッシュID（MD5先頭8文字）
    line_number: int       # 行番号（1始まり）
    text: str             # テキスト内容
    char_count: int       # 文字数
    is_empty: bool        # 空行かどうか

@dataclass(frozen=True)
class SentenceInfo:
    """文情報"""
    id: str                   # ハッシュID
    sentence_number: int      # 文番号（1始まり）
    text: str                # 文内容
    char_count: int          # 文字数
    start_line: int          # 開始行
    end_line: int            # 終了行
    terminator: str          # 終端記号（。！？など）

@dataclass(frozen=True)
class ParagraphInfo:
    """段落情報"""
    id: str                  # ハッシュID
    paragraph_number: int    # 段落番号（1始まり）
    char_count: int         # 文字数
    sentence_count: int     # 文の数
    line_count: int         # 行数

@dataclass(frozen=True)
class QualityWarning:
    """品質警告"""
    type: str               # warning種別 (long_line, long_sentence, etc.)
    target_id: str          # 対象のハッシュID
    message: str            # 警告メッセージ
    severity: str           # 重要度（info/warning/error）

@dataclass(frozen=True)
class TextAnalysisResult:
    """テキスト分析結果

    Functional Coreの出力データ構造。
    全て不変データとして設計。
    """
    total_characters: int                    # 総文字数
    total_lines: int                        # 総行数
    total_sentences: int                    # 総文数
    total_paragraphs: int                   # 総段落数
    breakdown: CharacterBreakdown           # 文字種別内訳
    lines: list[LineInfo]                   # 行詳細情報
    sentences: list[SentenceInfo]           # 文詳細情報
    paragraphs: list[ParagraphInfo]         # 段落詳細情報
    quality_warnings: list[QualityWarning]  # 品質警告

    @property
    def average_line_length(self) -> float:
        """平均行文字数"""
        if self.total_lines == 0:
            return 0.0
        non_empty_lines = [line for line in self.lines if not line.is_empty]
        if not non_empty_lines:
            return 0.0
        total_chars = sum(line.char_count for line in non_empty_lines)
        return total_chars / len(non_empty_lines)

    @property
    def average_sentence_length(self) -> float:
        """平均文文字数"""
        if self.total_sentences == 0:
            return 0.0
        return sum(sentence.char_count for sentence in self.sentences) / self.total_sentences

    @property
    def max_line_length(self) -> int:
        """最長行の文字数"""
        if not self.lines:
            return 0
        return max(line.char_count for line in self.lines)

    @property
    def max_sentence_length(self) -> int:
        """最長文の文字数"""
        if not self.sentences:
            return 0
        return max(sentence.char_count for sentence in self.sentences)

    def get_line_by_id(self, line_id: str) -> LineInfo | None:
        """ハッシュIDで行を取得"""
        for line in self.lines:
            if line.id == line_id:
                return line
        return None

    def get_sentence_by_id(self, sentence_id: str) -> SentenceInfo | None:
        """ハッシュIDで文を取得"""
        for sentence in self.sentences:
            if sentence.id == sentence_id:
                return sentence
        return None

    def get_warnings_by_type(self, warning_type: str) -> list[QualityWarning]:
        """種別別の警告を取得"""
        return [warning for warning in self.quality_warnings if warning.type == warning_type]
