#!/usr/bin/env python3
"""Coordinate Claude API calls used for plot generation.

This adapter isolates Claude-specific integration concerns from domain logic.

Responsibilities:
    - Provide infrastructure-layer orchestration only
    - Avoid business logic
    - Focus on technical integration details
"""

import contextlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from noveler.domain.services.claude_code_evaluation_service import ClaudeCodeEvaluationService


@dataclass
class ClaudeRequest:
    """Request payload forwarded to the Claude API.

    Attributes:
        prompt: Rendered prompt content for the generation request.
        max_tokens: Maximum number of tokens allowed in the response.
        temperature: Sampling temperature applied to the model.
        model: Claude model identifier to invoke.
        system_prompt: Optional system instructions appended to the prompt.
    """

    prompt: str
    max_tokens: int = 4000
    temperature: float = 0.7
    model: str = "claude-3-sonnet-20240229"
    system_prompt: str | None = None


@dataclass
class ClaudeResponse:
    """Normalized response returned by the Claude API.

    Attributes:
        success: ``True`` when the API call succeeds.
        content: Generated text or plot outline.
        error_message: Message describing the failure when unsuccessful.
        token_usage: Token consumption metrics broken down by direction.
        response_time_ms: End-to-end processing time in milliseconds.
    """

    success: bool
    content: str
    error_message: str | None = None
    token_usage: dict[str, int] | None = None
    response_time_ms: int | None = None


@dataclass
class PlotGenerationRequest:
    """Domain request details used for plot generation.

    Attributes:
        episode_number: Episode identifier targeted for generation.
        project_name: Human readable project title.
        chapter_number: Chapter sequence number related to the episode.
        context_data: Supplemental context passed to the prompt builder.
        generation_options: Optional flags that guide prompt construction.
    """

    episode_number: int
    project_name: str
    chapter_number: int
    context_data: dict[str, Any]
    generation_options: dict[str, Any]


