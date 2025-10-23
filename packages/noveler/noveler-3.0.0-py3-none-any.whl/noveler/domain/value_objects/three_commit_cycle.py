"""Domain.value_objects.three_commit_cycle
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""3コミット開発サイクル管理Value Object

仕様書: B20開発作業指示書準拠
"""


from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class CommitStage(Enum):
    """コミット段階定義"""

    COMMIT_1_SPEC = "commit_1_specification"  # Commit 1: 仕様書・設計
    COMMIT_2_IMPL = "commit_2_implementation"  # Commit 2: 実装・テスト
    COMMIT_3_DOC = "commit_3_documentation"  # Commit 3: ドキュメント・統合


class CommitRequirement(Enum):
    """コミット要件定義"""

    # Commit 1 要件
    SPECIFICATION_CREATED = "specification_created"
    DESIGN_DOCUMENT_CREATED = "design_document_created"
    CODEMAP_UPDATED = "codemap_updated"

    # Commit 2 要件
    IMPLEMENTATION_COMPLETED = "implementation_completed"
    UNIT_TESTS_CREATED = "unit_tests_created"
    INTEGRATION_TESTS_CREATED = "integration_tests_created"
    ALL_TESTS_PASSING = "all_tests_passing"

    # Commit 3 要件
    DOCUMENTATION_UPDATED = "documentation_updated"
    CHANGELOG_UPDATED = "changelog_updated"
    INTEGRATION_VERIFIED = "integration_verified"


