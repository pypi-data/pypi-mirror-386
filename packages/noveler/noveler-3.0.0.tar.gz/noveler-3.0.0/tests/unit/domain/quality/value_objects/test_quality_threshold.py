"""QualityThreshold値オブジェクトのテスト"""

import pytest
pytestmark = pytest.mark.quality_domain


from noveler.domain.value_objects.quality_threshold import QualityThreshold


class TestQualityThreshold:
    """QualityThreshold値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-QUALITY-008")
    def test_quality_value_creation(self) -> None:
        """品質閾値が正しく作成できることを確認"""
        threshold = QualityThreshold(name="max_hiragana_ratio", value=0.45, min_value=0.0, max_value=1.0)
        assert threshold.name == "max_hiragana_ratio"
        assert threshold.value == 0.45
        assert threshold.min_value == 0.0
        assert threshold.max_value == 1.0

    @pytest.mark.spec("SPEC-QUALITY-008")
    def test_value(self) -> None:
        """範囲内の値が受け入れられることを確認"""
        threshold = QualityThreshold(name="dialog_ratio", value=0.5, min_value=0.3, max_value=0.7)
        assert threshold.value == 0.5

    @pytest.mark.spec("SPEC-QUALITY-008")
    def test_minimal_value_value(self) -> None:
        """最小値と同じ値が受け入れられることを確認"""
        threshold = QualityThreshold(name="test", value=0.0, min_value=0.0, max_value=1.0)
        assert threshold.value == 0.0

    @pytest.mark.spec("SPEC-QUALITY-008")
    def test_value_value(self) -> None:
        """最大値と同じ値が受け入れられることを確認"""
        threshold = QualityThreshold(name="test", value=1.0, min_value=0.0, max_value=1.0)
        assert threshold.value == 1.0

    @pytest.mark.spec("SPEC-QUALITY-008")
    @pytest.mark.spec("SPEC-QUALITY-008")
    def test_value_1(self) -> None:
        """最大値より大きい値は拒否されることを確認"""
        with pytest.raises(ValueError, match="範囲外"):
            QualityThreshold(name="test", value=0.8, min_value=0.3, max_value=0.7)

    @pytest.mark.spec("SPEC-QUALITY-008")
    def test_empty(self) -> None:
        """空の名前は拒否されることを確認"""
        with pytest.raises(ValueError, match="名前は空にできません"):
            QualityThreshold(name="", value=0.5, min_value=0.0, max_value=1.0)

    @pytest.mark.spec("SPEC-QUALITY-008")
    def test_minimal_value_maxvalue_than(self) -> None:
        """最小値が最大値より大きい場合は拒否されることを確認"""
        with pytest.raises(ValueError, match="最小値は最大値以下である必要があります"):
            QualityThreshold(name="test", value=0.5, min_value=0.7, max_value=0.3)

    @pytest.mark.spec("SPEC-QUALITY-008")
    def test_value_new(self) -> None:
        """値を更新できることを確認"""
        threshold = QualityThreshold(name="test", value=0.5, min_value=0.0, max_value=1.0)

        updated = threshold.update_value(0.7)
        assert updated.value == 0.7
        assert updated.name == threshold.name
        assert updated.min_value == threshold.min_value
        assert updated.max_value == threshold.max_value

    @pytest.mark.spec("SPEC-QUALITY-008")
    def test_new_value_check(self) -> None:
        """更新時も範囲がチェックされることを確認"""
        threshold = QualityThreshold(name="test", value=0.5, min_value=0.3, max_value=0.7)

        with pytest.raises(ValueError, match="範囲外"):
            threshold.update_value(0.8)

    @pytest.mark.spec("SPEC-QUALITY-008")
    def test_verification(self) -> None:
        """同じ設定の閾値は等価であることを確認"""
        threshold1 = QualityThreshold("test", 0.5, 0.0, 1.0)
        threshold2 = QualityThreshold("test", 0.5, 0.0, 1.0)
        threshold3 = QualityThreshold("test", 0.6, 0.0, 1.0)

        assert threshold1 == threshold2
        assert threshold1 != threshold3

    @pytest.mark.spec("SPEC-QUALITY-008")
    def test_unnamed(self) -> None:
        """人間が読みやすい文字列表現を持つことを確認"""
        threshold = QualityThreshold(name="max_hiragana_ratio", value=0.45, min_value=0.0, max_value=1.0)

        str_repr = str(threshold)
        assert "max_hiragana_ratio" in str_repr
        assert "0.45" in str_repr
        assert "0.0-1.0" in str_repr
