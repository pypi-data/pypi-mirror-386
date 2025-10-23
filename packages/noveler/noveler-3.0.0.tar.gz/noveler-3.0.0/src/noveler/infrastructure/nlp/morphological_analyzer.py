"""Infrastructure.nlp.morphological_analyzer
Where: Infrastructure module performing morphological analysis.
What: Wraps external analyzers to tokenise and tag text for downstream processing.
Why: Enables the platform to extract linguistic features consistently.
"""

from noveler.presentation.shared.shared_utilities import console

"形態素解析の共通モジュール\n小説執筆支援システム用\n\nこのモジュールは、janomeを使用した形態素解析の共通機能を提供します。\nすべての品質チェックツールから利用可能な統一インターフェースを提供し、\nフォールバック機能により、janomeが利用できない環境でも動作します。\n"
import re
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger

try:
    from janome.tokenizer import Tokenizer

    JANOME_AVAILABLE = True
except ImportError:
    JANOME_AVAILABLE = False
logger = get_logger(__name__)


class Token:
    """トークン情報を格納するクラス(janomeのToken互換)"""

    def __init__(self, surface: str, pos: str, pos_detail: str | None = None, base_form: str | None = None) -> None:
        self.surface = surface
        self.part_of_speech = pos_detail if pos_detail else pos
        self.base_form = base_form if base_form else surface
        pos_parts = self.part_of_speech.split(",")
        self.pos = pos_parts[0] if pos_parts else pos
        self.pos_detail1 = pos_parts[1] if len(pos_parts) > 1 else ""
        self.pos_detail2 = pos_parts[2] if len(pos_parts) > 2 else ""

    @property
    def __str__(self) -> str:
        """文字列表現"""
        return f"{self.surface}\t{self.part_of_speech}"


