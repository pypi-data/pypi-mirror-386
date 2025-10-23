"""対立キャラクター個性化チェッカーのテスト

SPEC-QUALITY-023 v2.0準拠
敵キャラの台詞独自性と印象度の定量評価のテスト
"""

import pytest
from noveler.domain.services.antagonist_personality_checker import AntagonistPersonalityChecker


@pytest.mark.spec('SPEC-QUALITY-023')
class TestAntagonistPersonalityChecker:
    """対立キャラクター個性化チェッカーのテストクラス"""

    def setup_method(self):
        """各テスト前の準備"""
        self.checker = AntagonistPersonalityChecker()

    def test_check_text_with_unique_antagonist(self):
        """個性的な敵キャラで高スコアを確認"""
        # Arrange
        text = """
        エクスプロイト団のリーダーが微笑んだ。
        「SQLインジェクションとは、なんて美しいダンスなんだろうね」
        「データベースの詩的な構造を理解できない君たちには分からないだろうが」
        彼は技術を芸術として捉える変わった価値観を持っていた。
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        assert result["score"] > 70  # 個性的なので高スコア期待
        assert result["analysis"]["unique_expressions"]["count"] >= 1
        assert result["grade"] in ["A", "S"]

    def test_check_text_with_generic_villain(self):
        """定型悪役台詞で低スコアを確認"""
        # Arrange
        text = """
        敵のボスが現れた。
        「お前たちは無力だ！」
        「世界を支配するのが私の計画だ！」
        「これで終わりだ、愚か者めが！」
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        assert result["score"] < 40  # 定型台詞なので低スコア
        assert result["analysis"]["generic_phrases"]["count"] >= 2
        assert result["grade"] in ["D", "C"]
        assert "定型的な悪役台詞" in str(result["recommendations"])

    def test_check_text_with_no_antagonist(self):
        """敵キャラ不在時の中立スコア"""
        # Arrange
        text = """
        直人とあすかは穏やかに会話していた。
        「今日はいい天気ですね」
        「そうですね、散歩日和です」
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        assert result["score"] == 50  # 中立スコア
        assert "対立キャラクターの台詞が検出されませんでした" in result["analysis"]["message"]
        assert result["grade"] == "B"

    def test_check_text_with_tech_savvy_antagonist(self):
        """技術に詳しい敵キャラの個性検出"""
        # Arrange
        text = """
        ハッカー集団のリーダーが語った。
        「君たちのシステムのAPIは実にエレガントだね」
        「バックアップの復旧プロセスには愛を感じるよ」
        彼の口調には独特の丁寧語があった。
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        assert result["analysis"]["unique_expressions"]["count"] >= 1
        # 技術+美学の組み合わせが検出されるか
        unique_examples = result["analysis"]["unique_expressions"]["examples"]
        assert any("API" in expr or "バックアップ" in expr for expr in unique_examples)

    def test_check_text_with_character_quirks(self):
        """キャラクター癖の検出テスト"""
        # Arrange
        text = """
        「〜であるな、君たちの理解力は」
        「実に興味深いデータである」
        「美しい暗号化アルゴリズムであるよ」
        敵キャラは堅い口調と美学へのこだわりを持っていた。
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        assert result["analysis"]["character_quirks"]["count"] >= 1
        quirk_examples = result["analysis"]["character_quirks"]["examples"]
        assert any("である" in expr for expr in quirk_examples)

    def test_memorability_score_calculation(self):
        """印象度スコアの計算確認"""
        # Arrange
        text = """
        エクスプロイト団のボス登場。
        「ハッキングは美しいアートである」
        「実に、実に素晴らしいコードだね」
        「データベースを宝物のように扱う君の姿勢、嫌いじゃない」
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        assert result["analysis"]["unique_expressions"]["count"] >= 1
        assert result["analysis"]["character_quirks"]["count"] >= 1
        # 両方あるのでボーナスが付いて高い印象度スコア期待
        assert result["score"] > 60

    def test_antagonist_detection_by_context(self):
        """文脈による敵キャラ判定テスト"""
        # Arrange
        text = """
        エクスプロイト団の一員が立ち上がった。
        その時、リーダーが口を開いた。
        「諦めるのはまだ早いぞ」
        周囲の空気が張り詰める。
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        # エクスプロイト団という文脈で敵キャラ判定されるはず
        assert result["analysis"]["antagonist_dialogues_found"] >= 1

    def test_empty_text_handling(self):
        """空テキストのエラーハンドリング"""
        # Act
        result = self.checker.check_text("")

        # Assert
        assert result["success"] is True
        assert result["score"] == 0
        assert result["analysis"]["total_expressions"] == 0

    def test_recommendations_accuracy(self):
        """不足要素に対する適切な改善提案"""
        # Arrange - 身体反応のみで他が不足
        text = "直人の心臓がドキドキした。"

        # Act
        result = self.checker.check_text(text)

        # Assert
        recommendations = result["recommendations"]
        assert any("感覚的比喩を追加" in rec for rec in recommendations)
        assert any("内面独白を追加" in rec for rec in recommendations)
        # 身体反応はあるので提案されないはず
        assert not any("身体反応の表現を追加" in rec for rec in recommendations)
