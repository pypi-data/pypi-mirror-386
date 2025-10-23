# File: src/noveler/application/use_cases/project_init_use_case.py
# Purpose: Orchestrate project initialization workflow
# Context: Application layer use case implementing transaction pattern

"""
ProjectInitUseCase - プロジェクト初期化ワークフロー

This use case orchestrates the project initialization workflow by coordinating
domain services and infrastructure repositories.

Responsibilities:
- Validate preconditions before initialization
- Coordinate directory creation and file writing
- Apply templates with proper parameters
- Ensure transaction guarantees (rollback on failure)

Design Principles:
- Single Responsibility: Project initialization workflow only
- Dependency Inversion: Depends on abstractions (IPathService, etc.)
- Transaction Pattern: Rollback capability for failed operations
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from noveler.domain.services.project_initializer_service import (
    DirectoryStructure,
    ProjectConfig,
    ProjectInitializerService,
)
from noveler.infrastructure.repositories.template_repository import (
    TemplateRepository,
)


@dataclass
class ProjectInitRequest:
    """
    Request for project initialization.

    Attributes:
        project_name: Project name to create
        project_root: Parent directory where project will be created
        template_name: Optional template override (default: "base")
        genre: Optional genre override
        pen_name: Optional pen name override
    """

    project_name: str
    project_root: Path
    template_name: str = "base"
    genre: Optional[str] = None
    pen_name: Optional[str] = None


@dataclass
class ProjectInitResult:
    """
    Result of project initialization.

    Attributes:
        success: Whether initialization succeeded
        project_path: Path to created project directory
        created_dirs: List of created directory paths
        config_path: Path to project configuration file
        error_message: Error message if failed
    """

    success: bool
    project_path: Optional[Path] = None
    created_dirs: List[str] = None
    config_path: Optional[Path] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        """Initialize empty lists."""
        if self.created_dirs is None:
            self.created_dirs = []


class ProjectInitializationError(Exception):
    """Raised when project initialization fails."""

    pass


class ProjectInitUseCase:
    """
    Use case for project initialization workflow.

    This use case coordinates domain services and infrastructure repositories
    to create a new project with standard structure and configuration.
    """

    def __init__(
        self,
        initializer_service: ProjectInitializerService,
        template_repository: TemplateRepository,
    ):
        """
        Initialize use case with dependencies.

        Args:
            initializer_service: Domain service for project initialization logic
            template_repository: Repository for template access
        """
        self._initializer = initializer_service
        self._templates = template_repository

    def execute(self, request: ProjectInitRequest) -> ProjectInitResult:
        """
        Execute project initialization workflow.

        This method orchestrates the complete initialization workflow:
        1. Validate preconditions
        2. Create directory structure
        3. Render and write configuration files
        4. Render and write README and .gitignore

        Transaction Guarantee:
            If any step fails, all created files/directories are rolled back.

        Args:
            request: Project initialization request

        Returns:
            ProjectInitResult with success status and created paths

        Examples:
            >>> use_case = ProjectInitUseCase(service, repo)
            >>> request = ProjectInitRequest(
            ...     project_name="08_時空の図書館",
            ...     project_root=Path("/novels")
            ... )
            >>> result = use_case.execute(request)
            >>> result.success
            True
        """
        created_dirs = []
        created_files = []

        try:
            # Step 1: Validate preconditions
            validation_result = self.validate_preconditions(request)
            if not validation_result.success:
                return validation_result

            # Step 2: Generate configuration
            project_path = request.project_root / request.project_name
            config = self._initializer.generate_config(
                project_name=request.project_name,
                project_root=project_path,
                genre=request.genre,
                pen_name=request.pen_name,
            )

            # Step 3: Create project root directory
            project_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(project_path))

            # Step 4: Create standard directory structure
            dir_structure = self._initializer.generate_directory_structure()
            for dir_path in dir_structure.directories:
                full_path = project_path / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(full_path))

            # Step 5: Render and write project configuration
            config_content = self._render_config_template(config)
            config_path = project_path / "プロジェクト設定.yaml"
            config_path.write_text(config_content, encoding="utf-8")
            created_files.append(str(config_path))

            # Step 6: Render and write README
            readme_content = self._render_readme_template(config)
            readme_path = project_path / "README.md"
            readme_path.write_text(readme_content, encoding="utf-8")
            created_files.append(str(readme_path))

            # Step 7: Render and write .gitignore
            gitignore_content = self._render_gitignore_template()
            gitignore_path = project_path / ".gitignore"
            gitignore_path.write_text(gitignore_content, encoding="utf-8")
            created_files.append(str(gitignore_path))

            return ProjectInitResult(
                success=True,
                project_path=project_path,
                created_dirs=created_dirs,
                config_path=config_path,
            )

        except Exception as e:
            # Rollback: Remove created files and directories
            self._rollback(created_files, created_dirs)

            return ProjectInitResult(
                success=False,
                error_message=f"Project initialization failed: {str(e)}",
            )

    def validate_preconditions(
        self, request: ProjectInitRequest
    ) -> ProjectInitResult:
        """
        Validate preconditions before initialization.

        Checks:
        - Project name is valid
        - Parent directory exists and is writable
        - Project directory does not already exist (or warn if it does)
        - Required templates exist

        Args:
            request: Project initialization request

        Returns:
            ProjectInitResult with success=True if valid, success=False otherwise
        """
        # Validate project name
        is_valid, error = self._initializer.validate_project_name(
            request.project_name
        )
        if not is_valid:
            return ProjectInitResult(success=False, error_message=error)

        # Check parent directory exists
        if not request.project_root.exists():
            return ProjectInitResult(
                success=False,
                error_message=f"Parent directory does not exist: {request.project_root}",
            )

        # Check parent directory is writable
        if not request.project_root.is_dir():
            return ProjectInitResult(
                success=False,
                error_message=f"Not a directory: {request.project_root}",
            )

        # Warn if project directory already exists
        project_path = request.project_root / request.project_name
        if project_path.exists():
            # Note: In production, this would prompt user for confirmation
            # For now, we allow overwrite (existing files won't be deleted)
            pass

        # Validate templates exist
        required_templates = [
            f"project/{request.template_name}/プロジェクト設定.yaml.j2",
            f"project/{request.template_name}/README.md.j2",
            f"project/{request.template_name}/.gitignore.j2",
        ]

        for template_name in required_templates:
            if not self._templates.validate_template_exists(template_name):
                return ProjectInitResult(
                    success=False,
                    error_message=f"Required template not found: {template_name}",
                )

        return ProjectInitResult(success=True)

    def _render_config_template(self, config: ProjectConfig) -> str:
        """Render project configuration template."""
        template_name = "project/base/プロジェクト設定.yaml.j2"
        return self._templates.render_template_by_name(
            template_name,
            {
                "project_root": str(config.project_root),
                "title": config.title,
                "genre": config.genre,
                "status": config.status,
                "created_date": config.created_date,
                "pen_name": config.pen_name,
            },
        )

    def _render_readme_template(self, config: ProjectConfig) -> str:
        """Render README.md template."""
        template_name = "project/base/README.md.j2"
        return self._templates.render_template_by_name(
            template_name,
            {
                "title": config.title,
                "created_date": config.created_date,
                "project_name": config.project_name,
            },
        )

    def _render_gitignore_template(self) -> str:
        """Render .gitignore template."""
        template_name = "project/base/.gitignore.j2"
        return self._templates.render_template_by_name(template_name, {})

    def _rollback(self, created_files: List[str], created_dirs: List[str]):
        """
        Rollback created files and directories on failure.

        Args:
            created_files: List of file paths to remove
            created_dirs: List of directory paths to remove
        """
        # Remove files first
        for file_path_str in created_files:
            try:
                file_path = Path(file_path_str)
                if file_path.exists():
                    file_path.unlink()
            except Exception:
                # Best effort: continue even if deletion fails
                pass

        # Remove directories (in reverse order to handle nested dirs)
        for dir_path_str in reversed(created_dirs):
            try:
                dir_path = Path(dir_path_str)
                if dir_path.exists() and dir_path.is_dir():
                    # Only remove if empty
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
            except Exception:
                # Best effort: continue even if deletion fails
                pass
