# File: tests/unit/domain/writing_guide/test_writing_guide.py
# Purpose: Unit tests for WritingGuide Aggregate Root
# Context: Tests core business logic, template selection, and content validation

import pytest
from noveler.domain.writing_guide.models.writing_guide import WritingGuide
from noveler.domain.writing_guide.models.writing_request import WritingRequest, DetailLevel
from noveler.domain.writing_guide.models.prompt_template import PromptTemplate
from noveler.domain.writing_guide.models.validation_result import ValidationResult


class TestWritingGuideConstruction:
    """Tests for WritingGuide construction and validation."""

    def test_valid_guide_construction(self) -> None:
        """Verify valid guide can be constructed."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Test template {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {
            "forbidden_expressions": [],
            "supported_genres": ["fantasy"],
        }
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)
        assert guide.get_version() == "1.0.0"
        assert guide.supports_genre("fantasy") is True

    def test_empty_metadata_raises_error(self) -> None:
        """Verify empty metadata violates domain invariant."""
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Test {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {"forbidden_expressions": []}
        with pytest.raises(ValueError, match="metadata must contain 'version' key"):
            WritingGuide(metadata={}, templates=templates, constraints=constraints)

    def test_empty_templates_raises_error(self) -> None:
        """Verify empty templates violates domain invariant."""
        metadata = {"version": "1.0.0"}
        constraints = {"forbidden_expressions": []}
        with pytest.raises(ValueError, match="templates must not be empty"):
            WritingGuide(metadata=metadata, templates={}, constraints=constraints)

    def test_empty_constraints_raises_error(self) -> None:
        """Verify empty constraints violates domain invariant."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard": PromptTemplate(
                template_id="standard",
                content="Test {genre}",
                required_variables=["genre"],
            )
        }
        with pytest.raises(ValueError, match="constraints must not be empty"):
            WritingGuide(metadata=metadata, templates=templates, constraints={})


class TestWritingGuideGeneratePrompt:
    """Tests for WritingGuide.generate_prompt core business logic."""

    def test_generate_prompt_with_standard_template(self) -> None:
        """Verify prompt generation with standard template."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Genre: {genre}, Viewpoint: {viewpoint}",
                required_variables=["genre", "viewpoint"],
            )
        }
        constraints = {"forbidden_expressions": [], "supported_genres": ["fantasy"]}
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)

        request = WritingRequest.create_default(genre="fantasy")
        prompt = guide.generate_prompt(request)
        assert "Genre: fantasy" in prompt
        assert "Viewpoint: 三人称単元視点" in prompt

    def test_generate_prompt_with_stepwise_template(self) -> None:
        """Verify prompt generation selects stepwise template for stepwise request."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Standard: {genre}",
                required_variables=["genre"],
            ),
            "stepwise_prompt": PromptTemplate(
                template_id="stepwise_prompt",
                content="Stepwise: {genre}",
                required_variables=["genre"],
            ),
        }
        constraints = {"forbidden_expressions": [], "supported_genres": ["fantasy"]}
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)

        request = WritingRequest(
            genre="fantasy",
            word_count="4000-6000",
            viewpoint="三人称",
            viewpoint_character="主人公",
            difficulty="beginner",
            priority="critical",
            detail_level=DetailLevel.STEPWISE,
        )
        prompt = guide.generate_prompt(request)
        assert "Stepwise: fantasy" in prompt

    def test_generate_prompt_missing_template_raises_error(self) -> None:
        """Verify error when required template is missing."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Standard: {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {"forbidden_expressions": [], "supported_genres": ["fantasy"]}
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)

        request = WritingRequest(
            genre="fantasy",
            word_count="4000-6000",
            viewpoint="三人称",
            viewpoint_character="主人公",
            difficulty="beginner",
            priority="critical",
            detail_level=DetailLevel.STEPWISE,
        )
        with pytest.raises(ValueError, match="Template not found"):
            guide.generate_prompt(request)

    def test_generate_prompt_with_custom_requirements(self) -> None:
        """Verify prompt generation includes custom requirements."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Genre: {genre}\nCustom: {custom_requirements}",
                required_variables=["genre", "custom_requirements"],
            )
        }
        constraints = {"forbidden_expressions": [], "supported_genres": ["fantasy"]}
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)

        request = WritingRequest(
            genre="fantasy",
            word_count="4000-6000",
            viewpoint="一人称",
            viewpoint_character="主人公",
            difficulty="standard",
            priority="high",
            detail_level=DetailLevel.STANDARD,
            custom_requirements=["Add humor", "Include dialogue"],
        )
        prompt = guide.generate_prompt(request)
        # Custom requirements should be rendered in the prompt
        assert "Add humor" in prompt
        assert "Include dialogue" in prompt


