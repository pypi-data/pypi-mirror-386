#!/usr/bin/env python3
"""シーン演出指示値オブジェクトのテスト

TDD原則に基づく単体テスト


仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

import pytest

from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.scene_direction import SceneDirection

pytestmark = pytest.mark.vo_smoke



class TestSceneDirection:
    """SceneDirection値オブジェクトのテスト"""

    def test_valid_creation_minimal(self) -> None:
        """有効な値での作成 - 最小限"""
        direction = SceneDirection(pacing="medium", tension_curve="rising", emotional_flow="calm_to_excited")

        assert direction.pacing == "medium"
        assert direction.tension_curve == "rising"
        assert direction.emotional_flow == "calm_to_excited"
        assert direction.visual_direction is None
        assert direction.sound_design is None
        assert direction.special_effects is None

    def test_valid_creation_full(self) -> None:
        """有効な値での作成 - 全パラメータ"""
        visual_direction = {"camera_angle": "close_up", "lighting": "dramatic"}
        sound_design = {"bgm": "tense_music", "volume": "low"}
        special_effects = ["slow_motion", "fade_in"]

        direction = SceneDirection(
            pacing="fast",
            tension_curve="climax",
            emotional_flow="intense_fear",
            visual_direction=visual_direction,
            sound_design=sound_design,
            special_effects=special_effects,
        )

        assert direction.pacing == "fast"
        assert direction.tension_curve == "climax"
        assert direction.emotional_flow == "intense_fear"
        assert direction.visual_direction == visual_direction
        assert direction.sound_design == sound_design
        assert direction.special_effects == special_effects

    def test_invalid_pacing(self) -> None:
        """無効なpacing値"""
        with pytest.raises(
            DomainException,
            match="pacing は \\['slow', 'medium', 'fast'\\] のいずれかである必要があります",
        ):
            SceneDirection(pacing="invalid", tension_curve="rising", emotional_flow="calm")

    def test_valid_pacing_values(self) -> None:
        """有効なpacing値の境界テスト"""
        valid_pacings = ["slow", "medium", "fast"]

        for pacing in valid_pacings:
            direction = SceneDirection(pacing=pacing, tension_curve="rising", emotional_flow="calm")
            assert direction.pacing == pacing

    def test_empty_tension_curve(self) -> None:
        """空のtension_curve"""
        with pytest.raises(DomainException, match="tension_curve は必須です"):
            SceneDirection(pacing="medium", tension_curve="", emotional_flow="calm")

    def test_whitespace_tension_curve(self) -> None:
        """空白のみのtension_curve"""
        with pytest.raises(DomainException, match="tension_curve は必須です"):
            SceneDirection(pacing="medium", tension_curve="   ", emotional_flow="calm")

    def test_empty_emotional_flow(self) -> None:
        """空のemotional_flow"""
        with pytest.raises(DomainException, match="emotional_flow は必須です"):
            SceneDirection(pacing="medium", tension_curve="rising", emotional_flow="")

    def test_whitespace_emotional_flow(self) -> None:
        """空白のみのemotional_flow"""
        with pytest.raises(DomainException, match="emotional_flow は必須です"):
            SceneDirection(pacing="medium", tension_curve="rising", emotional_flow="   ")

    def test_to_dict_minimal(self) -> None:
        """辞書変換 - 最小限"""
        direction = SceneDirection(pacing="slow", tension_curve="building", emotional_flow="suspense")

        expected = {"pacing": "slow", "tension_curve": "building", "emotional_flow": "suspense"}

        result = direction.to_dict()
        assert result == expected

    def test_to_dict_full(self) -> None:
        """辞書変換 - 全パラメータ"""
        visual_direction = {"camera": "wide_shot"}
        sound_design = {"bgm": "orchestral"}
        special_effects = ["zoom_in", "color_filter"]

        direction = SceneDirection(
            pacing="fast",
            tension_curve="peak",
            emotional_flow="terror",
            visual_direction=visual_direction,
            sound_design=sound_design,
            special_effects=special_effects,
        )

        expected = {
            "pacing": "fast",
            "tension_curve": "peak",
            "emotional_flow": "terror",
            "visual_direction": visual_direction,
            "sound_design": sound_design,
            "special_effects": special_effects,
        }

        result = direction.to_dict()
        assert result == expected

    def test_from_dict_minimal(self) -> None:
        """辞書から復元 - 最小限"""
        data = {"pacing": "medium", "tension_curve": "steady", "emotional_flow": "contemplative"}

        direction = SceneDirection.from_dict(data)

        assert direction.pacing == "medium"
        assert direction.tension_curve == "steady"
        assert direction.emotional_flow == "contemplative"
        assert direction.visual_direction is None
        assert direction.sound_design is None
        assert direction.special_effects is None

    def test_from_dict_full(self) -> None:
        """辞書から復元 - 全パラメータ"""
        data = {
            "pacing": "slow",
            "tension_curve": "declining",
            "emotional_flow": "melancholy",
            "visual_direction": {"lighting": "dim"},
            "sound_design": {"volume": "quiet"},
            "special_effects": ["fade_out"],
        }

        direction = SceneDirection.from_dict(data)

        assert direction.pacing == "slow"
        assert direction.tension_curve == "declining"
        assert direction.emotional_flow == "melancholy"
        assert direction.visual_direction == {"lighting": "dim"}
        assert direction.sound_design == {"volume": "quiet"}
        assert direction.special_effects == ["fade_out"]

    def test_from_dict_with_invalid_data(self) -> None:
        """無効なデータからの復元"""
        data = {"pacing": "invalid_pace", "tension_curve": "rising", "emotional_flow": "calm"}

        with pytest.raises(DomainException, match=".*"):
            SceneDirection.from_dict(data)

    def test_roundtrip_conversion(self) -> None:
        """辞書変換の往復テスト"""
        original_data = {
            "pacing": "fast",
            "tension_curve": "explosive",
            "emotional_flow": "panic",
            "visual_direction": {"angle": "bird_eye"},
            "sound_design": {"effect": "echo"},
            "special_effects": ["shake", "flash"],
        }

        # 辞書 → オブジェクト → 辞書
        direction = SceneDirection.from_dict(original_data)
        result_data = direction.to_dict()

        assert result_data == original_data

    def test_get_summary_minimal(self) -> None:
        """要約生成 - 最小限"""
        direction = SceneDirection(pacing="medium", tension_curve="building", emotional_flow="anticipation")

        expected = "ペース: medium, 緊張: building, 感情: anticipation"
        assert direction.get_summary() == expected

    def test_get_summary_with_effects(self) -> None:
        """要約生成 - 特殊効果あり"""
        direction = SceneDirection(
            pacing="slow",
            tension_curve="relaxed",
            emotional_flow="peaceful",
            special_effects=["soft_focus", "warm_filter", "gentle_fade"],
        )

        expected = "ペース: slow, 緊張: relaxed, 感情: peaceful, 特殊効果: soft_focus, warm_filter, gentle_fade"
        assert direction.get_summary() == expected

    def test_get_summary_empty_effects(self) -> None:
        """要約生成 - 空の特殊効果"""
        direction = SceneDirection(pacing="fast", tension_curve="intense", emotional_flow="rage", special_effects=[])

        expected = "ペース: fast, 緊張: intense, 感情: rage"
        assert direction.get_summary() == expected

    def test_immutability(self) -> None:
        """不変性のテスト"""
        direction = SceneDirection(pacing="medium", tension_curve="steady", emotional_flow="calm")

        # dataclassがfrozen=Trueなので、属性変更は不可
        with pytest.raises(AttributeError, match=".*"):
            direction.pacing = "fast"  # type: ignore

    def test_equality(self) -> None:
        """等価性のテスト"""
        direction1 = SceneDirection(pacing="medium", tension_curve="rising", emotional_flow="excitement")

        direction2 = SceneDirection(pacing="medium", tension_curve="rising", emotional_flow="excitement")

        direction3 = SceneDirection(pacing="fast", tension_curve="rising", emotional_flow="excitement")

        # 同じ値は等価
        assert direction1 == direction2

        # 異なる値は非等価
        assert direction1 != direction3

    def test_complex_visual_direction(self) -> None:
        """複雑な視覚演出指示"""
        complex_visual = {
            "camera_movements": ["pan_left", "zoom_in", "tilt_up"],
            "lighting": {"main": "spotlight", "ambient": "blue_wash", "intensity": 75},
            "color_grading": {"temperature": "warm", "saturation": "high", "contrast": "dramatic"},
        }

        direction = SceneDirection(
            pacing="medium",
            tension_curve="building",
            emotional_flow="mysterious",
            visual_direction=complex_visual,
        )

        # 複雑な辞書もそのまま保持される
        assert direction.visual_direction == complex_visual

        # 辞書変換でも保持される
        result = direction.to_dict()
        assert result["visual_direction"] == complex_visual

    def test_complex_sound_design(self) -> None:
        """複雑なサウンドデザイン"""
        complex_sound = {
            "layers": [
                {"type": "ambient", "source": "wind", "volume": 0.3},
                {"type": "musical", "source": "string_section", "volume": 0.7},
                {"type": "effect", "source": "footsteps", "volume": 0.5},
            ],
            "reverb": {"type": "hall", "intensity": 0.6},
            "eq": {"bass": +3, "mid": 0, "treble": -2},
        }

        direction = SceneDirection(
            pacing="slow",
            tension_curve="suspenseful",
            emotional_flow="dread",
            sound_design=complex_sound,
        )

        # 複雑な辞書もそのまま保持される
        assert direction.sound_design == complex_sound

        # 辞書変換でも保持される
        result = direction.to_dict()
        assert result["sound_design"] == complex_sound
