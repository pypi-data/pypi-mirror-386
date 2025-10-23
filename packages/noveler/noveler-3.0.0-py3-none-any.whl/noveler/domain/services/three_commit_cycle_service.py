#!/usr/bin/env python3

"""Domain.services.three_commit_cycle_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from datetime import datetime, timedelta

"""3コミット開発サイクル管理サービス

仕様書: B20開発作業指示書準拠
"""


import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from noveler.domain.value_objects.project_time import project_now
from noveler.domain.value_objects.three_commit_cycle import CommitRequirement, CommitStage, ThreeCommitCycle

if TYPE_CHECKING:

    from pathlib import Path

    from noveler.domain.interfaces.logger_service import ILoggerService

# DDD準拠: Domain層はInfrastructure層に依存しない
# ロガーは依存性注入で受け取る


@dataclass
class CycleStatus:
    """サイクル状態"""

    cycle_exists: bool
    current_cycle: ThreeCommitCycle | None
    can_proceed_to_next_stage: bool
    next_stage_requirements: list[str]
    warnings: list[str]
    errors: list[str]


@dataclass
class CommitValidationResult:
    """コミット妥当性検証結果"""

    is_valid: bool
    can_commit: bool
    stage: CommitStage
    completed_requirements: list[CommitRequirement]
    pending_requirements: list[CommitRequirement]
    validation_errors: list[str]
    warnings: list[str]


class ThreeCommitCycleService:
    """3コミット開発サイクル管理サービス"""

    def __init__(self, project_root: Path, logger: ILoggerService | None = None) -> None:
        """初期化

        Args:
            project_root: プロジェクトルート
            logger: ロガーインスタンス（依存性注入）
        """
        self.project_root = project_root
        self.cycles_dir = project_root / ".cycles"
        self.cycles_dir.mkdir(exist_ok=True)
        # B20/DDD準拠: Domain層はInfrastructure層に依存しない（依存性注入）
        self.logger = logger

    def start_new_cycle(self, feature_name: str) -> ThreeCommitCycle:
        """新しい3コミットサイクルの開始"""
        # 既存の未完了サイクルチェック
        existing_cycle = self.get_current_cycle(feature_name)
        if existing_cycle and not existing_cycle.is_cycle_completed():
            msg = f"未完了のサイクルが存在します: {feature_name}"
            raise ValueError(msg)

        # 新しいサイクル作成
        new_cycle = ThreeCommitCycle.start_new_cycle(feature_name)

        # サイクル保存
        self._save_cycle(new_cycle)

        if self.logger:
            self.logger.info("新しい3コミットサイクル開始: %s", feature_name)
        return new_cycle

    def get_current_cycle(self, feature_name: str) -> ThreeCommitCycle | None:
        """現在のサイクル取得"""
        cycle_file = self._get_cycle_file_path(feature_name)

        if not cycle_file.exists():
            return None

        try:
            with open(cycle_file, encoding="utf-8") as f:
                cycle_data: dict[str, Any] = json.load(f)

            return self._deserialize_cycle(cycle_data)

        except Exception as e:
            if self.logger:
                self.logger.exception("サイクル読み込みエラー: %s", e)
            return None

    def get_cycle_status(self, feature_name: str) -> CycleStatus:
        """サイクル状態の取得"""
        current_cycle = self.get_current_cycle(feature_name)

        if not current_cycle:
            return CycleStatus(
                cycle_exists=False,
                current_cycle=None,
                can_proceed_to_next_stage=False,
                next_stage_requirements=[],
                warnings=[],
                errors=["サイクルが存在しません"],
            )

        # 次段階への進行可能性チェック
        can_proceed = current_cycle.can_commit_now()
        next_requirements = current_cycle.get_next_required_actions()

        warnings = []
        errors: list[Any] = []

        # サイクル状態の検証
        if current_cycle.is_cycle_completed():
            warnings.append("サイクルは既に完了しています")
        elif not can_proceed:
            warnings.append("次段階への進行には追加の作業が必要です")

        return CycleStatus(
            cycle_exists=True,
            current_cycle=current_cycle,
            can_proceed_to_next_stage=can_proceed,
            next_stage_requirements=next_requirements,
            warnings=warnings,
            errors=errors,
        )

    def validate_commit_readiness(self, feature_name: str, commit_message: str | None = None) -> CommitValidationResult:
        """コミット準備状態の検証"""
        current_cycle = self.get_current_cycle(feature_name)

        if not current_cycle:
            return CommitValidationResult(
                is_valid=False,
                can_commit=False,
                stage=CommitStage.COMMIT_1_SPEC,
                completed_requirements=[],
                pending_requirements=[],
                validation_errors=["サイクルが存在しません"],
                warnings=[],
            )

        # 要件完了状態の検証
        validation_errors = []
        warnings = []

        # 現在段階の要件チェック
        can_commit = current_cycle.can_commit_now()

        if not can_commit:
            validation_errors.append("未完了の要件があります")

        # コミットメッセージの検証
        if commit_message:
            expected_template = current_cycle.get_commit_message_template()
            if not self._validate_commit_message(commit_message, expected_template):
                warnings.append(f"推奨コミットメッセージ: {expected_template}")

        # ファイル変更状態の検証
        file_validation_result = self._validate_file_changes(current_cycle)
        if file_validation_result["has_errors"]:
            validation_errors.extend(file_validation_result["errors"])
        if file_validation_result["has_warnings"]:
            warnings.extend(file_validation_result["warnings"])

        return CommitValidationResult(
            is_valid=len(validation_errors) == 0,
            can_commit=can_commit and len(validation_errors) == 0,
            stage=current_cycle.current_stage,
            completed_requirements=list(current_cycle.completed_requirements),
            pending_requirements=list(current_cycle.pending_requirements),
            validation_errors=validation_errors,
            warnings=warnings,
        )

    def advance_cycle_stage(self, feature_name: str, commit_hash: str) -> ThreeCommitCycle:
        """サイクル段階の進行"""
        current_cycle = self.get_current_cycle(feature_name)

        if not current_cycle:
            msg = "サイクルが存在しません"
            raise ValueError(msg)

        if not current_cycle.can_commit_now():
            msg = "段階進行の要件が未完了です"
            raise ValueError(msg)

        # 段階に応じた進行処理
        if current_cycle.current_stage == CommitStage.COMMIT_1_SPEC:
            updated_cycle = current_cycle.advance_to_commit_2(commit_hash)
        elif current_cycle.current_stage == CommitStage.COMMIT_2_IMPL:
            updated_cycle = current_cycle.advance_to_commit_3(commit_hash)
        elif current_cycle.current_stage == CommitStage.COMMIT_3_DOC:
            updated_cycle = current_cycle.complete_cycle(commit_hash)
        else:
            msg = f"不明な段階: {current_cycle.current_stage}"
            raise ValueError(msg)

        # 更新されたサイクルを保存
        self._save_cycle(updated_cycle)

        if self.logger:
            self.logger.info(f"サイクル段階進行: {feature_name} -> {updated_cycle.current_stage.value}")

        return updated_cycle

    def mark_requirement_completed(self, feature_name: str, requirement: CommitRequirement) -> ThreeCommitCycle:
        """要件完了マーク"""
        current_cycle = self.get_current_cycle(feature_name)

        if not current_cycle:
            msg = "サイクルが存在しません"
            raise ValueError(msg)

        updated_cycle = current_cycle.mark_requirement_completed(requirement)

        # 更新されたサイクルを保存
        self._save_cycle(updated_cycle)

        if self.logger:
            self.logger.info("要件完了: %s -> %s", feature_name, requirement.value)

        return updated_cycle

    def auto_detect_completed_requirements(self, feature_name: str) -> list[CommitRequirement]:
        """完了要件の自動検出"""
        current_cycle = self.get_current_cycle(feature_name)

        if not current_cycle:
            return []

        detected_requirements = []

        # 各要件の自動検出ロジック
        for requirement in current_cycle.pending_requirements:
            if self._detect_requirement_completion(requirement, feature_name):
                detected_requirements.append(requirement)

        return detected_requirements

    def cleanup_completed_cycles(self, max_age_days: int = 30) -> int:
        """完了済みサイクルのクリーンアップ"""

        cleanup_count = 0
        cutoff_date = project_now().datetime - timedelta(days=max_age_days)

        for cycle_file in self.cycles_dir.glob("*.json"):
            try:
                with open(cycle_file, encoding="utf-8") as f:
                    cycle_data: dict[str, Any] = json.load(f)

                cycle = self._deserialize_cycle(cycle_data)

                if cycle.is_cycle_completed() and cycle.created_at < cutoff_date:
                    # アーカイブディレクトリに移動
                    archive_dir = self.cycles_dir / "archive"
                    archive_dir.mkdir(exist_ok=True)

                    archive_file = archive_dir / cycle_file.name
                    cycle_file.rename(archive_file)
                    cleanup_count += 1

            except Exception as e:
                if self.logger:
                    self.logger.warning("サイクルクリーンアップエラー: %s - %s", cycle_file.name, e)

        if self.logger:
            self.logger.info("完了済みサイクルクリーンアップ: %s件", cleanup_count)
        return cleanup_count

    def _save_cycle(self, cycle: ThreeCommitCycle) -> None:
        """サイクルの保存"""
        cycle_file = self._get_cycle_file_path(cycle.feature_name)
        cycle_data: dict[str, Any] = self._serialize_cycle(cycle)

        with open(cycle_file, "w", encoding="utf-8") as f:
            json.dump(cycle_data, f, indent=2, ensure_ascii=False)

    def _get_cycle_file_path(self, feature_name: str) -> Path:
        """サイクルファイルパスの取得"""
        safe_name = "".join(c for c in feature_name if c.isalnum() or c in "._-")
        return self.cycles_dir / f"{safe_name}.json"

    def _serialize_cycle(self, cycle: ThreeCommitCycle) -> dict[str, Any]:
        """サイクルのシリアライズ"""
        return {
            "cycle_id": cycle.cycle_id,
            "feature_name": cycle.feature_name,
            "current_stage": cycle.current_stage.value,
            "completed_requirements": [req.value for req in cycle.completed_requirements],
            "pending_requirements": [req.value for req in cycle.pending_requirements],
            "commit_history": list(cycle.commit_history),
            "stage_metadata": cycle.stage_metadata,
            "created_at": cycle.created_at.isoformat(),
        }

    def _deserialize_cycle(self, data: dict[str, Any]) -> ThreeCommitCycle:
        """サイクルのデシリアライズ"""

        return ThreeCommitCycle(
            cycle_id=data["cycle_id"],
            feature_name=data["feature_name"],
            current_stage=CommitStage(data["current_stage"]),
            completed_requirements=frozenset(CommitRequirement(req) for req in data["completed_requirements"]),
            pending_requirements=frozenset(CommitRequirement(req) for req in data["pending_requirements"]),
            commit_history=tuple(data["commit_history"]),
            stage_metadata=data["stage_metadata"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )

    def _validate_commit_message(self, commit_message: str, expected_template: str) -> bool:
        """コミットメッセージの妥当性検証"""
        # 基本的なパターンマッチング
        # 実装時により詳細なルールを追加可能
        return commit_message.startswith(expected_template.split(":")[0])

    def _validate_file_changes(self, cycle: ThreeCommitCycle) -> dict[str, Any]:
        """ファイル変更状態の検証"""
        # 実装時にGit status との連携を追加
        return {"has_errors": False, "has_warnings": False, "errors": [], "warnings": []}

    def _detect_requirement_completion(self, requirement: CommitRequirement, feature_name: str) -> bool:
        """要件完了の自動検出"""
        # 各要件の検出ロジック
        if requirement == CommitRequirement.SPECIFICATION_CREATED:
            return self._check_specification_exists(feature_name)
        if requirement == CommitRequirement.CODEMAP_UPDATED:
            return self._check_codemap_updated()
        if requirement == CommitRequirement.UNIT_TESTS_CREATED:
            return self._check_unit_tests_exist(feature_name)
        if requirement == CommitRequirement.ALL_TESTS_PASSING:
            return self._check_all_tests_passing()
        # ... 他の要件の検出ロジック

        return False  # デフォルトは未検出

    def _check_specification_exists(self, feature_name: str) -> bool:
        """仕様書存在確認"""
        specs_dir = self.project_root / "specs"

        if not specs_dir.exists():
            return False

        # 仕様書ファイルの検索
        spec_patterns = [f"SPEC-*{feature_name}*.md", f"*{feature_name}*.md"]

        return any(list(specs_dir.glob(pattern)) for pattern in spec_patterns)

    def _check_codemap_updated(self) -> bool:
        """CODEMAP更新確認"""
        codemap_file = self.project_root / "CODEMAP.yaml"
        return codemap_file.exists()

    def _check_unit_tests_exist(self, feature_name: str) -> bool:
        """単体テスト存在確認"""
        test_patterns = [f"**/test*{feature_name}*.py", f"**/*{feature_name}*test*.py"]

        return any(list(self.project_root.glob(pattern)) for pattern in test_patterns)

    def _check_all_tests_passing(self) -> bool:
        """全テスト成功確認"""
        # 実装時にテスト実行結果との連携を追加
        return True  # 暫定
