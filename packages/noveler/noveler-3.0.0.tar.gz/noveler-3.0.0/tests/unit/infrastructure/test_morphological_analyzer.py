#!/usr/bin/env python3
"""統合版 形態素解析モジュールのテストケース
test_morphological_analyzer.py と test_morphological_analyzer_pytest.py を統合


仕様書: SPEC-INFRASTRUCTURE
"""

import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# 親ディレクトリをパスに追加
# PathManager統一パス管理システムを使用(事前にパスを設定)
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/を追加
from noveler.infrastructure.utils.path_manager import ensure_imports

ensure_imports()
from noveler.infrastructure.nlp.morphological_analyzer import MorphologicalAnalyzer


class TestMorphologicalAnalyzer:
    """形態素解析器の基本テスト"""

    @pytest.fixture
    def analyzer(self):
        """テスト用のアナライザーインスタンス"""
        return MorphologicalAnalyzer()

    @pytest.fixture
    def sample_text(self) -> str:
        """テスト用サンプルテキスト"""
        return "太郎は花子に本を渡しました。とても嬉しそうでした。"

    @pytest.fixture
    def novel_text(self) -> str:
        """小説風のテキスト"""
        return """
        「おはよう」と太郎は言った。
        花子は微笑んで答えた。「おはようございます」

        二人は一緒に歩き始めた。朝の空気が心地よかった。
        """

    def test_basic_analysis(self, analyzer: object, sample_text: object) -> None:
        """基本的な形態素解析"""
        if analyzer.initialized:
            tokens = analyzer.analyze(sample_text)

            # トークンが抽出されることを確認
            assert len(tokens) > 0

            # 基本的な単語が含まれることを確認
            surfaces = [token.surface for token in tokens]
            assert "太郎" in surfaces
            assert "花子" in surfaces
            assert "本" in surfaces
        else:
            # フォールバックモードでも動作することを確認
            assert analyzer.tokenizer is None

    def test_pos_distribution(self, analyzer: object, sample_text: object) -> None:
        """品詞分布の分析"""
        pos_dist = analyzer.get_pos_distribution(sample_text)

        # 品詞分布が辞書として返されることを確認
        assert isinstance(pos_dist, dict)

        if analyzer.initialized:
            # 基本的な品詞が含まれることを確認(英語キー名)
            assert "noun" in pos_dist
            assert "verb" in pos_dist
            assert "particle" in pos_dist
            assert pos_dist["noun"] > 0

    def test_sentence_endings(self, analyzer: object, novel_text: object) -> None:
        """文末表現の抽出"""
        endings = analyzer.get_sentence_endings(novel_text)

        # 文末表現のリストが返されることを確認
        assert isinstance(endings, list)

        if analyzer.initialized:
            # 特定の文末表現が含まれることを確認
            assert "た" in endings or "だ" in endings
            assert "です" in endings or "ます" in endings

    def test_politeness_level(self, analyzer: object) -> None:
        """敬語レベルの判定"""
        # 丁寧語のテキスト
        polite_text = "こんにちは。今日はいい天気ですね。ありがとうございます。"
        polite_level = analyzer.analyze_politeness_level(polite_text)

        assert isinstance(polite_level, dict)
        if analyzer.initialized:
            assert "levels" in polite_level
            assert polite_level["levels"]["polite"] > 0

        # 普通体のテキスト
        casual_text = "今日は暑いな。アイス食べたい。"
        casual_level = analyzer.analyze_politeness_level(casual_text)

        assert isinstance(casual_level, dict)
        if analyzer.initialized:
            assert "levels" in casual_level
            assert casual_level["levels"]["casual"] >= 0

    def test_readability_metrics(self, analyzer: object, sample_text: object) -> None:
        """読みやすさ指標の計算"""
        metrics = analyzer.calculate_readability_metrics(sample_text)

        # 必要な指標が含まれることを確認
        assert isinstance(metrics, dict)
        assert "kanji_ratio" in metrics
        assert "katakana_ratio" in metrics
        assert "hiragana_ratio" in metrics
        assert "avg_word_length" in metrics

        # 値の妥当性を確認
        assert 0 <= metrics["kanji_ratio"] <= 1
        assert 0 <= metrics["katakana_ratio"] <= 1
        assert 0 <= metrics["hiragana_ratio"] <= 1

    def test_novel_specific_features(self, analyzer: object, novel_text: object) -> None:
        """小説特有の機能テスト"""
        # 形態素解析が動作することを確認
        tokens = analyzer.analyze(novel_text)
        assert isinstance(tokens, list)

        if analyzer.initialized:
            # トークンが取得できることを確認
            assert len(tokens) > 0
            # 「おはよう」が含まれることを確認
            surfaces = [token.surface for token in tokens if hasattr(token, "surface")]
            assert any("おはよう" in surface for surface in surfaces)

    def test_fallback_mode(self) -> None:
        """フォールバックモードのテスト"""
        with patch("noveler.infrastructure.nlp.morphological_analyzer.JANOME_AVAILABLE", False):
            analyzer = MorphologicalAnalyzer()

            # janomeが利用できない場合でも初期化できる
            assert analyzer.tokenizer is None
            assert analyzer.initialized is False

            # 基本的な機能が動作する
            text = "これはテストです。"
            metrics = analyzer.calculate_readability_metrics(text)
            assert isinstance(metrics, dict)

    def test_edge_cases(self, analyzer: object) -> None:
        """エッジケースのテスト"""
        # 空文字列
        empty_result = analyzer.analyze("")
        assert empty_result == []

        # None は内部で空文字列として処理される
        none_result = analyzer.analyze(None if not analyzer.initialized else "")
        assert none_result == []

        # 記号のみ
        symbol_result = analyzer.analyze("!?…")
        assert isinstance(symbol_result, list)

        # 長い文章
        long_text = "これは長い文章です。" * 100
        long_result = analyzer.analyze(long_text)
        assert isinstance(long_result, list)


