#!/usr/bin/env python3
"""B20実装着手前チェック管理サービステスト

仕様書: B20開発作業指示書準拠
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noveler.domain.services.b20_pre_implementation_check_service import (
    B20PreImplementationCheckService,
    ConflictAnalysisResult,
    PreImplementationCheckResult,
)
from noveler.domain.value_objects.b20_development_stage import DevelopmentStage, StageRequirement


class TestB20PreImplementationCheckService:
    """B20実装着手前チェック管理サービステスト"""

    @pytest.fixture
    def temp_project_root(self):
        """一時プロジェクトルートディレクトリ"""
        temp_dir = Path(tempfile.mkdtemp())

        # 基本的なディレクトリ構造を作成
        (temp_dir / "specs").mkdir()
        (temp_dir / "scripts").mkdir()
        (temp_dir / "scripts" / "domain").mkdir()
        (temp_dir / "scripts" / "application").mkdir()
        (temp_dir / "scripts" / "infrastructure").mkdir()
        (temp_dir / "scripts" / "presentation").mkdir()

        yield temp_dir

        # クリーンアップ
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def check_service(self, temp_project_root):
        """テスト用チェックサービス"""
        return B20PreImplementationCheckService(temp_project_root)

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-INITIALIZATION")
    def test_initialization(self, temp_project_root):
        """初期化テスト"""
        service = B20PreImplementationCheckService(temp_project_root)

        assert service.project_root == temp_project_root
        assert service.logger is not None

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-EXECUTE_PRE_IMPLEMEN")
    def test_execute_pre_implementation_check_with_spec(self, check_service, temp_project_root):
        """仕様書が存在する場合の実装着手前チェックテスト"""
        # 仕様書作成
        spec_file = temp_project_root / "specs" / "SPEC-TEST-FEATURE-001.md"
        spec_file.write_text("# Test Feature Specification\n\n## Overview\nTest feature description")
        # CODEMAP作成
        codemap_file = temp_project_root / "CODEMAP.yaml"
        codemap_file.write_text("project_structure:\n  name: test_project")

        result = check_service.execute_pre_implementation_check(feature_name="test_feature", target_layer="domain")

        assert isinstance(result, PreImplementationCheckResult)
        assert result.current_stage in [
            DevelopmentStage.CODEMAP_CHECK_REQUIRED,
            DevelopmentStage.IMPLEMENTATION_ALLOWED,
        ]
        assert result.completion_percentage >= 0.0
        assert isinstance(result.next_required_actions, list)

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-EXECUTE_PRE_IMPLEMEN")
    def test_execute_pre_implementation_check_without_spec(self, check_service, temp_project_root):
        """仕様書が存在しない場合の実装着手前チェックテスト"""
        result = check_service.execute_pre_implementation_check(
            feature_name="nonexistent_feature", target_layer="domain"
        )

        assert isinstance(result, PreImplementationCheckResult)
        assert not result.is_implementation_allowed
        assert result.current_stage == DevelopmentStage.SPECIFICATION_REQUIRED
        assert len(result.errors) > 0
        assert any("仕様書が見つかりません" in error for error in result.errors)

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-CHECK_SPECIFICATION_")
    def test_check_specification_requirement_exists(self, check_service, temp_project_root):
        """仕様書要件チェック（存在する場合）"""
        # 仕様書作成
        spec_file = temp_project_root / "specs" / "SPEC-TEST-001.md"
        spec_file.write_text("# Test Specification\n\n## Requirements\n- Test requirement")
        result = check_service._check_specification_requirement("TEST")

        assert result["exists"] is True
        assert len(result["spec_files"]) > 0
        assert str(spec_file) in result["spec_files"]

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-CHECK_SPECIFICATION_")
    def test_check_specification_requirement_not_exists(self, check_service):
        """仕様書要件チェック（存在しない場合）"""
        result = check_service._check_specification_requirement("NONEXISTENT")

        assert result["exists"] is False
        assert len(result["spec_files"]) == 0

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-CHECK_SPECIFICATION_")
    def test_check_specification_requirement_too_small(self, check_service, temp_project_root):
        """仕様書要件チェック（ファイルが小さすぎる場合）"""
        # 小さな仕様書作成
        spec_file = temp_project_root / "specs" / "SPEC-SMALL-001.md"
        spec_file.write_text("# Small")  # 100バイト未満

        result = check_service._check_specification_requirement("SMALL")

        assert result["exists"] is True
        assert result["has_warnings"] is True
        assert any("仕様書が短すぎます" in warning for warning in result["warnings"])

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-CHECK_CODEMAP_REQUIR")
    def test_check_codemap_requirements_exists(self, check_service, temp_project_root):
        """CODEMAP要件チェック（存在する場合）"""
        # CODEMAP作成
        codemap_file = temp_project_root / "CODEMAP.yaml"
        codemap_file.write_text("project_structure:\n  name: test")

        result = check_service._check_codemap_requirements()

        assert result["exists"] is True
        assert result["is_up_to_date"] is True  # 実装時により詳細な検証を追加

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-CHECK_CODEMAP_REQUIR")
    def test_check_codemap_requirements_not_exists(self, check_service):
        """CODEMAP要件チェック（存在しない場合）"""
        result = check_service._check_codemap_requirements()

        assert result["exists"] is False
        assert result["is_up_to_date"] is False
        assert result["needs_update"] is True

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-ANALYZE_IMPLEMENTATI")
    def test_analyze_implementation_conflicts(self, check_service, temp_project_root):
        """実装競合分析テスト"""
        result = check_service._analyze_implementation_conflicts(
            feature_name="test_feature", target_layer="domain", implementation_path=None
        )

        assert isinstance(result, ConflictAnalysisResult)
        assert isinstance(result.has_import_conflicts, bool)
        assert isinstance(result.import_conflict_details, list)
        assert isinstance(result.has_ddd_layer_violations, bool)
        assert isinstance(result.ddd_violation_details, list)

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-CHECK_DDD_LAYER_VIOL")
    def test_check_ddd_layer_violations_invalid_layer(self, check_service):
        """DDD層違反チェック（無効な層）"""
        violations = check_service._check_ddd_layer_violations("invalid_layer", None)

        assert len(violations) > 0
        assert any("無効な対象層" in violation for violation in violations)

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-CHECK_DDD_LAYER_VIOL")
    def test_check_ddd_layer_violations_valid_layer(self, check_service):
        """DDD層違反チェック（有効な層）"""
        valid_layers = ["domain", "application", "infrastructure", "presentation"]

        for layer in valid_layers:
            violations = check_service._check_ddd_layer_violations(layer, None)
            # 有効な層では層名に関するエラーはない
            assert not any("無効な対象層" in violation for violation in violations)

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-CHECK_EXISTING_IMPLE")
    def test_check_existing_implementation_conflicts(self, check_service, temp_project_root):
        """既存実装競合チェック"""
        # 類似ファイル作成
        domain_dir = temp_project_root / "scripts" / "domain"
        similar_file = domain_dir / "test_feature_entity.py"
        similar_file.write_text("# Existing implementation")
        conflicts = check_service._check_existing_implementation_conflicts("test_feature", "domain")

        assert len(conflicts) > 0
        assert any("類似ファイル存在" in conflict for conflict in conflicts)

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-CHECK_TEST_IMPLEMENT")
    def test_check_test_implementation_completed_exists(self, check_service, temp_project_root):
        """テスト実装完了チェック（存在する場合）"""
        # テストファイル作成
        test_file = temp_project_root / "test_feature_test.py"
        test_file.write_text("# Test implementation")
        result = check_service._check_test_implementation_completed("feature")

        assert result is True

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-CHECK_TEST_IMPLEMENT")
    def test_check_test_implementation_completed_not_exists(self, check_service):
        """テスト実装完了チェック（存在しない場合）"""
        result = check_service._check_test_implementation_completed("nonexistent_feature")

        assert result is False

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-ANALYZE_CURRENT_DEVE")
    def test_analyze_current_development_stage_no_spec(self, check_service):
        """現在の開発段階分析（仕様書なし）"""
        stage = check_service._analyze_current_development_stage("no_spec_feature")

        assert stage.current_stage == DevelopmentStage.SPECIFICATION_REQUIRED
        assert StageRequirement.SPEC_DOCUMENT_EXISTS in stage.pending_requirements

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-ANALYZE_CURRENT_DEVE")
    def test_analyze_current_development_stage_with_spec(self, check_service, temp_project_root):
        """現在の開発段階分析（仕様書あり）"""
        # 仕様書作成
        spec_file = temp_project_root / "specs" / "SPEC-WITH-SPEC-001.md"
        spec_file.write_text("# Feature with spec\n\n## Description\nTest feature")
        stage = check_service._analyze_current_development_stage("with_spec")

        assert stage.current_stage in [DevelopmentStage.CODEMAP_CHECK_REQUIRED, DevelopmentStage.IMPLEMENTATION_ALLOWED]
        assert StageRequirement.SPEC_DOCUMENT_EXISTS in stage.completed_requirements

    @patch("noveler.domain.services.b20_pre_implementation_check_service.NullLoggerService")
    def test_logging_integration(self, mock_null_logger, temp_project_root):
        """ログ統合テスト"""
        mock_logger = Mock()
        mock_null_logger.return_value = mock_logger

        service = B20PreImplementationCheckService(temp_project_root)

        # ログの実行
        service.execute_pre_implementation_check(feature_name="test_logging", target_layer="domain")

        # ログメソッドが呼ばれたことを確認
        mock_logger.info.assert_called()

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-EDGE_CASE_EMPTY_FEAT")
    def test_edge_case_empty_feature_name(self, check_service):
        """エッジケース: 空の機能名"""
        result = check_service.execute_pre_implementation_check(feature_name="", target_layer="domain")

        assert isinstance(result, PreImplementationCheckResult)
        assert not result.is_implementation_allowed

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-EDGE_CASE_SPECIAL_CH")
    def test_edge_case_special_characters_in_feature_name(self, check_service, temp_project_root):
        """エッジケース: 特殊文字を含む機能名"""
        feature_name = "test-feature_with.special@chars"

        # 対応する仕様書作成
        spec_file = temp_project_root / "specs" / f"SPEC-{feature_name}-001.md"
        spec_file.write_text("# Special chars feature")
        result = check_service.execute_pre_implementation_check(feature_name=feature_name, target_layer="domain")

        assert isinstance(result, PreImplementationCheckResult)

    @pytest.mark.spec("SPEC-B20_PRE_IMPLEMENTATION_CHECK_SERVICE-PERFORMANCE_WITH_LAR")
    def test_performance_with_large_project(self, check_service, temp_project_root):
        """パフォーマンステスト: 大きなプロジェクト"""
        # 多数のファイル作成
        for i in range(100):
            test_file = temp_project_root / "scripts" / "domain" / f"entity_{i}.py"
            test_file.write_text(f"# Entity {i}")
        # パフォーマンス測定
        import time

        start_time = time.time()

        result = check_service.execute_pre_implementation_check(feature_name="performance_test", target_layer="domain")

        execution_time = time.time() - start_time

        # 合理的な実行時間内であることを確認（5秒以内）
        assert execution_time < 5.0
        assert isinstance(result, PreImplementationCheckResult)
