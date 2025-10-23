#!/usr/bin/env python3
"""Foreshadowing値オブジェクト群のユニットテスト

仕様書: specs/foreshadowing.spec.md
TDD原則に従い、仕様書に基づいてテストを作成
"""

import pytest

from noveler.domain.value_objects.foreshadowing import (
    Foreshadowing,
    ForeshadowingCategory,
    ForeshadowingId,
    ForeshadowingRelationship,
    ForeshadowingStatus,
    Hint,
    PlantingInfo,
    ReaderReaction,
    ResolutionInfo,
    SubtletyLevel,
)

pytestmark = pytest.mark.vo_smoke


class TestForeshadowingId:
    """ForeshadowingIdのテストクラス"""

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_id_creation(self) -> None:
        """正しい形式のIDで作成できることを確認"""
        # Act
        fid = ForeshadowingId("F001")

        # Assert
        assert fid.value == "F001"
        assert str(fid) == "F001"

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_unnamed(self) -> None:
        """空文字列でValueErrorが発生することを確認"""
        with pytest.raises(ValueError) as exc_info:
            ForeshadowingId("")

        assert str(exc_info.value) == "伏線IDは必須です"

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_f_id(self) -> None:
        """'F'で始まらないIDでValueErrorが発生することを確認"""
        with pytest.raises(ValueError) as exc_info:
            ForeshadowingId("A001")

        assert str(exc_info.value) == "伏線IDは'F'で始まる必要があります(例: F001)"

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_4_id(self) -> None:
        """4文字でないIDでValueErrorが発生することを確認"""
        with pytest.raises(ValueError) as exc_info:
            ForeshadowingId("F01")

        assert str(exc_info.value) == "伏線IDは4文字である必要があります(例: F001)"


class TestPlantingInfo:
    """PlantingInfoのテストクラス"""

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_creation(self) -> None:
        """正常なパラメータで作成できることを確認"""
        # Act
        planting = PlantingInfo(
            episode="第001話",
            chapter=1,
            method="さりげない会話",
            content="主人公の謎めいた発言",
            subtlety_level=SubtletyLevel.HIGH,
        )

        # Assert
        assert planting.episode == "第001話"
        assert planting.chapter == 1
        assert planting.method == "さりげない会話"
        assert planting.content == "主人公の謎めいた発言"
        assert planting.subtlety_level == SubtletyLevel.HIGH

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_empty(self) -> None:
        """空のエピソードでValueErrorが発生することを確認"""
        with pytest.raises(ValueError) as exc_info:
            PlantingInfo(episode="", chapter=1, method="method", content="content")

        assert str(exc_info.value) == "仕込みエピソードは必須です"

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_0(self) -> None:
        """章番号が0以下でValueErrorが発生することを確認"""
        with pytest.raises(ValueError) as exc_info:
            PlantingInfo(episode="第001話", chapter=0, method="method", content="content")

        assert str(exc_info.value) == "章番号は1以上である必要があります"

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_is_subtle(self) -> None:
        """is_subtle()メソッドが正しく動作することを確認"""
        # Arrange
        subtle_planting = PlantingInfo(
            episode="第001話", chapter=1, method="m", content="c", subtlety_level=SubtletyLevel.HIGH
        )

        obvious_planting = PlantingInfo(
            episode="第001話", chapter=1, method="m", content="c", subtlety_level=SubtletyLevel.LOW
        )

        # Act & Assert
        assert subtle_planting.is_subtle() is True
        assert obvious_planting.is_subtle() is False