class MorphologicalAnalyzer:
    """形態素解析の共通機能を提供するクラス"""

    def __init__(self, logger_service: Any | None = None, console_service: Any | None = None) -> None:
        """初期化"""
        self.logger_service = logger_service or logger
        self.console_service = console_service or console
        self.tokenizer = None
        self.initialized = False
        if JANOME_AVAILABLE:
            try:
                self.tokenizer = Tokenizer()
                self.initialized = True
                self.logger_service.info("形態素解析器(janome)を初期化しました")
            except Exception as e:
                self.logger_service.warning("janomeの初期化に失敗しました: %s", e)
                self.initialized = False
        else:
            self.logger_service.warning("janomeが利用できません。フォールバックモードで動作します")
        self.pos_categories = {
            "noun": ["名詞"],
            "verb": ["動詞"],
            "adjective": ["形容詞", "形容動詞"],
            "adverb": ["副詞"],
            "particle": ["助詞"],
            "auxiliary_verb": ["助動詞"],
            "conjunction": ["接続詞"],
            "prefix": ["接頭詞"],
            "symbol": ["記号"],
            "other": ["その他", "感動詞", "フィラー", "連体詞"],
        }
        self.basic_vocabulary = {
            "pronouns": {
                "私": ("名詞", "代名詞"),
                "僕": ("名詞", "代名詞"),
                "俺": ("名詞", "代名詞"),
                "わたし": ("名詞", "代名詞"),
                "彼": ("名詞", "代名詞"),
                "彼女": ("名詞", "代名詞"),
            },
            "particles": {
                "は": ("助詞", "係助詞"),
                "が": ("助詞", "格助詞"),
                "を": ("助詞", "格助詞"),
                "に": ("助詞", "格助詞"),
                "で": ("助詞", "格助詞"),
                "と": ("助詞", "格助詞"),
                "から": ("助詞", "格助詞"),
                "まで": ("助詞", "副助詞"),
                "の": ("助詞", "連体化"),
            },
            "auxiliary_verbs": {
                "です": ("助動詞", "丁寧"),
                "ます": ("助動詞", "丁寧"),
                "だ": ("助動詞", "断定"),
                "である": ("助動詞", "断定"),
                "た": ("助動詞", "過去"),
                "ない": ("助動詞", "否定"),
            },
        }

    def analyze(self, text: str | None) -> list[Token]:
        """テキストを形態素解析してトークンのリストを返す

        Args:
            text: 解析対象のテキスト

        Returns:
            トークンのリスト
        """
        if text is None:
            return []
        if self.initialized and self.tokenizer:
            try:
                return list(self.tokenizer.tokenize(text))
            except Exception as e:
                self.logger_service.warning("janome解析エラー、フォールバックモードに切り替えます: %s", e)
                return self._fallback_analyze(text)
        else:
            return self._fallback_analyze(text)

    def _fallback_analyze(self, text: str) -> list[Token]:
        """janomeが使用できない場合のフォールバック解析

        基本的な正規表現とルールベースで簡易的な形態素解析を行う
        """
        if text is None or text == "":
            return []
        tokens = []
        parts = re.split("([。、!?「」『』()\\s]+)", text)
        for part in parts:
            if not part:
                continue
            if re.match("^[。、!?「」『』()\\s]+$", part):
                tokens.extend(Token(char, "記号", "記号,一般,*,*,*,*") for char in part if char.strip())
                continue
            words = self._simple_word_segmentation(part)
            for word in words:
                pos_info = self._estimate_pos(word)
                tokens.append(Token(word, pos_info[0], pos_info[1]))
        return tokens

    def _simple_word_segmentation(self, text: str) -> list[str]:
        """簡易的な単語分割(フォールバック用)"""
        words = []
        current_word = ""
        for _i, char in enumerate(text):
            current_word += char
            if char in self.basic_vocabulary["particles"]:
                if len(current_word) > 1:
                    words.append(current_word)
                words.append(char)
                current_word = ""
            elif len(current_word) > 4 and all(self._is_hiragana(c) for c in current_word):
                words.append(current_word)
                current_word = ""
        if current_word:
            words.append(current_word)
        return words

    def _estimate_pos(self, word: str) -> tuple[str, str]:
        """単語の品詞を推定(フォールバック用)"""
        for _category, words_dict in [
            ("pronouns", self.basic_vocabulary["pronouns"]),
            ("particles", self.basic_vocabulary["particles"]),
            ("auxiliary_verbs", self.basic_vocabulary["auxiliary_verbs"]),
        ]:
            if word in words_dict:
                return words_dict[word]
        if self._is_hiragana(word):
            if len(word) == 1:
                return ("助詞", "助詞,*,*,*,*,*")
            return ("動詞", "動詞,*,*,*,*,*")
        if self._is_katakana(word) or self._is_kanji(word):
            return ("名詞", "名詞,一般,*,*,*,*")
        return ("名詞", "名詞,一般,*,*,*,*")

    def _is_hiragana(self, text: str) -> bool:
        """ひらがなかどうか判定"""
        return all("\u3040" <= c <= "ゟ" for c in text)

    def _is_katakana(self, text: str) -> bool:
        """カタカナかどうか判定"""
        return all("゠" <= c <= "ヿ" for c in text)

    def _is_kanji(self, text: str) -> bool:
        """漢字かどうか判定"""
        return all("一" <= c <= "\u9fff" for c in text)

    def get_pos_distribution(self, text: str) -> dict[str, int]:
        """品詞の分布を取得

        Returns:
            品詞カテゴリごとのカウント辞書
        """
        tokens = self.analyze(text)
        distribution = dict.fromkeys(self.pos_categories, 0)
        for token in tokens:
            pos = token.part_of_speech.split(",")[0] if hasattr(token, "part_of_speech") else token.pos
            categorized = False
            for category, pos_list in self.pos_categories.items():
                if pos in pos_list:
                    distribution[category] += 1
                    categorized = True
                    break
            if not categorized:
                distribution["other"] += 1
        return distribution

    def extract_words_by_pos(self, text: str, pos_list: list[str]) -> list[tuple[str, str]]:
        """指定した品詞の単語を抽出

        Args:
            text: 解析対象テキスト
            pos_list: 抽出したい品詞のリスト

        Returns:
            (単語, 品詞)のタプルのリスト
        """
        tokens = self.analyze(text)
        words = []
        for token in tokens:
            pos = token.part_of_speech.split(",")[0] if hasattr(token, "part_of_speech") else token.pos
            if pos in pos_list:
                words.append((token.surface, pos))
        return words

    def get_sentence_endings(self, text: str) -> list[str]:
        """文末表現を抽出"""
        sentences = re.split("[。!?」]", text)
        endings = []
        for sentence in sentences:
            if not sentence.strip():
                continue
            tokens = self.analyze(sentence)
            if tokens:
                for token in reversed(tokens):
                    pos = token.part_of_speech.split(",")[0] if hasattr(token, "part_of_speech") else token.pos
                    if pos in ["動詞", "助動詞", "形容詞", "形容動詞"]:
                        endings.append(token.surface)
                        break
        return endings

    def analyze_politeness_level(self, text: str) -> dict[str, Any]:
        """敬語レベルを分析

        Returns:
            敬語レベルの分析結果
        """
        tokens = self.analyze(text)
        levels = {"casual": 0, "polite": 0, "respectful": 0, "humble": 0}
        politeness_markers = {
            "casual": ["だ", "である", "じゃん", "だよ", "だね"],
            "polite": ["です", "ます", "ございます"],
            "respectful": ["いらっしゃる", "おっしゃる", "なさる", "くださる"],
            "humble": ["いたす", "申す", "伺う", "参る"],
        }
        for token in tokens:
            for level, markers in politeness_markers.items():
                if token.surface in markers or token.base_form in markers:
                    levels[level] += 1
        total = sum(levels.values())
        if total > 0:
            dominant_level = max(levels, key=levels.get)
            consistency = levels[dominant_level] / total
        else:
            dominant_level = "neutral"
            consistency = 1.0
        return {"levels": levels, "dominant": dominant_level, "consistency": consistency, "total_markers": total}

    def calculate_readability_metrics(self, text: str) -> dict[str, float]:
        """読みやすさの指標を計算

        Returns:
            各種読みやすさ指標
        """
        tokens = self.analyze(text)
        total_tokens = len(tokens)
        if total_tokens == 0:
            return {
                "kanji_ratio": 0,
                "hiragana_ratio": 0,
                "katakana_ratio": 0,
                "avg_word_length": 0,
                "particle_ratio": 0,
            }
        kanji_count = 0
        hiragana_count = 0
        katakana_count = 0
        particle_count = 0
        total_chars = 0
        for token in tokens:
            total_chars += len(token.surface)
            pos = token.part_of_speech.split(",")[0] if hasattr(token, "part_of_speech") else token.pos
            if pos == "助詞":
                particle_count += 1
            for char in token.surface:
                if self._is_kanji(char):
                    kanji_count += 1
                elif self._is_hiragana(char):
                    hiragana_count += 1
                elif self._is_katakana(char):
                    katakana_count += 1
        return {
            "kanji_ratio": kanji_count / total_chars if total_chars > 0 else 0,
            "hiragana_ratio": hiragana_count / total_chars if total_chars > 0 else 0,
            "katakana_ratio": katakana_count / total_chars if total_chars > 0 else 0,
            "avg_word_length": total_chars / total_tokens,
            "particle_ratio": particle_count / total_tokens,
        }


