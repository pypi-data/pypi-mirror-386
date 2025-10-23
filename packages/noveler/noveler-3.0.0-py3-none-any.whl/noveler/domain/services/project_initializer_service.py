# File: src/noveler/domain/services/project_initializer_service.py
# Purpose: Core business logic for project initialization
# Context: Domain layer service implementing DDD principles

"""
ProjectInitializerService - プロジェクト初期化のドメインサービス

This service encapsulates the business logic for creating a new novel project
with standard directory structure and configuration files.

Responsibilities:
- Validate project names according to business rules
- Generate standard directory structure
- Create project configuration with default values
- Provide rollback capability for failed initialization

Design Principles:
- Single Responsibility: Project initialization only
- Pure domain logic: No I/O operations (delegated to infrastructure)
- Stateless: All methods are side-effect free
- Testable: No external dependencies in domain logic
"""

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ProjectConfig:
    """
    Value object representing project configuration.

    Attributes:
        project_name: プロジェクト名 (validated)
        project_root: プロジェクトルートパス
        title: 作品タイトル (derived from project_name)
        genre: ジャンル
        status: 進行状況
        created_date: 作成日
        pen_name: ペンネーム
    """

    project_name: str
    project_root: Path
    title: str
    genre: str = "ファンタジー"
    status: str = "planning"
    created_date: Optional[str] = None
    pen_name: str = "ペンネーム"

    def __post_init__(self):
        """Set created_date to today if not provided."""
        if self.created_date is None:
            self.created_date = datetime.now().strftime("%Y-%m-%d")


@dataclass(frozen=True)
class DirectoryStructure:
    """
    Value object representing standard directory structure.

    Attributes:
        directories: List of relative directory paths to create
    """

    directories: tuple[str, ...]

    @classmethod
    def standard(cls) -> "DirectoryStructure":
        """
        Return standard novel project directory structure.

        Returns:
            DirectoryStructure with standard layout
        """
        return cls(
            directories=(
                "10_企画",
                "20_プロット/章別プロット",
                "30_設定集",
                "40_原稿",
                "50_管理資料/執筆記録",
                "90_アーカイブ",
            )
        )


class ProjectInitializerService:
    """
    Domain service for project initialization.

    This service provides pure business logic for project creation.
    All I/O operations are delegated to infrastructure layer.
    """

    # Business rule: Valid project name pattern
    _VALID_NAME_PATTERN = re.compile(r"^[0-9]*_?[\w\-ぁ-んァ-ヶー一-龯]+$")
    _MIN_NAME_LENGTH = 1
    _MAX_NAME_LENGTH = 100

    def validate_project_name(self, name: str) -> tuple[bool, Optional[str]]:
        """
        Validate project name according to business rules.

        Business Rules:
        - Must contain Japanese characters, alphanumeric, underscore, or hyphen
        - No special characters like /, \\, :, *, ?, ", <, >, |
        - Length between 1 and 100 characters
        - Optional numeric prefix with underscore (e.g., "01_")
        - Leading/trailing whitespace is stripped before validation

        Args:
            name: Project name to validate

        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, error_message) if invalid

        Examples:
            >>> service.validate_project_name("08_時空の図書館")
            (True, None)
            >>> service.validate_project_name("Project/Name")
            (False, "プロジェクト名に使用できない文字が含まれています")
        """
        # Strip whitespace before validation
        name = name.strip() if name else ""

        if not name:
            return False, "プロジェクト名が空です"

        if len(name) < self._MIN_NAME_LENGTH or len(name) > self._MAX_NAME_LENGTH:
            return (
                False,
                f"プロジェクト名は{self._MIN_NAME_LENGTH}〜{self._MAX_NAME_LENGTH}文字で指定してください",
            )

        if not self._VALID_NAME_PATTERN.match(name):
            return False, "プロジェクト名に使用できない文字が含まれています"

        return True, None

    def extract_title_from_name(self, project_name: str) -> str:
        """
        Extract display title from project name.

        Removes numeric prefix if present (e.g., "08_時空の図書館" -> "時空の図書館").

        Args:
            project_name: Project name (may include numeric prefix)

        Returns:
            Display title without numeric prefix

        Examples:
            >>> service.extract_title_from_name("08_時空の図書館")
            "時空の図書館"
            >>> service.extract_title_from_name("MyProject")
            "MyProject"
        """
        # Remove leading digits and underscore
        return re.sub(r"^[0-9]+_", "", project_name)

    def generate_directory_structure(self) -> DirectoryStructure:
        """
        Generate standard directory structure.

        Returns:
            DirectoryStructure with standard novel project layout

        Design Note:
            This method returns a value object rather than performing I/O.
            Actual directory creation is delegated to infrastructure layer.
        """
        return DirectoryStructure.standard()

    def generate_config(
        self,
        project_name: str,
        project_root: Path,
        genre: Optional[str] = None,
        pen_name: Optional[str] = None,
    ) -> ProjectConfig:
        """
        Generate project configuration with business defaults.

        Args:
            project_name: Validated project name
            project_root: Project root directory path
            genre: Optional genre override (default: "ファンタジー")
            pen_name: Optional pen name override (default: "ペンネーム")

        Returns:
            ProjectConfig with default values

        Raises:
            ValueError: If project_name is invalid

        Preconditions:
            - project_name must be validated by validate_project_name()
        """
        is_valid, error = self.validate_project_name(project_name)
        if not is_valid:
            raise ValueError(f"Invalid project name: {error}")

        title = self.extract_title_from_name(project_name)

        return ProjectConfig(
            project_name=project_name,
            project_root=project_root,
            title=title,
            genre=genre or "ファンタジー",
            pen_name=pen_name or "ペンネーム",
        )
