"""統合執筆セッションエンティティ
仕様: specs/integrated_writing_workflow.spec.md
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.yaml_prompt_content import YamlPromptContent


class WritingWorkflowType(Enum):
    """執筆ワークフロータイプ"""

    TRADITIONAL = "traditional"  # 従来ワークフロー
    INTEGRATED = "integrated"  # 統合ワークフロー（YAML生成含む）


class WritingSessionStatus(Enum):
    """執筆セッション状態"""

    INITIALIZED = "initialized"  # 初期化完了
    PROMPT_GENERATED = "prompt_generated"  # プロンプト生成完了
    MANUSCRIPT_CREATED = "manuscript_created"  # 原稿作成完了
    EDITOR_OPENED = "editor_opened"  # エディタ起動完了
    COMPLETED = "completed"  # 全工程完了
    FAILED = "failed"  # 失敗


@dataclass
class IntegratedWritingSession:
    """統合執筆セッションエンティティ

    統合執筆ワークフローの状態と進行を管理する集約ルート
    """

    session_id: str
    episode_number: EpisodeNumber
    project_root: Path
    workflow_type: WritingWorkflowType
    status: WritingSessionStatus = WritingSessionStatus.INITIALIZED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # 統合ワークフロー固有の属性
    yaml_prompt_content: YamlPromptContent | None = None
    yaml_output_path: Path | None = None
    manuscript_path: Path | None = None
    custom_requirements: list[str] = field(default_factory=list)
    generation_metadata: dict[str, str] = field(default_factory=dict)

    # エラー情報
    error_message: str | None = None
    fallback_executed: bool = False

    def __post_init__(self) -> None:
        """エンティティ初期化後の検証"""
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        """ドメイン不変条件の検証"""
        if not self.session_id:
            msg = "session_idは必須です"
            raise ValueError(msg)

        if not isinstance(self.episode_number, EpisodeNumber):
            msg = "episode_numberはEpisodeNumber型である必要があります"
            raise ValueError(msg)

        if not self.project_root.exists():
            msg = f"プロジェクトルートが存在しません: {self.project_root}"
            raise ValueError(msg)

    def start_prompt_generation(self) -> None:
        """プロンプト生成開始"""
        if self.status != WritingSessionStatus.INITIALIZED:
            msg = f"プロンプト生成は初期化状態でのみ開始可能です。現在状態: {self.status}"
            raise ValueError(msg)

        self.status = WritingSessionStatus.PROMPT_GENERATED
        self.updated_at = datetime.now(timezone.utc)

    def complete_prompt_generation(self, yaml_content: YamlPromptContent, output_path: Path) -> None:
        """プロンプト生成完了"""
        if self.status != WritingSessionStatus.PROMPT_GENERATED:
            msg = "プロンプト生成完了は生成中状態でのみ可能です"
            raise ValueError(msg)

        self.yaml_prompt_content = yaml_content
        self.yaml_output_path = output_path
        self.updated_at = datetime.now(timezone.utc)

    def complete_manuscript_creation(self, manuscript_path: Path) -> None:
        """原稿作成完了"""
        self.manuscript_path = manuscript_path
        self.status = WritingSessionStatus.MANUSCRIPT_CREATED
        self.updated_at = datetime.now(timezone.utc)

    def complete_editor_opening(self) -> None:
        """エディタ起動完了"""
        if self.status != WritingSessionStatus.MANUSCRIPT_CREATED:
            msg = "エディタ起動は原稿作成完了後のみ可能です"
            raise ValueError(msg)

        self.status = WritingSessionStatus.EDITOR_OPENED
        self.updated_at = datetime.now(timezone.utc)

    def complete_session(self) -> None:
        """セッション完了"""
        if self.status != WritingSessionStatus.EDITOR_OPENED:
            msg = "セッション完了はエディタ起動完了後のみ可能です"
            raise ValueError(msg)

        self.status = WritingSessionStatus.COMPLETED
        self.updated_at = datetime.now(timezone.utc)

    def fail_with_error(self, error_message: str, enable_fallback: bool = True) -> None:
        """エラーによる失敗"""
        self.status = WritingSessionStatus.FAILED
        self.error_message = error_message
        self.fallback_executed = enable_fallback
        self.updated_at = datetime.now(timezone.utc)

    def add_custom_requirement(self, requirement: str) -> None:
        """カスタム要件追加"""
        if requirement and requirement not in self.custom_requirements:
            self.custom_requirements.append(requirement)
            self.updated_at = datetime.now(timezone.utc)

    def is_completed(self) -> bool:
        """セッション完了判定"""
        return self.status == WritingSessionStatus.COMPLETED

    def is_failed(self) -> bool:
        """セッション失敗判定"""
        return self.status == WritingSessionStatus.FAILED

    def should_fallback_to_traditional(self) -> bool:
        """従来ワークフローへのフォールバック判定"""
        return self.is_failed() and self.fallback_executed and self.workflow_type == WritingWorkflowType.INTEGRATED

    def get_session_duration_seconds(self) -> float:
        """セッション実行時間（秒）"""
        return (self.updated_at - self.created_at).total_seconds()
