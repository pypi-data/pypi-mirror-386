#!/usr/bin/env python3
"""Application service that consolidates scene management statistics."""

from collections import defaultdict
from typing import Any

from noveler.domain.entities.scene_management_entities import SceneCategory, SceneInfo, ValidationIssue


class SceneStatisticsService:
    """Aggregate scene metrics such as category totals and validation issues."""

    def __init__(self, logger=None) -> None:
        """Initialize the service with an optional logger dependency."""
        # DDD準拠: Infrastructure層への直接依存を回避（遅延初期化）
        self._logger = logger

    def _get_default_logger(self) -> Any:
        """Return the configured logger or lazily acquire the unified logger."""
        if self._logger is None:
            # 遅延初期化: Infrastructure層インポートを実行時まで遅延
            from noveler.infrastructure.logging.unified_logger import get_logger
            self._logger = get_logger(__name__)
        return self._logger

    def calculate_category_totals(self, scenes: list[SceneInfo]) -> dict[SceneCategory, int]:
        """Aggregate scene counts by category."""
        # DDD準拠: 遅延初期化されたロガーを使用
        logger = self._get_default_logger()
        logger.debug(f"カテゴリ別集計開始: {len(scenes)}シーン")

        total_by_category = defaultdict(int)
        for scene in scenes:
            total_by_category[scene.category] += 1

        logger.debug(f"カテゴリ別集計完了: {dict(total_by_category)}")
        return dict(total_by_category)

    def count_completion_status(self, scenes: list[SceneInfo]) -> dict[str, int]:
        """Return completion statistics across the provided scenes."""
        total_scenes = len(scenes)
        completed_scenes = sum(1 for scene in scenes if scene.completion_status == "完了")

        result = {"total": total_scenes, "completed": completed_scenes, "pending": total_scenes - completed_scenes}

        # DDD準拠: 遅延初期化されたロガーを使用
        logger = self._get_default_logger()
        logger.debug(f"完了状況集計: {result}")
        return result

    def count_validation_issues(self, issues: list[ValidationIssue]) -> dict[str, int]:
        """Count validation issues by severity level."""
        error_count = sum(1 for issue in issues if issue.severity == "error")
        warning_count = sum(1 for issue in issues if issue.severity == "warning")
        info_count = sum(1 for issue in issues if issue.severity == "info")

        result = {"errors": error_count, "warnings": warning_count, "info": info_count, "total": len(issues)}

        # DDD準拠: 遅延初期化されたロガーを使用
        logger = self._get_default_logger()
        logger.debug(f"問題集計: {result}")
        return result
