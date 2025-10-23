"""Domain.value_objects.b20_development_stage
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""B20開発プロセス段階管理Value Object

仕様書: B20開発作業指示書準拠
"""


from dataclasses import dataclass
from enum import Enum


class DevelopmentStage(Enum):
    """開発段階定義"""

    SPECIFICATION_REQUIRED = "specification_required"  # 仕様書作成必須段階
    CODEMAP_CHECK_REQUIRED = "codemap_check_required"  # CODEMAP確認必須段階
    IMPLEMENTATION_ALLOWED = "implementation_allowed"  # 実装許可段階
    TESTING_REQUIRED = "testing_required"  # テスト実装必須段階
    COMMIT_ALLOWED = "commit_allowed"  # コミット許可段階


class StageRequirement(Enum):
    """段階別要件定義"""

    SPEC_DOCUMENT_EXISTS = "spec_document_exists"
    CODEMAP_UPDATED = "codemap_updated"
    IMPORT_CONFLICTS_CHECKED = "import_conflicts_checked"
    DDD_LAYER_PLACEMENT_VALIDATED = "ddd_layer_placement_validated"
    EXISTING_IMPLEMENTATION_CHECKED = "existing_implementation_checked"
    TEST_IMPLEMENTATION_COMPLETED = "test_implementation_completed"


