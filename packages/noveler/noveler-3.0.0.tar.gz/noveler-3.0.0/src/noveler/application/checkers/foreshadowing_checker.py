#!/usr/bin/env python3

"""Application.checkers.foreshadowing_checker
Where: Application-layer checker orchestrating foreshadowing validation.
What: Runs validation sessions against foreshadowing definitions for episodes.
Why: Ensures manuscripts honour planned foreshadowing and reports actionable issues.
"""

from __future__ import annotations

"""伏線検証チェッカー

品質チェックシステムで使用する伏線検証チェッカーの実装
"""


from noveler.infrastructure.logging.unified_logger import get_logger as _get_logger

logger = _get_logger(__name__)
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from noveler.domain.value_objects.foreshadowing_issue import ForeshadowingIssue, ForeshadowingSeverity

# DDD準拠: Infrastructure層のパスサービスを使用（Presentation層依存を排除）
from noveler.infrastructure.adapters.path_service_adapter import create_path_service

if TYPE_CHECKING:
    from noveler.domain.entities.foreshadowing_validation_session import ForeshadowingValidationSession
    from noveler.domain.services.foreshadowing_validation_service import ForeshadowingValidationService
    from noveler.domain.value_objects.foreshadowing_issue import ForeshadowingDetectionResult


class ForeshadowingChecker:
    """伏線検証チェッカー"""

    def __init__(self, validation_service: ForeshadowingValidationService) -> None:
        self.validation_service = validation_service

    def execute(self, file_content: dict[str, Any]) -> dict[str, Any]:
        """伏線検証を実行"""
        try:
            filepath, manuscript_content = self._extract_file_info(file_content)
            project_root = self._find_project_root(filepath)
            episode_number = self._extract_episode_number_from_path(filepath)

            if not self._has_foreshadowing_file(project_root):
                return self._create_no_foreshadowing_result(episode_number)

            session = self._create_validation_session(project_root, episode_number, manuscript_content)
            result = self.validation_service.validate_episode_foreshadowing(session)

            return self._create_validation_result(result, episode_number)

        except Exception as e:
            return self._create_error_result(e)

    def _extract_file_info(self, file_content: dict[str, Any]) -> tuple[Path, str]:
        """ファイル情報を抽出"""
        if hasattr(file_content, "filepath"):
            return Path(file_content.filepath), file_content.content
        return Path(file_content.get("filepath", "")), file_content.get("content", "")

    def _has_foreshadowing_file(self, project_root: Path) -> bool:
        """伏線管理ファイルの存在確認"""
        return self.validation_service._foreshadowing_repository.exists(str(project_root))

    def _create_no_foreshadowing_result(self, episode_number: int) -> dict[str, Any]:
        """伏線管理ファイルがない場合の結果を作成"""
        return {
            "score": 100.0,
            "issues": [],
            "suggestions": ["伏線管理ファイルが存在しません。伏線を使用する場合は作成してください。"],
            "metadata": {"episode_number": episode_number},
            "execution_time": 0.01,
        }

    def _create_validation_session(
        self, project_root: Path, episode_number: int, manuscript_content: str
    ) -> ForeshadowingValidationSession:
        """検証セッションを作成"""
        return self.validation_service.create_validation_session(
            project_id=str(project_root), episode_number=episode_number, manuscript_content=manuscript_content
        )

    def _create_validation_result(self, result: ForeshadowingDetectionResult, episode_number: int) -> dict[str, Any]:
        """検証結果を作成"""
        issues = self._convert_issues(result.issues)
        score = self._calculate_score(result)
        suggestions = self.validation_service.generate_improvement_suggestions(result)

        return {
            "score": score,
            "issues": issues,
            "suggestions": suggestions,
            "metadata": {
                "episode_number": episode_number,
                "total_foreshadowing_checked": result.total_foreshadowing_checked,
                "has_critical_issues": result.has_critical_issues(),
            },
            "execution_time": 0.1,
        }

    def _convert_issues(self, issues: list[ForeshadowingIssue]) -> list[dict[str, Any]]:
        """課題を変換"""
        return [
            {
                "type": issue.issue_type.value,
                "severity": self._convert_foreshadowing_severity(issue.severity),
                "message": issue.message,
                "line": issue.episode_number,
                "column": 0,
                "suggestion": issue.suggestion,
            }
            for issue in issues
        ]

    def _calculate_score(self, result: ForeshadowingDetectionResult) -> float:
        """スコアを計算"""
        score = 100.0
        if result.has_critical_issues():
            score -= 30.0
        score -= len(result.get_issues_by_severity(ForeshadowingSeverity.HIGH)) * 10.0
        score -= len(result.get_issues_by_severity(ForeshadowingSeverity.MEDIUM)) * 5.0
        return max(score, 0.0)

    def _create_error_result(self, error: Exception) -> dict[str, Any]:
        """エラー結果を作成"""
        return {
            "score": 50.0,
            "issues": [
                {
                    "type": "foreshadowing_error",
                    "severity": "error",
                    "message": f"伏線検証エラー: {error}",
                    "line": 1,
                    "column": 0,
                    "suggestion": "伏線管理ファイルの形式を確認してください",
                }
            ],
            "suggestions": ["伏線検証中にエラーが発生しました"],
            "metadata": {},
            "execution_time": 0.05,
        }

    def _find_project_root(self, filepath: Path) -> Path:
        """ファイルパスからプロジェクトルートを推測"""
        # B30準拠: CommonPathService経由でプロジェクトルート検出
        current = filepath.parent
        while current != current.parent:
            try:
                # DDD準拠: Infrastructure層のパスサービスを使用
                path_service = create_path_service(current)
                # プロジェクトルートの判定
                if path_service.get_manuscript_dir().exists() and path_service.get_management_dir().exists():
                    return current
            except Exception as e:
                # セキュリティ改善: 例外を適切にログ記録
                logger.warning("プロジェクトルート検出エラー: %s", e)
            current = current.parent
        return filepath.parent.parent

    def _extract_episode_number_from_path(self, filepath: Path) -> int:
        """ファイルパスからエピソード番号を抽出"""
        filename = filepath.name
        match = re.search(r"第(\d+)話", filename)
        if match:
            return int(match.group(1))
        return 1

    def _convert_foreshadowing_severity(self, severity: ForeshadowingSeverity) -> str:
        """伏線の重要度を品質チェックの重要度に変換"""
        severity_mapping = {"CRITICAL": "error", "HIGH": "warning", "MEDIUM": "info", "LOW": "info"}
        severity_str = severity.value if hasattr(severity, "value") else str(severity)
        return severity_mapping.get(severity_str, "info")
