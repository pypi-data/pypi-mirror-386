"""緊張緩和バランスチェッカーのテスト

SPEC-QUALITY-023 v2.0準拠
シーン別緊張度と緊張緩和の最適タイミング評価のテスト
"""

import pytest
from noveler.domain.services.tension_relief_balance_checker import (
    TensionReliefBalanceChecker,
    TensionLevel
)


@pytest.mark.spec('SPEC-QUALITY-023')
class TestTensionReliefBalanceChecker:
    """緊張緩和バランスチェッカーのテストクラス"""

    def setup_method(self):
        """各テスト前の準備"""
        self.checker = TensionReliefBalanceChecker()

    def test_check_text_with_ideal_tension_curve(self):
        """理想的な緊張曲線で高スコアを確認"""
        # Arrange - 理想的な構成：低→高→中高→中
        text = """
        平穏な朝の始まり。

        突然、エクスプロイト団が襲撃してきた！
        激しい戦闘が始まる。直人は必死に応戦する。

        「え？SQLって呪文ですか？」あすかの天然発言で場が和む。
        しかし危機はまだ続いている。

        最終的に敵を退けたが、まだ完全解決ではない。
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        assert result["score"] > 70  # 理想的な曲線なので高スコア期待
        assert result["analysis"]["peak_tension_scenes"] >= 1
        assert result["analysis"]["relief_scenes"] >= 1
        assert result["grade"] in ["A", "S", "B"]

    def test_check_text_with_high_tension_only(self):
        """高緊張のみで緊張緩和不足の検出"""
        # Arrange
        text = """
        戦闘開始！エクスプロイト団が攻撃してくる。

        激しい攻防戦が続く。直人は必死に防御する。

        さらに強力な攻撃が襲いかかる。絶体絶命の危機だ。

        血が流れ、負傷者が続出する激戦。
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        assert result["score"] < 60  # 緊張緩和不足で低スコア
        assert result["analysis"]["relief_scenes"] == 0
        assert "緊張緩和要素が不足" in str(result["recommendations"])

    def test_check_text_with_comedy_relief(self):
        """コメディ要素の正確な検出"""
        # Arrange
        text = """
        緊迫した状況の中で。

        「SQLって呪文ですか？」
        「データベースって新しい料理？」
        あすかの天然発言が場を和ませた。

        しかし危機はまだ去っていない。
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        assert result["analysis"]["relief_scenes"] >= 1
        # コメディパターンが検出されているか確認（具体的な内容は実装による）

    def test_tension_level_determination(self):
        """緊張レベル判定の精度確認"""
        # Arrange - 各レベルのサンプルテキスト
        high_tension_text = "戦闘開始！爆発が起こり、血が流れる緊急事態だ！"
        medium_tension_text = "問題が発覚した。対立する意見が出て困った状況だ。"
        low_tension_text = "穏やかな日常。お茶を飲みながらの平和な会話。"

        # Act & Assert - 高緊張
        high_result = self.checker.check_text(high_tension_text)
        assert high_result["analysis"]["peak_tension_scenes"] >= 1

        # Act & Assert - 中緊張
        medium_result = self.checker.check_text(medium_tension_text)
        assert medium_result["success"] is True

        # Act & Assert - 低緊張
        low_result = self.checker.check_text(low_tension_text)
        assert low_result["success"] is True
        assert low_result["analysis"]["peak_tension_scenes"] == 0

    def test_consecutive_high_tension_penalty(self):
        """高緊張の長時間継続に対するペナルティ"""
        # Arrange - 高緊張が4シーン以上連続
        text = """
        激しい戦闘が始まった。

        さらに激化する戦闘。血が流れる。

        絶体絶命の危機。爆発が続く。

        まだ戦闘は続く。負傷者が増える。

        延々と続く激戦。疲労が限界に。
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        assert result["score"] < 50  # 長時間高緊張でペナルティ
        assert "高緊張状態が長時間続きすぎています" in str(result["recommendations"])

    def test_antagonist_dialogue_detection(self):
        """敵キャラ台詞の検出精度確認"""
        # Arrange
        text = """
        「俺の力を見せてやる」とエクスプロイト団リーダーが叫んだ。
        直人は「がんばろう」と応えた。
        「計画通りだ」と敵が笑う。
        あすかは「SQLって呪文ですか？」と尋ねた。
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        # 敵キャラの台詞（計画通りだ、俺の力を見せてやる）が検出されているはず
        assert result["analysis"]["antagonist_dialogues_found"] >= 1

    def test_tech_savvy_villain_detection(self):
        """技術に詳しい敵キャラの特殊検出"""
        # Arrange
        text = """
        ハッカー集団のボスが現れた。
        「君たちのAPIは実にエレガントだ」
        「システムの最適化に哲学を感じる」
        「SQLをこんなに美しく書けるなんて」
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        assert result["analysis"]["unique_expressions"]["count"] >= 2
        # 技術+美学の組み合わせが検出されているか
        unique_examples = result["analysis"]["unique_expressions"]["examples"]
        assert any("API" in expr or "システム" in expr or "SQL" in expr for expr in unique_examples)

    def test_scene_splitting_accuracy(self):
        """シーン分割の精度確認"""
        # Arrange - 明確なシーン区切りがあるテキスト
        text = """
        最初のシーン内容。

        ---

        二番目のシーン内容。

        　　＊

        三番目のシーン内容。
        """

        # Act
        result = self.checker.check_text(text)

        # Assert
        assert result["success"] is True
        assert result["analysis"]["scenes_found"] >= 2  # 最低2シーンは検出されるはず

    def test_balance_recommendations(self):
        """バランス不良時の的確な改善提案"""
        # Arrange - 緊張のみでバランス不良
        text = "戦闘だ！攻撃！危険！絶体絶命！"

        # Act
        result = self.checker.check_text(text)

        # Assert
        recommendations = result["recommendations"]
        assert any("緊張緩和要素が不足" in rec for rec in recommendations)
        assert any("息抜きを入れて" in rec for rec in recommendations)

    def test_file_read_error_handling(self):
        """存在しないファイルのエラーハンドリング"""
        # Act
        result = self.checker.check_file("/non/existent/file.txt")

        # Assert
        assert result["success"] is False
        assert "ファイル読み込みエラー" in result["error"]
        assert result["score"] == 0
