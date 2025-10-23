#!/usr/bin/env python3
"""固有名詞コレクションエンティティのユニットテスト

TDD+DDD原則に基づくリッチエンティティテスト
実行時間目標: < 0.05秒/テスト


仕様書: SPEC-DOMAIN-ENTITIES
"""

import pytest
pytestmark = pytest.mark.project

from noveler.domain.entities.proper_noun_collection import ProperNounCollection


class TestProperNounCollection:
    """固有名詞コレクションエンティティのユニットテスト"""

    # =================================================================
    # RED Phase: 失敗するテストを先に書く
    # =================================================================

    @pytest.mark.spec("SPEC-PROPER_NOUN_COLLECTION-SHOULD_VALIDATE_PROP")
    def test_should_validate_proper_noun_uniqueness(self) -> None:
        """固有名詞の一意性を検証する(RED→GREEN→REFACTOR)"""
        # RED: 固有名詞コレクションは重複を自動で除去するべき
        terms = {"綾瀬カノン", "律"}  # 重複あり
        collection = ProperNounCollection(terms)

        # Act & Assert: 重複は自動で除去される
        assert len(collection) == 2
        assert "綾瀬カノン" in collection
        assert "律" in collection

    @pytest.mark.spec("SPEC-PROPER_NOUN_COLLECTION-SHOULD_CREATE_COLLEC")
    def test_should_create_collection_from_set(self) -> None:
        """固有名詞セットからコレクションを作成する"""
        # Arrange
        terms = {"主人公", "魔法学園", "BUG.CHURCH"}

        # Act
        collection = ProperNounCollection(terms)

        # Assert
        assert len(collection) == 3
        assert "主人公" in collection
        assert "魔法学園" in collection
        assert "BUG.CHURCH" in collection

    # =================================================================
    # GREEN Phase: テストを通す最小実装
    # =================================================================

    @pytest.mark.spec("SPEC-PROPER_NOUN_COLLECTION-CREATES_EMPTY_COLLEC")
    def test_creates_empty_collection(self) -> None:
        """空のコレクションを作成(GREEN)"""
        # Arrange & Act
        collection = ProperNounCollection(set())

        # Assert
        assert len(collection) == 0

    @pytest.mark.spec("SPEC-PROPER_NOUN_COLLECTION-FILTERS_INVALID_TERM")
    def test_filters_invalid_terms(self) -> None:
        """無効な用語をフィルタする"""
        # Arrange
        terms = {"有効な用語", "", "  ", "  空白付き  "}

        # Act
        collection = ProperNounCollection(terms)

        # Assert: 有効な用語のみが残る
        assert len(collection) == 2  # "有効な用語" と "空白付き"
        assert "有効な用語" in collection
        assert "空白付き" in collection  # 空白は除去される

    @pytest.mark.spec("SPEC-PROPER_NOUN_COLLECTION-COLLECTION_ITERATION")
    def test_collection_iteration(self) -> None:
        """コレクションのイテレーション"""
        # Arrange
        terms = {"用語1", "用語2", "用語3"}
        collection = ProperNounCollection(terms)

        # Act & Assert
        collected_terms = set()
        for term in collection:
            collected_terms.add(term)

        assert collected_terms == terms

    @pytest.mark.spec("SPEC-PROPER_NOUN_COLLECTION-COLLECTION_MERGE")
    def test_collection_merge(self) -> None:
        """コレクションのマージ"""
        # Arrange
        collection1 = ProperNounCollection({"用語1", "用語2"})
        collection2 = ProperNounCollection({"用語2", "用語3"})

        # Act
        merged = collection1.merge(collection2)

        # Assert
        assert len(merged) == 3
        assert "用語1" in merged
        assert "用語2" in merged
        assert "用語3" in merged

    @pytest.mark.spec("SPEC-PROPER_NOUN_COLLECTION-COLLECTION_DIFF")
    def test_collection_diff(self) -> None:
        """コレクション間の差分計算"""
        # Arrange
        old_collection = ProperNounCollection({"用語1", "用語2", "削除される用語"})
        new_collection = ProperNounCollection({"用語1", "用語2", "新しい用語"})

        # Act
        diff = old_collection.get_diff(new_collection)

        # Assert
        assert "新しい用語" in diff.added
        assert "削除される用語" in diff.removed
        assert len(diff.unchanged) == 2

    @pytest.mark.spec("SPEC-PROPER_NOUN_COLLECTION-EMPTY_COLLECTION_BEH")
    def test_empty_collection_behavior(self) -> None:
        """空のコレクションの動作"""
        # Arrange
        collection = ProperNounCollection(set())

        # Act & Assert
        assert len(collection) == 0
        assert collection.is_empty()

        # 空のコレクション同士のマージ
        other_empty = ProperNounCollection(set())
        merged = collection.merge(other_empty)
        assert len(merged) == 0
