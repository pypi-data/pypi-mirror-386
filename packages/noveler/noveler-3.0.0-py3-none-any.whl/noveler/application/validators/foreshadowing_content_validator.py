#!/usr/bin/env python3

"""Application.validators.foreshadowing_content_validator
Where: Application validator ensuring foreshadowing content stays consistent.
What: Validates foreshadowing definitions and content relationships across episodes.
Why: Prevents foreshadowing drift by catching inconsistencies early.
"""

from __future__ import annotations

"""伏線管理・原稿内容の整合性検証

原稿と伏線管理.yamlの整合性をチェックし、以下を検証:
- 仕込み予定の伏線が原稿に記述されているか
- 回収予定の伏線が適切に回収されているか
- 未解決の伏線を適切に管理できているか

DDD準拠設計:
- Domain層のValidatorとして実装
- Infrastructure層のRepositoryを利用
- Application層から呼び出し
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from pathlib import Path


class ForeshadowingValidationSeverity(Enum):
    """伏線検証の重要度"""
    CRITICAL = "critical"  # 致命的: 重要な伏線が未実装
    HIGH = "high"         # 高: 伏線の品質に重大な問題
    MEDIUM = "medium"     # 中: 改善推奨
    LOW = "low"          # 低: 軽微な改善点


@dataclass
class ForeshadowingValidationIssue:
    """伏線検証で発見された問題"""
    foreshadowing_id: str
    issue_type: str
    severity: ForeshadowingValidationSeverity
    message: str
    line_number: int | None = None
    suggestion: str | None = None
    expected_content: str | None = None
    actual_content: str | None = None


@dataclass
class ForeshadowingValidationResult:
    """伏線検証結果"""
    episode_number: int
    total_foreshadowing_checked: int
    planted_count: int
    resolved_count: int
    missing_plantings: list[str]
    missing_resolutions: list[str]
    issues: list[ForeshadowingValidationIssue]
    score: float

    def has_critical_issues(self) -> bool:
        """致命的な問題があるか"""
        return any(issue.severity == ForeshadowingValidationSeverity.CRITICAL for issue in self.issues)

    def get_issues_by_severity(self, severity: ForeshadowingValidationSeverity) -> list[ForeshadowingValidationIssue]:
        """重要度別で問題を取得"""
        return [issue for issue in self.issues if issue.severity == severity]


class ForeshadowingContentValidator:
    """伏線管理・原稿内容の整合性検証クラス

    SPEC-FORESHADOWING-VALIDATION-001: 伏線・原稿整合性検証システム
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.foreshadowing_file = project_root / "50_管理資料" / "伏線管理.yaml"

    def validate_episode(self, episode_number: int, manuscript_content: str) -> ForeshadowingValidationResult:
        """指定エピソードの伏線実装状況を検証

        Args:
            episode_number: 検証対象の話数
            manuscript_content: 原稿内容

        Returns:
            ForeshadowingValidationResult: 検証結果
        """
        if not self.foreshadowing_file.exists():
            return self._create_no_foreshadowing_result(episode_number)

        try:
            foreshadowing_data = self._load_foreshadowing_data()
            return self._validate_episode_content(episode_number, manuscript_content, foreshadowing_data)
        except Exception as e:
            return self._create_error_result(episode_number, str(e))

    def _load_foreshadowing_data(self) -> dict[str, Any]:
        """伏線管理データを読み込み"""
        with self.foreshadowing_file.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _validate_episode_content(self, episode_number: int, manuscript_content: str,
                                foreshadowing_data: dict[str, Any]) -> ForeshadowingValidationResult:
        """エピソード内容の詳細検証"""
        issues = []
        planted_count = 0
        resolved_count = 0
        missing_plantings = []
        missing_resolutions = []

        foreshadowings = foreshadowing_data.get("foreshadowing", {})
        total_checked = 0

        for foreshadowing_id, foreshadowing_info in foreshadowings.items():
            total_checked += 1

            # 仕込み検証
            planting_result = self._validate_planting(episode_number, manuscript_content,
                                                    foreshadowing_id, foreshadowing_info)
            if planting_result.should_be_planted:
                if planting_result.is_planted:
                    planted_count += 1
                else:
                    missing_plantings.append(foreshadowing_id)
                    issues.append(ForeshadowingValidationIssue(
                        foreshadowing_id=foreshadowing_id,
                        issue_type="missing_planting",
                        severity=self._determine_planting_severity(foreshadowing_info),
                        message=f"伏線「{foreshadowing_info.get('title', foreshadowing_id)}」の仕込みが見つかりません",
                        suggestion=f"仕込み方法: {foreshadowing_info.get('planting', {}).get('method', '未定義')}",
                        expected_content=foreshadowing_info.get("planting", {}).get("content", "")
                    ))

            # 回収検証
            resolution_result = self._validate_resolution(episode_number, manuscript_content,
                                                        foreshadowing_id, foreshadowing_info)
            if resolution_result.should_be_resolved:
                if resolution_result.is_resolved:
                    resolved_count += 1
                else:
                    missing_resolutions.append(foreshadowing_id)
                    issues.append(ForeshadowingValidationIssue(
                        foreshadowing_id=foreshadowing_id,
                        issue_type="missing_resolution",
                        severity=self._determine_resolution_severity(foreshadowing_info),
                        message=f"伏線「{foreshadowing_info.get('title', foreshadowing_id)}」の回収が見つかりません",
                        suggestion=f"回収方法: {foreshadowing_info.get('resolution', {}).get('method', '未定義')}",
                        expected_content=foreshadowing_info.get("resolution", {}).get("method", "")
                    ))

            # ヒント検証
            hint_issues = self._validate_hints(episode_number, manuscript_content,
                                             foreshadowing_id, foreshadowing_info)
            issues.extend(hint_issues)

        # スコア計算
        score = self._calculate_validation_score(total_checked, planted_count, resolved_count, issues)

        return ForeshadowingValidationResult(
            episode_number=episode_number,
            total_foreshadowing_checked=total_checked,
            planted_count=planted_count,
            resolved_count=resolved_count,
            missing_plantings=missing_plantings,
            missing_resolutions=missing_resolutions,
            issues=issues,
            score=score
        )

    @dataclass
    class PlantingValidationResult:
        should_be_planted: bool
        is_planted: bool
        confidence: float

    @dataclass
    class ResolutionValidationResult:
        should_be_resolved: bool
        is_resolved: bool
        confidence: float

    def _validate_planting(self, episode_number: int, manuscript_content: str,
                         foreshadowing_id: str, foreshadowing_info: dict[str, Any]) -> PlantingValidationResult:
        """伏線仕込みの検証"""
        planting_info = foreshadowing_info.get("planting", {})
        planting_episode = planting_info.get("episode", "")

        # このエピソードで仕込み予定かチェック
        should_be_planted = self._is_target_episode(episode_number, planting_episode)
        if not should_be_planted:
            return self.PlantingValidationResult(False, False, 1.0)

        # 仕込み内容をチェック
        expected_content = planting_info.get("content", "")
        method = planting_info.get("method", "")

        is_planted, confidence = self._search_content_in_manuscript(manuscript_content, expected_content, method)

        return self.PlantingValidationResult(should_be_planted, is_planted, confidence)

    def _validate_resolution(self, episode_number: int, manuscript_content: str,
                           foreshadowing_id: str, foreshadowing_info: dict[str, Any]) -> ResolutionValidationResult:
        """伏線回収の検証"""
        resolution_info = foreshadowing_info.get("resolution", {})
        resolution_episode = resolution_info.get("episode", "")

        # このエピソードで回収予定かチェック
        should_be_resolved = self._is_target_episode(episode_number, resolution_episode)
        if not should_be_resolved:
            return self.ResolutionValidationResult(False, False, 1.0)

        # 回収内容をチェック
        method = resolution_info.get("method", "")
        impact = resolution_info.get("impact", "")

        # より複雑な回収検出ロジック
        is_resolved, confidence = self._search_resolution_in_manuscript(manuscript_content, method, impact)

        return self.ResolutionValidationResult(should_be_resolved, is_resolved, confidence)

    def _validate_hints(self, episode_number: int, manuscript_content: str,
                       foreshadowing_id: str, foreshadowing_info: dict[str, Any]) -> list[ForeshadowingValidationIssue]:
        """ヒント実装の検証"""
        issues = []
        hints = foreshadowing_info.get("hints", [])

        for hint in hints:
            hint_episode = hint.get("episode", "")
            if self._is_target_episode(episode_number, hint_episode):
                hint_content = hint.get("content", "")
                found, _ = self._search_content_in_manuscript(manuscript_content, hint_content, "hint")

                if not found:
                    issues.append(ForeshadowingValidationIssue(
                        foreshadowing_id=foreshadowing_id,
                        issue_type="missing_hint",
                        severity=ForeshadowingValidationSeverity.MEDIUM,
                        message=f"予定されたヒントが見つかりません: {hint_content[:50]}...",
                        suggestion="ヒントを適切に配置してください"
                    ))

        return issues

    def _is_target_episode(self, current_episode: int, target_episode: str) -> bool:
        """指定エピソードが対象かチェック"""
        if not target_episode:
            return False

        # "第001話" -> 1 に変換
        match = re.search(r"第(\d+)話", target_episode)
        if match:
            target_num = int(match.group(1))
            return current_episode == target_num

        # 数字のみの場合
        try:
            target_num = int(target_episode)
            return current_episode == target_num
        except ValueError:
            return False

    def _search_content_in_manuscript(self, manuscript: str, expected_content: str, method: str) -> tuple[bool, float]:
        """原稿内で期待する内容を検索"""
        if not expected_content.strip():
            return False, 0.0

        manuscript_lower = manuscript.lower()
        expected_lower = expected_content.lower()

        # 直接一致検索
        if expected_lower in manuscript_lower:
            return True, 1.0

        # キーワード分割検索
        keywords = [word.strip() for word in expected_content.split() if len(word.strip()) > 1]
        if not keywords:
            return False, 0.0

        found_keywords = sum(1 for keyword in keywords if keyword.lower() in manuscript_lower)
        confidence = found_keywords / len(keywords)

        # 閾値判定
        return confidence >= 0.6, confidence

    def _search_resolution_in_manuscript(self, manuscript: str, method: str, impact: str) -> tuple[bool, float]:
        """原稿内で伏線回収を検索"""
        total_score = 0.0
        checks = 0

        if method:
            found, confidence = self._search_content_in_manuscript(manuscript, method, "resolution")
            total_score += confidence
            checks += 1

        if impact:
            found, confidence = self._search_content_in_manuscript(manuscript, impact, "impact")
            total_score += confidence
            checks += 1

        if checks == 0:
            return False, 0.0

        average_confidence = total_score / checks
        return average_confidence >= 0.5, average_confidence

    def _determine_planting_severity(self, foreshadowing_info: dict[str, Any]) -> ForeshadowingValidationSeverity:
        """仕込み不備の重要度を判定"""
        importance = foreshadowing_info.get("importance", 3)

        if importance >= 5:
            return ForeshadowingValidationSeverity.CRITICAL
        if importance >= 4:
            return ForeshadowingValidationSeverity.HIGH
        if importance >= 3:
            return ForeshadowingValidationSeverity.MEDIUM
        return ForeshadowingValidationSeverity.LOW

    def _determine_resolution_severity(self, foreshadowing_info: dict[str, Any]) -> ForeshadowingValidationSeverity:
        """回収不備の重要度を判定"""
        importance = foreshadowing_info.get("importance", 3)

        # 回収は仕込みより重要度を上げる
        if importance >= 4:
            return ForeshadowingValidationSeverity.CRITICAL
        if importance >= 3:
            return ForeshadowingValidationSeverity.HIGH
        if importance >= 2:
            return ForeshadowingValidationSeverity.MEDIUM
        return ForeshadowingValidationSeverity.LOW

    def _calculate_validation_score(self, total_checked: int, planted_count: int,
                                  resolved_count: int, issues: list[ForeshadowingValidationIssue]) -> float:
        """検証スコアを計算"""
        if total_checked == 0:
            return 100.0

        base_score = 100.0

        # 問題による減点
        for issue in issues:
            if issue.severity == ForeshadowingValidationSeverity.CRITICAL:
                base_score -= 25.0
            elif issue.severity == ForeshadowingValidationSeverity.HIGH:
                base_score -= 15.0
            elif issue.severity == ForeshadowingValidationSeverity.MEDIUM:
                base_score -= 8.0
            elif issue.severity == ForeshadowingValidationSeverity.LOW:
                base_score -= 3.0

        return max(base_score, 0.0)

    def _create_no_foreshadowing_result(self, episode_number: int) -> ForeshadowingValidationResult:
        """伏線管理ファイルが存在しない場合の結果"""
        return ForeshadowingValidationResult(
            episode_number=episode_number,
            total_foreshadowing_checked=0,
            planted_count=0,
            resolved_count=0,
            missing_plantings=[],
            missing_resolutions=[],
            issues=[],
            score=100.0  # 伏線がなければ問題なし
        )

    def _create_error_result(self, episode_number: int, error_message: str) -> ForeshadowingValidationResult:
        """エラー時の結果"""
        return ForeshadowingValidationResult(
            episode_number=episode_number,
            total_foreshadowing_checked=0,
            planted_count=0,
            resolved_count=0,
            missing_plantings=[],
            missing_resolutions=[],
            issues=[ForeshadowingValidationIssue(
                foreshadowing_id="SYSTEM",
                issue_type="validation_error",
                severity=ForeshadowingValidationSeverity.HIGH,
                message=f"伏線検証エラー: {error_message}",
                suggestion="伏線管理.yamlファイルの形式を確認してください"
            )],
            score=50.0
        )