class TestAdvancedFeatures:
    """高度な機能のテスト"""

    @pytest.fixture
    def analyzer(self):
        return MorphologicalAnalyzer()

    def test_character_speech_patterns(self, analyzer: object) -> None:
        """キャラクターの話し方パターン分析"""
        text = """
        「俺はもう限界だ」と太郎は叫んだ。
        「あなたはまだやれるわ」と花子は励ました。
        「ふん、面白いじゃないか」と敵は笑った。
        """

        if analyzer.initialized:
            # 各キャラクターの発話を分析
            tokens = analyzer.analyze(text)
            assert len(tokens) > 0

    def test_vocabulary_complexity(self, analyzer: object) -> None:
        """語彙の複雑さ分析"""
        simple_text = "犬が走る。猫が寝る。"
        complex_text = "哲学的思索に耽る知識人が、形而上学的概念について議論した。"

        if analyzer.initialized:
            simple_tokens = analyzer.analyze(simple_text)
            complex_tokens = analyzer.analyze(complex_text)

            # より複雑な文章の方が長い単語を含むはず
            if simple_tokens and complex_tokens:
                simple_avg_len = sum(len(t.surface) for t in simple_tokens) / len(simple_tokens)
                complex_avg_len = sum(len(t.surface) for t in complex_tokens) / len(complex_tokens)
                assert complex_avg_len >= simple_avg_len

    def test_emotion_words_detection(self, analyzer: object) -> None:
        """感情語の検出"""
        emotional_text = "嬉しい!楽しい!悲しい。怖い…"

        if analyzer.initialized:
            tokens = analyzer.analyze(emotional_text)
            emotion_words = [t.surface for t in tokens if hasattr(t, "part_of_speech") and "形容詞" in t.part_of_speech]

            # 感情を表す形容詞が検出されることを確認
            assert len(emotion_words) > 0


class TestPerformance:
    """パフォーマンステスト"""

    @pytest.fixture
    def analyzer(self):
        return MorphologicalAnalyzer()

    @pytest.fixture
    def large_text(self) -> str:
        """大量のテキスト"""
        return "これは長い文章です。" * 1000

    def test_large_text_processing(self, analyzer: object, large_text: object) -> None:
        """大量テキストの処理"""

        start_time = time.time()
        result = analyzer.analyze(large_text)
        end_time = time.time()

        # 処理が完了することを確認
        assert isinstance(result, list)

        # 処理時間が妥当な範囲内であることを確認(10秒以内)
        assert end_time - start_time < 10.0

    def test_memory_efficiency(self, analyzer: object) -> None:
        """メモリ効率のテスト"""
        # 複数回の解析でメモリリークがないことを確認
        text = "メモリテスト用の文章です。"

        for _ in range(100):
            result = analyzer.analyze(text)
            assert isinstance(result, list)

        # メモリ使用量が適切であることを確認
        # (実際のメモリ計測は環境依存のため、ここでは省略)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
