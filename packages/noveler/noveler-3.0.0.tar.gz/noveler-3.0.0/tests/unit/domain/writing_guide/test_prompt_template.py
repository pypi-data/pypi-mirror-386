# File: tests/unit/domain/writing_guide/test_prompt_template.py
# Purpose: Unit tests for PromptTemplate Entity
# Context: Tests identity-based equality, rendering logic, and validation

import pytest
from noveler.domain.writing_guide.models.prompt_template import PromptTemplate


class TestPromptTemplateConstruction:
    """Tests for PromptTemplate construction and validation."""

    def test_valid_template_construction(self) -> None:
        """Verify valid template can be constructed."""
        template = PromptTemplate(
            template_id="test_template",
            content="Hello {name}, your score is {score}",
            required_variables=["name", "score"],
        )
        assert template.template_id == "test_template"
        assert "Hello" in template.content
        assert len(template.required_variables) == 2

    def test_empty_template_id_raises_error(self) -> None:
        """Verify empty template_id violates domain invariant."""
        with pytest.raises(ValueError, match="template_id must not be empty"):
            PromptTemplate(
                template_id="",
                content="Test content",
                required_variables=[],
            )

    def test_whitespace_template_id_raises_error(self) -> None:
        """Verify whitespace-only template_id violates domain invariant."""
        with pytest.raises(ValueError, match="template_id must not be empty"):
            PromptTemplate(
                template_id="   ",
                content="Test content",
                required_variables=[],
            )

    def test_empty_content_raises_error(self) -> None:
        """Verify empty content violates domain invariant."""
        with pytest.raises(ValueError, match="content must not be empty"):
            PromptTemplate(
                template_id="test_template",
                content="",
                required_variables=[],
            )

    def test_whitespace_content_is_accepted(self) -> None:
        """Verify whitespace-only content is accepted (implementation allows it)."""
        template = PromptTemplate(
            template_id="test_template",
            content="   ",
            required_variables=[],
        )
        assert template.content == "   "

    def test_template_with_no_required_variables(self) -> None:
        """Verify template without variables is valid."""
        template = PromptTemplate(
            template_id="static_template",
            content="This is a static template with no variables.",
            required_variables=[],
        )
        assert len(template.required_variables) == 0


class TestPromptTemplateEntityIdentity:
    """Tests for PromptTemplate entity identity-based equality."""

    def test_same_id_different_content_are_equal(self) -> None:
        """Verify entities with same ID are equal regardless of content."""
        template1 = PromptTemplate(
            template_id="template_1",
            content="Content A",
            required_variables=["var1"],
        )
        template2 = PromptTemplate(
            template_id="template_1",
            content="Content B",
            required_variables=["var2"],
        )
        assert template1 == template2

    def test_different_id_same_content_not_equal(self) -> None:
        """Verify entities with different IDs are not equal even with same content."""
        template1 = PromptTemplate(
            template_id="template_1",
            content="Same content",
            required_variables=["var1"],
        )
        template2 = PromptTemplate(
            template_id="template_2",
            content="Same content",
            required_variables=["var1"],
        )
        assert template1 != template2

    def test_hash_based_on_id_only(self) -> None:
        """Verify hash is based on template_id only."""
        template1 = PromptTemplate(
            template_id="template_1",
            content="Content A",
            required_variables=["var1"],
        )
        template2 = PromptTemplate(
            template_id="template_1",
            content="Content B",
            required_variables=["var2"],
        )
        assert hash(template1) == hash(template2)

    def test_can_be_used_in_set(self) -> None:
        """Verify entity can be used in sets (deduplication by ID)."""
        template1 = PromptTemplate(
            template_id="template_1",
            content="Content A",
            required_variables=["var1"],
        )
        template2 = PromptTemplate(
            template_id="template_1",
            content="Content B",
            required_variables=["var2"],
        )
        template3 = PromptTemplate(
            template_id="template_2",
            content="Content C",
            required_variables=["var3"],
        )
        template_set = {template1, template2, template3}
        # Only 2 unique templates (template1 and template2 are same by ID)
        assert len(template_set) == 2


class TestPromptTemplateRendering:
    """Tests for PromptTemplate rendering logic."""

    def test_render_with_all_variables_provided(self) -> None:
        """Verify rendering with all required variables succeeds."""
        template = PromptTemplate(
            template_id="greeting",
            content="Hello {name}, your score is {score}",
            required_variables=["name", "score"],
        )
        result = template.render({"name": "Alice", "score": "95"})
        assert result == "Hello Alice, your score is 95"

    def test_render_with_missing_variable_raises_error(self) -> None:
        """Verify rendering with missing required variable fails."""
        template = PromptTemplate(
            template_id="greeting",
            content="Hello {name}, your score is {score}",
            required_variables=["name", "score"],
        )
        with pytest.raises(ValueError, match="Missing required variable"):
            template.render({"name": "Alice"})

    def test_render_with_extra_variables_succeeds(self) -> None:
        """Verify rendering with extra variables (not required) succeeds."""
        template = PromptTemplate(
            template_id="greeting",
            content="Hello {name}",
            required_variables=["name"],
        )
        result = template.render({"name": "Bob", "extra": "ignored"})
        assert result == "Hello Bob"

    def test_render_with_no_variables(self) -> None:
        """Verify rendering static template (no variables) succeeds."""
        template = PromptTemplate(
            template_id="static",
            content="This is a static message.",
            required_variables=[],
        )
        result = template.render({})
        assert result == "This is a static message."

    def test_render_with_multiple_occurrences_of_same_variable(self) -> None:
        """Verify rendering with repeated variable substitutions."""
        template = PromptTemplate(
            template_id="repeated",
            content="{name} said hello to {name}",
            required_variables=["name"],
        )
        result = template.render({"name": "Charlie"})
        assert result == "Charlie said hello to Charlie"


