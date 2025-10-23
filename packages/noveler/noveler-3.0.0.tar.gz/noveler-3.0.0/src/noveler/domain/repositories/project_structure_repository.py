"""
SPEC-WORKFLOW-001: プロジェクト構造リポジトリインターフェース

プロジェクト構造の永続化を抽象化するリポジトリインターフェース。
DDD設計に基づくドメイン層のインターフェース定義。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from noveler.domain.services.project_structure_value_objects import (
    ProjectStructure,
    StandardStructure,
    ValidationResult,
)


@dataclass(frozen=True)
class ProjectPath:
    """プロジェクトパス値オブジェクト"""

    path: Path

    def __post_init__(self) -> None:
        if not self.path.exists():
            msg = f"プロジェクトパスが存在しません: {self.path}"
            raise ValueError(msg)


@dataclass(frozen=True)
class ProjectType:
    """プロジェクトタイプ値オブジェクト"""

    type_name: str

    def __post_init__(self) -> None:
        valid_types = ["novel", "short_story", "essay", "academic"]
        if self.type_name not in valid_types:
            msg = f"無効なプロジェクトタイプ: {self.type_name}"
            raise ValueError(msg)


@dataclass(frozen=True)
class BackupInfo:
    """バックアップ情報値オブジェクト"""

    backup_path: Path
    original_path: Path
    created_at: datetime
    backup_size: int


@dataclass(frozen=True)
class ValidationReport:
    """検証レポート値オブジェクト"""

    project_path: Path
    validation_result: ValidationResult
    generated_at: datetime
    report_format: str = "markdown"


class ProjectStructureRepository(ABC):
    """プロジェクト構造リポジトリインターフェース"""

    @abstractmethod
    def load_project_structure(self, project_path: Path) -> ProjectStructure:
        """プロジェクト構造を読み込み

        Args:
            project_path: プロジェクトパス

        Returns:
            プロジェクト構造

        Raises:
            FileNotFoundError: プロジェクトが存在しない場合
        """

    @abstractmethod
    def save_validation_report(self, report: ValidationReport) -> None:
        """検証レポートを保存

        Args:
            report: 検証レポート
        """

    @abstractmethod
    def get_standard_structure(self, project_type: ProjectType) -> StandardStructure:
        """標準構造を取得

        Args:
            project_type: プロジェクトタイプ

        Returns:
            標準構造定義
        """

    @abstractmethod
    def create_backup(self, project_path: Path) -> BackupInfo:
        """プロジェクトのバックアップを作成

        Args:
            project_path: バックアップ対象のプロジェクトパス

        Returns:
            バックアップ情報
        """

    @abstractmethod
    def restore_from_backup(self, backup_info: BackupInfo) -> bool:
        """バックアップから復元

        Args:
            backup_info: バックアップ情報

        Returns:
            復元成功の場合True
        """

    @abstractmethod
    def get_validation_history(self, project_path: Path) -> list[ValidationReport]:
        """検証履歴を取得

        Args:
            project_path: プロジェクトパス

        Returns:
            検証レポートの履歴
        """

    @abstractmethod
    def find_projects_by_compliance(self, min_score: float) -> list[Path]:
        """準拠スコアでプロジェクトを検索

        Args:
            min_score: 最小準拠スコア

        Returns:
            条件に一致するプロジェクトパスのリスト
        """

    @abstractmethod
    def get_project_metadata(self, project_path: Path) -> dict | None:
        """プロジェクトメタデータを取得

        Args:
            project_path: プロジェクトパス

        Returns:
            メタデータ辞書、存在しない場合はNone
        """
