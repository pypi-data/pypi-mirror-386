"""Quality check prompt generation use case.

Implements the SPEC-STAGE5-SEPARATION workflow to generate Claude Code prompts for quality checks.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from noveler.domain.entities.enhanced_episode_plot import EnhancedEpisodePlot
from noveler.domain.entities.quality_check_prompt import (
    PlotValidationResult,
    QualityCheckPromptGenerator,
)
from noveler.domain.repositories.quality_check_prompt_repository import QualityCheckPromptRepository
from noveler.domain.value_objects.quality_check_level import QualityCheckLevel, QualityCheckRequest, QualityCriterion

# Following DDD principles: avoid direct infrastructure dependencies via lazy initialization


@dataclass
class QualityCheckPromptGenerationRequest:
    """Request DTO describing how to generate quality check prompts.

    Attributes:
        project_name: Name of the project containing the episode.
        episode_number: Episode number targeted for quality checks.
        check_level: Desired quality check level.
        plot_file_path: Optional explicit path to the plot file.
        custom_criteria: Optional custom quality criteria to override defaults.
        force_regenerate: Force prompt regeneration even if one exists.
    """

    project_name: str
    episode_number: int
    check_level: QualityCheckLevel
    plot_file_path: str | None = None
    custom_criteria: list[QualityCriterion] | None = None
    force_regenerate: bool = False


@dataclass
class QualityCheckPromptGenerationResponse:
    """Response DTO returned after generating quality check prompts.

    Attributes:
        success: Indicates whether prompt generation succeeded.
        prompt_id: Identifier of the generated prompt.
        generated_prompt: Prompt text produced by the use case.
        prompt_length: Length of the generated prompt in characters.
        validation_result: Plot validation details when available.
        error_message: Error detail when generation fails.
        execution_time_ms: Execution time in milliseconds.
    """

    success: bool
    prompt_id: str | None = None
    generated_prompt: str | None = None
    prompt_length: int = 0
    validation_result: PlotValidationResult | None = None
    error_message: str | None = None
    execution_time_ms: int = 0

    def is_success(self) -> bool:
        """Return True when a prompt was generated successfully."""
        return self.success and self.generated_prompt is not None


class QualityCheckPromptUseCase:
    """Coordinate quality check prompt generation and persistence."""

    def __init__(
        self,
        prompt_generator: QualityCheckPromptGenerator,
        prompt_repository: QualityCheckPromptRepository,
        plot_repository: Any,  # TODO: replace with AbstractPlotRepository-like protocol
        common_path_service: Any,  # TODO: replace with CommonPathService protocol
    ) -> None:
        """Initialise the use case with prompt services and repositories.

        Args:
            prompt_generator: Domain service used to build quality check prompts.
            prompt_repository: Repository that persists generated prompts.
            plot_repository: Repository providing plot data (injected implementation).
            common_path_service: Service used to resolve common project paths.
        """
        self._prompt_generator = prompt_generator
        self._prompt_repository = prompt_repository
        self._plot_repository = plot_repository
        self._common_path_service = common_path_service

    async def generate_quality_check_prompt(
        self, request: QualityCheckPromptGenerationRequest
    ) -> QualityCheckPromptGenerationResponse:
        """Generate or reuse a quality check prompt for the requested episode.

        Args:
            request: Prompt generation request payload.

        Returns:
            QualityCheckPromptGenerationResponse: Generated prompt or cached result.
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Check for existing prompts
            if not request.force_regenerate:
                existing_prompts = self._prompt_repository.find_by_episode(request.project_name, request.episode_number)

                # Reuse prompts matching the same quality level when possible
                for existing in existing_prompts:
                    if (
                        existing.request
                        and existing.request.check_level == request.check_level
                        and existing.generated_prompt
                    ):
                        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                        return QualityCheckPromptGenerationResponse(
                            success=True,
                            prompt_id=str(existing.prompt_id),
                            generated_prompt=existing.generated_prompt,
                            prompt_length=len(existing.generated_prompt),
                            execution_time_ms=int(execution_time),
                        )

            # Load plot data for the episode
            episode_plot = await self._load_episode_plot(
                request.project_name, request.episode_number, request.plot_file_path
            )

            if not episode_plot:
                return QualityCheckPromptGenerationResponse(
                    success=False,
                    error_message=f"Episode plot not found: {request.project_name} episode {request.episode_number}",
                )

            # Build the quality check request object
            plot_file_path = request.plot_file_path or self._get_default_plot_path(
                request.project_name, request.episode_number
            )

            quality_request = QualityCheckRequest(
                episode_number=request.episode_number,
                project_name=request.project_name,
                plot_file_path=str(plot_file_path),
                check_level=request.check_level,
            )

            # Generate the quality check prompt
            prompt = self._prompt_generator.generate_prompt(
                request=quality_request, episode_plot=episode_plot, criteria=request.custom_criteria
            )

            # Persist the generated prompt
            self._prompt_repository.save(prompt)

            # Calculate execution time
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            # Build successful response payload
            return QualityCheckPromptGenerationResponse(
                success=True,
                prompt_id=str(prompt.prompt_id),
                generated_prompt=prompt.generated_prompt,
                prompt_length=len(prompt.generated_prompt) if prompt.generated_prompt else 0,
                execution_time_ms=int(execution_time),
            )

        except ValueError as e:
            # Plot validation or other expected errors
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            return QualityCheckPromptGenerationResponse(
                success=False, error_message=str(e), execution_time_ms=int(execution_time)
            )

        except Exception as e:
            # Unexpected errors
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            return QualityCheckPromptGenerationResponse(
                success=False, error_message=f"Unexpected error: {e!s}", execution_time_ms=int(execution_time)
            )

    async def get_existing_prompts(self, project_name: str, episode_number: int) -> list[dict[str, Any]]:
        """Retrieve summaries of previously generated prompts for an episode.

        Args:
            project_name: Project identifier.
            episode_number: Episode number used to filter prompts.

        Returns:
            list[dict[str, Any]]: Prompt summary objects.
        """
        try:
            prompts = self._prompt_repository.find_by_episode(project_name, episode_number)

            prompt_summaries = []
            for prompt in prompts:
                summary = {
                    "prompt_id": str(prompt.prompt_id),
                    "creation_timestamp": prompt.creation_timestamp.isoformat(),
                    "check_level": prompt.request.check_level.value if prompt.request else None,
                    "has_generated_prompt": prompt.generated_prompt is not None,
                    "prompt_length": len(prompt.generated_prompt) if prompt.generated_prompt else 0,
                    "has_result": prompt.check_result is not None,
                }

                if prompt.check_result:
                    summary["overall_score"] = prompt.check_result.overall_score
                    summary["is_passing"] = prompt.check_result.is_passing_grade()

                prompt_summaries.append(summary)

            return prompt_summaries

        except Exception:
            return []

    async def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a generated prompt from the repository.

        Args:
            prompt_id: Identifier of the prompt to delete.

        Returns:
            bool: True when deletion succeeded.
        """
        try:
            from noveler.domain.entities.quality_check_prompt import QualityCheckPromptId

            prompt_id_obj = QualityCheckPromptId(prompt_id)
            return self._prompt_repository.delete(prompt_id_obj)

        except Exception:
            return False

    async def get_repository_statistics(self) -> dict[str, Any]:
        """Return repository statistics when supported."""
        try:
            return self._prompt_repository.get_statistics()
        except Exception as e:
            return {"error": str(e)}

    async def _load_episode_plot(
        self, project_name: str, episode_number: int, plot_file_path: str | None = None
    ) -> EnhancedEpisodePlot | None:
        """Load the episode plot data, optionally from a custom path."""
        try:
            # Determine which plot file should be used
            if plot_file_path:
                plot_path = Path(plot_file_path)
            else:
                plot_path = self._get_default_plot_path(project_name, episode_number)

            if not plot_path.exists():
                return None

            # Load plot data through the injected repository
            # In production this should invoke the actual plot repository implementation
            plot_data: dict[str, Any] = await self._plot_repository.load_episode_plot(project_name, episode_number)

            return plot_data

        except Exception:
            return None

    def _get_default_plot_path(self, project_name: str, episode_number: int) -> Path:
        """Return the default plot file path for the episode."""
        # Resolve plot directory using the common path service
        plot_dir = self._common_path_service.get_plot_dir()

        # Prefer Stage 4 plot files when available
        stage4_file = plot_dir / f"第{episode_number:03d}話_stage4.yaml"
        if stage4_file.exists():
            return stage4_file

        # Fallback to the standard plot file naming convention
        return plot_dir / f"第{episode_number:03d}話.yaml"


class QualityCheckPromptUseCaseFactory:
    """Factory for constructing quality check prompt use cases."""

    @staticmethod
    def create_use_case(storage_directory: Path | None = None, common_path_service=None) -> QualityCheckPromptUseCase:
        """Create and configure a quality check prompt use case.

        Args:
            storage_directory: Directory where prompts should be stored.
            common_path_service: Shared path service instance.

        Returns:
            QualityCheckPromptUseCase: Configured use case instance.
        """
        # Obtain the common path service when not provided
        if not common_path_service:
            from noveler.presentation.shared.shared_utilities import get_common_path_service

            common_path_service = get_common_path_service()

        # Inject dependencies required by the use case
        from noveler.infrastructure.repositories.quality_check_prompt_repository import (
            FileSystemQualityCheckPromptRepository,
        )

        prompt_generator = QualityCheckPromptGenerator()

        # Instantiate the repository using the new directory structure
        prompt_repository = FileSystemQualityCheckPromptRepository(
            storage_directory or Path(".quality_check_prompts"),  # Fallback storage directory for compatibility
            common_path_service=common_path_service,
        )

        # Placeholder for injecting the actual plot repository implementation
        plot_repository = None  # Inject the concrete plot repository implementation when available

        return QualityCheckPromptUseCase(
            prompt_generator=prompt_generator,
            prompt_repository=prompt_repository,
            plot_repository=plot_repository,
            common_path_service=common_path_service,
        )
