"""Test enhanced character consistency service with A24 new schema"""

import pytest

from noveler.domain.entities.episode import Episode, EpisodeNumber
from noveler.domain.services.character_consistency_service import CharacterConsistencyService
from noveler.domain.value_objects.character_profile import CharacterProfile


@pytest.fixture
def consistency_service():
    """Create consistency service instance"""
    return CharacterConsistencyService(character_repository=None)


@pytest.fixture
def new_schema_character():
    """Create character with A24 new schema data"""
    return CharacterProfile(
        name="山田太郎",
        attributes={
            "personality": "分析的・効率重視",
            "speech_style": "丁寧語",
            "_raw_layers": {
                "layer1_psychology": {
                    "psychological_models": {
                        "summary_bullets": ["ログで状況把握 → 価値観/効率基準でスコア付け → 最小工数で実行"],
                        "decision_flow": {
                            "decision_step_perception": "ログで状況把握",
                            "decision_step_evaluation": "価値観/効率基準でスコア付け",
                            "decision_step_action": "最小工数で実行",
                            "decision_step_emotional_aftermath": "皮肉・諦観でカバー",
                        },
                    },
                },
            },
            "_raw_llm_prompt_profile": {
                "default_scene_goal": "効率的問題解決",
                "post_review_checklist": ["論理的思考の一貫性", "皮肉表現の適切性"],
            },
        },
    )


@pytest.fixture
def legacy_character():
    """Create character without new schema data"""
    return CharacterProfile(
        name="鈴木花子",
        attributes={
            "personality": "明るい",
            "speech_style": "カジュアル",
        },
    )


def test_check_decision_flow_violation_intuitive_approach(consistency_service, new_schema_character):
    """Test decision flow check detects intuitive approach violation"""
    episode = Episode(
        number=EpisodeNumber(1),
        title="Test Episode",
        content="山田太郎は直感でこの問題を解決しようとした。",
    )

    violations = consistency_service.analyze_consistency(episode, [new_schema_character])

    assert len(violations) > 0
    decision_flow_violations = [v for v in violations if v.attribute == "decision_flow_perception"]
    assert len(decision_flow_violations) == 1
    assert decision_flow_violations[0].character_name == "山田太郎"
    assert "Intuitive approach detected" in decision_flow_violations[0].actual


def test_check_decision_flow_no_violation_analytical_approach(consistency_service, new_schema_character):
    """Test decision flow check passes for analytical approach"""
    episode = Episode(
        number=EpisodeNumber(1),
        title="Test Episode",
        content="山田太郎はログを確認し、データに基づいて判断した。",
    )

    violations = consistency_service.analyze_consistency(episode, [new_schema_character])

    decision_flow_violations = [v for v in violations if v.attribute == "decision_flow_perception"]
    assert len(decision_flow_violations) == 0


def test_check_psychological_model_violation_solo_decision(consistency_service):
    """Test psychological model check detects solo decision without team consideration"""
    team_focused_character = CharacterProfile(
        name="リーダー",
        attributes={
            "personality": "チームワーク重視",
            "_raw_layers": {
                "layer1_psychology": {
                    "psychological_models": {
                        "summary_bullets": ["直感 → 仲間確認 → 行動 → 皮肉で締める"],
                    },
                },
            },
        },
    )

    episode = Episode(
        number=EpisodeNumber(1),
        title="Test Episode",
        content="リーダーは一人で決断した。",
    )

    violations = consistency_service.analyze_consistency(episode, [team_focused_character])

    psych_violations = [v for v in violations if v.attribute == "psychological_model"]
    assert len(psych_violations) == 1
    assert "Solo decision detected" in psych_violations[0].actual


def test_check_psychological_model_no_violation_team_decision(consistency_service):
    """Test psychological model check passes for team-based decision"""
    team_focused_character = CharacterProfile(
        name="リーダー",
        attributes={
            "personality": "チームワーク重視",
            "_raw_layers": {
                "layer1_psychology": {
                    "psychological_models": {
                        "summary_bullets": ["直感 → 仲間確認 → 行動 → 皮肉で締める"],
                    },
                },
            },
        },
    )

    episode = Episode(
        number=EpisodeNumber(1),
        title="Test Episode",
        content="リーダーはチームメンバーと相談して決めた。",
    )

    violations = consistency_service.analyze_consistency(episode, [team_focused_character])

    psych_violations = [v for v in violations if v.attribute == "psychological_model"]
    assert len(psych_violations) == 0


def test_legacy_character_uses_existing_checks_only(consistency_service, legacy_character):
    """Test legacy character without new schema only uses existing checks"""
    episode = Episode(
        number=EpisodeNumber(1),
        title="Test Episode",
        content="鈴木花子は直感で判断した。",  # Would violate if new schema check applied
    )

    violations = consistency_service.analyze_consistency(episode, [legacy_character])

    # Should not have decision_flow or psychological_model violations
    new_schema_violations = [
        v for v in violations if v.attribute in ("decision_flow_perception", "psychological_model")
    ]
    assert len(new_schema_violations) == 0


def test_mixed_characters_new_and_legacy(consistency_service, new_schema_character, legacy_character):
    """Test consistency check with both new schema and legacy characters"""
    episode = Episode(
        number=EpisodeNumber(1),
        title="Test Episode",
        content="""
        山田太郎は直感で判断した。
        鈴木花子も直感で判断した。
        """,
    )

    violations = consistency_service.analyze_consistency(episode, [new_schema_character, legacy_character])

    # Only new schema character should have decision flow violation
    decision_flow_violations = [v for v in violations if v.attribute == "decision_flow_perception"]
    assert len(decision_flow_violations) == 1
    assert decision_flow_violations[0].character_name == "山田太郎"


def test_has_new_schema_data_returns_true_for_new_schema(new_schema_character):
    """Test has_new_schema_data returns True for character with new schema"""
    assert new_schema_character.has_new_schema_data() is True


def test_has_new_schema_data_returns_false_for_legacy(legacy_character):
    """Test has_new_schema_data returns False for legacy character"""
    assert legacy_character.has_new_schema_data() is False


def test_get_decision_flow_returns_data_for_new_schema(new_schema_character):
    """Test get_decision_flow returns decision flow data"""
    decision_flow = new_schema_character.get_decision_flow()

    assert decision_flow is not None
    assert decision_flow["decision_step_perception"] == "ログで状況把握"
    assert decision_flow["decision_step_evaluation"] == "価値観/効率基準でスコア付け"


def test_get_decision_flow_returns_empty_for_legacy(legacy_character):
    """Test get_decision_flow returns empty dict for legacy character"""
    decision_flow = legacy_character.get_decision_flow()

    assert decision_flow == {}


def test_get_psychological_summary_returns_data_for_new_schema(new_schema_character):
    """Test get_psychological_summary returns summary bullets"""
    psych_summary = new_schema_character.get_psychological_summary()

    assert psych_summary is not None
    assert len(psych_summary) > 0
    assert "ログで状況把握" in psych_summary[0]


def test_get_psychological_summary_returns_empty_for_legacy(legacy_character):
    """Test get_psychological_summary returns empty list for legacy character"""
    psych_summary = legacy_character.get_psychological_summary()

    assert psych_summary == []