class TestWritingGuideValidateContent:
    """Tests for WritingGuide.validate_content business logic."""

    def test_validate_content_passes_for_clean_content(self) -> None:
        """Verify validation passes for clean content."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Test {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {
            "forbidden_expressions": ["禁止表現"],
        }
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)

        content = "これはクリーンなコンテンツです。禁止された表現は含まれていません。"
        result = guide.validate_content(content)
        assert result.is_valid() is True
        assert result.score == 100

    def test_validate_content_detects_forbidden_expression(self) -> None:
        """Verify validation detects forbidden expressions."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Test {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {
            "forbidden_expressions": ["禁止"],
        }
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)

        content = "このコンテンツには禁止表現が含まれています。"
        result = guide.validate_content(content)
        assert result.is_valid() is False
        assert any("禁止表現" in issue for issue in result.issues)

    def test_validate_content_detects_long_sentence(self) -> None:
        """Verify validation detects consecutive short sentences."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Test {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {
            "forbidden_expressions": [],
        }
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)

        # Create 8 consecutive short sentences to trigger issue
        short_sentences = "短い。短い。短い。短い。短い。短い。短い。短い。"
        result = guide.validate_content(short_sentences)
        assert not result.is_valid() or result.has_warnings()

    def test_validate_content_detects_short_paragraph(self) -> None:
        """Verify validation detects long paragraphs."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Test {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {
            "forbidden_expressions": [],
        }
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)

        # Create paragraph with 5 lines (exceeds 4 line limit)
        long_paragraph = "行1。\n行2。\n行3。\n行4。\n行5。"
        result = guide.validate_content(long_paragraph)
        assert result.has_warnings()

    def test_validate_content_with_multiple_issues(self) -> None:
        """Verify validation accumulates multiple issues."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Test {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {
            "forbidden_expressions": ["禁止"],
        }
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)

        # Forbidden expression + consecutive short sentences
        content = "禁止表現。短い。短い。短い。短い。短い。短い。短い。短い。"
        result = guide.validate_content(content)
        assert result.is_valid() is False
        # Should have multiple issues/warnings
        assert result.total_issue_count() > 1


class TestWritingGuideGetters:
    """Tests for WritingGuide getter methods."""

    def test_get_version_returns_metadata_version(self) -> None:
        """Verify get_version returns version from metadata."""
        metadata = {"version": "2.5.1"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Test {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {"forbidden_expressions": []}
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)
        assert guide.get_version() == "2.5.1"

    def test_supports_genre_returns_true_for_listed_genre(self) -> None:
        """Verify supports_genre returns True for supported genres."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Test {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {"forbidden_expressions": [], "supported_genres": ["fantasy", "mystery", "sci-fi"]}
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)
        assert guide.supports_genre("fantasy") is True
        assert guide.supports_genre("mystery") is True
        assert guide.supports_genre("sci-fi") is True

    def test_supports_genre_returns_false_when_not_in_constraints(self) -> None:
        """Verify supports_genre returns False when supported_genres not in constraints."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Test {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {"forbidden_expressions": []}
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)
        assert guide.supports_genre("fantasy") is False


class TestWritingGuideSupportGenre:
    """Tests for WritingGuide.supports_genre business logic method."""

    def test_supports_genre_returns_true_for_supported_genre(self) -> None:
        """Verify supports_genre returns True for listed genre."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Test {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {"forbidden_expressions": [], "supported_genres": ["fantasy", "mystery"]}
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)
        assert guide.supports_genre("fantasy") is True
        assert guide.supports_genre("mystery") is True

    def test_supports_genre_returns_false_for_unsupported_genre(self) -> None:
        """Verify supports_genre returns False for unlisted genre."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Test {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {"forbidden_expressions": [], "supported_genres": ["fantasy"]}
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)
        assert guide.supports_genre("sci-fi") is False

    def test_supports_genre_case_sensitive(self) -> None:
        """Verify supports_genre is case-sensitive."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Test {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {"forbidden_expressions": [], "supported_genres": ["fantasy"]}
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)
        assert guide.supports_genre("Fantasy") is False