class TestPromptTemplateContainsVariable:
    """Tests for contains_variable business logic method."""

    def test_contains_variable_returns_true_when_present(self) -> None:
        """Verify contains_variable detects presence of variable."""
        template = PromptTemplate(
            template_id="test",
            content="Hello {name}",
            required_variables=["name"],
        )
        assert template.contains_variable("name") is True

    def test_contains_variable_returns_false_when_absent(self) -> None:
        """Verify contains_variable detects absence of variable."""
        template = PromptTemplate(
            template_id="test",
            content="Hello {name}",
            required_variables=["name"],
        )
        assert template.contains_variable("age") is False

    def test_contains_variable_case_sensitive(self) -> None:
        """Verify contains_variable is case-sensitive."""
        template = PromptTemplate(
            template_id="test",
            content="Hello {name}",
            required_variables=["name"],
        )
        assert template.contains_variable("Name") is False


class TestPromptTemplateCanRenderWith:
    """Tests for can_render_with business logic method."""

    def test_can_render_with_returns_true_when_all_variables_present(self) -> None:
        """Verify can_render_with returns True when context has all variables."""
        template = PromptTemplate(
            template_id="test",
            content="Hello {name}, age {age}",
            required_variables=["name", "age"],
        )
        assert template.can_render_with({"name": "Alice", "age": "30"}) is True

    def test_can_render_with_returns_false_when_missing_variable(self) -> None:
        """Verify can_render_with returns False when missing required variable."""
        template = PromptTemplate(
            template_id="test",
            content="Hello {name}, age {age}",
            required_variables=["name", "age"],
        )
        assert template.can_render_with({"name": "Alice"}) is False

    def test_can_render_with_returns_true_with_extra_variables(self) -> None:
        """Verify can_render_with returns True even with extra variables."""
        template = PromptTemplate(
            template_id="test",
            content="Hello {name}",
            required_variables=["name"],
        )
        assert template.can_render_with({"name": "Bob", "extra": "value"}) is True

    def test_can_render_with_returns_true_for_no_variables_template(self) -> None:
        """Verify can_render_with returns True for static templates."""
        template = PromptTemplate(
            template_id="static",
            content="Static message",
            required_variables=[],
        )
        assert template.can_render_with({}) is True


class TestPromptTemplateMutability:
    """Tests for PromptTemplate mutability (not frozen)."""

    def test_content_can_be_modified_after_construction(self) -> None:
        """Verify entity fields can be modified (entities are mutable)."""
        template = PromptTemplate(
            template_id="test",
            content="Original content",
            required_variables=["var1"],
        )
        # Entity is mutable, so modification is allowed
        template.content = "Modified content"
        assert template.content == "Modified content"

    def test_required_variables_can_be_modified(self) -> None:
        """Verify required_variables list can be modified."""
        template = PromptTemplate(
            template_id="test",
            content="Test {var1}",
            required_variables=["var1"],
        )
        template.required_variables.append("var2")
        assert len(template.required_variables) == 2


class TestPromptTemplateEdgeCases:
    """Tests for PromptTemplate edge cases and boundary conditions."""

    def test_template_with_curly_braces_in_content(self) -> None:
        """Verify template handles literal curly braces correctly."""
        template = PromptTemplate(
            template_id="test",
            content="Use {{literal}} braces and {variable}",
            required_variables=["variable"],
        )
        result = template.render({"variable": "VALUE"})
        assert result == "Use {literal} braces and VALUE"

    def test_template_with_unicode_content(self) -> None:
        """Verify template handles Unicode content correctly."""
        template = PromptTemplate(
            template_id="test",
            content="こんにちは {name}さん",
            required_variables=["name"],
        )
        result = template.render({"name": "太郎"})
        assert result == "こんにちは 太郎さん"

    def test_template_with_very_long_content(self) -> None:
        """Verify template handles long content correctly."""
        long_content = "A" * 10000 + " {var} " + "B" * 10000
        template = PromptTemplate(
            template_id="long",
            content=long_content,
            required_variables=["var"],
        )
        result = template.render({"var": "VALUE"})
        assert "VALUE" in result
        assert len(result) > 20000

    def test_template_with_numeric_variable_values(self) -> None:
        """Verify template converts numeric values to strings during rendering."""
        template = PromptTemplate(
            template_id="test",
            content="Score: {score}",
            required_variables=["score"],
        )
        result = template.render({"score": 95})
        assert result == "Score: 95"
