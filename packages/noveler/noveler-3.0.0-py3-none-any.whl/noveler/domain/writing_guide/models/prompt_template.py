# File: src/noveler/domain/writing_guide/models/prompt_template.py
# Purpose: Define entity for prompt templates with rendering logic.
# Context: Domain entity representing prompt templates with identity and behavior.

"""Entity for prompt templates with rendering capabilities.

Purpose:
    Provide entity representing prompt templates with identity,
    validation, and rendering business logic.

Inputs:
    Template ID, content, and required variables.

Outputs:
    Rendered prompts with variable substitution.

Preconditions:
    Template content must contain placeholders for required variables.

Side Effects:
    None (stateless rendering).

Exceptions:
    ValueError: When required variables are missing during rendering.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class PromptTemplate:
    """Entity representing a prompt template with rendering logic.

    Purpose:
        Encapsulate prompt template with identity and behavior,
        providing variable validation and substitution capabilities.

    Attributes:
        template_id: Unique identifier for this template.
        content: Template string with placeholders (e.g., "{genre}").
        required_variables: List of variable names that must be provided during rendering.

    Preconditions:
        - template_id must not be empty
        - content must contain placeholders for all required_variables
        - required_variables must not contain duplicates

    Side Effects:
        None.

    Exceptions:
        ValueError: When domain invariants are violated.
    """

    template_id: str
    content: str
    required_variables: list[str]

    def __post_init__(self) -> None:
        """Validate domain invariants.

        Purpose:
            Ensure template has valid identity and required variables.

        Raises:
            ValueError: When invariants are violated.

        Side Effects:
            None beyond potential exception.
        """
        if not self.template_id or not self.template_id.strip():
            raise ValueError("template_id must not be empty")

        if not self.content:
            raise ValueError("content must not be empty")

        if len(self.required_variables) != len(set(self.required_variables)):
            raise ValueError("required_variables must not contain duplicates")

    def __eq__(self, other: object) -> bool:
        """Entity equality based on identity.

        Purpose:
            Implement entity equality: two templates are equal if they have the same ID.

        Args:
            other: Object to compare.

        Returns:
            bool: True if other is PromptTemplate with same template_id.

        Preconditions:
            None.

        Side Effects:
            None.

        Exceptions:
            None.
        """
        if not isinstance(other, PromptTemplate):
            return False
        return self.template_id == other.template_id

    def __hash__(self) -> int:
        """Entity hash based on identity.

        Purpose:
            Make template hashable for use in sets and dicts.

        Returns:
            int: Hash of template_id.

        Preconditions:
            None.

        Side Effects:
            None.

        Exceptions:
            None.
        """
        return hash(self.template_id)

    def render(self, context: dict[str, Any]) -> str:
        """Render template with variable substitution.

        Purpose:
            Business logic: Substitute template placeholders with context values,
            validating that all required variables are provided.

        Args:
            context: Dictionary mapping variable names to values.

        Returns:
            str: Rendered template string with substituted values.

        Preconditions:
            context must contain all required_variables as keys.

        Side Effects:
            None.

        Exceptions:
            ValueError: When required variables are missing from context.
        """
        self._validate_context(context)
        return self.content.format(**context)

    def _validate_context(self, context: dict[str, Any]) -> None:
        """Validate that context contains all required variables.

        Purpose:
            Domain rule enforcement: Ensure complete variable provision.

        Args:
            context: Dictionary to validate.

        Raises:
            ValueError: When required variables are missing.

        Preconditions:
            None.

        Side Effects:
            None beyond potential exception.

        Exceptions:
            ValueError: When validation fails.
        """
        missing = [var for var in self.required_variables if var not in context]
        if missing:
            raise ValueError(
                f"Missing required variables for template '{self.template_id}': {', '.join(missing)}"
            )

    def contains_variable(self, variable_name: str) -> bool:
        """Check if template requires a specific variable.

        Purpose:
            Query method: Determine if variable is needed for rendering.

        Args:
            variable_name: Variable to check.

        Returns:
            bool: True if variable is in required_variables list.

        Preconditions:
            None.

        Side Effects:
            None.

        Exceptions:
            None.
        """
        return variable_name in self.required_variables

    def can_render_with(self, context: dict[str, Any]) -> bool:
        """Check if template can be rendered with given context.

        Purpose:
            Query method: Determine if context is sufficient for rendering
            without throwing exceptions.

        Args:
            context: Dictionary to check.

        Returns:
            bool: True if all required variables are present in context.

        Preconditions:
            None.

        Side Effects:
            None.

        Exceptions:
            None.
        """
        return all(var in context for var in self.required_variables)