class TestWritingGuideTemplateSelection:
    """Tests for WritingGuide template selection strategy."""

    def test_select_template_prefers_stepwise_when_requested(self) -> None:
        """Verify template selection prioritizes stepwise for stepwise requests."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Standard {genre}",
                required_variables=["genre"],
            ),
            "stepwise_prompt": PromptTemplate(
                template_id="stepwise_prompt",
                content="Stepwise {genre}",
                required_variables=["genre"],
            ),
        }
        constraints = {"forbidden_expressions": []}
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)

        request = WritingRequest(
            genre="fantasy",
            word_count="4000-6000",
            viewpoint="三人称",
            viewpoint_character="主人公",
            difficulty="beginner",
            priority="critical",
            detail_level=DetailLevel.STEPWISE,
        )
        prompt = guide.generate_prompt(request)
        assert "Stepwise" in prompt

    def test_select_template_falls_back_to_standard_when_stepwise_missing(self) -> None:
        """Verify template selection raises error when required template unavailable."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Standard {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {"forbidden_expressions": []}
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)

        request = WritingRequest(
            genre="fantasy",
            word_count="4000-6000",
            viewpoint="三人称",
            viewpoint_character="主人公",
            difficulty="beginner",
            priority="critical",
            detail_level=DetailLevel.STEPWISE,
        )
        # Should raise error since stepwise_prompt is required but missing
        with pytest.raises(ValueError):
            guide.generate_prompt(request)


class TestWritingGuideEdgeCases:
    """Tests for WritingGuide edge cases and boundary conditions."""

    def test_generate_prompt_with_empty_custom_requirements(self) -> None:
        """Verify empty custom requirements list is handled correctly."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Genre: {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {"forbidden_expressions": []}
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)

        request = WritingRequest(
            genre="fantasy",
            word_count="4000-6000",
            viewpoint="一人称",
            viewpoint_character="主人公",
            difficulty="standard",
            priority="high",
            detail_level=DetailLevel.STANDARD,
            custom_requirements=[],
        )
        prompt = guide.generate_prompt(request)
        assert "Genre: fantasy" in prompt

    def test_validate_content_with_empty_string(self) -> None:
        """Verify validation handles empty content."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Test {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {"forbidden_expressions": []}
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)

        result = guide.validate_content("")
        # Empty content is valid (returns score 100)
        assert result.is_valid() is True
        assert result.score == 100

    def test_validate_content_with_unicode(self) -> None:
        """Verify validation handles Unicode content correctly."""
        metadata = {"version": "1.0.0"}
        templates = {
            "standard_prompt": PromptTemplate(
                template_id="standard_prompt",
                content="Test {genre}",
                required_variables=["genre"],
            )
        }
        constraints = {"forbidden_expressions": []}
        guide = WritingGuide(metadata=metadata, templates=templates, constraints=constraints)

        content = "これは日本語のテストコンテンツです。問題なく処理されるべきです。"
        result = guide.validate_content(content)
        assert isinstance(result, ValidationResult)
        assert result.is_valid() is True
