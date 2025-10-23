# File: src/noveler/domain/writing_guide/models/writing_guide.py
# Purpose: Define aggregate root for writing guide with business logic.
# Context: Central domain model coordinating templates, validation, and prompt generation.

"""Aggregate root for writing guide domain model.

Purpose:
    Provide rich domain model serving as aggregate root for A30 writing guide,
    encapsulating prompt generation and content validation business logic.

Inputs:
    Guide metadata, templates, constraints from repository.

Outputs:
    Generated prompts, validation results, version information.

Preconditions:
    Must be constructed with valid templates and constraints collections.

Side Effects:
    None (stateless business logic).

Exceptions:
    ValueError: When domain invariants are violated or requests cannot be fulfilled.
"""

import re
from typing import Any, Optional

from noveler.domain.writing_guide.models.prompt_template import PromptTemplate
from noveler.domain.writing_guide.models.validation_result import ValidationResult
from noveler.domain.writing_guide.models.writing_request import WritingRequest


class WritingGuide:
    """Aggregate root for writing guide domain model.

    Purpose:
        Coordinate prompt generation, content validation, and guide queries,
        serving as the central aggregate root for the writing guide bounded context.

    Attributes:
        _metadata: Guide metadata (version, author, etc.).
        _templates: Dictionary mapping template IDs to PromptTemplate entities.
        _constraints: Writing constraints (forbidden expressions, limits).

    Preconditions:
        - metadata must contain "version" key
        - templates must not be empty
        - constraints must contain required keys (forbidden_expressions, etc.)

    Side Effects:
        None.

    Exceptions:
        ValueError: When domain invariants are violated during construction.
    """

    def __init__(
        self,
        metadata: dict[str, Any],
        templates: dict[str, PromptTemplate],
        constraints: dict[str, Any],
    ) -> None:
        """Initialize aggregate root with guide data.

        Args:
            metadata: Guide metadata dictionary.
            templates: Dictionary mapping template IDs to PromptTemplate entities.
            constraints: Writing constraints dictionary.

        Raises:
            ValueError: When required data is missing or invalid.

        Preconditions:
            All arguments must be non-None and satisfy domain rules.

        Side Effects:
            Stores references to provided data structures.
        """
        self._validate_construction_params(metadata, templates, constraints)

        self._metadata = metadata
        self._templates = templates
        self._constraints = constraints

    @staticmethod
    def _validate_construction_params(
        metadata: dict[str, Any],
        templates: dict[str, PromptTemplate],
        constraints: dict[str, Any],
    ) -> None:
        """Validate construction parameters.

        Purpose:
            Enforce domain invariants for aggregate root construction.

        Args:
            metadata: Metadata to validate.
            templates: Templates to validate.
            constraints: Constraints to validate.

        Raises:
            ValueError: When validation fails.

        Preconditions:
            None.

        Side Effects:
            None beyond potential exception.
        """
        if not metadata or "version" not in metadata:
            raise ValueError("metadata must contain 'version' key")

        if not templates:
            raise ValueError("templates must not be empty")

        if not constraints:
            raise ValueError("constraints must not be empty")

    def generate_prompt(self, request: WritingRequest) -> str:
        """Generate writing prompt for given request.

        Purpose:
            Core business logic: Select appropriate template and render prompt
            based on request parameters and detail level.

        Args:
            request: WritingRequest value object specifying requirements.

        Returns:
            str: Rendered prompt text ready for LLM consumption.

        Preconditions:
            request must be valid WritingRequest with supported detail_level.

        Side Effects:
            None.

        Exceptions:
            ValueError: When template for detail_level is unavailable.
        """
        template = self._select_template(request)
        context = self._build_context(request)
        return template.render(context)

    def _select_template(self, request: WritingRequest) -> PromptTemplate:
        """Select appropriate template based on request detail level.

        Purpose:
            Template selection strategy: Map detail_level to template ID.

        Args:
            request: WritingRequest specifying detail_level.

        Returns:
            PromptTemplate: Selected template entity.

        Preconditions:
            None.

        Side Effects:
            None.

        Exceptions:
            ValueError: When template for detail_level is not found.
        """
        template_id = f"{request.detail_level.value}_prompt"

        if template_id not in self._templates:
            raise ValueError(
                f"Template not found for detail_level '{request.detail_level.value}'"
            )

        return self._templates[template_id]

    def _build_context(self, request: WritingRequest) -> dict[str, Any]:
        """Build rendering context from request.

        Purpose:
            Context preparation: Extract all parameters needed for template rendering.

        Args:
            request: WritingRequest with parameters.

        Returns:
            dict[str, Any]: Context dictionary for template substitution.

        Preconditions:
            None.

        Side Effects:
            None.

        Exceptions:
            None.
        """
        context = {
            "genre": request.genre,
            "word_count": request.word_count,
            "viewpoint": request.viewpoint,
            "viewpoint_character": request.viewpoint_character,
            "difficulty": request.difficulty,
            "priority": request.priority,
        }

        # Add custom requirements if present
        if request.has_custom_requirements():
            context["custom_requirements"] = "\n".join(request.custom_requirements)

        return context

    def validate_content(self, content: str) -> ValidationResult:
        """Validate story content against guide constraints.

        Purpose:
            Content validation business logic: Check for forbidden expressions,
            excessive short sentences, and paragraph length issues.

        Args:
            content: Narrative text to validate.

        Returns:
            ValidationResult: Validation outcome with issues, warnings, and score.

        Preconditions:
            content must be non-None (empty string is valid).

        Side Effects:
            None.

        Exceptions:
            None (returns ValidationResult even for invalid content).
        """
        issues: list[str] = []
        warnings: list[str] = []
        score = 100

        # Check forbidden expressions
        forbidden = self._constraints.get("forbidden_expressions", [])
        for expr in forbidden:
            pattern = expr.replace("〜", r"[^」]*?")
            if re.search(pattern, content):
                issues.append(f"禁止表現が含まれています: {expr}")
                score -= 10

        # Check consecutive short sentences
        sentences = re.split(r"[。！？]", content)
        max_consecutive = 0
        current_consecutive = 0

        for sentence in sentences:
            if len(sentence.strip()) < 30:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        if max_consecutive >= 8:
            issues.append(f"連続短文問題: {max_consecutive}文連続")
            score -= 15
        elif max_consecutive >= 5:
            warnings.append(f"連続短文注意: {max_consecutive}文連続")
            score -= 5

        # Check paragraph length
        paragraphs = content.split("\n\n")
        long_paragraphs = [p for p in paragraphs if len(p.split("\n")) > 4]

        if long_paragraphs:
            warnings.append(f"長い段落が{len(long_paragraphs)}個あります（4行超）")
            score -= 5

        return ValidationResult(
            issues=issues,
            warnings=warnings,
            score=max(0, score),  # Ensure score doesn't go negative
            recommendations=[],
        )

    def get_version(self) -> str:
        """Get guide version string.

        Purpose:
            Query method: Retrieve version information from metadata.

        Returns:
            str: Version string (e.g., "1.0.0").

        Preconditions:
            metadata must contain "version" key (enforced in __init__).

        Side Effects:
            None.

        Exceptions:
            None.
        """
        return self._metadata["version"]

    def get_metadata(self) -> dict[str, Any]:
        """Get guide metadata.

        Purpose:
            Query method: Retrieve complete metadata dictionary.

        Returns:
            dict[str, Any]: Metadata including version, author, description, etc.

        Preconditions:
            None.

        Side Effects:
            None (returns reference, caller should not mutate).

        Exceptions:
            None.
        """
        return self._metadata

    def supports_genre(self, genre: str) -> bool:
        """Check if guide supports specified genre.

        Purpose:
            Query method: Determine if genre is supported by this guide.

        Args:
            genre: Genre name to check.

        Returns:
            bool: True if genre is in supported genres list.

        Preconditions:
            None.

        Side Effects:
            None.

        Exceptions:
            None.
        """
        supported_genres = self._constraints.get("supported_genres", [])
        return genre in supported_genres
