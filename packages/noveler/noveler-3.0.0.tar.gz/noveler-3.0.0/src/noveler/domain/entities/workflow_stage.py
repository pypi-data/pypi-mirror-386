#!/usr/bin/env python3

"""Domain.entities.workflow_stage
Where: Domain entity describing workflow stages.
What: Encapsulates stage metadata, transitions, and ordering.
Why: Provides structured workflow definitions for orchestration.
"""

from __future__ import annotations

from typing import Any

"""ワークフロー段階エンティティ

プロット作成ワークフローの各段階を表現するエンティティ
ビジネスルールを含む
"""


from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from noveler.domain.value_objects.prerequisite_rule import PrerequisiteRule


class FileChecker(Protocol):
    """ファイル存在確認プロトコル"""

    def exists(self, file_path: str) -> bool:
        """ファイルが存在するかチェック"""
        ...


@dataclass(frozen=True)
class PrerequisiteCheckResult:
    """前提条件チェック結果"""

    rule: PrerequisiteRule
    file_path: str
    satisfied: bool


class WorkflowStage:
    """ワークフロー段階エンティティ"""

    def __init__(self, stage_type: str, prerequisites: list, output_files: list | None = None) -> None:
        """Args:
        stage_type: ワークフロー段階タイプ
        prerequisites: 前提条件ルールのリスト
        output_files: 出力ファイルのリスト
        """
        self.stage_type = stage_type
        self.prerequisites = prerequisites
        self.output_files = output_files or []

    def check_prerequisites(
        self, file_checker: object, **parameters: object
    ) -> tuple[bool, list[PrerequisiteCheckResult]]:
        """前提条件をチェック

        Args:
            file_checker: ファイル存在確認オブジェクト
            **parameters: パス展開用パラメータ

        Returns:
            Tuple[bool, list[PrerequisiteCheckResult]]: (全て満たしているか, 詳細結果)
        """
        results: list[Any] = []
        all_satisfied = True

        for rule in self.prerequisites:
            expanded_path = rule.expand_path(**parameters)
            exists = file_checker.exists(expanded_path)

            result = PrerequisiteCheckResult(
                rule=rule,
                file_path=expanded_path,
                satisfied=exists,
            )

            results.append(result)

            # 必須ファイルが不足している場合
            if rule.required and not exists:
                all_satisfied = False

        return all_satisfied, results

    def has_output_conflicts(self, file_checker: FileChecker, **parameters: object) -> bool:
        """出力ファイルが既に存在するかチェック

        Args:
            file_checker: ファイル存在確認オブジェクト
            **parameters: パス展開用パラメータ

        Returns:
            bool: 衝突する場合True
        """
        for output_file in self.output_files:
            try:
                expanded_path = output_file.format(**parameters)
            except KeyError:
                expanded_path = output_file

            if file_checker.exists(expanded_path):
                return True

        return False
