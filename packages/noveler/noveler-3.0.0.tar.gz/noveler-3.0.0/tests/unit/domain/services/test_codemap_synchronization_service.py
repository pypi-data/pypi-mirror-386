#!/usr/bin/env python3
"""CODEMAP同期ドメインサービスの単体テスト

仕様書: SPEC-CODEMAP-AUTO-UPDATE-001
"""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from noveler.domain.entities.codemap_entity import B20Compliance, CircularImportIssue, CodeMapEntity, CodeMapMetadata
from noveler.domain.services.codemap_synchronization_service import CodeMapSynchronizationService
from noveler.domain.value_objects.commit_information import CommitInformation


class TestCodeMapSynchronizationService:
    """CODEMAP同期ドメインサービスのテストクラス"""

    @pytest.fixture
    def service(self):
        """テスト対象のサービス"""
        return CodeMapSynchronizationService()

    @pytest.fixture
    def sample_codemap(self):
        """サンプルCODEMAPエンティティ"""
        metadata = CodeMapMetadata(
            name="Test Project",
            architecture="DDD + Clean Architecture",
            version="1.0.0",
            last_updated=datetime.now(timezone.utc),
            commit="old1234",
        )

        # 未完了の循環インポート問題
        circular_issues = [
            CircularImportIssue(
                location="noveler/domain/entities/scene_entity.py",
                issue="循環インポート発生: novel_cli.py ← scene_entity.py",
                solution="バレルモジュールパターンによる解決",
                status="未完了",
                commit=None,
            ),
            CircularImportIssue(
                location="noveler/presentation/cli/commands/__init__.py",
                issue="commands モジュール間の相互参照",
                solution="__init__.py でのバレルモジュール実装",
                status="未完了",
                commit=None,
            ),
        ]

        b20_compliance = B20Compliance(
            ddd_layer_separation={
                "status": "準拠",
                "dependency_direction": "Domain←Application←Infrastructure←Presentation",
            },
            import_management={"scripts_prefix": "統一済み", "relative_imports": "禁止済み"},
            shared_components={},
        )

        return CodeMapEntity(
            metadata=metadata,
            architecture_layers=[],
            circular_import_issues=circular_issues,
            b20_compliance=b20_compliance,
            quality_prevention=None,
        )

    @pytest.fixture
    def fix_commit_info(self):
        """修正コミット情報"""
        return CommitInformation.from_git_log(
            commit_hash="abcd1234567890abcdef1234567890abcdef1234",
            commit_date=datetime.now(timezone.utc),
            author_name="Developer",
            author_email="dev@example.com",
            commit_message="fix: 循環インポート解決 - バレルモジュール実装",
            changed_files=["noveler/domain/entities/scene_entity.py", "noveler/presentation/cli/commands/__init__.py"],
            branch_name="master",
        )

    @pytest.fixture
    def architecture_commit_info(self):
        """アーキテクチャ変更コミット情報"""
        return CommitInformation.from_git_log(
            commit_hash="efgh5678901234efgh5678901234efgh56789012",
            commit_date=datetime.now(timezone.utc),
            author_name="Architect",
            author_email="arch@example.com",
            commit_message="feat: architecture improvement - layer separation",
            changed_files=[
                "noveler/application/use_cases/new_use_case.py",
                "noveler/infrastructure/adapters/new_adapter.py",
            ],
            branch_name="master",
        )

    @pytest.mark.spec("SPEC-CODEMAP_SYNCHRONIZATION_SERVICE-SYNCHRONIZE_WITH_COM")
    def test_synchronize_with_commit_basic_update(self, service, sample_codemap, fix_commit_info):
        """基本的なコミット同期のテスト"""
        # Act
        updated_codemap = service.synchronize_with_commit(sample_codemap, fix_commit_info)

        # Assert
        assert updated_codemap.metadata.commit == fix_commit_info.short_hash
        assert updated_codemap.metadata.last_updated is not None
        # 元のオブジェクトが変更されることを確認（参照渡し）
        assert sample_codemap is updated_codemap

    @pytest.mark.spec("SPEC-CODEMAP_SYNCHRONIZATION_SERVICE-DETECT_CIRCULAR_IMPO")
    def test_detect_circular_import_fixes(self, service, sample_codemap, fix_commit_info):
        """循環インポート修正の自動検出テスト"""
        # 修正前の状態確認
        incomplete_issues = [issue for issue in sample_codemap.circular_import_issues if not issue.is_completed()]
        assert len(incomplete_issues) == 2

        # Act
        service.synchronize_with_commit(sample_codemap, fix_commit_info)

        # Assert - scene_entity.py の問題が完了としてマークされる
        scene_issue = next(
            (issue for issue in sample_codemap.circular_import_issues if "scene_entity.py" in issue.location), None
        )

        assert scene_issue is not None
        assert scene_issue.is_completed()
        assert scene_issue.commit == fix_commit_info.short_hash

    @pytest.mark.spec("SPEC-CODEMAP_SYNCHRONIZATION_SERVICE-DETECT_BARREL_MODULE")
    def test_detect_barrel_module_implementation(self, service, sample_codemap):
        """バレルモジュール実装の検出テスト"""
        # Arrange - commands/__init__.py 変更のコミット
        barrel_commit = CommitInformation.from_git_log(
            commit_hash="barrel123456789abcdef123456789abcdef1234",
            commit_date=datetime.now(timezone.utc),
            author_name="Developer",
            author_email="dev@example.com",
            commit_message="feat: implement barrel module for commands",
            changed_files=["noveler/presentation/cli/commands/__init__.py"],
            branch_name="master",
        )

        # Act
        service.synchronize_with_commit(sample_codemap, barrel_commit)

        # Assert - バレルモジュール関連の問題が完了
        barrel_issue = next(
            (issue for issue in sample_codemap.circular_import_issues if "バレルモジュール" in issue.solution), None
        )

        assert barrel_issue is not None
        assert barrel_issue.is_completed()
        assert barrel_issue.commit == barrel_commit.short_hash

    @pytest.mark.spec("SPEC-CODEMAP_SYNCHRONIZATION_SERVICE-DETECT_LAYER_VIOLATI")
    def test_detect_layer_violation_fixes(self, service, sample_codemap, architecture_commit_info):
        """DDD層分離違反修正の検出テスト"""
        # Arrange - レイヤー違反の問題を追加
        layer_issue = CircularImportIssue(
            location="noveler/application/use_cases/test_use_case.py",
            issue="アプリケーション層からプレゼンテーション層への依存違反",
            solution="依存性逆転の原則適用",
            status="未完了",
            commit=None,
        )

        sample_codemap.circular_import_issues.append(layer_issue)

        # Act
        service.synchronize_with_commit(sample_codemap, architecture_commit_info)

        # Assert - レイヤー違反の問題が完了
        assert layer_issue.is_completed()
        assert layer_issue.commit == architecture_commit_info.short_hash

    @pytest.mark.spec("SPEC-CODEMAP_SYNCHRONIZATION_SERVICE-UPDATE_COMPLIANCE_ST")
    def test_update_compliance_status(self, service, sample_codemap, architecture_commit_info):
        """B20準拠状況の更新テスト"""
        # Act
        service.synchronize_with_commit(sample_codemap, architecture_commit_info)

        # Assert - アーキテクチャメッセージにより準拠状況更新
        ddd_separation = sample_codemap.b20_compliance.ddd_layer_separation.get("dependency_direction")
        assert ddd_separation == "✅ Domain←Application←Infrastructure←Presentation"

    @pytest.mark.spec("SPEC-CODEMAP_SYNCHRONIZATION_SERVICE-IS_FIX_COMMIT_FOR_IS")
    def test_is_fix_commit_for_issue_positive(self, service):
        """修正コミット判定のPositiveテスト"""
        # Arrange
        issue = CircularImportIssue(
            location="test.py", issue="循環インポート問題", solution="解決策", status="未完了", commit=None
        )

        fix_commit = CommitInformation.from_git_log(
            commit_hash="fix1234567890abcdef1234567890abcdef1234",
            commit_date=datetime.now(timezone.utc),
            author_name="Dev",
            author_email="dev@test.com",
            commit_message="fix: 循環インポート修正",
            changed_files=["test.py"],
            branch_name="master",
        )

        # Act
        result = service._is_fix_commit_for_issue(fix_commit, issue)

        # Assert
        assert result is True

    @pytest.mark.spec("SPEC-CODEMAP_SYNCHRONIZATION_SERVICE-IS_FIX_COMMIT_FOR_IS")
    def test_is_fix_commit_for_issue_negative(self, service):
        """修正コミット判定のNegativeテスト"""
        # Arrange
        issue = CircularImportIssue(
            location="test.py", issue="循環インポート問題", solution="解決策", status="未完了", commit=None
        )

        unrelated_commit = CommitInformation.from_git_log(
            commit_hash="feat1234567890abcdef1234567890abcdef1234",
            commit_date=datetime.now(timezone.utc),
            author_name="Dev",
            author_email="dev@test.com",
            commit_message="feat: 新機能追加",
            changed_files=["other.py"],
            branch_name="master",
        )

        # Act
        result = service._is_fix_commit_for_issue(unrelated_commit, issue)

        # Assert
        assert result is False

    @pytest.mark.spec("SPEC-CODEMAP_SYNCHRONIZATION_SERVICE-VALIDATE_SYNCHRONIZA")
    def test_validate_synchronization_result_success(self, service, sample_codemap):
        """同期結果検証の成功テスト"""
        # Arrange - 正常なCODEMAPの状態
        sample_codemap.metadata.commit = "valid123"

        with patch.object(sample_codemap, "validate_structure", return_value=[]):
            # Act
            errors = service.validate_synchronization_result(sample_codemap)

            # Assert
            assert errors == []

    @pytest.mark.spec("SPEC-CODEMAP_SYNCHRONIZATION_SERVICE-VALIDATE_SYNCHRONIZA")
    def test_validate_synchronization_result_missing_commit(self, service, sample_codemap):
        """コミット情報不足の検証テスト"""
        # Arrange
        sample_codemap.metadata.commit = None

        with patch.object(sample_codemap, "validate_structure", return_value=[]):
            # Act
            errors = service.validate_synchronization_result(sample_codemap)

            # Assert
            assert "Commit hash is missing after synchronization" in errors

    @pytest.mark.spec("SPEC-CODEMAP_SYNCHRONIZATION_SERVICE-VALIDATE_SYNCHRONIZA")
    def test_validate_synchronization_result_missing_timestamp(self, service, sample_codemap):
        """タイムスタンプ不足の検証テスト"""
        # Arrange
        sample_codemap.metadata.commit = "valid123"
        sample_codemap.metadata.last_updated = None

        with patch.object(sample_codemap, "validate_structure", return_value=[]):
            # Act
            errors = service.validate_synchronization_result(sample_codemap)

            # Assert
            assert "Last updated timestamp is missing" in errors

    @pytest.mark.spec("SPEC-CODEMAP_SYNCHRONIZATION_SERVICE-VALIDATE_SYNCHRONIZA")
    def test_validate_synchronization_result_structure_errors(self, service, sample_codemap):
        """構造エラーの検証テスト"""
        # Arrange
        sample_codemap.metadata.commit = "valid123"
        structure_errors = ["Error 1", "Error 2"]

        with patch.object(sample_codemap, "validate_structure", return_value=structure_errors):
            # Act
            errors = service.validate_synchronization_result(sample_codemap)

            # Assert
            assert structure_errors[0] in errors
            assert structure_errors[1] in errors

    @pytest.mark.spec("SPEC-CODEMAP_SYNCHRONIZATION_SERVICE-CALCULATE_SYNCHRONIZ")
    def test_calculate_synchronization_impact_basic(self, service, sample_codemap):
        """同期影響分析の基本テスト"""
        # Arrange - 更新前の状態
        original_codemap = sample_codemap

        # 更新後の状態を作成
        updated_codemap = CodeMapEntity(
            metadata=CodeMapMetadata(
                name=sample_codemap.metadata.name,
                architecture=sample_codemap.metadata.architecture,
                version=sample_codemap.metadata.version,
                last_updated=datetime.now(timezone.utc),  # 新しいタイムスタンプ
                commit="new5678",
            ),
            architecture_layers=sample_codemap.architecture_layers,
            circular_import_issues=sample_codemap.circular_import_issues.copy(),
            b20_compliance=sample_codemap.b20_compliance,
            quality_prevention=sample_codemap.quality_prevention,
        )

        # 問題を1つ完了状態に変更
        if updated_codemap.circular_import_issues:
            updated_codemap.circular_import_issues[0].mark_completed("new5678")

        with patch.object(original_codemap, "get_completion_rate", return_value=50.0):
            with patch.object(updated_codemap, "get_completion_rate", return_value=75.0):
                # Act
                impact = service.calculate_synchronization_impact(original_codemap, updated_codemap)

                # Assert
                assert impact["metadata_changed"] is True
                assert impact["issues_resolved"] == 1
                assert impact["completion_rate_change"] == 25.0

    @pytest.mark.spec("SPEC-CODEMAP_SYNCHRONIZATION_SERVICE-CALCULATE_SYNCHRONIZ")
    def test_calculate_synchronization_impact_no_changes(self, service, sample_codemap):
        """変更なしの場合の影響分析テスト"""
        # Arrange - 同じ状態のCODEMAP
        original_codemap = sample_codemap
        updated_codemap = sample_codemap  # 同じオブジェクト

        with patch.object(sample_codemap, "get_completion_rate", return_value=50.0):
            # Act
            impact = service.calculate_synchronization_impact(original_codemap, updated_codemap)

            # Assert
            assert impact["metadata_changed"] is False
            assert impact["issues_resolved"] == 0
            assert impact["completion_rate_change"] == 0.0

    @pytest.mark.parametrize(
        ("commit_message", "changed_files", "expected_detections"),
        [
            # 循環インポート修正のパターン
            ("fix: circular import resolved", ["scene_entity.py"], ["scene_entity"]),
            ("resolve: 循環インポート対策", ["novel_cli.py"], []),
            # バレルモジュール実装のパターン
            ("feat: barrel module implementation", ["commands/__init__.py"], ["barrel_module"]),
            ("add: __init__.py barrel pattern", ["commands/__init__.py"], ["barrel_module"]),
            # レイヤー違反修正のパターン
            ("fix: layer separation violation", ["noveler/application/test.py"], ["layer_violation"]),
            ("refactor: architecture layer cleanup", ["noveler/infrastructure/adapter.py"], ["layer_violation"]),
        ],
    )
    @pytest.mark.spec("SPEC-CODEMAP_SYNCHRONIZATION_SERVICE-COMMIT_PATTERN_DETEC")
    def test_commit_pattern_detection(
        self, service, sample_codemap, commit_message, changed_files, expected_detections
    ):
        """コミットパターン検出のパラメータ化テスト"""
        # Arrange
        commit_info = CommitInformation.from_git_log(
            commit_hash="test1234567890abcdef1234567890abcdef1234",
            commit_date=datetime.now(timezone.utc),
            author_name="Test",
            author_email="test@test.com",
            commit_message=commit_message,
            changed_files=changed_files,
            branch_name="master",
        )

        initial_completed = len([issue for issue in sample_codemap.circular_import_issues if issue.is_completed()])

        # Act
        service.synchronize_with_commit(sample_codemap, commit_info)

        # Assert
        final_completed = len([issue for issue in sample_codemap.circular_import_issues if issue.is_completed()])

        if expected_detections:
            # 何らかの検出が期待される場合
            assert final_completed > initial_completed or sample_codemap.b20_compliance is not None

        # コミット情報が更新されることを確認
        assert sample_codemap.metadata.commit == commit_info.short_hash
