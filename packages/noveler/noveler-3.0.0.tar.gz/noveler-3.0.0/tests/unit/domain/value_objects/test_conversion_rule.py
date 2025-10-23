"""ConversionRule値オブジェクトのユニットテスト

現行ドメイン実装（patternベース変換ルール）に合わせた検証。
"""

from __future__ import annotations

import pytest

from noveler.domain.exceptions import ValidationError
from noveler.domain.value_objects.conversion_rule import ConversionRule, ConversionType

pytestmark = pytest.mark.vo_smoke


class TestConversionRuleCreation:
    """ConversionRule生成に関するテスト"""

    def test_creates_valid_rule(self) -> None:
        """必須フィールドを満たしたルールは生成できる"""
        rule = ConversionRule(
            rule_id="rule-001",
            name="Replace legacy header",
            conversion_type=ConversionType.TEXT_REPLACE,
            source_pattern=r"^旧見出し:(?P<value>.*)$",
            target_pattern=r"新見出し:{value}",
            enabled=True,
            priority=10,
            conditions={"format": "legacy"},
        )

        assert rule.rule_id == "rule-001"
        assert rule.name == "Replace legacy header"
        assert rule.conversion_type is ConversionType.TEXT_REPLACE
        assert rule.source_pattern.startswith("^旧見出し")
        assert rule.target_pattern.startswith("新見出し")
        assert rule.enabled is True
        assert rule.priority == 10
        assert rule.conditions == {"format": "legacy"}

    @pytest.mark.parametrize(
        "field, value",
        [
            ("rule_id", ""),
            ("name", " "),
            ("source_pattern", ""),
            ("target_pattern", ""),
        ],
    )
    def test_missing_required_fields_raise_validation_error(self, field: str, value: str) -> None:
        """必須フィールドが空の場合はValidationErrorになる"""
        params = {
            "rule_id": "rule-001",
            "name": "Dummy",
            "conversion_type": ConversionType.TEXT_REPLACE,
            "source_pattern": "pattern",
            "target_pattern": "replacement",
        }
        params[field] = value

        with pytest.raises(ValidationError) as exc:
            ConversionRule(**params)

        assert exc.value.field == field

    def test_negative_priority_is_rejected(self) -> None:
        """優先度が負の値の場合はValidationError"""
        with pytest.raises(ValidationError) as exc:
            ConversionRule(
                rule_id="rule-001",
                name="Invalid priority",
                conversion_type=ConversionType.TEXT_REPLACE,
                source_pattern="pattern",
                target_pattern="target",
                priority=-1,
            )

        assert exc.value.field == "priority"


class TestConversionRuleApplicability:
    """条件判定のテスト"""

    def test_disabled_rule_is_not_applicable(self) -> None:
        rule = ConversionRule(
            rule_id="rule-disabled",
            name="Disabled rule",
            conversion_type=ConversionType.TEXT_REPLACE,
            source_pattern="pattern",
            target_pattern="target",
            enabled=False,
        )

        assert rule.is_applicable({"format": "legacy"}) is False

    def test_conditions_must_match(self) -> None:
        rule = ConversionRule(
            rule_id="rule-conditions",
            name="Conditional rule",
            conversion_type=ConversionType.TEXT_REPLACE,
            source_pattern="pattern",
            target_pattern="target",
            conditions={"format": "legacy", "language": "ja"},
        )

        assert rule.is_applicable({"format": "legacy", "language": "ja"}) is True
        assert rule.is_applicable({"format": "legacy", "language": "en"}) is False
        assert rule.is_applicable({}) is False

    def test_no_conditions_applies_when_enabled(self) -> None:
        rule = ConversionRule(
            rule_id="rule-basic",
            name="Basic rule",
            conversion_type=ConversionType.TEXT_REPLACE,
            source_pattern="pattern",
            target_pattern="target",
        )

        assert rule.is_applicable({}) is True
