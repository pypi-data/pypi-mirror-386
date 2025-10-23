#!/usr/bin/env python3

"""Domain.services.foreshadowing_validation_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""
伏線検証ドメインサービス
SPEC-FORESHADOWING-001準拠のビジネスロジック
"""


import re

# Phase 6修正: Service → Repository循環依存解消
from typing import Protocol

from noveler.domain.entities.foreshadowing_validation_session import ForeshadowingValidationSession
from noveler.domain.value_objects.foreshadowing import Foreshadowing
from noveler.domain.value_objects.foreshadowing_issue import (
    ForeshadowingDetectionResult,
    ForeshadowingValidationConfig,
)


class IForeshadowingRepository(Protocol):
    """伏線リポジトリインターフェース（循環依存解消）"""

    def find_by_episode(self, episode_number: int) -> list[Foreshadowing]: ...
    def find_unresolved(self) -> list[Foreshadowing]: ...
    def save_foreshadowing(self, foreshadowing: Foreshadowing) -> bool: ...


class ForeshadowingValidationService:
    """伏線検証ドメインサービス"""

    def __init__(self, foreshadowing_repository: IForeshadowingRepository) -> None:
        self._foreshadowing_repository = foreshadowing_repository

    def create_validation_session(
        self,
        project_id: str,
        episode_number: int,
        manuscript_content: str,
        config: ForeshadowingValidationConfig | None = None,
    ) -> ForeshadowingValidationSession:
        """伏線検証セッションを作成"""

        # プロジェクトの全伏線を読み込み
        all_foreshadowing = self._foreshadowing_repository.load_all(project_id)

        # 該当エピソードに関連する伏線のみ抽出
        relevant_foreshadowing = self._filter_relevant_foreshadowing(all_foreshadowing, episode_number)

        # セッション作成
        return ForeshadowingValidationSession(
            project_id=project_id,
            episode_number=episode_number,
            manuscript_content=manuscript_content,
            foreshadowing_list=relevant_foreshadowing,
            config=config or ForeshadowingValidationConfig(),
        )

    def validate_episode_foreshadowing(self, session: ForeshadowingValidationSession) -> ForeshadowingDetectionResult:
        """エピソードの伏線を検証"""

        if session.is_completed():
            return session.validation_result

        # セッションで検証実行
        return session.validate_foreshadowing()

    def _filter_relevant_foreshadowing(
        self, all_foreshadowing: list[Foreshadowing], episode_number: int
    ) -> list[Foreshadowing]:
        """該当エピソードに関連する伏線を抽出"""
        relevant = []

        for foreshadowing in all_foreshadowing:
            # 仕込み予定エピソードかチェック
            if (
                hasattr(foreshadowing, "planting")
                and self._extract_episode_number(foreshadowing.planting.episode) == episode_number
            ):
                relevant.append(foreshadowing)
                continue

            # 回収予定エピソードかチェック
            if (
                hasattr(foreshadowing, "resolution")
                and self._extract_episode_number(foreshadowing.resolution.episode) == episode_number
            ):
                relevant.append(foreshadowing)
                continue

            # ヒント予定エピソードかチェック
            if hasattr(foreshadowing, "hints"):
                for hint in foreshadowing.hints:
                    if self._extract_episode_number(hint.get("episode", "")) == episode_number:
                        relevant.append(foreshadowing)
                        break

        return relevant

    def _extract_episode_number(self, episode_str: str) -> int:
        """エピソード文字列から番号を抽出"""

        # 文字列でない場合は0を返す(モックオブジェクト対応)
        if not isinstance(episode_str, str):
            return 0

        match = re.search(r"第(\d+)話", episode_str)
        if match:
            return int(match.group(1))
        return 0

    def update_foreshadowing_implementation_status(
        self, project_id: str, foreshadowing_id: str, new_status: str, _implementation_note: str = ""
    ) -> bool:
        """伏線の実装ステータスを更新"""

        try:
            # 伏線を取得
            foreshadowing = self._foreshadowing_repository.find_by_id(foreshadowing_id, project_id)

            if not foreshadowing:
                return False

            # ステータス更新のビジネスルール検証
            return self._validate_status_transition(foreshadowing.status.value, new_status)

        except Exception:
            return False

    def _validate_status_transition(self, current_status: str, new_status: str) -> bool:
        """ステータス遷移の妥当性を検証"""

        # 許可されたステータス遷移
        valid_transitions = {
            "planned": ["planted"],
            "planted": ["resolved", "ready_to_resolve"],
            "ready_to_resolve": ["resolved"],
            "resolved": [],  # 完了後は変更不可
        }

        return new_status in valid_transitions.get(current_status, [])

    def generate_improvement_suggestions(self, detection_result: ForeshadowingDetectionResult) -> list[str]:
        """改善提案を生成"""

        suggestions = []

        # 仕込み漏れの提案
        for issue in detection_result.get_planting_issues():
            if issue.expected_content:
                suggestions.append(f"💡 {issue.foreshadowing_id}: {issue.expected_content} を仕込んでください")

            if issue.suggestion:
                suggestions.append(f"   {issue.suggestion}")

        # 回収漏れの提案
        for issue in detection_result.get_resolution_issues():
            if issue.expected_content:
                suggestions.append(f"🎯 {issue.foreshadowing_id}: {issue.expected_content} で回収してください")

            if issue.suggestion:
                suggestions.append(f"   {issue.suggestion}")

        return suggestions
