#!/usr/bin/env python3
"""
Plot generation workflow orchestrator

This application layer orchestrator coordinates the workflow between
domain services and infrastructure adapters for plot generation,
implementing the Strangler Fig pattern for gradual migration.

Follows DDD principles:
    - Application layer responsibilities only
- Workflow coordination and business process management
- No direct domain logic or infrastructure details
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from noveler.domain.interfaces.claude_plot_interface import ClaudePlotInterface, ClaudeResponse, PlotGenerationRequest
from noveler.domain.interfaces.plot_template_interface import PlotTemplateInterface, TemplateData, TemplateResult
from noveler.domain.services.plot_quality_service import PlotQualityService
from noveler.domain.services.plot_structure_service import PlotStructureService


@dataclass
class PlotGenerationWorkflowRequest:
    """Request for plot generation workflow"""

    project_name: str
    episode_number: int
    chapter_number: int
    context_data: dict[str, Any]
    generation_method: str = "hybrid"  # "claude", "template", "hybrid"
    template_id: str | None = None
    quality_threshold: float = 7.0
    max_iterations: int = 3


@dataclass
class PlotGenerationWorkflowResult:
    """Result of plot generation workflow"""

    success: bool
    generated_plot: str | None = None
    quality_score: float | None = None
    method_used: str | None = None
    iteration_count: int = 0
    generation_time_ms: int | None = None
    error_message: str | None = None
    improvement_suggestions: list[str] = None


class PlotGenerationOrchestrator:
    """
    Application orchestrator for plot generation workflow

    Responsibilities:
    - Coordinate between domain services and infrastructure adapters
    - Implement business workflow logic
    - Handle quality validation and improvement iterations
    - Manage fallback strategies for plot generation
    """

    def __init__(
        self,
        plot_structure_service: PlotStructureService,
        plot_quality_service: PlotQualityService,
        claude_adapter: ClaudePlotInterface,
        template_adapter: PlotTemplateInterface,
    ) -> None:
        """Initialize plot generation orchestrator

        Args:
            plot_structure_service: Domain service for plot structure
            plot_quality_service: Domain service for plot quality
            claude_adapter: Domain interface for Claude API
            template_adapter: Domain interface for templates
        """
        self._structure_service = plot_structure_service
        self._quality_service = plot_quality_service
        self._claude_adapter = claude_adapter
        self._template_adapter = template_adapter

    def generate_plot(self, request: PlotGenerationWorkflowRequest) -> PlotGenerationWorkflowResult:
        """Execute plot generation workflow

        Args:
            request: Plot generation workflow request

        Returns:
            PlotGenerationWorkflowResult: Complete workflow result
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Validate request
            validation_errors = self._validate_request(request)
            if validation_errors:
                return PlotGenerationWorkflowResult(
                    success=False, error_message=f"Request validation failed: {', '.join(validation_errors)}"
                )

            # Execute generation workflow based on method
            result = self._execute_generation_workflow(request)

            # Calculate total execution time
            end_time = datetime.now(timezone.utc)
            result.generation_time_ms = int((end_time - start_time).total_seconds() * 1000)

            return result

        except Exception as e:
            end_time = datetime.now(timezone.utc)
            return PlotGenerationWorkflowResult(
                success=False,
                error_message=f"Workflow execution error: {e!s}",
                generation_time_ms=int((end_time - start_time).total_seconds() * 1000),
            )

    def get_available_methods(self) -> dict[str, Any]:
        """Get information about available generation methods

        Returns:
            dict: Available methods and their capabilities
        """
        return {
            "methods": {
                "claude": {
                    "available": self._claude_adapter.is_claude_available(),
                    "description": "AI-powered plot generation using Claude",
                    "quality": "high",
                    "speed": "medium",
                },
                "template": {
                    "available": True,
                    "description": "Template-based plot generation",
                    "quality": "medium",
                    "speed": "fast",
                },
                "hybrid": {
                    "available": True,
                    "description": "Combined approach with fallback strategy",
                    "quality": "high",
                    "speed": "medium",
                },
            },
            "recommended_method": self._get_recommended_method(),
            "available_templates": len(self._template_adapter.get_available_templates()),
        }

    def validate_generation_context(self, _project_name: str, context_data: dict[str, Any]) -> list[str]:
        """Validate context data for plot generation

        Args:
            project_name: Project name
            context_data: Context data to validate

        Returns:
            list[str]: List of validation errors (empty if valid)
        """
        errors: list[Any] = []

        # Use domain service for business validation
        structure_validation = self._structure_service.validate_episode_structure(
            context_data.get("episode_structure", {})
        )

        errors.extend(structure_validation)

        # Check required context elements
        required_elements = ["characters", "world_setting", "previous_episodes"]
        errors.extend([
            f"Missing required context element: {element}"
            for element in required_elements
            if element not in context_data
        ])

        return errors

    def _execute_generation_workflow(self, request: PlotGenerationWorkflowRequest) -> PlotGenerationWorkflowResult:
        """Execute the main generation workflow

        Args:
            request: Generation request

        Returns:
            PlotGenerationWorkflowResult: Workflow result
        """
        iteration_count = 0
        best_plot = None
        best_quality = 0.0
        method_used = request.generation_method

        while iteration_count < request.max_iterations:
            iteration_count += 1

            # Generate plot using specified method
            if request.generation_method == "claude":
                plot_result = self._generate_with_claude(request)
            elif request.generation_method == "template":
                plot_result = self._generate_with_template(request)
            else:  # hybrid
                plot_result = self._generate_hybrid(request)

            if not plot_result or not plot_result.success:
                continue

            # Evaluate quality using domain service
            quality_score = self._quality_service.evaluate_plot_quality(
                plot_result.content,
                {
                    "episode_number": request.episode_number,
                    "chapter_number": request.chapter_number,
                    "context": request.context_data,
                },
            )

            # Track best result
            if quality_score > best_quality:
                best_plot = plot_result.content
                best_quality = quality_score
                method_used = (
                    plot_result.template_used if hasattr(plot_result, "template_used") else request.generation_method
                )

            # Check if quality threshold is met
            if quality_score >= request.quality_threshold:
                break

            # Generate improvement suggestions for next iteration
            improvement_suggestions = self._quality_service.suggest_improvements(
                plot_result.content, quality_score, request.quality_threshold
            )

            # Update context with improvement suggestions for next iteration
            request.context_data["improvement_suggestions"] = improvement_suggestions

        # Generate final improvement suggestions
        final_suggestions = []
        if best_quality < request.quality_threshold:
            final_suggestions = self._quality_service.suggest_improvements(
                best_plot or "", best_quality, request.quality_threshold
            )

        return PlotGenerationWorkflowResult(
            success=best_plot is not None,
            generated_plot=best_plot,
            quality_score=best_quality,
            method_used=method_used,
            iteration_count=iteration_count,
            improvement_suggestions=final_suggestions,
        )

    def _generate_with_claude(self, request: PlotGenerationWorkflowRequest) -> ClaudeResponse | None:
        """Generate plot using Claude API

        Args:
            request: Generation request

        Returns:
            ClaudeResponse: Claude API response or None if failed
        """
        if not self._claude_adapter.is_claude_available():
            return None

        claude_request = PlotGenerationRequest(
            episode_number=request.episode_number,
            project_name=request.project_name,
            chapter_number=request.chapter_number,
            context_data=request.context_data,
            generation_options={},
        )

        # Validate request before sending
        validation_errors = self._claude_adapter.validate_request(claude_request)
        if validation_errors:
            return None

        return self._claude_adapter.generate_with_claude(claude_request)

    def _generate_with_template(self, request: PlotGenerationWorkflowRequest) -> TemplateResult | None:
        """Generate plot using template system

        Args:
            request: Generation request

        Returns:
            TemplateResult: Template generation result or None if failed
        """
        template_id = request.template_id or self._select_best_template(request)
        if not template_id:
            return None

        template_data: dict[str, Any] = TemplateData(
            episode_number=request.episode_number,
            chapter_number=request.chapter_number,
            project_name=request.project_name,
            context_data=request.context_data,
            variables=request.context_data.get("template_variables", {}),
        )

        # Validate template data
        validation_errors = self._template_adapter.validate_template_data(template_id, template_data)

        if validation_errors:
            return None

        return self._template_adapter.generate_with_template(template_id, template_data)

    def _generate_hybrid(self, request: PlotGenerationWorkflowRequest) -> dict[str, object] | None:
        """Generate plot using hybrid approach

        Args:
            request: Generation request

        Returns:
            Generation result or None if failed
        """
        # Try Claude first if available
        if self._claude_adapter.is_claude_available():
            claude_result = self._generate_with_claude(request)
            if claude_result and claude_result.success:
                return claude_result

        # Fall back to template-based generation
        template_result = self._generate_with_template(request)
        if template_result and template_result.success:
            return template_result

        return None

    def _select_best_template(self, request: PlotGenerationWorkflowRequest) -> str | None:
        """Select the best template for the request

        Args:
            request: Generation request

        Returns:
            str: Template ID or None if no suitable template found
        """
        available_templates = self._template_adapter.get_available_templates()

        # Simple selection logic - can be enhanced with ML/domain rules
        for template in available_templates:
            if template.category in {"episode", "general"}:
                return template.template_id

        return None

    def _get_recommended_method(self) -> str:
        """Get recommended generation method based on current capabilities

        Returns:
            str: Recommended method name
        """
        if self._claude_adapter.is_claude_available():
            return "hybrid"
        return "template"

    def _validate_request(self, request: PlotGenerationWorkflowRequest) -> list[str]:
        """Validate plot generation workflow request

        Args:
            request: Request to validate

        Returns:
            list[str]: List of validation errors (empty if valid)
        """
        errors: list[Any] = []

        if not request.project_name.strip():
            errors.append("Project name is required")

        if request.episode_number <= 0:
            errors.append("Episode number must be positive")

        if request.chapter_number <= 0:
            errors.append("Chapter number must be positive")

        if request.quality_threshold < 0.0 or request.quality_threshold > 10.0:
            errors.append("Quality threshold must be between 0.0 and 10.0")

        if request.max_iterations < 1 or request.max_iterations > 10:
            errors.append("Max iterations must be between 1 and 10")

        if request.generation_method not in ["claude", "template", "hybrid"]:
            errors.append("Invalid generation method")

        # Validate context data using domain services
        context_validation = self.validate_generation_context(request.project_name, request.context_data)

        errors.extend(context_validation)

        return errors
