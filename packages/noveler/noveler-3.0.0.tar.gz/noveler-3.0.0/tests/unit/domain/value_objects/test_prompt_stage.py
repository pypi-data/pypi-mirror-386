"""
SPEC-STAGED-001: PromptStage値オブジェクトのテスト

段階的プロンプト生成における段階値オブジェクトの
不変性、検証、比較機能をテストする。
"""

import pytest

from noveler.domain.value_objects.prompt_stage import PromptStage, get_all_stages, get_stage_by_number

pytestmark = pytest.mark.vo_smoke



class TestPromptStageValidation:
    """段階検証機能のテスト"""

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_valid_stage_creation(self):
        """正常な段階作成のテスト"""
        stage = PromptStage(
            stage_number=1,
            stage_name="テスト段階",
            estimated_duration_minutes=15,
            required_elements=("element1", "element2"),
            completion_criteria=("criterion1", "criterion2"),
        )

        assert stage.stage_number == 1
        assert stage.stage_name == "テスト段階"
        assert stage.estimated_duration_minutes == 15
        assert stage.required_elements == ("element1", "element2")
        assert stage.completion_criteria == ("criterion1", "criterion2")

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_invalid_stage_number_raises_error(self):
        """段階番号の範囲外エラーテスト"""
        with pytest.raises(ValueError, match="Stage number must be between 1 and 5"):
            PromptStage(
                stage_number=0,
                stage_name="無効段階",
                estimated_duration_minutes=15,
                required_elements=("element1",),
                completion_criteria=("criterion1",),
            )

        with pytest.raises(ValueError, match="Stage number must be between 1 and 5"):
            PromptStage(
                stage_number=6,
                stage_name="無効段階",
                estimated_duration_minutes=15,
                required_elements=("element1",),
                completion_criteria=("criterion1",),
            )

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_empty_stage_name_raises_error(self):
        """空の段階名エラーテスト"""
        with pytest.raises(ValueError, match="Stage name cannot be empty"):
            PromptStage(
                stage_number=1,
                stage_name="",
                estimated_duration_minutes=15,
                required_elements=("element1",),
                completion_criteria=("criterion1",),
            )

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_invalid_duration_raises_error(self):
        """無効な所要時間エラーテスト"""
        with pytest.raises(ValueError, match="Duration must be positive"):
            PromptStage(
                stage_number=1,
                stage_name="テスト段階",
                estimated_duration_minutes=0,
                required_elements=("element1",),
                completion_criteria=("criterion1",),
            )

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_empty_required_elements_raises_error(self):
        """空の必須要素エラーテスト"""
        with pytest.raises(ValueError, match="Required elements cannot be empty"):
            PromptStage(
                stage_number=1,
                stage_name="テスト段階",
                estimated_duration_minutes=15,
                required_elements=(),
                completion_criteria=("criterion1",),
            )

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_empty_completion_criteria_raises_error(self):
        """空の完了基準エラーテスト"""
        with pytest.raises(ValueError, match="Completion criteria cannot be empty"):
            PromptStage(
                stage_number=1,
                stage_name="テスト段階",
                estimated_duration_minutes=15,
                required_elements=("element1",),
                completion_criteria=(),
            )


class TestPromptStageImmutability:
    """不変性のテスト"""

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_stage_is_frozen(self):
        """段階オブジェクトの不変性テスト"""
        stage = PromptStage(
            stage_number=1,
            stage_name="テスト段階",
            estimated_duration_minutes=15,
            required_elements=["element1"],
            completion_criteria=["criterion1"],
        )

        # フリーズされたdataclassなので属性変更不可
        with pytest.raises(AttributeError):
            stage.stage_number = 2


class TestPromptStageMethods:
    """段階メソッドのテスト"""

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_is_basic_stage(self):
        """基本段階判定テスト"""
        stage1 = PromptStage.STAGE_1
        stage2 = PromptStage.STAGE_2
        stage3 = PromptStage.STAGE_3

        assert stage1.is_basic_stage()
        assert stage2.is_basic_stage()
        assert not stage3.is_basic_stage()

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_is_advanced_stage(self):
        """高度段階判定テスト"""
        stage3 = PromptStage.STAGE_3
        stage4 = PromptStage.STAGE_4
        stage5 = PromptStage.STAGE_5

        assert not stage3.is_advanced_stage()
        assert stage4.is_advanced_stage()
        assert stage5.is_advanced_stage()

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_get_quality_level_stars(self):
        """品質レベル表示テスト"""
        assert PromptStage.STAGE_1.get_quality_level_stars() == "⭐"
        assert PromptStage.STAGE_3.get_quality_level_stars() == "⭐⭐⭐"
        assert PromptStage.STAGE_5.get_quality_level_stars() == "⭐⭐⭐⭐⭐"

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_can_advance_to(self):
        """段階進行可能性判定テスト"""
        stage1 = PromptStage.STAGE_1
        stage2 = PromptStage.STAGE_2
        stage3 = PromptStage.STAGE_3

        assert stage1.can_advance_to(stage2)
        assert not stage1.can_advance_to(stage3)
        assert not stage2.can_advance_to(stage1)

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_can_rollback_to(self):
        """段階戻り可能性判定テスト"""
        stage1 = PromptStage.STAGE_1
        stage2 = PromptStage.STAGE_2
        stage3 = PromptStage.STAGE_3

        assert stage3.can_rollback_to(stage2)
        assert stage3.can_rollback_to(stage1)
        assert not stage1.can_rollback_to(stage2)


