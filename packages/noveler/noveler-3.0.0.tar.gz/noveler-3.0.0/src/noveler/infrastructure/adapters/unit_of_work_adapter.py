#!/usr/bin/env python3
"""Unit of Work アダプター

既存のunit_of_work.pyの実装をアダプター層として再エクスポート
DDD準拠のアーキテクチャパターンに従った依存関係管理
"""

# 既存のUnit of Work実装を再エクスポート
from noveler.infrastructure.unit_of_work import (
    IUnitOfWork,
    UnitOfWork,
    create_unit_of_work,
)

# アダプター層での型エイリアス
UnitOfWorkAdapter = UnitOfWork

__all__ = [
    "IUnitOfWork",
    "UnitOfWork",
    "UnitOfWorkAdapter",
    "create_unit_of_work"
]
