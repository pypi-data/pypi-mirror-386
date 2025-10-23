#!/usr/bin/env python3

"""Domain.entities.proper_noun_collection
Where: Domain entity managing proper noun collections.
What: Stores terminology and naming conventions used across manuscripts.
Why: Helps maintain consistency of proper nouns.
"""

from __future__ import annotations

"""固有名詞コレクション値オブジェクト

固有名詞の集合を管理し、マージや差分計算などの
ビジネスロジックを提供する値オブジェクト
"""


import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(frozen=True)
class ProperNounDiff:
    """固有名詞コレクションの差分"""

    added: set[str]
    removed: set[str]
    unchanged: set[str]

    @property
    def has_changes(self) -> bool:
        """変更があるかどうか"""
        return len(self.added) > 0 or len(self.removed) > 0


class ProperNounCollection:
    """固有名詞コレクション値オブジェクト"""

    def __init__(self, terms: set[str] | list[str] | tuple[str, ...]) -> None:
        """Args:
        terms: 固有名詞のセット
        """
        # 重複を自動で除去し、空文字列や不正な値をフィルタ
        self._terms = {term.strip() for term in terms if term and isinstance(term, str) and term.strip()}

    def __len__(self) -> int:
        """コレクションのサイズ"""
        return len(self._terms)

    def __contains__(self, term: str) -> bool:
        """指定された用語が含まれているか"""
        return term in self._terms

    def __iter__(self) -> Iterator[str]:
        """イテレータ"""
        return iter(self._terms)

    def __eq__(self, other: object) -> bool:
        """等価比較"""
        if not isinstance(other, ProperNounCollection):
            return False
        return self._terms == other._terms

    def __hash__(self) -> int:
        """ハッシュ値(値オブジェクトとして不変)"""
        return hash(frozenset(self._terms))

    def is_empty(self) -> bool:
        """コレクションが空かどうか"""
        return len(self._terms) == 0

    def merge(self, other: ProperNounCollection) -> ProperNounCollection:
        """他のコレクションとマージ

        Args:
            other: マージ対象のコレクション

        Returns:
            ProperNounCollection: マージされた新しいコレクション
        """
        if not isinstance(other, ProperNounCollection):
            msg = "ProperNounCollectionとのマージのみ可能です"
            raise TypeError(msg)

        merged_terms = self._terms | other._terms
        return ProperNounCollection(merged_terms)

    def get_diff(self, other: ProperNounCollection) -> ProperNounDiff:
        """他のコレクションとの差分を計算

        Args:
            other: 比較対象のコレクション

        Returns:
            ProperNounDiff: 差分情報
        """
        if not isinstance(other, ProperNounCollection):
            msg = "ProperNounCollectionとの比較のみ可能です"
            raise TypeError(msg)

        added = other._terms - self._terms
        removed = self._terms - other._terms
        unchanged = self._terms & other._terms

        return ProperNounDiff(
            added=added,
            removed=removed,
            unchanged=unchanged,
        )

    def subtract(self, other: ProperNounCollection) -> ProperNounCollection:
        """他のコレクションの要素を除外

        Args:
            other: 除外対象のコレクション

        Returns:
            ProperNounCollection: 除外後の新しいコレクション
        """
        if not isinstance(other, ProperNounCollection):
            msg = "ProperNounCollectionとの除外のみ可能です"
            raise TypeError(msg)

        remaining_terms = self._terms - other._terms
        return ProperNounCollection(remaining_terms)

    def filter_by_prefix(self, prefix: str) -> ProperNounCollection:
        """指定されたプレフィックスでフィルタ

        Args:
            prefix: フィルタ用プレフィックス

        Returns:
            ProperNounCollection: フィルタされた新しいコレクション
        """
        filtered_terms = {term for term in self._terms if term.startswith(prefix)}
        return ProperNounCollection(filtered_terms)

    def filter_by_pattern(self, pattern: str) -> ProperNounCollection:
        """指定されたパターンでフィルタ(部分一致)

        Args:
            pattern: フィルタ用パターン

        Returns:
            ProperNounCollection: フィルタされた新しいコレクション
        """
        filtered_terms = {term for term in self._terms if pattern in term}
        return ProperNounCollection(filtered_terms)

    def to_set(self) -> set[str]:
        """セットとして取得(コピー)"""
        return self._terms.copy()

    def to_list(self) -> list:
        """リストとして取得(ソート済み)"""
        return sorted(self._terms)

    def get_stats(self) -> dict:
        """統計情報を取得"""
        return {
            "total_count": len(self._terms),
            "character_names": len([t for t in self._terms if self._looks_like_character_name(t)]),
            "organization_names": len([t for t in self._terms if self._looks_like_organization(t)]),
            "technical_terms": len([t for t in self._terms if self._looks_like_technical_term(t)]),
            "shortest_term": min(self._terms, key=len) if self._terms else None,
            "longest_term": max(self._terms, key=len) if self._terms else None,
        }

    def _looks_like_character_name(self, term: str) -> bool:
        """キャラクター名らしいかどうかの簡易判定"""
        # 漢字・ひらがな・カタカナが含まれ、短い場合はキャラクター名の可能性

        return len(term) <= 10 and re.search(r"[ぁ-んァ-ヶ一-龯]", term) and not re.search(r"[A-Z]{2,}", term)

    def _looks_like_organization(self, term: str) -> bool:
        """組織名らしいかどうかの簡易判定"""

        # 英数字が多い、または特定のパターンを含む
        return re.search(r"[A-Z]{2,}", term) or "学園" in term or "組織" in term or "CHURCH" in term

    def _looks_like_technical_term(self, term: str) -> bool:
        """技術用語らしいかどうかの簡易判定"""

        # 英数字と記号の組み合わせ
        return re.search(r"[A-Z0-9\-]+", term) and len(term) <= 20
