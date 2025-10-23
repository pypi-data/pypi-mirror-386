"""
段階的プロンプト生成のメインエンティティ

SPEC-STAGED-002: StagedPromptエンティティの実装
- 段階進行の状態管理
- 段階移行のビジネスルール
- 段階結果の保持・管理
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.prompt_stage import PromptStage, get_stage_by_number


class StageTransitionError(Exception):
    """段階移行エラー"""


class StagedPrompt:
    """段階的プロンプト生成を管理するエンティティ

    エピソード別の段階的プロンプト生成の状態を管理し、
    段階移行のビジネスルールを実装する。
    """

    def __init__(self, episode_number: int, project_name: str, project_root: Path | None = None) -> None:
        """段階的プロンプトの初期化

        Args:
            episode_number: 対象エピソード番号
            project_name: プロジェクト名
            project_root: プロジェクトルートパス
        """
        if episode_number <= 0:
            msg = f"Episode number must be positive, got: {episode_number}"
            raise ValueError(msg)
        if not project_name.strip():
            msg = "Project name cannot be empty"
            raise ValueError(msg)

        self._episode_number = episode_number
        self._project_name = project_name.strip()
        self._project_root = project_root
        self._current_stage = PromptStage.STAGE_1
        self._completed_stages: list[PromptStage] = []
        self._stage_results: dict[int, dict[str, Any]] = {}
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = datetime.now(timezone.utc)

        # 段階品質スコア
        self._stage_quality_scores: dict[int, float] = {}

        # 段階実行時間記録
        self._stage_execution_times: dict[int, int] = {}

    @property
    def episode_number(self) -> int:
        """エピソード番号"""
        return self._episode_number

    @property
    def project_name(self) -> str:
        """プロジェクト名"""
        return self._project_name

    @property
    def project_root(self) -> Path | None:
        """プロジェクトルートパス"""
        return self._project_root

    @property
    def current_stage(self) -> PromptStage:
        """現在の段階"""
        return self._current_stage

    @property
    def completed_stages(self) -> list[PromptStage]:
        """完了済み段階のリスト"""
        return self._completed_stages.copy()

    @property
    def stage_results(self) -> dict[int, dict[str, Any]]:
        """段階別結果の辞書"""
        return self._stage_results.copy()

    @property
    def created_at(self) -> datetime:
        """作成日時"""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """更新日時"""
        return self._updated_at

    def get_stage_result(self, stage: PromptStage) -> dict[str, Any] | None:
        """指定段階の結果取得"""
        return self._stage_results.get(stage.stage_number)

    def get_stage_quality_score(self, stage: PromptStage) -> float | None:
        """指定段階の品質スコア取得"""
        return self._stage_quality_scores.get(stage.stage_number)

    def get_stage_execution_time(self, stage: PromptStage) -> int | None:
        """指定段階の実行時間取得（分）"""
        return self._stage_execution_times.get(stage.stage_number)

    def get_total_execution_time(self) -> int:
        """総実行時間取得（分）"""
        return sum(self._stage_execution_times.values())

    def is_stage_completed(self, stage: PromptStage) -> bool:
        """指定段階の完了状態確認"""
        return stage in self._completed_stages

    def is_fully_completed(self) -> bool:
        """全段階完了状態確認"""
        return len(self._completed_stages) == 5 and self._current_stage == PromptStage.STAGE_5

    def can_advance_to_stage(self, target_stage: PromptStage) -> bool:
        """指定段階への進行可能性判定

        Args:
            target_stage: 目標段階

        Returns:
            進行可能な場合True
        """
        # 現在の段階以下には進行できない
        if target_stage.stage_number <= self._current_stage.stage_number:
            return False

        # Stage 1以外は現在段階から次の段階への進行のみ許可
        if target_stage.stage_number != self._current_stage.stage_number + 1:
            return False

        # 現在段階が完了していることを確認
        return self._current_stage in self._completed_stages

    def can_rollback_to_stage(self, target_stage: PromptStage) -> bool:
        """指定段階への戻り可能性判定

        Args:
            target_stage: 目標段階

        Returns:
            戻り可能な場合True
        """
        # より前の段階への戻りのみ許可
        return target_stage.stage_number < self._current_stage.stage_number

    def advance_to_stage(self, target_stage: PromptStage) -> bool:
        """指定段階に進む

        Args:
            target_stage: 目標段階

        Returns:
            進行に成功した場合True

        Raises:
            StageTransitionError: 進行できない場合
        """
        if not self.can_advance_to_stage(target_stage):
            msg = (
                f"Cannot advance from stage {self._current_stage.stage_number} "
                f"to stage {target_stage.stage_number}. "
                f"Current stage must be completed and target stage must be next."
            )
            raise StageTransitionError(
                msg
            )

        self._current_stage = target_stage
        self._updated_at = datetime.now(timezone.utc)
        return True

    def rollback_to_stage(self, target_stage: PromptStage) -> bool:
        """指定段階に戻る

        Args:
            target_stage: 目標段階

        Returns:
            戻りに成功した場合True

        Raises:
            StageTransitionError: 戻りできない場合
        """
        if not self.can_rollback_to_stage(target_stage):
            msg = (
                f"Cannot rollback from stage {self._current_stage.stage_number} "
                f"to stage {target_stage.stage_number}. "
                f"Can only rollback to previous stages."
            )
            raise StageTransitionError(
                msg
            )

        # 目標段階以降の完了状態をクリア
        stages_to_clear = [stage for stage in self._completed_stages if stage.stage_number > target_stage.stage_number]

        for stage in stages_to_clear:
            self._completed_stages.remove(stage)
            # 結果とスコアもクリア
            if stage.stage_number in self._stage_results:
                del self._stage_results[stage.stage_number]
            if stage.stage_number in self._stage_quality_scores:
                del self._stage_quality_scores[stage.stage_number]
            if stage.stage_number in self._stage_execution_times:
                del self._stage_execution_times[stage.stage_number]

        self._current_stage = target_stage
        self._updated_at = datetime.now(timezone.utc)
        return True

    def complete_current_stage(
        self, stage_result: dict[str, Any], quality_score: float, execution_time_minutes: int
    ) -> bool:
        """現在段階を完了する

        Args:
            stage_result: 段階実行結果
            quality_score: 品質スコア（0-100）
            execution_time_minutes: 実行時間（分）

        Returns:
            完了に成功した場合True
        """
        if not 0 <= quality_score <= 100:
            msg = f"Quality score must be between 0 and 100, got: {quality_score}"
            raise ValueError(msg)

        if execution_time_minutes < 0:
            msg = f"Execution time must be non-negative, got: {execution_time_minutes}"
            raise ValueError(msg)

        current_stage_number = self._current_stage.stage_number

        # 段階結果を保存
        self._stage_results[current_stage_number] = stage_result.copy()
        self._stage_quality_scores[current_stage_number] = quality_score
        self._stage_execution_times[current_stage_number] = execution_time_minutes

        # 完了済み段階に追加（重複チェック）
        if self._current_stage not in self._completed_stages:
            self._completed_stages.append(self._current_stage)

        self._updated_at = datetime.now(timezone.utc)
        return True

    def get_next_stage(self) -> PromptStage | None:
        """次の段階を取得

        Returns:
            次の段階が存在する場合そのPromptStage、存在しない場合None
        """
        next_stage_number = self._current_stage.stage_number + 1
        if next_stage_number > 5:
            return None

        return get_stage_by_number(next_stage_number)

    def get_completion_percentage(self) -> float:
        """完了率を取得（0.0-1.0）"""
        return len(self._completed_stages) / 5.0

    def get_average_quality_score(self) -> float:
        """平均品質スコアを取得"""
        if not self._stage_quality_scores:
            return 0.0

        return sum(self._stage_quality_scores.values()) / len(self._stage_quality_scores)

    def get_status_summary(self) -> dict[str, Any]:
        """状態サマリーを取得"""
        return {
            "episode_number": self._episode_number,
            "project_name": self._project_name,
            "current_stage": {"number": self._current_stage.stage_number, "name": self._current_stage.stage_name},
            "completion_percentage": self.get_completion_percentage(),
            "completed_stages_count": len(self._completed_stages),
            "average_quality_score": self.get_average_quality_score(),
            "total_execution_time_minutes": self.get_total_execution_time(),
            "is_fully_completed": self.is_fully_completed(),
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
        }

    def validate_stage_completion_criteria(self, stage: PromptStage, content: dict[str, Any]) -> list[str]:
        """段階完了基準の検証

        Args:
            stage: 検証対象段階
            content: 検証対象コンテンツ

        Returns:
            検証エラーのリスト（空の場合は検証成功）
        """
        errors: list[Any] = []

        # 必須要素の存在チェック
        for required_element in stage.required_elements:
            if required_element not in content:
                errors.append(f"Required element missing: {required_element}")
            elif not content[required_element]:
                errors.append(f"Required element is empty: {required_element}")

        # 段階固有の検証ロジック
        stage_number = stage.stage_number

        if stage_number == 1:
            # Stage 1: 基本骨格の検証
            synopsis = content.get("synopsis", "")
            if len(synopsis) < 100:  # 最小文字数チェック:
                errors.append("Synopsis too short (minimum 100 characters)")

        elif stage_number == 2:
            # Stage 2: 構造の検証
            story_structure = content.get("story_structure", {})
            if not all(act in story_structure for act in ["setup", "confrontation", "resolution"]):
                errors.append("Three-act structure incomplete")

        elif stage_number == 3:
            # Stage 3: シーン詳細の検証
            detailed_scenes = content.get("detailed_scenes", {})
            if len(detailed_scenes) < 3:
                errors.append("Insufficient number of detailed scenes (minimum 3)")

        elif stage_number == 4:
            # Stage 4: 統合要素の検証
            integration_elements = ["foreshadowing_integration", "technical_elements", "thematic_elements"]
            missing_integrations = [elem for elem in integration_elements if elem not in content]
            if missing_integrations:
                errors.append(f"Missing integration elements: {missing_integrations}")

        elif stage_number == 5:
            # Stage 5: 品質確認
            quality_metrics = content.get("quality_metrics", {})
            overall_score = quality_metrics.get("overall_score", 0)
            if overall_score < 80:
                errors.append(f"Overall quality score below threshold: {overall_score} < 80")

        return errors

    def __eq__(self, other: object) -> bool:
        """等価性の比較"""
        if not isinstance(other, StagedPrompt):
            return NotImplemented

        return self._episode_number == other._episode_number and self._project_name == other._project_name

    def __hash__(self) -> int:
        """ハッシュ値の計算"""
        return hash((self._episode_number, self._project_name))

    def __repr__(self) -> str:
        """文字列表現"""
        return (
            f"StagedPrompt("
            f"episode={self._episode_number}, "
            f"project='{self._project_name}', "
            f"current_stage={self._current_stage.stage_number}, "
            f"completed={len(self._completed_stages)}/5)"
        )
