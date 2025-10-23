#!/usr/bin/env python3
"""B20開発段階Value Objectのテスト

仕様書: B20開発作業指示書準拠
"""

import pytest

from noveler.domain.value_objects.b20_development_stage import B20DevelopmentStage, DevelopmentStage, StageRequirement

pytestmark = pytest.mark.vo_smoke



class TestB20DevelopmentStage:
    """B20開発段階Value Objectのテスト"""

    @pytest.mark.spec("SPEC-B20_DEVELOPMENT_STAGE-CREATE_SPECIFICATION")
    def test_create_specification_stage(self):
        """仕様書作成段階の作成テスト"""
        stage = B20DevelopmentStage.create_specification_stage()

        assert stage.current_stage == DevelopmentStage.SPECIFICATION_REQUIRED
        assert len(stage.completed_requirements) == 0
        assert StageRequirement.SPEC_DOCUMENT_EXISTS in stage.pending_requirements
        assert "仕様書作成必須段階" in stage.stage_metadata["description"]

    @pytest.mark.spec("SPEC-B20_DEVELOPMENT_STAGE-CREATE_CODEMAP_CHECK")
    def test_create_codemap_check_stage(self):
        """CODEMAP確認段階の作成テスト"""
        stage = B20DevelopmentStage.create_codemap_check_stage()

        assert stage.current_stage == DevelopmentStage.CODEMAP_CHECK_REQUIRED
        assert StageRequirement.SPEC_DOCUMENT_EXISTS in stage.completed_requirements
        assert StageRequirement.CODEMAP_UPDATED in stage.pending_requirements
        assert StageRequirement.IMPORT_CONFLICTS_CHECKED in stage.pending_requirements

    @pytest.mark.spec("SPEC-B20_DEVELOPMENT_STAGE-CREATE_IMPLEMENTATIO")
    def test_create_implementation_stage(self):
        """実装許可段階の作成テスト"""
        stage = B20DevelopmentStage.create_implementation_stage()

        assert stage.current_stage == DevelopmentStage.IMPLEMENTATION_ALLOWED
        assert StageRequirement.SPEC_DOCUMENT_EXISTS in stage.completed_requirements
        assert StageRequirement.CODEMAP_UPDATED in stage.completed_requirements
        assert StageRequirement.TEST_IMPLEMENTATION_COMPLETED in stage.pending_requirements

    @pytest.mark.spec("SPEC-B20_DEVELOPMENT_STAGE-ADVANCE_TO_NEXT_STAG")
    def test_advance_to_next_stage(self):
        """次段階への進行テスト"""
        # 仕様書段階から開始
        stage = B20DevelopmentStage.create_specification_stage()

        # 仕様書完了で次段階へ進行
        next_stage = stage.advance_to_next_stage(StageRequirement.SPEC_DOCUMENT_EXISTS)

        assert next_stage.current_stage == DevelopmentStage.CODEMAP_CHECK_REQUIRED
        assert StageRequirement.SPEC_DOCUMENT_EXISTS in next_stage.completed_requirements
        assert StageRequirement.SPEC_DOCUMENT_EXISTS not in next_stage.pending_requirements

    @pytest.mark.spec("SPEC-B20_DEVELOPMENT_STAGE-ADVANCE_TO_NEXT_STAG")
    def test_advance_to_next_stage_invalid_requirement(self):
        """無効な要件での段階進行テスト"""
        stage = B20DevelopmentStage.create_specification_stage()

        # 未ペンディングの要件で進行を試行
        with pytest.raises(ValueError, match="要件が未ペンディング"):
            stage.advance_to_next_stage(StageRequirement.CODEMAP_UPDATED)

    @pytest.mark.spec("SPEC-B20_DEVELOPMENT_STAGE-GET_NEXT_REQUIRED_AC")
    def test_get_next_required_actions(self):
        """次に必要な作業項目の取得テスト"""
        stage = B20DevelopmentStage.create_specification_stage()
        actions = stage.get_next_required_actions()

        assert len(actions) > 0
        assert "仕様書の作成（specs/ディレクトリ）" in actions

    @pytest.mark.spec("SPEC-B20_DEVELOPMENT_STAGE-IS_IMPLEMENTATION_AL")
    def test_is_implementation_allowed(self):
        """実装許可状態の確認テスト"""
        # 仕様書段階では実装不可
        spec_stage = B20DevelopmentStage.create_specification_stage()
        assert not spec_stage.is_implementation_allowed()

        # 実装段階では実装可能
        impl_stage = B20DevelopmentStage.create_implementation_stage()
        assert impl_stage.is_implementation_allowed()

    @pytest.mark.spec("SPEC-B20_DEVELOPMENT_STAGE-IS_COMMIT_ALLOWED")
    def test_is_commit_allowed(self):
        """コミット許可状態の確認テスト"""
        # 実装段階ではコミット不可
        impl_stage = B20DevelopmentStage.create_implementation_stage()
        assert not impl_stage.is_commit_allowed()

        # 全要件完了でコミット許可段階になる
        all_completed = frozenset(
            [
                StageRequirement.SPEC_DOCUMENT_EXISTS,
                StageRequirement.CODEMAP_UPDATED,
                StageRequirement.IMPORT_CONFLICTS_CHECKED,
                StageRequirement.DDD_LAYER_PLACEMENT_VALIDATED,
                StageRequirement.EXISTING_IMPLEMENTATION_CHECKED,
                StageRequirement.TEST_IMPLEMENTATION_COMPLETED,
            ]
        )

        commit_stage = B20DevelopmentStage(
            current_stage=DevelopmentStage.COMMIT_ALLOWED,
            completed_requirements=all_completed,
            pending_requirements=frozenset(),
            stage_metadata={"test": True},
        )

        assert commit_stage.is_commit_allowed()

    @pytest.mark.spec("SPEC-B20_DEVELOPMENT_STAGE-GET_COMPLETION_PERCE")
    def test_get_completion_percentage(self):
        """完了率の計算テスト"""
        # 仕様書段階（0%完了）
        spec_stage = B20DevelopmentStage.create_specification_stage()
        assert spec_stage.get_completion_percentage() == 0.0

        # 1つの要件完了（約16.7%完了）
        one_completed = frozenset([StageRequirement.SPEC_DOCUMENT_EXISTS])
        partial_stage = B20DevelopmentStage(
            current_stage=DevelopmentStage.CODEMAP_CHECK_REQUIRED,
            completed_requirements=one_completed,
            pending_requirements=frozenset(
                [
                    StageRequirement.CODEMAP_UPDATED,
                    StageRequirement.IMPORT_CONFLICTS_CHECKED,
                    StageRequirement.DDD_LAYER_PLACEMENT_VALIDATED,
                    StageRequirement.EXISTING_IMPLEMENTATION_CHECKED,
                    StageRequirement.TEST_IMPLEMENTATION_COMPLETED,
                ]
            ),
            stage_metadata={"test": True},
        )

        completion = partial_stage.get_completion_percentage()
        assert 16.0 <= completion <= 17.0  # 約16.7%

    @pytest.mark.spec("SPEC-B20_DEVELOPMENT_STAGE-GET_STAGE_DESCRIPTIO")
    def test_get_stage_description(self):
        """段階説明の取得テスト"""
        stages_and_descriptions = [
            (DevelopmentStage.SPECIFICATION_REQUIRED, "仕様書作成が必要です"),
            (DevelopmentStage.CODEMAP_CHECK_REQUIRED, "CODEMAPの確認・更新が必要です"),
            (DevelopmentStage.IMPLEMENTATION_ALLOWED, "実装を開始できます"),
            (DevelopmentStage.COMMIT_ALLOWED, "コミットが許可されています"),
        ]

        for stage_enum, expected_desc in stages_and_descriptions:
            stage = B20DevelopmentStage(
                current_stage=stage_enum,
                completed_requirements=frozenset(),
                pending_requirements=frozenset(),
                stage_metadata={"test": True},
            )

            assert stage.get_stage_description() == expected_desc

    @pytest.mark.spec("SPEC-B20_DEVELOPMENT_STAGE-INITIALIZATION_VALID")
    def test_initialization_validation(self):
        """初期化時の検証テスト"""
        # 要件の重複エラー
        with pytest.raises(ValueError, match="要件の重複検出"):
            B20DevelopmentStage(
                current_stage=DevelopmentStage.SPECIFICATION_REQUIRED,
                completed_requirements=frozenset([StageRequirement.SPEC_DOCUMENT_EXISTS]),
                pending_requirements=frozenset([StageRequirement.SPEC_DOCUMENT_EXISTS]),  # 重複
                stage_metadata={"test": True},
            )

    @pytest.mark.spec("SPEC-B20_DEVELOPMENT_STAGE-STAGE_TRANSITION_LOG")
    def test_stage_transition_logic(self):
        """段階遷移ロジックのテスト"""
        # 仕様書 -> CODEMAP確認 -> 実装許可 -> コミット許可の流れをテスト
        stage = B20DevelopmentStage.create_specification_stage()

        # Step 1: 仕様書完了
        stage = stage.advance_to_next_stage(StageRequirement.SPEC_DOCUMENT_EXISTS)
        assert stage.current_stage == DevelopmentStage.CODEMAP_CHECK_REQUIRED

        # Step 2: CODEMAP関連の要件を順次完了
        requirements_to_complete = [
            StageRequirement.CODEMAP_UPDATED,
            StageRequirement.IMPORT_CONFLICTS_CHECKED,
            StageRequirement.DDD_LAYER_PLACEMENT_VALIDATED,
            StageRequirement.EXISTING_IMPLEMENTATION_CHECKED,
        ]

        for requirement in requirements_to_complete:
            stage = stage.advance_to_next_stage(requirement)

        assert stage.current_stage == DevelopmentStage.IMPLEMENTATION_ALLOWED

        # Step 3: テスト実装完了
        stage = stage.advance_to_next_stage(StageRequirement.TEST_IMPLEMENTATION_COMPLETED)
        assert stage.current_stage == DevelopmentStage.COMMIT_ALLOWED

    @pytest.mark.spec("SPEC-B20_DEVELOPMENT_STAGE-IMMUTABILITY")
    def test_immutability(self):
        """Value Objectの不変性テスト"""
        stage = B20DevelopmentStage.create_specification_stage()
        original_completed = stage.completed_requirements

        # 新しい段階を作成
        new_stage = stage.advance_to_next_stage(StageRequirement.SPEC_DOCUMENT_EXISTS)

        # 元のオブジェクトは変更されていないことを確認
        assert stage.completed_requirements == original_completed
        assert stage.current_stage == DevelopmentStage.SPECIFICATION_REQUIRED

        # 新しいオブジェクトは変更されていることを確認
        assert new_stage.completed_requirements != original_completed
        assert new_stage.current_stage != DevelopmentStage.SPECIFICATION_REQUIRED