class TestPromptStageConstants:
    """段階定数のテスト"""

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_stage_constants_are_properly_initialized(self):
        """段階定数の適切な初期化テスト"""
        assert PromptStage.STAGE_1 is not None
        assert PromptStage.STAGE_2 is not None
        assert PromptStage.STAGE_3 is not None
        assert PromptStage.STAGE_4 is not None
        assert PromptStage.STAGE_5 is not None

        assert PromptStage.STAGE_1.stage_number == 1
        assert PromptStage.STAGE_2.stage_number == 2
        assert PromptStage.STAGE_3.stage_number == 3
        assert PromptStage.STAGE_4.stage_number == 4
        assert PromptStage.STAGE_5.stage_number == 5

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_stage_1_properties(self):
        """Stage 1定数のプロパティテスト"""
        stage1 = PromptStage.STAGE_1

        assert stage1.stage_name == "基本骨格設定"
        assert stage1.estimated_duration_minutes == 15
        assert "episode_number" in stage1.required_elements
        assert "title" in stage1.required_elements
        assert len(stage1.completion_criteria) > 0

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_stage_5_properties(self):
        """Stage 5定数のプロパティテスト"""
        stage5 = PromptStage.STAGE_5

        assert stage5.stage_name == "品質確認・完成"
        assert stage5.estimated_duration_minutes == 15
        assert "quality_metrics" in stage5.required_elements
        assert len(stage5.completion_criteria) > 0


class TestPromptStageUtilityFunctions:
    """ユーティリティ関数のテスト"""

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_get_all_stages(self):
        """全段階取得関数テスト"""
        stages = get_all_stages()

        assert len(stages) == 5
        assert stages[0] == PromptStage.STAGE_1
        assert stages[4] == PromptStage.STAGE_5

        # 順序確認
        for i, stage in enumerate(stages):
            assert stage.stage_number == i + 1

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_get_stage_by_number_valid(self):
        """番号による段階取得（正常値）テスト"""
        assert get_stage_by_number(1) == PromptStage.STAGE_1
        assert get_stage_by_number(3) == PromptStage.STAGE_3
        assert get_stage_by_number(5) == PromptStage.STAGE_5

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_get_stage_by_number_invalid(self):
        """番号による段階取得（無効値）テスト"""
        with pytest.raises(ValueError, match="Invalid stage number"):
            get_stage_by_number(0)

        with pytest.raises(ValueError, match="Invalid stage number"):
            get_stage_by_number(6)

        with pytest.raises(ValueError, match="Invalid stage number"):
            get_stage_by_number(-1)


class TestPromptStageEquality:
    """段階等価性のテスト"""

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_stage_equality(self):
        """段階等価性テスト"""
        stage1a = PromptStage(
            stage_number=1,
            stage_name="テスト段階",
            estimated_duration_minutes=15,
            required_elements=("element1",),
            completion_criteria=("criterion1",),
        )

        stage1b = PromptStage(
            stage_number=1,
            stage_name="テスト段階",
            estimated_duration_minutes=15,
            required_elements=("element1",),
            completion_criteria=("criterion1",),
        )

        stage2 = PromptStage(
            stage_number=2,
            stage_name="異なる段階",
            estimated_duration_minutes=20,
            required_elements=("element2",),
            completion_criteria=("criterion2",),
        )

        assert stage1a == stage1b
        assert stage1a != stage2
        assert hash(stage1a) == hash(stage1b)

    @pytest.mark.spec("SPEC-STAGED-001")
    def test_constant_stage_equality(self):
        """定数段階の等価性テスト"""
        assert PromptStage.STAGE_1 == PromptStage.STAGE_1
        assert PromptStage.STAGE_1 != PromptStage.STAGE_2

        # 同じ値で新規作成したオブジェクトとの比較
        new_stage1 = get_stage_by_number(1)
        assert new_stage1 == PromptStage.STAGE_1