class TestResolutionInfo:
    """ResolutionInfoのテストクラス"""

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_creation(self) -> None:
        """正常なパラメータで作成できることを確認"""
        # Act
        resolution = ResolutionInfo(
            episode="第020話", chapter=3, method="衝撃的な真実の開示", impact="主人公の正体が明らかになる"
        )

        # Assert
        assert resolution.episode == "第020話"
        assert resolution.chapter == 3
        assert resolution.method == "衝撃的な真実の開示"
        assert resolution.impact == "主人公の正体が明らかになる"

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_validation(self) -> None:
        """必須フィールドが空の場合にValueErrorが発生することを確認"""
        # エピソードが空
        with pytest.raises(ValueError, match="回収エピソードは必須です"):
            ResolutionInfo(episode="", chapter=1, method="m", impact="i")

        # 章番号が無効
        with pytest.raises(ValueError, match="章番号は1以上である必要があります"):
            ResolutionInfo(episode="第001話", chapter=0, method="m", impact="i")

        # メソッドが空
        with pytest.raises(ValueError, match="回収方法は必須です"):
            ResolutionInfo(episode="第001話", chapter=1, method="", impact="i")

        # インパクトが空
        with pytest.raises(ValueError, match="期待される影響は必須です"):
            ResolutionInfo(episode="第001話", chapter=1, method="m", impact="")


class TestHint:
    """Hintのテストクラス"""

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_creation(self) -> None:
        """正常なパラメータで作成できることを確認"""
        # Act
        hint = Hint(episode="第005話", content="違和感のある描写", subtlety=SubtletyLevel.MEDIUM)

        # Assert
        assert hint.episode == "第005話"
        assert hint.content == "違和感のある描写"
        assert hint.subtlety == SubtletyLevel.MEDIUM

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_validation(self) -> None:
        """必須フィールドが空の場合にValueErrorが発生することを確認"""
        # エピソードが空
        with pytest.raises(ValueError, match="ヒントのエピソードは必須です"):
            Hint(episode="", content="content", subtlety=SubtletyLevel.MEDIUM)

        # コンテンツが空
        with pytest.raises(ValueError, match="ヒント内容は必須です"):
            Hint(episode="第001話", content="", subtlety=SubtletyLevel.MEDIUM)


class TestReaderReaction:
    """ReaderReactionのテストクラス"""

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_read_creation(self) -> None:
        """正常なパラメータで作成できることを確認"""
        # Act
        reaction = ReaderReaction(on_planting="気づかない", on_hints="違和感を覚える", on_resolution="驚愕する")

        # Assert
        assert reaction.on_planting == "気づかない"
        assert reaction.on_hints == "違和感を覚える"
        assert reaction.on_resolution == "驚愕する"

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_validation(self) -> None:
        """いずれかのフィールドが空の場合にValueErrorが発生することを確認"""
        with pytest.raises(ValueError, match="すべての読者反応予測は必須です"):
            ReaderReaction(on_planting="", on_hints="h", on_resolution="r")

        with pytest.raises(ValueError, match="すべての読者反応予測は必須です"):
            ReaderReaction(on_planting="p", on_hints="", on_resolution="r")

        with pytest.raises(ValueError, match="すべての読者反応予測は必須です"):
            ReaderReaction(on_planting="p", on_hints="h", on_resolution="")