@dataclass(frozen=True)
class ThreeCommitCycle:
    """3コミット開発サイクル管理"""

    cycle_id: str
    feature_name: str
    current_stage: CommitStage
    completed_requirements: frozenset[CommitRequirement]
    pending_requirements: frozenset[CommitRequirement]
    commit_history: tuple[str, ...]  # (commit_hash_1, commit_hash_2, commit_hash_3)
    stage_metadata: dict[str, Any]
    created_at: datetime

    def __post_init__(self) -> None:
        """初期化後検証"""
        if not isinstance(self.current_stage, CommitStage):
            msg = f"無効なコミット段階: {self.current_stage}"
            raise ValueError(msg)

        # 要件の重複チェック
        overlap = self.completed_requirements & self.pending_requirements
        if overlap:
            msg = f"要件の重複検出: {overlap}"
            raise ValueError(msg)

        # コミット履歴の検証
        if len(self.commit_history) > 3:
            msg = "コミット履歴は最大3つまでです"
            raise ValueError(msg)

    @classmethod
    def start_new_cycle(cls, feature_name: str) -> ThreeCommitCycle:
        """新しい3コミットサイクルの開始"""
        return cls(
            cycle_id=f"{feature_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            feature_name=feature_name,
            current_stage=CommitStage.COMMIT_1_SPEC,
            completed_requirements=frozenset(),
            pending_requirements=frozenset(
                [
                    CommitRequirement.SPECIFICATION_CREATED,
                    CommitRequirement.DESIGN_DOCUMENT_CREATED,
                    CommitRequirement.CODEMAP_UPDATED,
                ]
            ),
            commit_history=(),
            stage_metadata={"description": "Commit 1: 仕様書・設計段階"},
            created_at=datetime.now(timezone.utc),
        )

    def advance_to_commit_2(self, commit_1_hash: str) -> ThreeCommitCycle:
        """Commit 2段階への進行"""
        if self.current_stage != CommitStage.COMMIT_1_SPEC:
            msg = f"Commit 2への進行は不可能な段階: {self.current_stage}"
            raise ValueError(msg)

        # Commit 1要件の完了確認
        commit_1_requirements = {
            CommitRequirement.SPECIFICATION_CREATED,
            CommitRequirement.DESIGN_DOCUMENT_CREATED,
            CommitRequirement.CODEMAP_UPDATED,
        }

        if not commit_1_requirements.issubset(self.completed_requirements):
            missing = commit_1_requirements - self.completed_requirements
            msg = f"Commit 1要件が未完了: {missing}"
            raise ValueError(msg)

        return ThreeCommitCycle(
            cycle_id=self.cycle_id,
            feature_name=self.feature_name,
            current_stage=CommitStage.COMMIT_2_IMPL,
            completed_requirements=self.completed_requirements,
            pending_requirements=frozenset(
                [
                    CommitRequirement.IMPLEMENTATION_COMPLETED,
                    CommitRequirement.UNIT_TESTS_CREATED,
                    CommitRequirement.INTEGRATION_TESTS_CREATED,
                    CommitRequirement.ALL_TESTS_PASSING,
                ]
            ),
            commit_history=(*self.commit_history, commit_1_hash),
            stage_metadata={"description": "Commit 2: 実装・テスト段階"},
            created_at=self.created_at,
        )

    def advance_to_commit_3(self, commit_2_hash: str) -> ThreeCommitCycle:
        """Commit 3段階への進行"""
        if self.current_stage != CommitStage.COMMIT_2_IMPL:
            msg = f"Commit 3への進行は不可能な段階: {self.current_stage}"
            raise ValueError(msg)

        # Commit 2要件の完了確認
        commit_2_requirements = {
            CommitRequirement.IMPLEMENTATION_COMPLETED,
            CommitRequirement.UNIT_TESTS_CREATED,
            CommitRequirement.INTEGRATION_TESTS_CREATED,
            CommitRequirement.ALL_TESTS_PASSING,
        }

        if not commit_2_requirements.issubset(self.completed_requirements):
            missing = commit_2_requirements - self.completed_requirements
            msg = f"Commit 2要件が未完了: {missing}"
            raise ValueError(msg)

        return ThreeCommitCycle(
            cycle_id=self.cycle_id,
            feature_name=self.feature_name,
            current_stage=CommitStage.COMMIT_3_DOC,
            completed_requirements=self.completed_requirements,
            pending_requirements=frozenset(
                [
                    CommitRequirement.DOCUMENTATION_UPDATED,
                    CommitRequirement.CHANGELOG_UPDATED,
                    CommitRequirement.INTEGRATION_VERIFIED,
                ]
            ),
            commit_history=(*self.commit_history, commit_2_hash),
            stage_metadata={"description": "Commit 3: ドキュメント・統合段階"},
            created_at=self.created_at,
        )

    def complete_cycle(self, commit_3_hash: str) -> ThreeCommitCycle:
        """サイクル完了"""
        if self.current_stage != CommitStage.COMMIT_3_DOC:
            msg = f"サイクル完了は不可能な段階: {self.current_stage}"
            raise ValueError(msg)

        # Commit 3要件の完了確認
        commit_3_requirements = {
            CommitRequirement.DOCUMENTATION_UPDATED,
            CommitRequirement.CHANGELOG_UPDATED,
            CommitRequirement.INTEGRATION_VERIFIED,
        }

        if not commit_3_requirements.issubset(self.completed_requirements):
            missing = commit_3_requirements - self.completed_requirements
            msg = f"Commit 3要件が未完了: {missing}"
            raise ValueError(msg)

        return ThreeCommitCycle(
            cycle_id=self.cycle_id,
            feature_name=self.feature_name,
            current_stage=self.current_stage,
            completed_requirements=self.completed_requirements,
            pending_requirements=frozenset(),
            commit_history=(*self.commit_history, commit_3_hash),
            stage_metadata={"description": "サイクル完了", "completed": True},
            created_at=self.created_at,
        )

    def mark_requirement_completed(self, requirement: CommitRequirement) -> ThreeCommitCycle:
        """要件完了マーク"""
        if requirement not in self.pending_requirements:
            msg = f"要件が未ペンディング: {requirement}"
            raise ValueError(msg)

        new_completed = self.completed_requirements | {requirement}
        new_pending = self.pending_requirements - {requirement}

        return ThreeCommitCycle(
            cycle_id=self.cycle_id,
            feature_name=self.feature_name,
            current_stage=self.current_stage,
            completed_requirements=new_completed,
            pending_requirements=new_pending,
            commit_history=self.commit_history,
            stage_metadata=self.stage_metadata,
            created_at=self.created_at,
        )

    def get_current_stage_requirements(self) -> list[CommitRequirement]:
        """現在段階の要件一覧"""
        stage_requirements = {
            CommitStage.COMMIT_1_SPEC: [
                CommitRequirement.SPECIFICATION_CREATED,
                CommitRequirement.DESIGN_DOCUMENT_CREATED,
                CommitRequirement.CODEMAP_UPDATED,
            ],
            CommitStage.COMMIT_2_IMPL: [
                CommitRequirement.IMPLEMENTATION_COMPLETED,
                CommitRequirement.UNIT_TESTS_CREATED,
                CommitRequirement.INTEGRATION_TESTS_CREATED,
                CommitRequirement.ALL_TESTS_PASSING,
            ],
            CommitStage.COMMIT_3_DOC: [
                CommitRequirement.DOCUMENTATION_UPDATED,
                CommitRequirement.CHANGELOG_UPDATED,
                CommitRequirement.INTEGRATION_VERIFIED,
            ],
        }

        return stage_requirements.get(self.current_stage, [])

    def get_next_required_actions(self) -> list[str]:
        """次に必要な作業の取得"""
        actions = []

        for requirement in self.pending_requirements:
            if requirement == CommitRequirement.SPECIFICATION_CREATED:
                actions.append("仕様書の作成（specs/ディレクトリ）")
            elif requirement == CommitRequirement.DESIGN_DOCUMENT_CREATED:
                actions.append("設計ドキュメントの作成")
            elif requirement == CommitRequirement.CODEMAP_UPDATED:
                actions.append("CODEMAPの更新")
            elif requirement == CommitRequirement.IMPLEMENTATION_COMPLETED:
                actions.append("実装の完了")
            elif requirement == CommitRequirement.UNIT_TESTS_CREATED:
                actions.append("単体テストの作成")
            elif requirement == CommitRequirement.INTEGRATION_TESTS_CREATED:
                actions.append("統合テストの作成")
            elif requirement == CommitRequirement.ALL_TESTS_PASSING:
                actions.append("全テストの成功確認")
            elif requirement == CommitRequirement.DOCUMENTATION_UPDATED:
                actions.append("ドキュメントの更新")
            elif requirement == CommitRequirement.CHANGELOG_UPDATED:
                actions.append("変更ログの更新")
            elif requirement == CommitRequirement.INTEGRATION_VERIFIED:
                actions.append("統合検証の実行")

        return actions

    def can_commit_now(self) -> bool:
        """現在コミット可能か判定"""
        return len(self.pending_requirements) == 0

    def get_completion_percentage(self) -> float:
        """完了率の計算"""
        current_stage_requirements = self.get_current_stage_requirements()
        if not current_stage_requirements:
            return 100.0

        completed_count = sum(1 for req in current_stage_requirements if req in self.completed_requirements)

        return (completed_count / len(current_stage_requirements)) * 100.0

    def get_overall_progress(self) -> dict[str, Any]:
        """全体進捗の取得"""
        total_commits = 3
        completed_commits = len(self.commit_history)

        if len(self.pending_requirements) == 0 and completed_commits < total_commits:
            completed_commits += 1  # 次のコミット準備完了

        return {
            "completed_commits": completed_commits,
            "total_commits": total_commits,
            "current_stage": self.current_stage.value,
            "stage_completion": self.get_completion_percentage(),
            "overall_completion": (completed_commits / total_commits) * 100.0,
            "commit_history": list(self.commit_history),
            "is_cycle_completed": self.is_cycle_completed(),
        }

    def is_cycle_completed(self) -> bool:
        """サイクル完了判定"""
        return (
            len(self.commit_history) == 3
            and len(self.pending_requirements) == 0
            and self.stage_metadata.get("completed", False)
        )

    def get_stage_description(self) -> str:
        """段階説明の取得"""
        descriptions = {
            CommitStage.COMMIT_1_SPEC: "Commit 1: 仕様書・設計段階",
            CommitStage.COMMIT_2_IMPL: "Commit 2: 実装・テスト段階",
            CommitStage.COMMIT_3_DOC: "Commit 3: ドキュメント・統合段階",
        }

        return descriptions.get(self.current_stage, "不明な段階")

    def get_commit_message_template(self) -> str:
        """コミットメッセージテンプレートの取得"""
        templates = {
            CommitStage.COMMIT_1_SPEC: f"feat: {self.feature_name} 仕様書・設計完了",
            CommitStage.COMMIT_2_IMPL: f"feat: {self.feature_name} 実装・テスト完了",
            CommitStage.COMMIT_3_DOC: f"docs: {self.feature_name} ドキュメント・統合完了",
        }

        return templates.get(self.current_stage, f"feat: {self.feature_name}")