@dataclass(frozen=True)
class B20DevelopmentStage:
    """B20開発プロセス段階管理"""

    current_stage: DevelopmentStage
    completed_requirements: frozenset[StageRequirement]
    pending_requirements: frozenset[StageRequirement]
    stage_metadata: dict[str, str]

    def __post_init__(self) -> None:
        """初期化後検証"""
        if not isinstance(self.current_stage, DevelopmentStage):
            msg = f"無効な開発段階: {self.current_stage}"
            raise ValueError(msg)

        # 要件の重複チェック
        overlap = self.completed_requirements & self.pending_requirements
        if overlap:
            msg = f"要件の重複検出: {overlap}"
            raise ValueError(msg)

    @classmethod
    def create_specification_stage(cls) -> B20DevelopmentStage:
        """仕様書作成段階の作成"""
        return cls(
            current_stage=DevelopmentStage.SPECIFICATION_REQUIRED,
            completed_requirements=frozenset(),
            pending_requirements=frozenset([StageRequirement.SPEC_DOCUMENT_EXISTS]),
            stage_metadata={"description": "仕様書作成必須段階"},
        )

    @classmethod
    def create_codemap_check_stage(cls) -> B20DevelopmentStage:
        """CODEMAP確認段階の作成"""
        return cls(
            current_stage=DevelopmentStage.CODEMAP_CHECK_REQUIRED,
            completed_requirements=frozenset([StageRequirement.SPEC_DOCUMENT_EXISTS]),
            pending_requirements=frozenset(
                [
                    StageRequirement.CODEMAP_UPDATED,
                    StageRequirement.IMPORT_CONFLICTS_CHECKED,
                    StageRequirement.DDD_LAYER_PLACEMENT_VALIDATED,
                    StageRequirement.EXISTING_IMPLEMENTATION_CHECKED,
                ]
            ),
            stage_metadata={"description": "CODEMAP確認・競合チェック段階"},
        )

    @classmethod
    def create_implementation_stage(cls) -> B20DevelopmentStage:
        """実装許可段階の作成"""
        return cls(
            current_stage=DevelopmentStage.IMPLEMENTATION_ALLOWED,
            completed_requirements=frozenset(
                [
                    StageRequirement.SPEC_DOCUMENT_EXISTS,
                    StageRequirement.CODEMAP_UPDATED,
                    StageRequirement.IMPORT_CONFLICTS_CHECKED,
                    StageRequirement.DDD_LAYER_PLACEMENT_VALIDATED,
                    StageRequirement.EXISTING_IMPLEMENTATION_CHECKED,
                ]
            ),
            pending_requirements=frozenset([StageRequirement.TEST_IMPLEMENTATION_COMPLETED]),
            stage_metadata={"description": "実装許可段階"},
        )

    def advance_to_next_stage(self, completed_requirement: StageRequirement) -> B20DevelopmentStage:
        """次段階への進行"""
        if completed_requirement not in self.pending_requirements:
            msg = f"要件が未ペンディング: {completed_requirement}"
            raise ValueError(msg)

        new_completed = self.completed_requirements | {completed_requirement}
        new_pending = self.pending_requirements - {completed_requirement}

        # 次段階決定ロジック
        next_stage = self._determine_next_stage(new_completed, new_pending)
        blueprint = self._stage_blueprint(next_stage)

        refreshed_completed = frozenset(set(new_completed) | set(blueprint.completed_requirements))
        refreshed_pending = frozenset(
            (set(new_pending) | set(blueprint.pending_requirements)) - set(refreshed_completed)
        )

        return B20DevelopmentStage(
            current_stage=next_stage,
            completed_requirements=refreshed_completed,
            pending_requirements=refreshed_pending,
            stage_metadata=dict(blueprint.stage_metadata),
        )

    @classmethod
    def _stage_blueprint(cls, stage: DevelopmentStage) -> B20DevelopmentStage:
        if stage == DevelopmentStage.SPECIFICATION_REQUIRED:
            return cls.create_specification_stage()
        if stage == DevelopmentStage.CODEMAP_CHECK_REQUIRED:
            return cls.create_codemap_check_stage()
        if stage == DevelopmentStage.IMPLEMENTATION_ALLOWED:
            return cls.create_implementation_stage()
        if stage == DevelopmentStage.TESTING_REQUIRED:
            return cls(
                current_stage=DevelopmentStage.TESTING_REQUIRED,
                completed_requirements=frozenset(
                    [
                        StageRequirement.SPEC_DOCUMENT_EXISTS,
                        StageRequirement.CODEMAP_UPDATED,
                        StageRequirement.IMPORT_CONFLICTS_CHECKED,
                        StageRequirement.DDD_LAYER_PLACEMENT_VALIDATED,
                        StageRequirement.EXISTING_IMPLEMENTATION_CHECKED,
                    ]
                ),
                pending_requirements=frozenset([StageRequirement.TEST_IMPLEMENTATION_COMPLETED]),
                stage_metadata={"description": "テスト実装必須段階"},
            )
        if stage == DevelopmentStage.COMMIT_ALLOWED:
            return cls(
                current_stage=DevelopmentStage.COMMIT_ALLOWED,
                completed_requirements=frozenset(StageRequirement),
                pending_requirements=frozenset(),
                stage_metadata={"description": "コミット許可段階"},
            )
        return cls.create_specification_stage()

    def _determine_next_stage(
        self, completed: frozenset[StageRequirement], pending: frozenset[StageRequirement]
    ) -> DevelopmentStage:
        """次段階決定ロジック"""
        if StageRequirement.SPEC_DOCUMENT_EXISTS not in completed:
            return DevelopmentStage.SPECIFICATION_REQUIRED

        codemap_requirements = {
            StageRequirement.CODEMAP_UPDATED,
            StageRequirement.IMPORT_CONFLICTS_CHECKED,
            StageRequirement.DDD_LAYER_PLACEMENT_VALIDATED,
            StageRequirement.EXISTING_IMPLEMENTATION_CHECKED,
        }

        if not codemap_requirements.issubset(completed):
            return DevelopmentStage.CODEMAP_CHECK_REQUIRED

        if StageRequirement.TEST_IMPLEMENTATION_COMPLETED not in completed:
            return DevelopmentStage.IMPLEMENTATION_ALLOWED

        return DevelopmentStage.COMMIT_ALLOWED

    def get_next_required_actions(self) -> list[str]:
        """次に必要な作業項目の取得"""
        actions = []

        for requirement in self.pending_requirements:
            if requirement == StageRequirement.SPEC_DOCUMENT_EXISTS:
                actions.append("仕様書の作成（specs/ディレクトリ）")
            elif requirement == StageRequirement.CODEMAP_UPDATED:
                actions.append("CODEMAP更新の実行（novel codemap update）")
            elif requirement == StageRequirement.IMPORT_CONFLICTS_CHECKED:
                actions.append("インポート競合チェック実行")
            elif requirement == StageRequirement.DDD_LAYER_PLACEMENT_VALIDATED:
                actions.append("DDD層配置妥当性検証")
            elif requirement == StageRequirement.EXISTING_IMPLEMENTATION_CHECKED:
                actions.append("既存実装との競合チェック")
            elif requirement == StageRequirement.TEST_IMPLEMENTATION_COMPLETED:
                actions.append("テスト実装の完了")

        return actions

    def is_implementation_allowed(self) -> bool:
        """実装許可状態の確認"""
        return self.current_stage in [
            DevelopmentStage.IMPLEMENTATION_ALLOWED,
            DevelopmentStage.TESTING_REQUIRED,
            DevelopmentStage.COMMIT_ALLOWED,
        ]

    def is_commit_allowed(self) -> bool:
        """コミット許可状態の確認"""
        return self.current_stage == DevelopmentStage.COMMIT_ALLOWED

    def get_completion_percentage(self) -> float:
        """完了率の計算"""
        total_requirements = 6  # 全要件数
        completed_count = len(self.completed_requirements)
        return (completed_count / total_requirements) * 100.0

    def get_stage_description(self) -> str:
        """段階説明の取得"""
        descriptions = {
            DevelopmentStage.SPECIFICATION_REQUIRED: "仕様書作成が必要です",
            DevelopmentStage.CODEMAP_CHECK_REQUIRED: "CODEMAPの確認・更新が必要です",
            DevelopmentStage.IMPLEMENTATION_ALLOWED: "実装を開始できます",
            DevelopmentStage.TESTING_REQUIRED: "テスト実装が必要です",
            DevelopmentStage.COMMIT_ALLOWED: "コミットが許可されています",
        }
        return descriptions.get(self.current_stage, "未知の段階")
