"""Domain.services.backup_analysis_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""バックアップ分析サービス

B20準拠実装 - Domain Service Interface
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path



@dataclass
class ChaosAnalysisResult:
    """カオス分析結果"""

    backup_folders: list
    total_folders: int
    analysis_timestamp: datetime


@dataclass
class BackupStatistics:
    """バックアップ統計情報"""

    total_size_mb: float
    oldest_backup_date: datetime | None
    newest_backup_date: datetime | None
    duplicate_candidates: list[str]


class BackupAnalysisService(ABC):
    """バックアップ分析サービス - Domain Service Interface

    B20準拠 Domain Service:
    - ビジネスロジックの抽象化
    - インフラストラクチャからの分離
    - Pure Domain Logic
    """

    @abstractmethod
    def analyze_chaos_state(self, project_root: Path) -> ChaosAnalysisResult:
        """カオス状態分析"""

    @abstractmethod
    def generate_statistics(self, chaos_result: ChaosAnalysisResult) -> BackupStatistics:
        """統計情報生成"""

    @abstractmethod
    def generate_recommendations(self, statistics: BackupStatistics) -> list[str]:
        """推奨事項生成"""