class TestForeshadowing:
    """Foreshadowingのテストクラス"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.default_planting = PlantingInfo(episode="第001話", chapter=1, method="method", content="content")
        self.default_resolution = ResolutionInfo(episode="第020話", chapter=3, method="method", impact="impact")

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_creation(self) -> None:
        """正常なパラメータで作成できることを確認"""
        # Act
        foreshadowing = Foreshadowing(
            id=ForeshadowingId("F001"),
            title="主人公の秘密",
            category=ForeshadowingCategory.CHARACTER,
            description="主人公の隠された過去",
            importance=5,
            planting=self.default_planting,
            resolution=self.default_resolution,
            status=ForeshadowingStatus.PLANTED,
        )

        # Assert
        assert foreshadowing.id.value == "F001"
        assert foreshadowing.title == "主人公の秘密"
        assert foreshadowing.category == ForeshadowingCategory.CHARACTER
        assert foreshadowing.importance == 5
        assert foreshadowing.status == ForeshadowingStatus.PLANTED

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_basic_functionality(self) -> None:
        """タイトルが空でValueErrorが発生することを確認"""
        with pytest.raises(ValueError, match="伏線タイトルは必須です"):
            Foreshadowing(
                id=ForeshadowingId("F001"),
                title="",
                category=ForeshadowingCategory.MAIN,
                description="desc",
                importance=3,
                planting=self.default_planting,
                resolution=self.default_resolution,
                status=ForeshadowingStatus.PLANNED,
            )

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_validation(self) -> None:
        """重要度が1-5の範囲外でValueErrorが発生することを確認"""
        with pytest.raises(ValueError, match="重要度は1-5の範囲である必要があります"):
            Foreshadowing(
                id=ForeshadowingId("F001"),
                title="title",
                category=ForeshadowingCategory.MAIN,
                description="desc",
                importance=0,
                planting=self.default_planting,
                resolution=self.default_resolution,
                status=ForeshadowingStatus.PLANNED,
            )

        with pytest.raises(ValueError, match="重要度は1-5の範囲である必要があります"):
            Foreshadowing(
                id=ForeshadowingId("F001"),
                title="title",
                category=ForeshadowingCategory.MAIN,
                description="desc",
                importance=6,
                planting=self.default_planting,
                resolution=self.default_resolution,
                status=ForeshadowingStatus.PLANNED,
            )

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_episodes(self) -> None:
        """get_planting_to_resolution_distance()が正しく動作することを確認"""
        # Arrange
        foreshadowing = Foreshadowing(
            id=ForeshadowingId("F001"),
            title="test",
            category=ForeshadowingCategory.MAIN,
            description="desc",
            importance=3,
            planting=PlantingInfo(episode="第005話", chapter=1, method="m", content="c"),
            resolution=ResolutionInfo(episode="第025話", chapter=3, method="m", impact="i"),
            status=ForeshadowingStatus.PLANTED,
        )

        # Act
        distance = foreshadowing.get_planting_to_resolution_distance()

        # Assert
        assert distance == 20

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_determine(self) -> None:
        """is_long_term()が正しく動作することを確認"""
        # 短期伏線(9話差)
        short_term = Foreshadowing(
            id=ForeshadowingId("F001"),
            title="test",
            category=ForeshadowingCategory.MAIN,
            description="desc",
            importance=3,
            planting=PlantingInfo(episode="第001話", chapter=1, method="m", content="c"),
            resolution=ResolutionInfo(episode="第010話", chapter=2, method="m", impact="i"),
            status=ForeshadowingStatus.PLANTED,
        )

        # 長期伏線(10話差)
        long_term = Foreshadowing(
            id=ForeshadowingId("F002"),
            title="test",
            category=ForeshadowingCategory.MAIN,
            description="desc",
            importance=3,
            planting=PlantingInfo(episode="第001話", chapter=1, method="m", content="c"),
            resolution=ResolutionInfo(episode="第011話", chapter=2, method="m", impact="i"),
            status=ForeshadowingStatus.PLANTED,
        )

        # Assert
        assert short_term.is_long_term() is False
        assert long_term.is_long_term() is True

    @pytest.mark.spec("SPEC-PLOT-001")
    @pytest.mark.spec("SPEC-PLOT-001")
    def test_state_determine(self) -> None:
        """can_be_resolved()が正しく動作することを確認"""
        # 回収可能な状態
        planted = Foreshadowing(
            id=ForeshadowingId("F001"),
            title="test",
            category=ForeshadowingCategory.MAIN,
            description="desc",
            importance=3,
            planting=self.default_planting,
            resolution=self.default_resolution,
            status=ForeshadowingStatus.PLANTED,
        )

        ready = Foreshadowing(
            id=ForeshadowingId("F002"),
            title="test",
            category=ForeshadowingCategory.MAIN,
            description="desc",
            importance=3,
            planting=self.default_planting,
            resolution=self.default_resolution,
            status=ForeshadowingStatus.READY_TO_RESOLVE,
        )

        # 回収不可能な状態
        planned = Foreshadowing(
            id=ForeshadowingId("F003"),
            title="test",
            category=ForeshadowingCategory.MAIN,
            description="desc",
            importance=3,
            planting=self.default_planting,
            resolution=self.default_resolution,
            status=ForeshadowingStatus.PLANNED,
        )

        resolved = Foreshadowing(
            id=ForeshadowingId("F004"),
            title="test",
            category=ForeshadowingCategory.MAIN,
            description="desc",
            importance=3,
            planting=self.default_planting,
            resolution=self.default_resolution,
            status=ForeshadowingStatus.RESOLVED,
        )

        # Assert
        assert planted.can_be_resolved() is True
        assert ready.can_be_resolved() is True
        assert planned.can_be_resolved() is False
        assert resolved.can_be_resolved() is False

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_get(self) -> None:
        """get_hint_episodes()が正しく動作することを確認"""
        # ヒントありの伏線
        with_hints = Foreshadowing(
            id=ForeshadowingId("F001"),
            title="test",
            category=ForeshadowingCategory.MAIN,
            description="desc",
            importance=3,
            planting=self.default_planting,
            resolution=self.default_resolution,
            status=ForeshadowingStatus.PLANTED,
            hints=[
                Hint("第005話", "hint1", SubtletyLevel.HIGH),
                Hint("第010話", "hint2", SubtletyLevel.MEDIUM),
                Hint("第015話", "hint3", SubtletyLevel.LOW),
            ],
        )

        # ヒントなしの伏線
        without_hints = Foreshadowing(
            id=ForeshadowingId("F002"),
            title="test",
            category=ForeshadowingCategory.MAIN,
            description="desc",
            importance=3,
            planting=self.default_planting,
            resolution=self.default_resolution,
            status=ForeshadowingStatus.PLANTED,
        )

        # Act
        hint_episodes = with_hints.get_hint_episodes()
        no_hint_episodes = without_hints.get_hint_episodes()

        # Assert
        assert hint_episodes == ["第005話", "第010話", "第015話"]
        assert no_hint_episodes == []

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_generation(self) -> None:
        """to_summary()が正しく動作することを確認"""
        # Arrange
        foreshadowing = Foreshadowing(
            id=ForeshadowingId("F001"),
            title="主人公の秘密",
            category=ForeshadowingCategory.CHARACTER,
            description="desc",
            importance=4,
            planting=self.default_planting,
            resolution=self.default_resolution,
            status=ForeshadowingStatus.PLANTED,
        )

        # Act
        summary = foreshadowing.to_summary()

        # Assert
        assert "F001" in summary
        assert "主人公の秘密" in summary
        assert "[character]" in summary
        assert "⭐⭐⭐⭐" in summary  # importance=4
        assert "🌱" in summary  # PLANTED status


class TestForeshadowingRelationship:
    """ForeshadowingRelationshipのテストクラス"""

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_creation(self) -> None:
        """正常なパラメータで作成できることを確認"""
        # Act
        relationship = ForeshadowingRelationship(
            from_id=ForeshadowingId("F001"),
            to_id=ForeshadowingId("F002"),
            relationship_type="prerequisite",
            description="F001はF002の前提条件",
        )

        # Assert
        assert relationship.from_id.value == "F001"
        assert relationship.to_id.value == "F002"
        assert relationship.relationship_type == "prerequisite"
        assert relationship.description == "F001はF002の前提条件"

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_id(self) -> None:
        """同じID同士の関係でValueErrorが発生することを確認"""
        with pytest.raises(ValueError, match="同じ伏線同士の関係は定義できません"):
            ForeshadowingRelationship(
                from_id=ForeshadowingId("F001"),
                to_id=ForeshadowingId("F001"),
                relationship_type="parallel",
                description="desc",
            )

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_edge_cases(self) -> None:
        """無効な関係タイプでValueErrorが発生することを確認"""
        with pytest.raises(ValueError, match="関係タイプが不正です"):
            ForeshadowingRelationship(
                from_id=ForeshadowingId("F001"),
                to_id=ForeshadowingId("F002"),
                relationship_type="invalid_type",
                description="desc",
            )

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_error_handling(self) -> None:
        """すべての有効な関係タイプで作成できることを確認"""
        valid_types = ["prerequisite", "parallel", "contradictory"]

        for rel_type in valid_types:
            relationship = ForeshadowingRelationship(
                from_id=ForeshadowingId("F001"),
                to_id=ForeshadowingId("F002"),
                relationship_type=rel_type,
                description=f"{rel_type} relationship",
            )

            assert relationship.relationship_type == rel_type