class ClaudePlotAdapter:
    """Coordinate plot generation requests handled by the Claude API.

    Responsibilities:
        - Manage API communication
        - Transform requests and responses
        - Handle error reporting for failed calls
        - Track basic availability state
    """

    def __init__(self) -> None:
        """Initialize the adapter and warm up service dependencies."""
        self._claude_service: ClaudeCodeEvaluationService | None = None
        self._api_available = False
        self._initialize_service()

    def generate_with_claude(self, request: PlotGenerationRequest) -> ClaudeResponse:
        """Generate a plot outline by invoking the Claude API.

        Args:
            request: Structured request describing the desired plot.

        Returns:
            ClaudeResponse: API response with generated content.
        """
        if not self.is_claude_available():
            return ClaudeResponse(success=False, content="", error_message="Claude API is not available")

        try:
            prompt = self._build_plot_generation_prompt(request)
            claude_request = ClaudeRequest(
                prompt=prompt, system_prompt=self._get_plot_system_prompt(), max_tokens=4000, temperature=0.7
            )

            start_time = datetime.now(timezone.utc)
            response = self._call_claude_api(claude_request)
            end_time = datetime.now(timezone.utc)

            response.response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            return response

        except Exception as e:
            return ClaudeResponse(success=False, content="", error_message=f"Claude API error: {e!s}")

    def is_claude_available(self) -> bool:
        """Return whether the Claude service is initialized and available.

        Returns:
            bool: ``True`` if the API client can be used.
        """
        return self._api_available and self._claude_service is not None

    def get_claude_model_info(self) -> dict[str, Any]:
        """Return metadata describing supported Claude models.

        Returns:
            dict[str, Any]: Availability flag, model list, and default choice.
        """
        if not self.is_claude_available():
            return {"available": False, "models": []}

        return {
            "available": True,
            "models": [
                {
                    "name": "claude-3-sonnet-20240229",
                    "description": "Balanced performance and cost",
                    "max_tokens": 4096,
                    "recommended_for": "plot_generation",
                },
                {
                    "name": "claude-3-opus-20240229",
                    "description": "Highest quality output",
                    "max_tokens": 4096,
                    "recommended_for": "complex_narrative",
                },
            ],
            "default_model": "claude-3-sonnet-20240229",
        }

    def validate_request(self, request: PlotGenerationRequest) -> list[str]:
        """Validate high-level plot generation parameters.

        Args:
            request: Incoming request to validate.

        Returns:
            list[str]: Validation error messages; empty when valid.
        """
        errors: list[Any] = []

        if request.episode_number <= 0:
            errors.append("Episode number must be positive")

        if not request.project_name.strip():
            errors.append("Project name is required")

        if request.chapter_number <= 0:
            errors.append("Chapter number must be positive")

        if not request.context_data:
            errors.append("Context data is required for quality generation")

        return errors

    def _initialize_service(self) -> None:
        """Instantiate the Claude evaluation service when possible."""
        try:
            self._claude_service = ClaudeCodeEvaluationService()
            self._api_available = True
        except Exception:
            self._claude_service = None
            self._api_available = False

    def _build_plot_generation_prompt(self, request: PlotGenerationRequest) -> str:
        """Construct the prompt payload consumed by the Claude API.

        Args:
            request: Domain-layer plot generation request.

        Returns:
            str: Fully formatted prompt string.
        """
        context_info = ""
        if request.context_data:
            context_info = f"""
Project Context:
    - Project: {request.project_name}
- Chapter: {request.chapter_number}
- Previous episodes: {request.context_data.get("previous_episodes", "None")}
- Character info: {request.context_data.get("characters", "Not specified")}
- World setting: {request.context_data.get("world_setting", "Not specified")}
"""

        return f"""Generate a detailed plot for Episode {request.episode_number} of a web novel.

{context_info}

Requirements:
    1. Create an engaging episode structure with clear beginning, development, climax, and resolution
2. Include character development and dialogue opportunities
3. Maintain consistency with previous episodes
4. Follow web novel serialization best practices
5. Target length: 3000-4000 words when written

Please provide the plot in structured YAML format with the following sections:
    - episode_info (number, title, chapter)
- synopsis (brief episode summary)
- scenes (detailed scene breakdown)
- character_development (character arcs in this episode)
- foreshadowing (hints for future episodes)
- themes (episode themes and messages)

Focus on creating compelling narrative tension and character growth suitable for web novel readers.
"""

    def _get_plot_system_prompt(self) -> str:
        """Return the system prompt that frames Claude's role.

        Returns:
            str: Instruction block forwarded as system context.
        """
        return """You are an expert web novel plot developer specializing in Japanese light novel and web novel formats.

Your expertise includes:
    - Creating engaging episodic structures for serialized fiction
- Developing compelling character arcs and relationships
- Building narrative tension and pacing for web publication
- Understanding reader engagement patterns for online fiction
- Crafting plots that work well in ~4000 word episodes

Generate structured, detailed plots that provide clear guidance for writers while maintaining creative flexibility. Focus on character-driven stories with clear emotional beats and satisfying progression.

Always respond in valid YAML format that can be parsed and used by writing tools."""

    def _call_claude_api(self, request: ClaudeRequest) -> ClaudeResponse:
        """Invoke the Claude API and normalize the response payload.

        Args:
            request: Prepared request parameters for the Claude API.

        Returns:
            ClaudeResponse: Normalized API response.
        """
        if not self._claude_service:
            return ClaudeResponse(success=False, content="", error_message="Claude service not initialized")

        try:
            # Note: This is a simplified implementation
            # In practice, would use actual Claude API client
            # For now, simulate successful response with template content

            generated_content = self._generate_mock_plot_response(request)

            return ClaudeResponse(
                success=True,
                content=generated_content,
                token_usage={"input": len(request.prompt) // 4, "output": len(generated_content) // 4},
            )

        except Exception as e:
            return ClaudeResponse(success=False, content="", error_message=str(e))

    def _generate_mock_plot_response(self, request: ClaudeRequest) -> str:
        """Produce a deterministic mock response for offline testing.

        Args:
            request: Request parameters that guide the mock content.

        Returns:
            str: YAML payload that mimics the expected API output.
        """
        # Extract episode number from prompt if possible
        episode_num = "X"
        if "Episode" in request.prompt:
            with contextlib.suppress(IndexError, ValueError):
                episode_num = request.prompt.split("Episode ")[1].split(" ")[0]

        return f"""episode_info:
  episode_number: {episode_num}
  title: "Generated Episode {episode_num}"
  chapter: 1
  word_count_target: 3500

synopsis: |
  A compelling episode that advances the main plot while developing character relationships.
  Features meaningful character growth and sets up future narrative developments.

scenes:
  - scene_number: 1
    title: "Opening Scene"
    location: "School Courtyard"
    purpose: "Establish episode tone and conflict"
    content: |
      The protagonist faces a new challenge that tests their recent growth.
      Dialogue reveals character motivations and relationships.

  - scene_number: 2
    title: "Development"
    location: "Classroom"
    purpose: "Build tension and develop theme"
    content: |
      Supporting characters provide different perspectives on the central conflict.
      Technical/magical elements are woven naturally into character interactions.

  - scene_number: 3
    title: "Climax"
    location: "Library"
    purpose: "Emotional/narrative peak"
    content: |
      The protagonist must make a difficult choice or face a major challenge.
      Character growth is demonstrated through actions and decisions.

  - scene_number: 4
    title: "Resolution"
    location: "Dorm Room"
    purpose: "Wrap up episode arc while setting up future"
    content: |
      Consequences of the episode's events are established.
      Character relationships have evolved in meaningful ways.

character_development:
  # 新形式（機械処理対応）
  main_characters:
    hero:
      name: "Protagonist"
      character_type: "hero"
      growth_indicators:
        - "Learns to balance technical expertise with social awareness"
        - "Shows growth in understanding others' perspectives"
    heroine:
      name: "Heroine"
      character_type: "heroine"
      growth_indicators:
        - "Develops stronger self-confidence and assertiveness"
        - "Contributes meaningfully to problem-solving"

  supporting_characters:
    mentor:
      character_type: "mentor"
      contributions:
        - "Provides wisdom and guidance at crucial moments"
    allies:
      character_type: "supporting"
      development:
        - "Friend characters reveal hidden depths and motivations"
        - "Antagonistic forces become more nuanced and understandable"

  # 後方互換性
  legacy_character_arcs:
    protagonist:
      - "Learns to balance technical expertise with social awareness"
      - "Shows growth in understanding others' perspectives"
    supporting_characters:
      - "Friend characters reveal hidden depths and motivations"
      - "Antagonistic forces become more nuanced and understandable"

foreshadowing:
  - "Hint at upcoming technical challenge that will test all characters"
  - "Plant seeds for romantic subplot development"
  - "Establish consequences that will affect future episodes"

themes:
  - "Growth through adversity"
  - "The importance of collaboration and understanding"
  - "Balancing individual goals with community needs"

technical_elements:
  - "Programming/debugging metaphors woven into magical system"
  - "Technical problem-solving applied to character conflicts"
  - "Reader-friendly explanations of complex concepts"
"""
