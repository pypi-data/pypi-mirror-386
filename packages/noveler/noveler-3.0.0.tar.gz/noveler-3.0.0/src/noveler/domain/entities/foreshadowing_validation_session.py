#!/usr/bin/env python3

"""Domain.entities.foreshadowing_validation_session
Where: Domain entity modelling foreshadowing validation sessions.
What: Tracks validation inputs, results, and follow-up actions.
Why: Keeps foreshadowing validation workflows consistent.
"""

from __future__ import annotations

"""
伏線検証セッションエンティティ
SPEC-FORESHADOWING-001準拠のドメインモデル
"""


import re
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from noveler.domain.value_objects.foreshadowing_issue import (
    ForeshadowingDetectionResult,
    ForeshadowingIssue,
    ForeshadowingIssueType,
    ForeshadowingSeverity,
    ForeshadowingValidationConfig,
)
from noveler.domain.value_objects.project_time import project_now

if TYPE_CHECKING:
    from datetime import datetime

    from noveler.domain.value_objects.foreshadowing import Foreshadowing


@dataclass
class ForeshadowingValidationSession:
    """伏線検証セッションエンティティ"""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    episode_number: int = 0
    manuscript_content: str = ""
    foreshadowing_list: list[Foreshadowing] = field(default_factory=list)
    config: ForeshadowingValidationConfig = field(default_factory=ForeshadowingValidationConfig)
    created_at: datetime = field(default_factory=lambda: project_now().datetime)
    completed_at: datetime | None = None
    validation_result: ForeshadowingDetectionResult | None = None

    def __post_init__(self) -> None:
        if not self.session_id:
            msg = "セッションIDは必須です"
            raise ValueError(msg)
        if self.episode_number < 1:
            msg = "エピソード番号は1以上である必要があります"
            raise ValueError(msg)

    def validate_foreshadowing(self) -> ForeshadowingDetectionResult:
        """伏線検証を実行"""
        if self.is_completed():
            msg = "既に完了したセッションです"
            raise ValueError(msg)

        issues = []

        # 仕込み漏れチェック
        if self.config.enable_planting_check:
            issues.extend(self._check_planting_issues())

        # 回収漏れチェック
        if self.config.enable_resolution_check:
            issues.extend(self._check_resolution_issues())

        # 結果を作成
        self.validation_result = ForeshadowingDetectionResult(
            episode_number=self.episode_number,
            issues=issues,
            total_foreshadowing_checked=len(self.foreshadowing_list),
            detection_timestamp=project_now().datetime,
        )

        self.completed_at = project_now().datetime
        return self.validation_result

    def _check_planting_issues(self) -> list[ForeshadowingIssue]:
        """仕込み漏れチェック"""
        issues = []

        for foreshadowing in self.foreshadowing_list:
            # 該当エピソードで仕込み予定かチェック
            if (
                hasattr(foreshadowing, "planting")
                and self._extract_episode_number(foreshadowing.planting.episode) == self.episode_number
            ):
                # ステータスが"planned"の場合は仕込み漏れ
                if foreshadowing.status.value == "planned":
                    severity = self._determine_planting_severity(foreshadowing.importance)

                    issue = ForeshadowingIssue(
                        foreshadowing_id=str(foreshadowing.id),
                        issue_type=ForeshadowingIssueType.MISSING_PLANTING,
                        severity=severity,
                        episode_number=self.episode_number,
                        message=f"伏線「{foreshadowing.title}」が仕込まれていません",
                        expected_content=foreshadowing.planting.content if hasattr(foreshadowing, "planting") else "",
                        suggestion=f"方法: {foreshadowing.planting.method}"
                        if hasattr(foreshadowing, "planting")
                        else "",
                    )

                    issues.append(issue)

        return issues

    def _check_resolution_issues(self) -> list[ForeshadowingIssue]:
        """回収漏れチェック"""
        issues = []

        for foreshadowing in self.foreshadowing_list:
            # 該当エピソードで回収予定かチェック
            if (
                hasattr(foreshadowing, "resolution")
                and self._extract_episode_number(foreshadowing.resolution.episode) == self.episode_number
            ):
                # ステータスが"planted"または"ready_to_resolve"の場合は回収漏れ
                if foreshadowing.status.value in ["planted", "ready_to_resolve"]:
                    issue = ForeshadowingIssue(
                        foreshadowing_id=str(foreshadowing.id),
                        issue_type=ForeshadowingIssueType.MISSING_RESOLUTION,
                        severity=ForeshadowingSeverity.CRITICAL,  # 回収漏れは常にクリティカル
                        episode_number=self.episode_number,
                        message=f"伏線「{foreshadowing.title}」の回収が必要です",
                        expected_content=foreshadowing.resolution.content
                        if hasattr(foreshadowing, "resolution")
                        else "",
                        suggestion=f"方法: {foreshadowing.resolution.method}"
                        if hasattr(foreshadowing, "resolution")
                        else "",
                    )

                    issues.append(issue)

        return issues

    def _determine_planting_severity(self, importance: int) -> ForeshadowingSeverity:
        """仕込み問題の重要度判定"""
        if importance >= self.config.min_importance_for_high_severity:
            return ForeshadowingSeverity.HIGH
        return ForeshadowingSeverity.MEDIUM

    def _extract_episode_number(self, episode_str: str) -> int:
        """エピソード文字列から番号を抽出"""
        # "第001話"形式から数値を抽出

        # 文字列でない場合は0を返す(モックオブジェクト対応)
        if not isinstance(episode_str, str):
            return 0

        match = re.search(r"第(\d+)話", episode_str)
        if match:
            return int(match.group(1))
        return 0

    def is_completed(self) -> bool:
        """セッションが完了しているかどうか"""
        return self.completed_at is not None

    def has_critical_issues(self) -> bool:
        """クリティカルな問題があるかどうか"""
        if not self.validation_result:
            return False
        return self.validation_result.has_critical_issues()

    def get_validation_summary(self) -> str:
        """検証結果のサマリー"""
        if not self.validation_result:
            return "検証未実行"
        return self.validation_result.format_summary()

    def mark_foreshadowing_as_implemented(self, foreshadowing_id: str, implementation_type: str) -> bool:
        """伏線を実装済みとしてマーク"""
        for foreshadowing in self.foreshadowing_list:
            if str(foreshadowing.id) == foreshadowing_id:
                if implementation_type == "planted":
                    # 仕込み済みとしてマーク(実際の更新はRepositoryで行う)
                    return True
                if implementation_type == "resolved":
                    # 回収済みとしてマーク(実際の更新はRepositoryで行う)
                    return True
        return False

    def get_issues_requiring_confirmation(self) -> list[ForeshadowingIssue]:
        """確認が必要な問題を取得"""
        if not self.validation_result:
            return []

        if self.config.enable_interactive_confirmation:
            return self.validation_result.issues
        # インタラクティブ確認が無効の場合はクリティカルな問題のみ
        return self.validation_result.get_issues_by_severity(ForeshadowingSeverity.CRITICAL)
