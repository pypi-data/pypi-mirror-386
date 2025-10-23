"""感情表現深度チェッカーのテスト

SPEC-QUALITY-023 v2.0準拠
身体反応・感覚比喩・内面独白の三層構造分析のテスト
"""

import pytest
from noveler.domain.services.emotion_expression_checker import EmotionExpressionChecker


@pytest.mark.spec('SPEC-QUALITY-023')
class TestEmotionExpressionChecker:
    """感情表現深度チェッカーのテストクラス"""

    def setup_method(self):
        """各テスト前の準備"""
        self.checker = EmotionExpressionChecker()

    def test_check_text_with_full_expression_layers(self):
        """三層構造完備のテキストで高スコアを確認"""
        # Arrange
        text = """
        直人の心臓がドキドキと激しく鼓動した。
        冷たい刃物のような恐怖が胸を締め付ける。
        （これは本当にやばい状況だ）と彼は思った。
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        assert result["score"] > 70  # 三層構造なので高スコア期待
        assert result["analysis"]["physical_reactions"]["count"] >= 1
        assert result["analysis"]["sensory_metaphors"]["count"] >= 1
        assert result["analysis"]["inner_monologues"]["count"] >= 1
        assert result["grade"] in ["A", "S"]

    def test_check_text_with_only_physical_reactions(self):
        """身体反応のみの場合の中程度スコア"""
        # Arrange
        text = """
        直人の心臓が跳ねた。手が震え、息が切れた。
        筋肉がこわばり、背筋に冷たいものが走る。
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        assert 20 <= result["score"] <= 60  # 一層のみなので中程度
        assert result["analysis"]["physical_reactions"]["count"] >= 2
        assert result["analysis"]["sensory_metaphors"]["count"] == 0
        assert result["analysis"]["inner_monologues"]["count"] == 0

    def test_check_text_with_no_expressions(self):
        """感情表現なしの場合の低スコア"""
        # Arrange
        text = """
        直人は部屋に入った。机の上に本があった。
        彼は本を手に取り、ページをめくった。
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        assert result["score"] == 0  # 感情表現なしなので0点
        assert result["analysis"]["total_expressions"] == 0
        assert result["grade"] == "D"
        assert "身体反応の表現を追加してください" in result["recommendations"]

    def test_check_text_with_mixed_expressions(self):
        """複数層の混合表現でバランススコア確認"""
        # Arrange
        text = """
        あすかの心臓がバクバクと音を立てる。
        まるで雷が頭を突き抜けるような衝撃だった。
        「これは危険すぎる」と彼女は考えた。
        胃が重く沈んでいく感覚に、彼女は眉をひそめた。
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        assert result["score"] > 80  # 三層+複数表現でかなり高スコア
        assert result["analysis"]["physical_reactions"]["count"] >= 2
        assert result["analysis"]["sensory_metaphors"]["count"] >= 1
        assert result["analysis"]["inner_monologues"]["count"] >= 1

    def test_check_text_with_antagonist_dialogue_comedy(self):
        """敵キャラとコメディ要素の組み合わせテスト"""
        # Arrange
        text = """
        エクスプロイト団のリーダーが笑みを浮かべた。
        「SQLインジェクションなんて、なんて美しいダンスなんだ」
        直人の心臓が嫌なリズムで跳ねた。（こいつ、本当にヤバい奴だ）
        「え？SQLって呪文ですか？」あすかが首をかしげる。
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        assert result["analysis"]["physical_reactions"]["count"] >= 1
        assert result["analysis"]["inner_monologues"]["count"] >= 1

    def test_recommendations_for_missing_layers(self):
        """不足している層に対する的確な提案"""
        # Arrange
        text = "直人は考えた。これは難しい問題だ。"  # 内面独白のみ

        # Act
        result = self.checker.check_text(text)

        # Assert
        recommendations = result["recommendations"]
        assert any("身体反応" in rec for rec in recommendations)
        assert any("感覚的比喩" in rec for rec in recommendations)
        assert not any("内面独白" in rec for rec in recommendations)  # 既に存在するため提案されない

    def test_file_read_error_handling(self):
        """存在しないファイルのエラーハンドリング"""
        # Act
        result = self.checker.check_file("/non/existent/file.txt")

        # Assert
        assert result["success"] is False
        assert "ファイル読み込みエラー" in result["error"]
        assert result["score"] == 0

    def test_pattern_detection_accuracy(self):
        """パターン検出の精度確認"""
        # Arrange
        text = """
        心臓がドキドキと鼓動し、冷たい刃物のような恐怖が走った。
        （これは本当に危険だ）と直人は思考する。
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        analysis = result["analysis"]

        # 身体反応が正しく検出されているか
        physical_examples = analysis["physical_reactions"]["expressions"]
        assert any("心臓" in expr for expr in physical_examples)

        # 感覚的比喩が正しく検出されているか
        metaphor_examples = analysis["sensory_metaphors"]["expressions"]
        assert any("冷たい刃物" in expr for expr in metaphor_examples)

        # 内面独白が正しく検出されているか
        monologue_examples = analysis["inner_monologues"]["expressions"]
        assert any("思考" in expr or "思" in expr for expr in monologue_examples)
