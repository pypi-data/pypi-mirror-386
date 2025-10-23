#!/usr/bin/env python3
"""ReaderSegment列挙型

読者セグメントを分類する列挙型
SPEC-ANALYSIS-001準拠
"""

from enum import Enum


class ReaderSegment(Enum):
    """読者セグメント分類"""

    NEW = "new"  # 新規読者
    REGULAR = "regular"  # 継続読者
    AT_RISK = "at_risk"  # 離脱リスク読者