def create_analyzer() -> MorphologicalAnalyzer:
    """形態素解析器のインスタンスを作成"""
    return MorphologicalAnalyzer()


def analyze_text(text: str) -> list[dict[str, Any]]:
    """テキストを解析して辞書形式で結果を返す

    Returns:
        各トークンの情報を含む辞書のリスト
    """
    analyzer = MorphologicalAnalyzer()
    tokens = analyzer.analyze(text)
    return [
        {"surface": token.surface, "pos": token.pos, "pos_detail": token.part_of_speech, "base_form": token.base_form}
        for token in tokens
    ]


if __name__ == "__main__":
    test_text = "私は今日、友達と一緒に公園へ行きました。とても楽しかったです。"
    analyzer = create_analyzer()
    console.print("=== 形態素解析テスト ===")
    console.print(f"janome利用可能: {analyzer.initialized}")
    console.print(f"\nテキスト: {test_text}")
    tokens = analyzer.analyze(test_text)
    console.print("\nトークン解析結果:")
    for i, token in enumerate(tokens):
        pos = token.part_of_speech.split(",")[0] if hasattr(token, "part_of_speech") else token.pos
        console.print(f"{i + 1}: {token.surface} ({pos})")
    console.print("\n品詞分布:")
    distribution = analyzer.get_pos_distribution(test_text)
    for pos, count in distribution.items():
        if count > 0:
            console.print(f"  {pos}: {count}件")
    console.print("\n敬語レベル分析:")
    politeness = analyzer.analyze_politeness_level(test_text)
    console.print(f"  主要レベル: {politeness['dominant']}")
    console.print(f"  一貫性: {politeness['consistency']:.2f}")
    console.print("\n読みやすさ指標:")
    metrics = analyzer.calculate_readability_metrics(test_text)
    console.print(f"  漢字率: {metrics['kanji_ratio']:.2f}")
    console.print(f"  ひらがな率: {metrics['hiragana_ratio']:.2f}")
    console.print(f"  助詞率: {metrics['particle_ratio']:.2f}")
